#!/usr/bin/env python3
"""
Demo script to test the email service in console mode.
Run this to verify that the email service works correctly.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.email import send_verification_email, email_service


async def demo():
    """Demo the email service functionality."""
    print("🚀 Email Service Demo")
    print("=" * 50)
    
    # Verify we're in console mode (development)
    if email_service.use_console:
        print("✅ Console mode active (good for development)")
    else:
        print("📧 SMTP mode active (production configuration)")
    
    print("\n1. Testing verification email...")
    print("-" * 30)
    
    result = await send_verification_email(
        to_email="demo@example.com",
        full_name="Demo User",
        token="demo_token_12345"
    )
    
    print(f"✅ Verification email sent: {result}")
    
    print("\n2. Testing order confirmation...")
    print("-" * 30)
    
    # Create a mock order for demo
    class MockOrder:
        def __init__(self):
            import uuid
            from datetime import datetime, timezone
            self.id = uuid.uuid4()
            self.status = type('Status', (), {'value': 'pending'})()
            self.total_net = 123.45
            self.total_gross = 151.64
            self.payment_method = type('PaymentMethod', (), {'value': 'cod'})()
            self.shipping_address = "123 Demo Street\nDemo City, DC 12345"
            self.company_name = "Demo Company Ltd"
            self.recipient_name = "Demo Recipient"
            self.recipient_phone = "+1-555-DEMO"
            self.created_at = datetime.now(timezone.utc)
            self.items = [
                type('Item', (), {
                    'product_name_snapshot': 'Demo Product 1',
                    'pack_size_snapshot': 12,
                    'pack_quantity': 2,
                    'price_net_snapshot': 25.50
                })(),
                type('Item', (), {
                    'product_name_snapshot': 'Demo Product 2', 
                    'pack_size_snapshot': 6,
                    'pack_quantity': 3,
                    'price_net_snapshot': 24.15
                })()
            ]
    
    mock_order = MockOrder()
    
    result = await email_service.send_order_confirmation(
        to_email="buyer@example.com",
        full_name="Demo Buyer", 
        order=mock_order
    )
    
    print(f"✅ Order confirmation sent: {result}")
    
    print("\n3. Testing product archived notice...")
    print("-" * 30)
    
    result = await email_service.send_product_archived_notice(
        to_email="affected-buyer@example.com",
        full_name="Affected Buyer",
        order_id=str(mock_order.id),
        product_names=["Discontinued Product A", "Out of Stock Product B"]
    )
    
    print(f"✅ Product archived notice sent: {result}")
    
    print("\n🎉 Demo completed successfully!")
    print("\nIn development mode, all emails are logged to console.")
    print("In production, configure SMTP settings in .env to send real emails.")


if __name__ == "__main__":
    asyncio.run(demo())