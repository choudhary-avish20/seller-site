from datetime import datetime
from typing import Optional, List, ForwardRef
from uuid import UUID
import enum

from pydantic import BaseModel, Field, field_serializer


# ---------- Category request status (defined here; model created when feature is fully implemented) ----------
class CategoryRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ---------- helpers ----------
def slugify(value: str) -> str:
    import re
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "category"


# ---------- Category ----------
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255, description="Optional; auto-generated from name if omitted")
    parent_id: Optional[UUID] = None
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    @field_serializer('id', 'parent_id')
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        return str(value) if value else None

    class Config:
        from_attributes = True


class CategoryTreeNode(CategoryResponse):
    children: List["CategoryTreeNode"] = Field(default_factory=list)


# needed for self-referencing
CategoryTreeNode.model_rebuild()


class CategoryPathResponse(BaseModel):
    category: CategoryResponse
    ancestors: List[CategoryResponse]
    path: str  # e.g. "electronics/phones/smartphones"


# ---------- Category Requests ----------
class CategoryRequestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[UUID] = None
    description: Optional[str] = None
    slug: Optional[str] = Field(None, max_length=255)


class CategoryRequestResponse(BaseModel):
    id: UUID
    requester_id: UUID
    name: str
    slug: str
    parent_id: Optional[UUID]
    description: Optional[str]
    status: CategoryRequestStatus
    rejection_reason: Optional[str]
    created_category_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    # optional denormalized for admin list
    requester_email: Optional[str] = None
    parent_name: Optional[str] = None

    @field_serializer('id', 'requester_id', 'parent_id', 'created_category_id')
    def serialize_uuid_opt(self, value: Optional[UUID]) -> Optional[str]:
        return str(value) if value else None

    class Config:
        from_attributes = True


class CategoryRequestDecision(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = None
