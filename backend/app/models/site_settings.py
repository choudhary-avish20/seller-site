from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, UUIDPKMixin


class SiteSettings(UUIDPKMixin, TimestampMixin, Base):
    """Store-wide contact info shown on the public Contact page.

    Single-row table (first row wins) so the storefront always has one
    canonical set of contact details, editable by admins only.
    """

    __tablename__ = "site_settings"

    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms_content: Mapped[str | None] = mapped_column(Text, nullable=True)
