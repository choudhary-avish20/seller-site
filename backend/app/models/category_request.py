import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class CategoryRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class CategoryRequest(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "category_requests"

    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # proposed name/slug
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    # parent under which the new category should be created, null => top-level
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[CategoryRequestStatus] = mapped_column(
        Enum(CategoryRequestStatus, name="category_request_status"),
        default=CategoryRequestStatus.pending,
        nullable=False,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # optional: link to created category after approval
    created_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    requester: Mapped["User"] = relationship()
    parent: Mapped["Category"] = relationship(foreign_keys=[parent_id])
    created_category: Mapped["Category"] = relationship(foreign_keys=[created_category_id])
