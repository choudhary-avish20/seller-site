from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.models.coupon import CouponDiscountType


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=64)
    discount_type: CouponDiscountType
    discount_value: float = Field(..., gt=0)
    min_order_net: Optional[float] = Field(None, ge=0)
    max_uses: Optional[int] = Field(None, ge=1)
    active: bool = True
    expires_at: Optional[datetime] = None

    @field_validator('code')
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator('discount_value')
    @classmethod
    def cap_percent(cls, v: float, info) -> float:
        if info.data.get('discount_type') == CouponDiscountType.percent and v > 100:
            raise ValueError('Percent discount cannot exceed 100')
        return v


class CouponUpdate(BaseModel):
    discount_type: Optional[CouponDiscountType] = None
    discount_value: Optional[float] = Field(None, gt=0)
    min_order_net: Optional[float] = Field(None, ge=0)
    max_uses: Optional[int] = Field(None, ge=1)
    active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class CouponResponse(BaseModel):
    id: UUID
    code: str
    discount_type: CouponDiscountType
    discount_value: float
    min_order_net: Optional[float]
    max_uses: Optional[int]
    used_count: int
    active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    @field_serializer('id')
    def ser(self, v: UUID) -> str:
        return str(v)

    class Config:
        from_attributes = True


class CouponValidateRequest(BaseModel):
    code: str
    order_net: float = Field(..., ge=0)


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: Optional[CouponDiscountType] = None
    discount_value: Optional[float] = None
    min_order_net: Optional[float] = None
    discount_amount: float = 0
    message: Optional[str] = None
