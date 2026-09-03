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
        admin_email = os.getenv("ADMIN_EMAIL", "seller@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "seller123")
        admin_name = os.getenv("ADMIN_NAME", "Store Owner")

        existing = db.query(User).filter(User.email == admin_email).first()
        if existing:
            print(f"Admin account already exists: {admin_email}")
            return

        # This is the store owner's account. It must be role=admin, not role=seller,
        # so it can reach admin-only endpoints (approve sellers, approve buyers) —
        # there is no other path in the app that ever creates a UserRole.admin user.
        user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name=admin_name,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Not required for the admin role, but harmless to keep so the account
        # has a business_name on file if it's ever displayed alongside orders.
        profile = SellerProfile(
            user_id=user.id,
            business_name=admin_name,
            status=SellerStatus.approved,
        )
        db.add(profile)
        db.commit()
        print(f"✅ Admin account created: {admin_email} / {admin_password}")
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
