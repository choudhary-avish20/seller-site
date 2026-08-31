import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class BuyerStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.buyer, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Buyer verification (for REQUIRE_BUYER_APPROVAL)
    buyer_status: Mapped[BuyerStatus] = mapped_column(
        Enum(BuyerStatus, name="buyer_status"), default=BuyerStatus.approved, nullable=False
    )
    buyer_rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Company / required info for COD (buyers must submit)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="buyer")
    seller_profile: Mapped["SellerProfile | None"] = relationship(back_populates="user", uselist=False)  # type: ignore[name-defined]
    verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined]
