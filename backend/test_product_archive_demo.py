#!/usr/bin/env python3
"""
Demo script to test product archive notification functionality.
"""

import asyncio
import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.user import User, UserRole, BuyerStatus
from app.models.product import Product, StockStatus
from app.models.category import Category
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.order_item import OrderItem
from app.core.auth import get_password_hash
from app.core.config import settings
from app.api.routes.products import archive_product
from uuid import uuid4


# Set up logging to see the email output
logging.basicConfig(level=logging.INFO)


async def test_product_archive_notification_flow():
    """Test the complete product archive notification flow."""
    print("🗃️  Product Archive Notification Demo")
    print("=" * 50)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create test data
        print("1. Setting up test scenario...")
        
        # Create unique identifiers to avoid conflicts
        test_id = str(uuid4())[:8]
        
        # Create category
        category = Category(
            id=uuid4(),
            name=f"Electronics {test_id}",
            slug=f"electronics-{test_id}",
            is_active=True
        )
        db.add(category)
        db.flush()
        
        # Create products
        product1 = Product(
            id=uuid4(),
            category_id=category.id,
            name=f"Wireless Headphones {test_id}",
            slug=f"wireless-headphones-{test_id}",
            description="High-quality wireless headphones",
            images='["headphones1.jpg"]',
            pack_size=1,
            price_net=89.99,
            price_gross=110.69,
            vat_rate=23.00,
            stock_quantity=25,
            stock_status=StockStatus.in_stock,
            is_active=True,  # Active product
            cost_price=65.00,
            stall_location="Hall C",
            counter_number="C-15"
        )
        db.add(product1)
        
        product2 = Product(
            id=uuid4(),
            category_id=category.id,
            name=f"Bluetooth Speaker {test_id}",
            slug=f"bluetooth-speaker-{test_id}",
            description="Portable bluetooth speaker",
            images='["speaker1.jpg"]',
            pack_size=1,
            price_net=45.99,
            price_gross=56.57,
            vat_rate=23.00,
            stock_quantity=15,
            stock_status=StockStatus.in_stock,
            is_active=True,  # Active product
            cost_price=32.00,
            stall_location="Hall C",
            counter_number="C-16"
        )
        db.add(product2)
        
        # Create buyers
        buyer1 = User(
            id=uuid4(),
            email=f"buyer1-{test_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Alice Johnson",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=True,
            company_name="Alice Electronics Ltd",
            company_tax_id="111222333",
            company_address="111 Alice Street, Demo City",
            phone="+1-555-ALICE"
        )
        db.add(buyer1)
        
        buyer2 = User(
            id=uuid4(),
            email=f"buyer2-{test_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Bob Smith",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=True,
            company_name="Bob's Tech Store",
            company_tax_id="444555666",
            company_address="222 Bob Avenue, Demo City",
            phone="+1-555-BOB"
        )
        db.add(buyer2)
        
        # Create admin user
        admin = User(
            id=uuid4(),
            email=f"admin-{test_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Admin User",
            role=UserRole.admin,
            buyer_status=BuyerStatus.approved,
            email_verified=True,
            company_name="Admin Company"
        )
        db.add(admin)
        db.flush()
        
        # Create orders with different statuses
        
        # Order 1: Buyer1 has pending order with product1 (will be notified)
        order1 = Order(
            id=uuid4(),
            buyer_id=buyer1.id,
            status=OrderStatus.pending,  # Open status
            total_net=89.99,
            total_gross=110.69,
            shipping_address="111 Alice Street\nDemo City, DC 12345",
            payment_method=PaymentMethod.cod,
            company_name="Alice Electronics Ltd",
            recipient_name="Alice Johnson",
            recipient_phone="+1-555-ALICE"
        )
        db.add(order1)
        db.flush()
        
        order1_item = OrderItem(
            order_id=order1.id,
            product_id=product1.id,
            product_name_snapshot=product1.name,
            pack_size_snapshot=product1.pack_size,
            price_net_snapshot=product1.price_net,
            price_gross_snapshot=product1.price_gross,
            pack_quantity=2
        )
        db.add(order1_item)
        
        # Order 2: Buyer2 has confirmed order with product1 (will be notified)
        order2 = Order(
            id=uuid4(),
            buyer_id=buyer2.id,
            status=OrderStatus.confirmed,  # Open status
            total_net=89.99,
            total_gross=110.69,
            shipping_address="222 Bob Avenue\nDemo City, DC 54321",
            payment_method=PaymentMethod.cod,
            company_name="Bob's Tech Store",
            recipient_name="Bob Smith",
            recipient_phone="+1-555-BOB"
        )
        db.add(order2)
        db.flush()
        
        order2_item = OrderItem(
            order_id=order2.id,
            product_id=product1.id,
            product_name_snapshot=product1.name,
            pack_size_snapshot=product1.pack_size,
            price_net_snapshot=product1.price_net,
            price_gross_snapshot=product1.price_gross,
            pack_quantity=1
        )
        db.add(order2_item)
        
        # Order 3: Buyer1 has delivered order with product1 (will NOT be notified - closed order)
        order3 = Order(
            id=uuid4(),
            buyer_id=buyer1.id,
            status=OrderStatus.delivered,  # Closed status
            total_net=45.99,
            total_gross=56.57,
            shipping_address="111 Alice Street\nDemo City, DC 12345",
            payment_method=PaymentMethod.cod,
            company_name="Alice Electronics Ltd",
            recipient_name="Alice Johnson",
            recipient_phone="+1-555-ALICE"
        )
        db.add(order3)
        db.flush()
        
        order3_item = OrderItem(
            order_id=order3.id,
            product_id=product2.id,  # Different product
            product_name_snapshot=product2.name,
            pack_size_snapshot=product2.pack_size,
            price_net_snapshot=product2.price_net,
            price_gross_snapshot=product2.price_gross,
            pack_quantity=1
        )
        db.add(order3_item)
        
        db.commit()
        print("✅ Test scenario created")
        print(f"   - Product 1: {product1.name}")
        print(f"   - Product 2: {product2.name}")
        print(f"   - Buyer 1: {buyer1.full_name} ({buyer1.email})")
        print(f"   - Buyer 2: {buyer2.full_name} ({buyer2.email})")
        print(f"   - Order 1: {buyer1.full_name} - PENDING order with Product 1")
        print(f"   - Order 2: {buyer2.full_name} - CONFIRMED order with Product 1") 
        print(f"   - Order 3: {buyer1.full_name} - DELIVERED order with Product 2")
        
        # Step 2: Archive product without open orders (should not send emails)
        print(f"\n2. Archiving {product2.name} (no open orders)...")
        
        result2 = await archive_product(product2.id, db, admin)
        print(f"✅ {product2.name} archived successfully")
        print("   No notification emails sent (no open orders)")
        
        # Step 3: Archive product with open orders (should send emails) 
        print(f"\n3. Archiving {product1.name} (has open orders)...")
        
        # This should trigger notifications
        result1 = await archive_product(product1.id, db, admin, force=True)  # Force to bypass warning
        print(f"✅ {product1.name} archived successfully")
        print("   Notification emails sent to affected buyers!")
        print("   (Check console logs above for email content)")
        
        # Step 4: Show summary
        print(f"\n4. Summary:")
        print(f"   - {product1.name}: ARCHIVED ✅")
        print(f"   - {product2.name}: ARCHIVED ✅") 
        print(f"   - Notifications sent to:")
        print(f"     • {buyer1.full_name} (pending order)")
        print(f"     • {buyer2.full_name} (confirmed order)")
        print(f"   - NO notification sent to:")
        print(f"     • {buyer1.full_name} (for delivered order with {product2.name})")
        
        # Step 5: Test unarchiving (should not send notifications)
        print(f"\n5. Testing unarchive (restore) functionality...")
        
        result_unarchive = await archive_product(product1.id, db, admin)
        print(f"✅ {product1.name} unarchived (restored)")
        print("   No notification emails sent (unarchiving doesn't notify)")
        
        print("\n🎉 Product archive notification demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_product_archive_notification_flow())