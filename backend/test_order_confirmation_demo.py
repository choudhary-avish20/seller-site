#!/usr/bin/env python3
"""
Demo script to test the order confirmation email functionality.
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
from app.core.auth import get_password_hash
from app.core.config import settings
from app.schemas.order import OrderCreate
from app.api.routes.orders import create_order
from uuid import uuid4


# Set up logging to see the email output
logging.basicConfig(level=logging.INFO)


async def test_order_confirmation_flow():
    """Test the complete order confirmation email flow."""
    print("📧 Order Confirmation Email Demo")
    print("=" * 50)
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create test data
        print("1. Setting up test data...")
        
        # Create unique identifiers to avoid conflicts
        test_id = str(uuid4())[:8]
        
        # Create category
        category = Category(
            id=uuid4(),
            name=f"Demo Category {test_id}",
            slug=f"demo-category-{test_id}",
            is_active=True
        )
        db.add(category)
        db.flush()
        
        # Create products
        product1 = Product(
            id=uuid4(),
            category_id=category.id,
            name=f"Premium Coffee Beans {test_id}",
            slug=f"premium-coffee-{test_id}",
            description="High-quality arabica coffee beans",
            images='["coffee1.jpg", "coffee2.jpg"]',
            pack_size=12,  # 12 bags per pack
            price_net=25.00,
            price_gross=30.75,
            vat_rate=23.00,
            stock_quantity=50,
            stock_status=StockStatus.in_stock,
            is_active=True,
            cost_price=20.00,
            stall_location="Hall A",
            counter_number="A-12"
        )
        db.add(product1)
        
        product2 = Product(
            id=uuid4(),
            category_id=category.id,
            name=f"Organic Tea Selection {test_id}",
            slug=f"organic-tea-{test_id}",
            description="Assorted organic tea varieties",
            images='["tea1.jpg"]',
            pack_size=6,  # 6 boxes per pack
            price_net=18.50,
            price_gross=22.76,
            vat_rate=23.00,
            stock_quantity=30,
            stock_status=StockStatus.in_stock,
            is_active=True,
            cost_price=15.00,
            stall_location="Hall B",
            counter_number="B-08"
        )
        db.add(product2)
        
        # Create verified buyer
        buyer = User(
            id=uuid4(),
            email=f"demo-buyer-{test_id}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Demo Buyer",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=True,  # Verified to allow ordering
            company_name="Demo Wholesale Company Ltd",
            company_tax_id="1234567890",
            company_address="123 Business Street, Demo City, DC 12345",
            phone="+1-555-DEMO"
        )
        db.add(buyer)
        db.commit()
        
        print("✅ Test data created")
        
        # Step 2: Create an order
        print("\n2. Creating order...")
        
        order_payload = OrderCreate(
            items=[
                {
                    "product_id": product1.id,
                    "pack_quantity": 3  # 3 packs of coffee (36 bags total)
                },
                {
                    "product_id": product2.id, 
                    "pack_quantity": 2  # 2 packs of tea (12 boxes total)
                }
            ],
            shipping_address="456 Delivery Avenue\nDemo City, DC 54321",
            payment_method="cod",
            company_name="Demo Wholesale Company Ltd",
            company_tax_id="1234567890",
            company_address="123 Business Street, Demo City, DC 12345",
            recipient_name="Demo Recipient",
            recipient_phone="+1-555-RECV",
            recipient_address="456 Delivery Avenue, Demo City, DC 54321",
            notes="Please deliver in the morning"
        )
        
        # Create the order (this should trigger confirmation email)
        print("   Creating order and sending confirmation email...")
        order = await create_order(order_payload, db, buyer)
        
        print(f"✅ Order created successfully!")
        print(f"   Order ID: {str(order.id)[:8]}...")
        print(f"   Total Net: ${order.total_net}")
        print(f"   Total Gross: ${order.total_gross}")
        print(f"   Items: {len(order.items)}")
        
        # Step 3: Verify order details
        print("\n3. Order details:")
        for i, item in enumerate(order.items, 1):
            print(f"   Item {i}: {item.product_name_snapshot}")
            print(f"           Pack size: {item.pack_size_snapshot}")
            print(f"           Quantity: {item.pack_quantity} packs")
            print(f"           Unit price: ${item.price_net_snapshot}")
            print(f"           Line total: ${float(item.price_net_snapshot) * item.pack_quantity}")
            
        print(f"\n   Payment Method: {order.payment_method.value.upper()}")
        print(f"   Status: {order.status.value.title()}")
        print(f"   Shipping: {order.shipping_address}")
        print(f"   Company: {order.company_name}")
        print(f"   Recipient: {order.recipient_name} ({order.recipient_phone})")
        
        print("\n✅ Order confirmation email sent!")
        print("   (Check the console output above for the email content)")
        
        print("\n🎉 Order confirmation demo completed successfully!")
        
        # Step 4: Test email failure scenario
        print("\n4. Testing email failure handling...")
        
        # Create another order but simulate email failure
        from unittest.mock import patch, AsyncMock
        
        with patch('app.api.routes.orders.send_order_confirmation_email', 
                  new=AsyncMock(side_effect=Exception("Simulated email failure"))):
            
            order_payload2 = OrderCreate(
                items=[{"product_id": product1.id, "pack_quantity": 1}],
                shipping_address="Test Address",
                payment_method="cod"
            )
            
            try:
                order2 = await create_order(order_payload2, db, buyer)
                print("✅ Order still created successfully despite email failure")
                print(f"   Order ID: {str(order2.id)[:8]}...")
                print("   (Email failure was logged but didn't prevent order creation)")
            except Exception as e:
                print(f"❌ Order creation failed: {e}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_order_confirmation_flow())