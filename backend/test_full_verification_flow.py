#!/usr/bin/env python3
"""
Test the full email verification flow using the database directly.
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.auth import create_user, create_verification_token, verify_email_token
from app.models.user import UserRole
from app.services.email import send_verification_email
from app.core.config import settings


async def test_full_verification_flow():
    """Test the complete email verification flow."""
    print("🔐 Full Email Verification Flow Test")
    print("=" * 50)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create a user
        print("1. Creating user...")
        user = create_user(
            db=db,
            email="flowtest@example.com",
            password="password123",
            full_name="Flow Test User",
            role=UserRole.buyer
        )
        db.commit()
        print(f"✅ User created: {user.email}, email_verified: {user.email_verified}")
        
        # Step 2: Create verification token
        print("\n2. Creating verification token...")
        token = create_verification_token(db, user)
        db.commit()
        print(f"✅ Token created: {token[:10]}...")
        
        # Step 3: Send verification email (this will log to console)
        print("\n3. Sending verification email...")
        email_sent = await send_verification_email(user.email, user.full_name, token)
        print(f"✅ Email sent: {email_sent}")
        
        # Step 4: Verify the token
        print("\n4. Verifying email with token...")
        verified_user = verify_email_token(db, token)
        if verified_user:
            db.commit()
            print(f"✅ Email verified: {verified_user.email}, email_verified: {verified_user.email_verified}")
        else:
            print("❌ Email verification failed")
        
        # Step 5: Try to use token again (should fail)
        print("\n5. Testing token reuse (should fail)...")
        reuse_result = verify_email_token(db, token)
        if reuse_result is None:
            print("✅ Token correctly rejected on reuse")
        else:
            print("❌ Token was incorrectly accepted on reuse")
        
        print("\n🎉 Full verification flow test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_full_verification_flow())