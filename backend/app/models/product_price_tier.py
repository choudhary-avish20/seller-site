import uuid

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class ProductPriceTier(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "product_price_tiers"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # inclusive
    max_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # inclusive, null = infinity (e.g. Over 50)
    price_net: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="price_tiers")
