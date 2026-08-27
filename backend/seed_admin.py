import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.core.auth import get_password_hash
from app.models.user import User, UserRole


def seed_admin():
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@wholesale.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin12345")
        admin_name = os.getenv("ADMIN_NAME", "Platform Admin")

        existing = db.query(User).filter(User.email == admin_email).first()
        if existing:
            print(f"Admin user already exists: {admin_email}")
            return

        admin = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name=admin_name,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin user created: {admin_email} / {admin_password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
