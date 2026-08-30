import json
import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.product import Product, StockStatus
from app.models.product_variant import ProductVariant
from app.models.product_price_tier import ProductPriceTier
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    StockToggleRequest,
    slugify,
)

router = APIRouter(prefix="/products", tags=["products"])


def _require_admin(user: User):
    if user.role not in (UserRole.admin, UserRole.seller):
        raise HTTPException(status_code=403, detail="Only the store owner can manage products")


def _ensure_product_slug_unique(db: Session, slug: str, exclude_id: Optional[UUID] = None):
    q = db.query(Product).filter(Product.slug == slug)
    if exclude_id:
        q = q.filter(Product.id != exclude_id)
    if q.first():
        raise HTTPException(status_code=400, detail=f"Product slug '{slug}' already exists")


def _compute_gross(price_net: float, vat_rate: float, price_gross: Optional[float]) -> float:
    if price_gross is not None:
        return round(float(price_gross), 2)
    return round(float(price_net) * (1 + float(vat_rate) / 100), 2)


def _parse_images(images_str: str) -> List[str]:
    if not images_str:
        return []
    try:
        data = json.loads(images_str)
        if isinstance(data, list):
            return [str(x) for x in data]
        return []
    except Exception:
        return []


def _serialize_images(images: List[str]) -> str:
    return json.dumps(images)


def _get_tiered_price(product: Product, quantity: int, db: Session) -> float:
    tiers = db.query(ProductPriceTier).filter(ProductPriceTier.product_id == product.id).order_by(ProductPriceTier.min_quantity).all()
    if not tiers:
        return float(product.price_net)
    for t in tiers:
        max_q = t.max_quantity if t.max_quantity is not None else float('inf')
        if t.min_quantity <= quantity <= max_q:
            return float(t.price_net)
    # if quantity beyond all tiers, use last tier (highest)
    if quantity > tiers[-1].min_quantity:
        return float(tiers[-1].price_net)
    return float(product.price_net)


def _validate_tiers(tiers):
    if not tiers:
        return
    # sort by min_quantity
    sorted_tiers = sorted(tiers, key=lambda x: x.min_quantity)
    for i, t in enumerate(sorted_tiers):
        if t.max_quantity is not None and t.min_quantity > t.max_quantity:
            raise HTTPException(status_code=400, detail=f"Tier {i}: min_quantity > max_quantity")
        if i > 0:
            prev = sorted_tiers[i-1]
            # ensure no overlap and sequential
            prev_max = prev.max_quantity
            if prev_max is not None and t.min_quantity <= prev_max:
                raise HTTPException(status_code=400, detail=f"Tier {i} overlaps previous tier")
            if prev_max is not None and t.min_quantity != prev_max + 1:
                # allow gap but warn? enforce contiguous? allow gap
                pass


def _to_product_response(product: Product, db: Session, hide_prices: bool = False) -> ProductResponse:
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    images_list = _parse_images(product.images)
    tiers = (
        db.query(ProductPriceTier)
        .filter(ProductPriceTier.product_id == product.id)
        .order_by(ProductPriceTier.min_quantity)
        .all()
    )
    variants = (
        db.query(ProductVariant)
        .filter(ProductVariant.product_id == product.id)
        .all()
    )
    price_net = 0 if hide_prices else float(product.price_net)
    price_gross = 0 if hide_prices else float(product.price_gross)
    return ProductResponse(
        id=product.id,
        category_id=product.category_id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        images=images_list,
        pack_size=product.pack_size,
        price_net=price_net,
        price_gross=price_gross,
        vat_rate=float(product.vat_rate),
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        is_active=product.is_active,
        pack_increment=product.pack_increment,
        cost_price=float(product.cost_price) if product.cost_price is not None and not hide_prices else None,
        stall_location=product.stall_location,
        counter_number=product.counter_number,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category_name=cat.name if cat else None,
        category_slug=cat.slug if cat else None,
        variants=variants,
        price_tiers=tiers if not hide_prices else [],
    )


def _to_list_response(product: Product, db: Session, hide_prices: bool = False) -> ProductListResponse:
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    images_list = _parse_images(product.images)
    tiers = db.query(ProductPriceTier).filter(ProductPriceTier.product_id == product.id).order_by(ProductPriceTier.min_quantity).all()
    price_net = 0 if hide_prices else float(product.price_net)
    price_gross = 0 if hide_prices else float(product.price_gross)
    return ProductListResponse(
        id=product.id,
        category_id=product.category_id,
        name=product.name,
        slug=product.slug,
        images=images_list,
        pack_size=product.pack_size,
        price_net=price_net,
        price_gross=price_gross,
        vat_rate=float(product.vat_rate),
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        is_active=product.is_active,
        pack_increment=product.pack_increment,
        cost_price=float(product.cost_price) if product.cost_price is not None and not hide_prices else None,
        stall_location=product.stall_location,
        counter_number=product.counter_number,
        created_at=product.created_at,
        category_name=cat.name if cat else None,
        category_slug=cat.slug if cat else None,
        price_tiers=tiers if not hide_prices else [],
    )


def _should_hide_prices(request: Request, db: Session) -> bool:
    if not settings.REQUIRE_LOGIN_TO_SEE_PRICES:
        return False
    # try to get user from Authorization header
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return True
    token = auth.split(" ", 1)[1]
    from app.core.auth import decode_token, get_user_by_id
    import uuid
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return True
    try:
        uid = uuid.UUID(payload.get("sub"))
    except:
        return True
    user = get_user_by_id(db, uid)
    if not user or not user.is_active:
        return True
    # if buyer approval required, also check buyer_status
    if user.role == UserRole.buyer and settings.REQUIRE_BUYER_APPROVAL:
        if user.buyer_status != "approved":
            return True
    return False


# ---------- Public ----------
@router.get("", response_model=List[ProductListResponse])
def list_products(
    request: Request,
    db: Session = Depends(get_db),
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    hide = _should_hide_prices(request, db)
    q = db.query(Product)
    if not include_inactive:
        q = q.filter(Product.is_active == True)  # noqa
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        term = f"%{search}%"
        q = q.outerjoin(Category, Product.category_id == Category.id).filter(
            or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Category.name.ilike(term),
                Category.slug.ilike(term),
            )
        )
    q = q.order_by(Product.created_at.desc())
    offset = (page - 1) * limit
    products = q.offset(offset).limit(limit).all()
    return [_to_list_response(p, db, hide_prices=hide) for p in products]


@router.get("/slug/{slug}", response_model=ProductResponse)
def get_by_slug(slug: str, request: Request, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.slug == slug).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    hide = _should_hide_prices(request, db)
    return _to_product_response(prod, db, hide_prices=hide)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, request: Request, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    hide = _should_hide_prices(request, db)
    return _to_product_response(prod, db, hide_prices=hide)


# ---------- Seller CRUD ----------
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    cat = db.query(Category).filter(Category.id == payload.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if not cat.is_active:
        raise HTTPException(status_code=400, detail="Category is inactive")
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    if not slug:
        slug = slugify(payload.name)
    _ensure_product_slug_unique(db, slug)
    price_gross = _compute_gross(payload.price_net, payload.vat_rate, payload.price_gross)
    images_json = _serialize_images(payload.images or [])
    _validate_tiers(payload.price_tiers)
    product = Product(
        category_id=payload.category_id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description.strip() if payload.description else None,
        images=images_json,
        pack_size=payload.pack_size,
        price_net=round(float(payload.price_net), 2),
        price_gross=price_gross,
        vat_rate=round(float(payload.vat_rate), 2),
        stock_quantity=payload.stock_quantity,
        stock_status=payload.stock_status,
        is_active=payload.is_active,
        pack_increment=payload.pack_increment,
        cost_price=round(float(payload.cost_price),2) if payload.cost_price is not None else None,
        stall_location=payload.stall_location.strip() if payload.stall_location else None,
        counter_number=payload.counter_number.strip() if payload.counter_number else None,
    )
    db.add(product)
    db.flush()
    for v in payload.variants:
        if db.query(ProductVariant).filter(ProductVariant.sku == v.sku).first():
            raise HTTPException(status_code=400, detail=f"SKU '{v.sku}' already exists")
        variant = ProductVariant(
            product_id=product.id,
            sku=v.sku,
            option_name=v.option_name,
            option_value=v.option_value,
            price_net_override=round(float(v.price_net_override), 2) if v.price_net_override is not None else None,
            stock_quantity=v.stock_quantity,
        )
        db.add(variant)
    for t in payload.price_tiers:
        tier = ProductPriceTier(
            product_id=product.id,
            min_quantity=t.min_quantity,
            max_quantity=t.max_quantity,
            price_net=round(float(t.price_net),2),
        )
        db.add(tier)
    db.commit()
    db.refresh(product)
    return _to_product_response(product, db, hide_prices=False)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.name is not None:
        prod.name = payload.name.strip()
    if payload.slug is not None:
        new_slug = payload.slug.strip() or slugify(prod.name)
        _ensure_product_slug_unique(db, new_slug, exclude_id=prod.id)
        prod.slug = new_slug
    if payload.description is not None:
        prod.description = payload.description.strip() if payload.description else None
    if payload.images is not None:
        prod.images = _serialize_images(payload.images)
    if payload.category_id is not None:
        cat = db.query(Category).filter(Category.id == payload.category_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        prod.category_id = payload.category_id
    if payload.pack_size is not None:
        prod.pack_size = payload.pack_size
    if payload.pack_increment is not None:
        prod.pack_increment = payload.pack_increment
    if payload.cost_price is not None:
        prod.cost_price = round(float(payload.cost_price),2) if payload.cost_price is not None else None
    if payload.stall_location is not None:
        prod.stall_location = payload.stall_location.strip() if payload.stall_location else None
    if payload.counter_number is not None:
        prod.counter_number = payload.counter_number.strip() if payload.counter_number else None
    if payload.price_net is not None:
        prod.price_net = round(float(payload.price_net), 2)
    if payload.vat_rate is not None:
        prod.vat_rate = round(float(payload.vat_rate), 2)
    if payload.price_net is not None or payload.vat_rate is not None or payload.price_gross is not None:
        net = float(payload.price_net) if payload.price_net is not None else float(prod.price_net)
        vat = float(payload.vat_rate) if payload.vat_rate is not None else float(prod.vat_rate)
        gross_in = payload.price_gross if payload.price_gross is not None else None
        if gross_in is not None:
            prod.price_gross = round(float(gross_in), 2)
        else:
            prod.price_gross = _compute_gross(net, vat, None)
    elif payload.price_gross is not None:
        prod.price_gross = round(float(payload.price_gross), 2)
    if payload.stock_quantity is not None:
        prod.stock_quantity = payload.stock_quantity
    if payload.stock_status is not None:
        prod.stock_status = payload.stock_status
    if payload.is_active is not None:
        prod.is_active = payload.is_active
    if payload.variants is not None:
        db.query(ProductVariant).filter(ProductVariant.product_id == prod.id).delete()
        for v in payload.variants:
            if db.query(ProductVariant).filter(ProductVariant.sku == v.sku).first():
                raise HTTPException(status_code=400, detail=f"SKU '{v.sku}' already exists")
            variant = ProductVariant(
                product_id=prod.id,
                sku=v.sku,
                option_name=v.option_name,
                option_value=v.option_value,
                price_net_override=round(float(v.price_net_override), 2) if v.price_net_override is not None else None,
                stock_quantity=v.stock_quantity,
            )
            db.add(variant)
    if payload.price_tiers is not None:
        _validate_tiers(payload.price_tiers)
        db.query(ProductPriceTier).filter(ProductPriceTier.product_id == prod.id).delete()
        for t in payload.price_tiers:
            tier = ProductPriceTier(
                product_id=prod.id,
                min_quantity=t.min_quantity,
                max_quantity=t.max_quantity,
                price_net=round(float(t.price_net),2),
            )
            db.add(tier)
    db.commit()
    db.refresh(prod)
    return _to_product_response(prod, db, hide_prices=False)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(prod)
    db.commit()
    return None


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def toggle_stock(
    product_id: UUID,
    payload: StockToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.stock_status is not None:
        prod.stock_status = payload.stock_status
    if payload.stock_quantity is not None:
        prod.stock_quantity = payload.stock_quantity
    db.commit()
    db.refresh(prod)
    return _to_product_response(prod, db)


@router.patch("/{product_id}/archive", response_model=ProductResponse)
def archive_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    prod.is_active = not prod.is_active
    db.commit()
    db.refresh(prod)
    return _to_product_response(prod, db)
