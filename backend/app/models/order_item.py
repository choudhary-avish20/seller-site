import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class OrderItem(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=True
    )

    # Snapshot fields so historical orders stay accurate even if the product changes later
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    pack_size_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    price_net_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_gross_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    pack_quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # number of packs ordered

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")
    variant: Mapped["ProductVariant"] = relationship(back_populates="order_items")
