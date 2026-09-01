from pydantic import BaseModel, EmailStr, Field, field_serializer
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.user import UserRole, BuyerStatus
from app.models.seller import SellerStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.buyer
    # optional company info for buyers (required for COD)
    company_name: Optional[str] = Field(None, max_length=255)
    company_tax_id: Optional[str] = Field(None, max_length=64)
    company_address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=32)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int
    type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    buyer_status: BuyerStatus
    email_verified: bool
    company_name: Optional[str]
    company_tax_id: Optional[str]
    company_address: Optional[str]
    phone: Optional[str]
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True


class SellerProfileBase(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=64)
    business_address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=32)


class SellerProfileCreate(SellerProfileBase):
    pass


class SellerProfileResponse(SellerProfileBase):
    id: UUID
    user_id: UUID
    status: SellerStatus
    rejection_reason: Optional[str]
    created_at: datetime

    @field_serializer('id', 'user_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True


class SellerRegistrationRequest(UserCreate):
    seller_profile: SellerProfileCreate

    class Config:
        json_schema_extra = {
            "example": {
                "email": "seller@example.com",
                "password": "securepassword123",
                "full_name": "John Seller",
                "role": "seller",
                "seller_profile": {
                    "business_name": "ABC Wholesale",
                    "tax_id": "123456789",
                    "business_address": "123 Business St, City",
                    "phone": "+1234567890"
                }
            }
        }


class SellerRegistrationResponse(BaseModel):
    user: UserResponse
    seller_profile: SellerProfileResponse


class SellerApprovalRequest(BaseModel):
    status: SellerStatus
    rejection_reason: Optional[str] = None


class SellerListResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    business_name: str
    status: SellerStatus
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True


class BuyerApprovalRequest(BaseModel):
    status: BuyerStatus
    rejection_reason: Optional[str] = None


class BuyerListResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    company_name: Optional[str]
    status: BuyerStatus
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        return str(value)

    class Config:
        from_attributes = True


class EmailVerifyRequest(BaseModel):
    token: str


class EmailVerifyResponse(BaseModel):
    message: str
    user: UserResponse


class ResendVerificationResponse(BaseModel):
    message: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str
