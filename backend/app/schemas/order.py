from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: UUID
    variant_id: Optional[UUID] = None
    pack_quantity: int = Field(..., ge=1, description="Number of packs")


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=5, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


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
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = Field(default_factory=list)

    @field_serializer('id', 'buyer_id')
    def ser(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True
