from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product, StockStatus
from app.models.product_variant import ProductVariant
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def _require_buyer(user: User) -> User:
    if user.role not in (UserRole.buyer, UserRole.admin):
        # allow admin for testing; primary role is buyer
        if user.role != UserRole.buyer:
            raise HTTPException(status_code=403, detail="Only buyers can place orders")
    return user


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_buyer(current_user)

    # optional: buyer must be active etc already checked
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
        # stock check pack-quantity based: stock_quantity is total units? For MVP compare against pack_quantity (packs)
        if product.stock_quantity < item.pack_quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}: {product.stock_quantity} packs available")

        variant = None
        price_net = float(product.price_net)
        price_gross = float(product.price_gross)
        if item.variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id, ProductVariant.product_id == product.id).first()
            if not variant:
                raise HTTPException(status_code=404, detail=f"Variant {item.variant_id} not found for product {product.name}")
            if variant.stock_quantity < item.pack_quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient variant stock for {product.name} ({variant.option_value})")
            if variant.price_net_override is not None:
                price_net = float(variant.price_net_override)
                # recompute gross with product vat
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

    order = Order(
        buyer_id=current_user.id,
        status=OrderStatus.pending,
        total_net=round(total_net, 2),
        total_gross=round(total_gross, 2),
        shipping_address=payload.shipping_address.strip(),
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(order)
    db.flush()

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
        )
        db.add(oi)
        # decrement stock (pack-based)
        p.stock_quantity -= entry["pack_quantity"]
        if p.stock_quantity < 0:
            p.stock_quantity = 0
        # optional: auto out_of_stock if 0
        if p.stock_quantity == 0:
            p.stock_status = StockStatus.out_of_stock
        if entry["variant"]:
            v = entry["variant"]
            v.stock_quantity -= entry["pack_quantity"]
            if v.stock_quantity < 0:
                v.stock_quantity = 0

    db.commit()
    db.refresh(order)
    # load items
    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # buyer sees own, admin sees all, seller sees orders containing their products
    q = db.query(Order)
    if current_user.role == UserRole.admin:
        orders = q.order_by(Order.created_at.desc()).all()
    elif current_user.role == UserRole.seller:
        # seller sees orders that contain at least one of their products
        from app.models.seller import SellerProfile
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if not seller:
            return []
        # filter via join
        orders = (
            db.query(Order)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(Product.seller_id == seller.id)
            .order_by(Order.created_at.desc())
            .distinct()
            .all()
        )
    else:
        orders = db.query(Order).filter(Order.buyer_id == current_user.id).order_by(Order.created_at.desc()).all()

    for o in orders:
        o.items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # auth: buyer owns, admin sees all, seller sees if contains their product
    if current_user.role == UserRole.buyer and order.buyer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.seller:
        from app.models.seller import SellerProfile
        seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
        if seller:
            has = db.query(OrderItem).join(Product, OrderItem.product_id == Product.id).filter(OrderItem.order_id == order.id, Product.seller_id == seller.id).first()
            if not has:
                raise HTTPException(status_code=403, detail="Not authorized")
    order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return order
