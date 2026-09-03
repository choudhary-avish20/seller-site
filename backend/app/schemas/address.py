from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class AddressCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    recipient_name: Optional[str] = Field(None, max_length=255)
    recipient_phone: Optional[str] = Field(None, max_length=32)
    street: str = Field(..., min_length=1, max_length=255)
    zip_code: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=120)
    company_name: Optional[str] = Field(None, max_length=255)
    company_tax_id: Optional[str] = Field(None, max_length=64)
    is_default: bool = False


class AddressResponse(BaseModel):
    id: UUID
    label: str
    recipient_name: Optional[str]
    recipient_phone: Optional[str]
    street: str
    zip_code: str
    city: str
    company_name: Optional[str]
    company_tax_id: Optional[str]
    is_default: bool
    created_at: datetime

    @field_serializer('id')
    def ser_id(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True
