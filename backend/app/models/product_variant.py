import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class ProductVariant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # e.g. "size", "color" - kept simple/flat for MVP rather than a full attribute system
    option_name: Mapped[str] = mapped_column(String(64), nullable=False)
    option_value: Mapped[str] = mapped_column(String(64), nullable=False)

    # Optional price override; falls back to parent product value if null
    price_net_override: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="variants")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="variant")
