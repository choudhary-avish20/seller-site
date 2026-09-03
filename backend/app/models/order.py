import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"


class PaymentMethod(str, enum.Enum):
    cod = "cod"  # cash on delivery only for MVP


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

    # Company and recipient details (required for COD — account must submit information)
    company_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recipient_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), default=PaymentMethod.cod, nullable=False
    )

    coupon_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Lets a buyer clear a cancelled order out of their own order list without
    # touching the underlying record — sellers/admins always see every order
    # regardless of this flag, so nothing is lost from their side.
    hidden_by_buyer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    buyer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    # Note: an order can span multiple sellers, since each OrderItem
    # references its own product -> seller. Per-seller fulfillment status
    # can be tracked at the OrderItem level if needed (see Phase 5).
