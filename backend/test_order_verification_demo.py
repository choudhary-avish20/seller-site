#!/usr/bin/env python3
"""
Demo script to test order verification enforcement.
"""

import asyncio
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.user import User, UserRole, BuyerStatus
from app.models.product import Product, StockStatus
from app.models.category import Category
from app.core.auth import get_password_hash
from app.core.config import settings
from app.schemas.order import OrderCreate
from uuid import uuid4


async def test_order_verification_logic():
    """Test the order verification logic directly."""
    print("🛒 Order Email Verification Test")
    print("=" * 50)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create test data
        print("1. Setting up test data...")
        
        # Create category
        category_id = str(uuid4())[:8]
        category = Category(
            id=uuid4(),
            name=f"Test Category {category_id}",
            slug=f"test-category-{category_id}",
            is_active=True
        )
        db.add(category)
        db.flush()
        
        # Create product
        product_id = str(uuid4())[:8]
        product = Product(
            id=uuid4(),
            category_id=category.id,
            name=f"Test Product {product_id}",
            slug=f"test-product-{product_id}",
            description="Test product",
            images="[]",
            pack_size=12,
            price_net=10.00,
            price_gross=12.30,
            vat_rate=23.00,
            stock_quantity=100,
            stock_status=StockStatus.in_stock,
            is_active=True
        )
        db.add(product)
        
        # Create unverified user
        user_id = str(uuid4())[:8]
        unverified_user = User(
            id=uuid4(),
            email=f"unverified-{user_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Unverified User",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=False,  # Key: not verified
            company_name="Test Company",
            phone="+1234567890"
        )
        db.add(unverified_user)
        
        # Create verified user
        verified_user = User(
            id=uuid4(),
            email=f"verified-{user_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Verified User",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=True,  # Key: verified
            company_name="Test Company",
            phone="+1234567890"
        )
        db.add(verified_user)
        
        db.commit()
        print("✅ Test data created")
        
        # Step 2: Test the verification logic
        print("\n2. Testing verification enforcement...")
        
        # Import the create_order function
        from app.api.routes.orders import create_order
        
        # Create test order payload
        order_payload = OrderCreate(
            items=[{
                "product_id": product.id,
                "pack_quantity": 1
            }],
            shipping_address="Test Shipping Address",
            payment_method="cod"
        )
        
        # Test with unverified user
        print("\n   Testing with unverified user...")
        
        with patch('app.api.routes.orders.create_verification_token') as mock_create_token, \
             patch('app.api.routes.orders.send_verification_email', new=AsyncMock()) as mock_send_email:
            
            mock_create_token.return_value = "test_token_123"
            
            try:
                await create_order(order_payload, db, unverified_user)
                print("❌ Order creation should have been blocked!")
            except Exception as e:
                if "verify your email address" in str(e):
                    print("✅ Unverified user correctly blocked")
                    print(f"   Error message: {e}")
                    
                    # Check if verification email was sent
                    if mock_create_token.called and mock_send_email.called:
                        print("✅ Verification email auto-sent")
                    else:
                        print("❌ Verification email not sent")
                else:
                    print(f"❌ Unexpected error: {e}")
        
        # Test with verified user
        print("\n   Testing with verified user...")
        try:
            order = await create_order(order_payload, db, verified_user)
            print("✅ Verified user can create orders")
            print(f"   Order ID: {str(order.id)[:8]}...")
        except Exception as e:
            print(f"❌ Verified user blocked: {e}")
        
        # Test with admin user (should bypass verification)
        print("\n   Testing with admin user (unverified)...")
        admin_user = User(
            id=uuid4(),
            email=f"admin-{user_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Admin User",
            role=UserRole.admin,  # Admin role
            buyer_status=BuyerStatus.approved,
            email_verified=False,  # Unverified but should bypass
            company_name="Admin Company",
            phone="+1234567890"
        )
        db.add(admin_user)
        db.commit()
        
        try:
            order = await create_order(order_payload, db, admin_user)
            print("✅ Admin user bypasses email verification")
        except Exception as e:
            if "verify your email address" in str(e):
                print("❌ Admin user should bypass email verification")
            else:
                print(f"Note: Admin blocked for other reason: {e}")
        
        print("\n🎉 Order verification test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_order_verification_logic())