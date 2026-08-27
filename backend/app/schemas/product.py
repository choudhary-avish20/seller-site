from datetime import datetime
from typing import Optional, List
from uuid import UUID
import re

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.models.product import StockStatus


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "product"


# ---------- Variants ----------
class ProductVariantCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    option_name: str = Field(..., min_length=1, max_length=64, examples=["size"])
    option_value: str = Field(..., min_length=1, max_length=64, examples=["XL"])
    price_net_override: Optional[float] = Field(None, ge=0)
    stock_quantity: int = Field(0, ge=0)


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=64)
    option_name: Optional[str] = None
    option_value: Optional[str] = None
    price_net_override: Optional[float] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)


class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    sku: str
    option_name: str
    option_value: str
    price_net_override: Optional[float]
    stock_quantity: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('id', 'product_id')
    def ser_uuid(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True


# ---------- Products ----------
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list, description="List of image URLs/paths")
    category_id: UUID
    pack_size: int = Field(1, ge=1, description="Units per pack")
    price_net: float = Field(..., ge=0)
    price_gross: Optional[float] = Field(None, ge=0, description="If omitted, computed from net + VAT")
    vat_rate: float = Field(23.00, ge=0, le=100)
    stock_quantity: int = Field(0, ge=0)
    stock_status: StockStatus = StockStatus.in_stock
    is_active: bool = True


class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: Optional[UUID] = None
    pack_size: Optional[int] = Field(None, ge=1)
    price_net: Optional[float] = Field(None, ge=0)
    price_gross: Optional[float] = Field(None, ge=0)
    vat_rate: Optional[float] = Field(None, ge=0, le=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    stock_status: Optional[StockStatus] = None
    is_active: Optional[bool] = None
    variants: Optional[List[ProductVariantCreate]] = None  # replace all if provided


class ProductResponse(BaseModel):
    id: UUID
    seller_id: UUID
    category_id: UUID
    name: str
    slug: str
    description: Optional[str]
    images: List[str]
    pack_size: int
    price_net: float
    price_gross: float
    vat_rate: float
    stock_quantity: int
    stock_status: StockStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # denormalized
    category_name: Optional[str] = None
    category_slug: Optional[str] = None
    seller_business_name: Optional[str] = None
    variants: List[ProductVariantResponse] = Field(default_factory=list)

    @field_serializer('id', 'seller_id', 'category_id')
    def ser_uuid(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: UUID
    seller_id: UUID
    category_id: UUID
    name: str
    slug: str
    images: List[str]
    pack_size: int
    price_net: float
    price_gross: float
    vat_rate: float
    stock_quantity: int
    stock_status: StockStatus
    is_active: bool
    created_at: datetime
    category_name: Optional[str] = None
    category_slug: Optional[str] = None

    @field_serializer('id', 'seller_id', 'category_id')
    def ser_uuid(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True


class StockToggleRequest(BaseModel):
    stock_status: Optional[StockStatus] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
