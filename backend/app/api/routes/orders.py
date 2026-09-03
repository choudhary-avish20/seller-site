import html
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.auth import create_verification_token
from app.db.session import get_db
from app.api.routes.coupons import get_valid_coupon
from app.models.coupon import Coupon
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.order_item import OrderItem
from app.models.product import Product, StockStatus
from app.models.product_variant import ProductVariant
from app.models.product_price_tier import ProductPriceTier
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.email import send_verification_email, send_order_confirmation_email, send_order_status_email

router = APIRouter(prefix="/orders", tags=["orders"])


def _require_buyer(user: User) -> User:
    # All authenticated roles can place orders: buyers, sellers (store owner), and admins.
    # Sellers/admins bypass the buyer-approval check entirely.
    if user.role == UserRole.buyer and settings.REQUIRE_BUYER_APPROVAL:
        val = user.buyer_status.value if hasattr(user.buyer_status, 'value') else str(user.buyer_status)
        if val != 'approved':
            raise HTTPException(
                status_code=403,
                detail=f"Buyer account not approved (status: {val}). Admin must verify before buying.",
            )
    return user


def _base_price(product: Product) -> float:
    """Regular net price, or the active sale price when the product is on sale."""
    if product.is_on_sale and product.sale_price_net is not None:
        return float(product.sale_price_net)
    return float(product.price_net)


def _tiered_price(product: Product, quantity: int, db: Session) -> float:
    tiers = db.query(ProductPriceTier).filter(ProductPriceTier.product_id == product.id).order_by(ProductPriceTier.min_quantity).all()
    if not tiers:
        return _base_price(product)
    for t in tiers:
        max_q = t.max_quantity if t.max_quantity is not None else float('inf')
        if t.min_quantity <= quantity <= max_q:
            return float(t.price_net)
    if quantity > tiers[-1].min_quantity:
        return float(tiers[-1].price_net)
    return _base_price(product)


def _atomic_decrement_stock(db: Session, model, obj_id, quantity: int, label: str) -> None:
    """Decrement stock in a single guarded UPDATE so two concurrent orders for the
    same product can't both pass a check-then-act stock check and oversell it."""
    result = db.execute(
        sa_update(model)
        .where(model.id == obj_id, model.stock_quantity >= quantity)
        .values(stock_quantity=model.stock_quantity - quantity)
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock for {label} changed while placing your order. Please review your cart and try again.",
        )


def _restore_stock_for_order(db: Session, order: Order) -> None:
    """Return reserved stock to inventory when an order is cancelled, undoing the
    decrement applied at order-creation time."""
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for item in items:
        db.execute(
            sa_update(Product)
            .where(Product.id == item.product_id)
            .values(stock_quantity=Product.stock_quantity + item.pack_quantity)
        )
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            db.refresh(product)
            if product.stock_quantity > 0:
                product.stock_status = StockStatus.in_stock
        if item.variant_id:
            db.execute(
                sa_update(ProductVariant)
                .where(ProductVariant.id == item.variant_id)
                .values(stock_quantity=ProductVariant.stock_quantity + item.pack_quantity)
            )


def _redact_cost_price(resp: OrderResponse, viewer: User) -> OrderResponse:
    """Cost price is internal margin data — never show it to the buyer who placed the order."""
    if viewer.role == UserRole.buyer:
        for item in resp.items:
            item.cost_price_snapshot = None
    return resp


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_buyer(current_user)

    # Check email verification - only enforce for buyer users (admin/seller bypass)
    if current_user.role == UserRole.buyer and not current_user.email_verified:
        try:
            # Auto-resend verification email
            verification_token = create_verification_token(db, current_user)
            await send_verification_email(current_user.email, current_user.full_name, verification_token)
            db.commit()
        except Exception as e:
            # Log error but don't fail the verification check
            import logging
            logging.getLogger(__name__).error(f"Failed to resend verification email to {current_user.email}: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address. A new verification link has been sent.",
        )

    if settings.ALLOW_CASH_ON_DELIVERY_ONLY and payload.payment_method != PaymentMethod.cod:
        raise HTTPException(status_code=400, detail="Only cash on delivery (COD) is allowed")

    # Validate required company/recipient info for COD (account must submit required information)
    # For COD, require at least company_name or recipient_name and shipping address
    if not payload.company_name and not current_user.company_name:
        # allow if either payload has company or user has company, but require one
        pass  # not strict for MVP, but warn
    # If buyer has no company info and payload also no company, still allow but frontend will require

    total_net = 0.0
    total_gross = 0.0
    items_to_create = []

    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"Product {product.name} is archived")
        if product.stock_status == StockStatus.out_of_stock:
            raise HTTPException(status_code=400, detail=f"Product {product.name} out of stock")
        # pack increment validation (e.g. +12 or +40)
        inc = product.pack_increment or 1
        if item.pack_quantity % inc != 0:
            raise HTTPException(status_code=400, detail=f"Product {product.name} must be ordered in increments of {inc} packs (got {item.pack_quantity})")
        if product.stock_quantity < item.pack_quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}: {product.stock_quantity} packs available")

        variant = None
        # tiered pricing: use quantity to get price_net
        price_net = _tiered_price(product, item.pack_quantity, db)
        price_gross = round(price_net * (1 + float(product.vat_rate) / 100), 2)
        if item.variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id, ProductVariant.product_id == product.id).first()
            if not variant:
                raise HTTPException(status_code=404, detail=f"Variant {item.variant_id} not found for product {product.name}")
            if variant.stock_quantity < item.pack_quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient variant stock for {product.name} ({variant.option_value})")
            if variant.price_net_override is not None:
                price_net = float(variant.price_net_override)
                price_gross = round(price_net * (1 + float(product.vat_rate) / 100), 2)

        line_net = price_net * item.pack_quantity
        line_gross = price_gross * item.pack_quantity
        total_net += line_net
        total_gross += line_gross

        items_to_create.append({
            "product": product,
            "variant": variant,
            "pack_quantity": item.pack_quantity,
            "price_net": price_net,
            "price_gross": price_gross,
        })

    coupon: Coupon | None = None
    discount_amount = 0.0
    if payload.coupon_code:
        coupon, discount_amount, coupon_error = get_valid_coupon(db, payload.coupon_code, total_net)
        if coupon_error:
            raise HTTPException(status_code=400, detail=coupon_error)
        if discount_amount > 0 and total_net > 0:
            total_gross = round(total_gross - (discount_amount / total_net) * total_gross, 2)
        total_net = round(total_net - discount_amount, 2)

    order = Order(
        buyer_id=current_user.id,
        status=OrderStatus.pending,
        total_net=round(total_net, 2),
        total_gross=round(total_gross, 2),
        coupon_code=coupon.code if coupon else None,
        discount_amount=discount_amount,
        shipping_address=payload.shipping_address.strip(),
        notes=payload.notes.strip() if payload.notes else None,
        company_name=payload.company_name.strip() if payload.company_name else current_user.company_name,
        company_tax_id=payload.company_tax_id.strip() if payload.company_tax_id else current_user.company_tax_id,
        company_address=payload.company_address.strip() if payload.company_address else current_user.company_address,
        recipient_name=payload.recipient_name.strip() if payload.recipient_name else current_user.full_name,
        recipient_phone=payload.recipient_phone.strip() if payload.recipient_phone else current_user.phone,
        recipient_address=payload.recipient_address.strip() if payload.recipient_address else payload.shipping_address.strip(),
        payment_method=payload.payment_method,
    )
    db.add(order)
    db.flush()

    if coupon:
        coupon.used_count += 1

    for entry in items_to_create:
        p = entry["product"]
        oi = OrderItem(
            order_id=order.id,
            product_id=p.id,
            variant_id=entry["variant"].id if entry["variant"] else None,
            product_name_snapshot=p.name,
            pack_size_snapshot=p.pack_size,
            price_net_snapshot=entry["price_net"],
            price_gross_snapshot=entry["price_gross"],
            pack_quantity=entry["pack_quantity"],
            cost_price_snapshot=float(p.cost_price) if p.cost_price is not None else None,
            stall_location_snapshot=p.stall_location,
            counter_number_snapshot=p.counter_number,
        )
        db.add(oi)
        _atomic_decrement_stock(db, Product, p.id, entry["pack_quantity"], p.name)
        if entry["variant"]:
            v = entry["variant"]
            _atomic_decrement_stock(db, ProductVariant, v.id, entry["pack_quantity"], f"{p.name} ({v.option_value})")

    for entry in items_to_create:
        p = entry["product"]
        db.refresh(p)
        if p.stock_quantity == 0:
            p.stock_status = StockStatus.out_of_stock

    db.commit()
    db.refresh(order)
    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    resp = OrderResponse.model_validate(order)
    _redact_cost_price(resp, current_user)

    # Send order confirmation email (fire-and-forget, don't block response on email failure)
    try:
        await send_order_confirmation_email(current_user.email, current_user.full_name, resp)
    except Exception as e:
        # Log the error but don't fail the order creation
        import logging
        logging.getLogger(__name__).error(f"Failed to send order confirmation email to {current_user.email}: {e}")

    return resp


@router.get("", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Order)
    if current_user.role in (UserRole.admin, UserRole.seller):
        # Staff always see every order regardless of hidden_by_buyer — that flag
        # only controls the buyer's own list, never the seller's records.
        orders = q.order_by(Order.created_at.desc()).all()
    else:
        orders = (
            db.query(Order)
            .filter(Order.buyer_id == current_user.id, Order.hidden_by_buyer.is_(False))
            .order_by(Order.created_at.desc())
            .all()
        )

    # Collect all buyer ids and fetch in one query to avoid N+1
    buyer_ids = list({o.buyer_id for o in orders})
    buyers = {u.id: u for u in db.query(User).filter(User.id.in_(buyer_ids)).all()} if buyer_ids else {}

    result = []
    for o in orders:
        o.items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
        resp = OrderResponse.model_validate(o)
        buyer = buyers.get(o.buyer_id)
        if buyer and current_user.role in (UserRole.admin, UserRole.seller):
            resp.buyer_email = buyer.email
            resp.buyer_full_name = buyer.full_name
        result.append(_redact_cost_price(resp, current_user))
    return result


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role == UserRole.buyer and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    resp = OrderResponse.model_validate(order)
    return _redact_cost_price(resp, current_user)


# Linear fulfillment flow; delivered/cancelled are terminal. Enforced server-side so the
# API can't be pushed into a nonsensical state even by staff, regardless of what the UI sends.
_ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
    OrderStatus.confirmed: {OrderStatus.shipped, OrderStatus.cancelled},
    OrderStatus.shipped: {OrderStatus.delivered, OrderStatus.cancelled},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seller/admin can advance an order through the fulfillment flow or cancel it.
    Buyer can only cancel their own pending order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.buyer:
        if order.buyer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if payload.status != OrderStatus.cancelled:
            raise HTTPException(status_code=403, detail="Buyers can only cancel orders")
        if order.status != OrderStatus.pending:
            raise HTTPException(status_code=400, detail="Only pending orders can be cancelled")
    elif payload.status not in _ALLOWED_STATUS_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from '{order.status.value}' to '{payload.status.value}'",
        )

    old_status = order.status
    if payload.status == OrderStatus.cancelled and old_status != OrderStatus.cancelled:
        _restore_stock_for_order(db, order)

    order.status = payload.status
    db.commit()
    db.refresh(order)
    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

    # Enrich with buyer info for the response
    resp = OrderResponse.model_validate(order)
    _redact_cost_price(resp, current_user)
    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    if buyer and current_user.role in (UserRole.admin, UserRole.seller):
        resp.buyer_email = buyer.email
        resp.buyer_full_name = buyer.full_name

    # Send status-change email to the buyer when seller marks delivered or cancelled
    notify_statuses = {OrderStatus.delivered, OrderStatus.cancelled, OrderStatus.confirmed, OrderStatus.shipped}
    if buyer and old_status != order.status and order.status in notify_statuses:
        try:
            await send_order_status_email(
                buyer.email,
                buyer.full_name,
                str(order.id),
                order.status.value,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Błąd wysyłki e-mail o statusie zamówienia do {buyer.email}: {e}"
            )

    return resp


@router.patch("/{order_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
def hide_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lets a buyer clear a cancelled order out of their own list. This never
    deletes the order — sellers/admins keep full visibility for their records."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if order.status != OrderStatus.cancelled:
        raise HTTPException(status_code=400, detail="Only cancelled orders can be removed from your list")
    order.hidden_by_buyer = True
    db.commit()
    return None


def _e(value) -> str:
    """HTML-escape any value headed into the print view — several fields
    (shipping address, recipient name, company name) are buyer-controlled input."""
    if value is None:
        return ""
    return html.escape(str(value))


@router.get("/{order_id}/print", response_class=HTMLResponse)
def print_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # only seller/admin can print with stall/cost info (buyer can also but staff view)
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # auth check same as get_order
    if current_user.role == UserRole.buyer and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    is_staff = current_user.role in (UserRole.admin, UserRole.seller)
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    buyer = db.query(User).filter(User.id == order.buyer_id).first()

    company_name = order.company_name or (buyer.company_name if buyer else None)
    company_tax_id = order.company_tax_id or (buyer.company_tax_id if buyer else None)
    cost_col_header = "<th>Cost price</th>" if is_staff else ""

    doc = f"""
    <html><head><meta charset="utf-8"><title>Order {_e(str(order.id)[:8])} Print</title>
    <style>body{{font-family:Arial,sans-serif;padding:24px;color:#0f172a}} table{{width:100%;border-collapse:collapse;margin-top:16px}} th,td{{border:1px solid #cbd5e1;padding:8px;font-size:12px;text-align:left}} th{{background:#f1f5f9}} h1{{font-size:20px}} .meta{{margin-top:12px;font-size:12px;color:#475569}} @media print{{button{{display:none}}}}</style></head>
    <body>
    <button onclick="window.print()" style="padding:8px 16px;background:#0f172a;color:#fff;border:0;border-radius:999px;cursor:pointer">Print</button>
    <h1>Order #{_e(str(order.id)[:8])} — {_e(order.status.value)}</h1>
    <div class="meta">Buyer: {_e(buyer.full_name if buyer else '')} ({_e(buyer.email if buyer else '')})<br>Company: {_e(company_name)} NIP: {_e(company_tax_id)}<br>Shipping: {_e(order.shipping_address)}<br>Recipient: {_e(order.recipient_name)} {_e(order.recipient_phone)} {_e(order.recipient_address)}<br>Payment: {_e(order.payment_method.value)} (COD only)<br>Date: {_e(order.created_at)}</div>
    <table><thead><tr><th>Product</th><th>Pack</th><th>Qty (packs)</th><th>Stall / Counter</th>{cost_col_header}<th>Sell net</th><th>Total net</th></tr></thead><tbody>
    """
    for it in items:
        cost_cell = f"<td>{_e(it.cost_price_snapshot) if it.cost_price_snapshot is not None else '-'}</td>" if is_staff else ""
        doc += (
            f"<tr><td>{_e(it.product_name_snapshot)} (pack {_e(it.pack_size_snapshot)})</td>"
            f"<td>{_e(it.pack_size_snapshot)}</td><td>{_e(it.pack_quantity)}</td>"
            f"<td>{_e(it.stall_location_snapshot or '-')} / {_e(it.counter_number_snapshot or '-')}</td>"
            f"{cost_cell}"
            f"<td>{_e(it.price_net_snapshot)}</td><td>{_e(round(float(it.price_net_snapshot) * it.pack_quantity, 2))}</td></tr>"
        )
    footer_note = "Print for staff: buy goods at stall after order. Cost price shown for margin." if is_staff else "Print for staff: buy goods at stall after order."
    doc += f"</tbody></table><p style='margin-top:12px;font-weight:700'>Total net: {_e(order.total_net)} | Total gross: {_e(order.total_gross)}</p><p style='font-size:11px;color:#64748b'>{_e(footer_note)}</p></body></html>"
    return HTMLResponse(content=doc)
