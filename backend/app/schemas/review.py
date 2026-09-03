from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewResponse(BaseModel):
    id: UUID
    product_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime
    reviewer_name: str
    is_own: bool = False

    @field_serializer('id', 'product_id')
    def ser_uuid(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True
