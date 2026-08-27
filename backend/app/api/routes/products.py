import json
import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.product import Product, StockStatus
from app.models.product_variant import ProductVariant
from app.models.category import Category
from app.models.seller import SellerProfile, SellerStatus
from app.models.user import User, UserRole
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductVariantResponse,
    StockToggleRequest,
    slugify,
)

router = APIRouter(prefix="/products", tags=["products"])


def _get_approved_seller(db: Session, user: User) -> SellerProfile:
    if user.role != UserRole.seller:
        raise HTTPException(status_code=403, detail="Only sellers can manage products")
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    if seller.status != SellerStatus.approved:
        raise HTTPException(status_code=403, detail="Seller not approved; cannot manage products")
    return seller


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


def _to_product_response(product: Product, db: Session) -> ProductResponse:
    # load category and seller for denormalization if not already
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    seller = db.query(SellerProfile).filter(SellerProfile.id == product.seller_id).first()
    images_list = _parse_images(product.images)
    variants = db.query(ProductVariant).filter(ProductVariant.product_id == product.id).all()
    return ProductResponse(
        id=product.id,
        seller_id=product.seller_id,
        category_id=product.category_id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        images=images_list,
        pack_size=product.pack_size,
        price_net=float(product.price_net),
        price_gross=float(product.price_gross),
        vat_rate=float(product.vat_rate),
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category_name=cat.name if cat else None,
        category_slug=cat.slug if cat else None,
        seller_business_name=seller.business_name if seller else None,
        variants=variants,
    )


def _to_list_response(product: Product, db: Session) -> ProductListResponse:
    cat = db.query(Category).filter(Category.id == product.category_id).first()
    images_list = _parse_images(product.images)
    return ProductListResponse(
        id=product.id,
        seller_id=product.seller_id,
        category_id=product.category_id,
        name=product.name,
        slug=product.slug,
        images=images_list,
        pack_size=product.pack_size,
        price_net=float(product.price_net),
        price_gross=float(product.price_gross),
        vat_rate=float(product.vat_rate),
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        is_active=product.is_active,
        created_at=product.created_at,
        category_name=cat.name if cat else None,
        category_slug=cat.slug if cat else None,
    )


# ---------- Public ----------
@router.get("", response_model=List[ProductListResponse])
def list_products(
    db: Session = Depends(get_db),
    category_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    seller_id: Optional[UUID] = Query(None),
    include_inactive: bool = Query(False),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = db.query(Product)
    if not include_inactive:
        q = q.filter(Product.is_active == True)  # noqa
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if category_id:
        q = q.filter(Product.category_id == category_id)
    if seller_id:
        q = q.filter(Product.seller_id == seller_id)
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
    return [_to_list_response(p, db) for p in products]


@router.get("/my", response_model=List[ProductListResponse])
def list_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seller = _get_approved_seller(db, current_user)
    # seller can see own even if inactive (archived), so include_inactive
    products = db.query(Product).filter(Product.seller_id == seller.id).order_by(Product.created_at.desc()).all()
    return [_to_list_response(p, db) for p in products]


@router.get("/slug/{slug}", response_model=ProductResponse)
def get_by_slug(slug: str, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.slug == slug).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    # optionally hide inactive for public
    return _to_product_response(prod, db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return _to_product_response(prod, db)


# ---------- Seller CRUD ----------
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seller = _get_approved_seller(db, current_user)

    # validate category
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

    # validate images: allow empty, but ensure list of strings
    images_json = _serialize_images(payload.images or [])

    # pack_size check already via pydantic, stock_status etc.

    product = Product(
        seller_id=seller.id,
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
    )
    db.add(product)
    db.flush()  # get id for variants

    # variants
    for v in payload.variants:
        # SKU unique check
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

    db.commit()
    db.refresh(product)
    return _to_product_response(product, db)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seller = _get_approved_seller(db, current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if prod.seller_id != seller.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not owner of product")

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
    if payload.price_net is not None:
        prod.price_net = round(float(payload.price_net), 2)
    if payload.vat_rate is not None:
        prod.vat_rate = round(float(payload.vat_rate), 2)
    # recompute gross if either net/vat/gross changed
    if payload.price_net is not None or payload.vat_rate is not None or payload.price_gross is not None:
        # use new values if provided else existing
        net = float(payload.price_net) if payload.price_net is not None else float(prod.price_net)
        vat = float(payload.vat_rate) if payload.vat_rate is not None else float(prod.vat_rate)
        gross_in = payload.price_gross if payload.price_gross is not None else None
        # if gross_in is None and only net/vat changed, recompute; if gross_in provided, use it
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
        # replace all variants
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

    db.commit()
    db.refresh(prod)
    return _to_product_response(prod, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    seller = _get_approved_seller(db, current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if prod.seller_id != seller.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not owner")
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
    seller = _get_approved_seller(db, current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if prod.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not owner")
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
    seller = _get_approved_seller(db, current_user)
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    if prod.seller_id != seller.id:
        raise HTTPException(status_code=403, detail="Not owner")
    prod.is_active = not prod.is_active
    db.commit()
    db.refresh(prod)
    return _to_product_response(prod, db)
