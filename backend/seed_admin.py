import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.core.auth import get_password_hash
from app.models.user import User, UserRole
from app.models.seller import SellerProfile, SellerStatus


def seed_admin():
    db = SessionLocal()
    try:
        seller_email = os.getenv("ADMIN_EMAIL", "seller@example.com")
        seller_password = os.getenv("ADMIN_PASSWORD", "seller123")
        seller_name = os.getenv("ADMIN_NAME", "Store Owner")

        existing = db.query(User).filter(User.email == seller_email).first()
        if existing:
            print(f"Seller account already exists: {seller_email}")
            return

        user = User(
            email=seller_email,
            hashed_password=get_password_hash(seller_password),
            full_name=seller_name,
            role=UserRole.seller,
            is_active=True,
        )
        db.add(user)
        db.flush()

        profile = SellerProfile(
            user_id=user.id,
            business_name=seller_name,
            status=SellerStatus.approved,
        )
        db.add(profile)
        db.commit()
        print(f"Seller account created: {seller_email} / {seller_password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
