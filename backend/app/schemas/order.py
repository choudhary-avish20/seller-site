from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.models.order import OrderStatus, PaymentMethod


class OrderItemCreate(BaseModel):
    product_id: UUID
    variant_id: Optional[UUID] = None
    pack_quantity: int = Field(..., ge=1, description="Number of packs")


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=5, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)
    # Company and recipient details (required for COD)
    company_name: Optional[str] = Field(None, max_length=255)
    company_tax_id: Optional[str] = Field(None, max_length=64)
    company_address: Optional[str] = Field(None, max_length=1000)
    recipient_name: Optional[str] = Field(None, max_length=255)
    recipient_phone: Optional[str] = Field(None, max_length=32)
    recipient_address: Optional[str] = Field(None, max_length=1000)
    payment_method: PaymentMethod = Field(default=PaymentMethod.cod, description="Only COD for MVP")


class OrderItemResponse(BaseModel):
    id: UUID
    order_id: UUID
    product_id: UUID
    variant_id: Optional[UUID]
    product_name_snapshot: str
    pack_size_snapshot: int
    price_net_snapshot: float
    price_gross_snapshot: float
    pack_quantity: int
    cost_price_snapshot: Optional[float] = None
    stall_location_snapshot: Optional[str] = None
    counter_number_snapshot: Optional[str] = None
    created_at: datetime

    @field_serializer('id', 'order_id', 'product_id', 'variant_id')
    def ser(self, v: Optional[UUID]) -> Optional[str]:
        return str(v) if v else None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    buyer_id: UUID
    status: OrderStatus
    total_net: float
    total_gross: float
    shipping_address: str
    notes: Optional[str]
    company_name: Optional[str]
    company_tax_id: Optional[str]
    company_address: Optional[str]
    recipient_name: Optional[str]
    recipient_phone: Optional[str]
    recipient_address: Optional[str]
    payment_method: PaymentMethod
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = Field(default_factory=list)

    @field_serializer('id', 'buyer_id')
    def ser(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True
