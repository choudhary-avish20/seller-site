import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.pending, nullable=False
    )

    total_net: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_gross: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    buyer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    # Note: an order can span multiple sellers, since each OrderItem
    # references its own product -> seller. Per-seller fulfillment status
    # can be tracked at the OrderItem level if needed (see Phase 5).
