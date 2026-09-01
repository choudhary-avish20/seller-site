import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, BuyerStatus
from app.models.product import Product, StockStatus
from app.models.category import Category
from app.models.order import Order, OrderStatus, PaymentMethod
from app.core.auth import get_password_hash


def create_test_user_and_product(db_session: Session):
    """Helper to create test user and product."""
    # Create category
    category = Category(
        id=uuid4(),
        name=f"Test Category {uuid4().hex[:8]}",
        slug=f"test-category-{uuid4().hex[:8]}",
        is_active=True
    )
    db_session.add(category)
    db_session.flush()
    
    # Create product
    product = Product(
        id=uuid4(),
        category_id=category.id,
        name=f"Test Product {uuid4().hex[:8]}",
        slug=f"test-product-{uuid4().hex[:8]}",
        description="A test product",
        images="[]",
        pack_size=12,
        price_net=10.00,
        price_gross=12.30,
        vat_rate=23.00,
        stock_quantity=100,
        stock_status=StockStatus.in_stock,
        is_active=True
    )
    db_session.add(product)
    db_session.flush()
    
    # Create verified user
    user = User(
        id=uuid4(),
        email=f"buyer-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Buyer",
        role=UserRole.buyer,
        buyer_status=BuyerStatus.approved,
        email_verified=True,  # Verified so order can be placed
        company_name="Test Company",
        company_tax_id="123456789",
        company_address="Test Address",
        phone="+1234567890"
    )
    db_session.add(user)
    db_session.flush()
    
    return user, product


@pytest.mark.asyncio
async def test_order_confirmation_email_sent_on_successful_order(db_session: Session):
    """Test that order confirmation email is sent when order is created successfully."""
    from app.api.routes.orders import create_order
    from app.schemas.order import OrderCreate
    
    # Create test data
    user, product = create_test_user_and_product(db_session)
    db_session.commit()
    
    # Create order payload
    order_payload = OrderCreate(
        items=[{
            "product_id": product.id,
            "pack_quantity": 2
        }],
        shipping_address="Test Shipping Address",
        payment_method="cod",
        company_name="Test Order Company",
        recipient_name="Test Recipient",
        recipient_phone="+1234567890"
    )
    
    # Mock the email sending function
    with patch('app.api.routes.orders.send_order_confirmation_email', new=AsyncMock()) as mock_send_email:
        
        # Create the order
        order = await create_order(order_payload, db_session, user)
        
        # Verify order was created successfully
        assert order is not None
        assert order.buyer_id == user.id
        assert len(order.items) == 1
        assert order.items[0].pack_quantity == 2
        assert order.status == OrderStatus.pending
        
        # Verify confirmation email was sent
        mock_send_email.assert_called_once_with(user.email, user.full_name, order)


@pytest.mark.asyncio
async def test_order_creation_succeeds_even_if_email_fails(db_session: Session):
    """Test that order is still created successfully even if confirmation email fails."""
    from app.api.routes.orders import create_order
    from app.schemas.order import OrderCreate
    
    # Create test data
    user, product = create_test_user_and_product(db_session)
    db_session.commit()
    
    # Create order payload
    order_payload = OrderCreate(
        items=[{
            "product_id": product.id,
            "pack_quantity": 1
        }],
        shipping_address="Test Shipping Address",
        payment_method="cod"
    )
    
    # Mock email sending to fail
    with patch('app.api.routes.orders.send_order_confirmation_email', 
               new=AsyncMock(side_effect=Exception("Email service down"))):
        
        # Create the order - should still succeed despite email failure
        order = await create_order(order_payload, db_session, user)
        
        # Verify order was created successfully despite email failure
        assert order is not None
        assert order.buyer_id == user.id
        assert len(order.items) == 1
        assert order.status == OrderStatus.pending
        
        # Verify the order exists in database
        db_order = db_session.query(Order).filter(Order.id == order.id).first()
        assert db_order is not None
        assert db_order.buyer_id == user.id


def test_order_confirmation_email_content():
    """Test that the order confirmation email contains expected content."""
    from app.services.email import email_service
    
    # Create a mock order with items
    mock_order = MagicMock()
    mock_order.id = uuid4()
    mock_order.status.value = "pending"
    mock_order.total_net = 25.50
    mock_order.total_gross = 31.37
    mock_order.payment_method.value = "cod"
    mock_order.shipping_address = "123 Test Street\nTest City, TC 12345"
    mock_order.company_name = "Test Company Ltd"
    mock_order.recipient_name = "Test Recipient"
    mock_order.recipient_phone = "+1234567890"
    mock_order.created_at = datetime.now(timezone.utc)
    
    # Mock order items
    mock_item1 = MagicMock()
    mock_item1.product_name_snapshot = "Test Product 1"
    mock_item1.pack_size_snapshot = 12
    mock_item1.pack_quantity = 2
    mock_item1.price_net_snapshot = 10.50
    
    mock_item2 = MagicMock()
    mock_item2.product_name_snapshot = "Test Product 2"
    mock_item2.pack_size_snapshot = 6
    mock_item2.pack_quantity = 1
    mock_item2.price_net_snapshot = 4.50
    
    mock_order.items = [mock_item1, mock_item2]
    
    # Test in console mode (should log email content)
    email_service.use_console = True
    
    import asyncio
    import logging
    
    # Capture log output
    with patch('app.services.email.logger') as mock_logger:
        asyncio.run(email_service.send_order_confirmation(
            "buyer@example.com",
            "Test Buyer",
            mock_order
        ))
        
        # Verify logger was called (email was "sent" to console)
        mock_logger.info.assert_called_once()
        email_content = mock_logger.info.call_args[0][0]
        
        # Verify email content contains expected elements
        assert "Order Confirmation" in email_content
        assert "buyer@example.com" in email_content
        assert "Test Buyer" in email_content
        assert str(mock_order.id)[:8] in email_content
        assert "Test Product 1" in email_content
        assert "Test Product 2" in email_content
        assert "25.50" in email_content  # total_net
        assert "31.37" in email_content  # total_gross
        assert "COD" in email_content
        assert "123 Test Street" in email_content


@pytest.mark.asyncio
async def test_multiple_orders_send_multiple_confirmation_emails(db_session: Session):
    """Test that multiple orders each get their own confirmation email."""
    from app.api.routes.orders import create_order
    from app.schemas.order import OrderCreate
    
    # Create test data
    user, product = create_test_user_and_product(db_session)
    db_session.commit()
    
    # Mock the email sending function
    with patch('app.api.routes.orders.send_order_confirmation_email', new=AsyncMock()) as mock_send_email:
        
        # Create first order
        order1_payload = OrderCreate(
            items=[{"product_id": product.id, "pack_quantity": 1}],
            shipping_address="Address 1",
            payment_method="cod"
        )
        order1 = await create_order(order1_payload, db_session, user)
        
        # Create second order
        order2_payload = OrderCreate(
            items=[{"product_id": product.id, "pack_quantity": 2}],
            shipping_address="Address 2", 
            payment_method="cod"
        )
        order2 = await create_order(order2_payload, db_session, user)
        
        # Verify both orders were created
        assert order1.id != order2.id
        
        # Verify two separate email calls were made
        assert mock_send_email.call_count == 2
        
        # Verify each call was made with the correct order
        call_args_list = mock_send_email.call_args_list
        assert call_args_list[0][0][2] == order1  # Third argument is the order
        assert call_args_list[1][0][2] == order2


@pytest.mark.asyncio
async def test_order_confirmation_email_not_sent_for_unverified_users():
    """Test that no confirmation email is sent if user is unverified (order blocked)."""
    from app.api.routes.orders import create_order
    from app.schemas.order import OrderCreate
    
    # Create unverified user
    user = User(
        id=uuid4(),
        email=f"unverified-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Unverified Buyer",
        role=UserRole.buyer,
        buyer_status=BuyerStatus.approved,
        email_verified=False,  # Not verified
        company_name="Test Company"
    )
    
    with patch('app.api.routes.orders.send_order_confirmation_email', new=AsyncMock()) as mock_send_confirmation, \
         patch('app.api.routes.orders.send_verification_email', new=AsyncMock()) as mock_send_verification, \
         patch('app.api.routes.orders.create_verification_token') as mock_create_token:
        
        mock_create_token.return_value = "test_token"
        
        order_payload = OrderCreate(
            items=[{"product_id": uuid4(), "pack_quantity": 1}],
            shipping_address="Test Address",
            payment_method="cod"
        )
        
        # Attempt to create order - should be blocked
        try:
            await create_order(order_payload, MagicMock(), user)
            assert False, "Order should have been blocked"
        except Exception as e:
            assert "verify your email" in str(e).lower()
        
        # Verify verification email was sent but confirmation email was NOT sent
        mock_send_verification.assert_called_once()
        mock_send_confirmation.assert_not_called()