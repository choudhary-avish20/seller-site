import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class StockStatus(str, enum.Enum):
    in_stock = "in_stock"
    out_of_stock = "out_of_stock"


class Product(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "products"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    images: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Wholesale pack pricing: buyers purchase in units of `pack_size`
    pack_size: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_net: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_gross: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    vat_rate: Mapped[float] = mapped_column(Numeric(4, 2), default=23.00, nullable=False)

    # Quantity-based tiered pricing (e.g. 1-10:10, 11-50:9.5, 50+:9)
    # If no tiers, single price_net is used
    pack_increment: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # e.g. 12 or 40 pcs per increment

    # Stock management: where to buy after order (wholesale works by buying after order)
    cost_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # purchase (cost) price for staff
    stall_location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "Hall A"
    counter_number: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "Counter 12"

    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stock_status: Mapped[StockStatus] = mapped_column(
        Enum(StockStatus, name="stock_status"), default=StockStatus.in_stock, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # archived if False

    # Storefront merchandising badges — manually toggled by the seller in admin
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_on_sale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sale_price_net: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # shown when is_on_sale

    category: Mapped["Category"] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    price_tiers: Mapped[list["ProductPriceTier"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductPriceTier.min_quantity"
    )
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
