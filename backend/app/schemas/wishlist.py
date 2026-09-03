from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer

from app.schemas.product import ProductListResponse


class WishlistItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    created_at: datetime
    product: ProductListResponse

    @field_serializer('id', 'product_id')
    def ser_uuid(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True
