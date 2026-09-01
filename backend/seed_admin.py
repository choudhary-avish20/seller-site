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
        print(f"✅ Seller account created: {seller_email} / {seller_password}")
        print()
        print("⚠️  Next steps for handover:")
        print("   1. Share these credentials with the owner via a secure channel")
        print("      (e.g. 1Password, Signal, or in person — NOT plain email).")
        print(f"   2. Give the owner the admin login URL: <your-domain>/admin-login.html")
        print("      Ask them to bookmark it — it is not linked from the public site.")
        print("   3. After first login, the owner should go to Settings → Change Password")
        print("      so you no longer know their credentials.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
