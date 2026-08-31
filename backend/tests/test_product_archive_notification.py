import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import User, UserRole, BuyerStatus
from app.models.product import Product, StockStatus
from app.models.category import Category
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.order_item import OrderItem
from app.core.auth import get_password_hash


def create_test_data(db_session: Session):
    """Helper to create test user, product, and order."""
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
        is_active=True  # Active product
    )
    db_session.add(product)
    db_session.flush()
    
    # Create buyer
    buyer = User(
        id=uuid4(),
        email=f"buyer-{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Buyer",
        role=UserRole.buyer,
        buyer_status=BuyerStatus.approved,
        email_verified=True,
        company_name="Test Company"
    )
    db_session.add(buyer)
    db_session.flush()
    
    # Create open order with the product
    order = Order(
        id=uuid4(),
        buyer_id=buyer.id,
        status=OrderStatus.pending,  # Open status
        total_net=20.00,
        total_gross=24.60,
        shipping_address="Test Address",
        payment_method=PaymentMethod.cod,
        company_name="Test Company",
        recipient_name="Test Recipient"
    )
    db_session.add(order)
    db_session.flush()
    
    # Create order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name_snapshot=product.name,
        pack_size_snapshot=product.pack_size,
        price_net_snapshot=product.price_net,
        price_gross_snapshot=product.price_gross,
        pack_quantity=2
    )
    db_session.add(order_item)
    db_session.flush()
    
    return buyer, product, order


@pytest.mark.asyncio
async def test_archive_product_with_open_orders_sends_notification(db_session: Session):
    """Test that archiving a product with open orders sends notification emails."""
    from app.api.routes.products import archive_product
    
    # Create test data
    buyer, product, order = create_test_data(db_session)
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock the email sending function
    with patch('app.api.routes.products.send_product_archived_email', new=AsyncMock()) as mock_send_email:
        
        # Archive the product (force=True to bypass the warning)
        result = await archive_product(product.id, db_session, admin_user, force=True)
        
        # Verify product was archived
        assert result.is_active is False
        
        # Verify notification email was sent
        mock_send_email.assert_called_once_with(
            buyer.email,
            buyer.full_name,
            str(order.id),
            [product.name]
        )


@pytest.mark.asyncio
async def test_archive_product_without_open_orders_no_notification(db_session: Session):
    """Test that archiving a product without open orders doesn't send notifications."""
    from app.api.routes.products import archive_product
    
    # Create category and product only (no orders)
    category = Category(
        id=uuid4(),
        name=f"Test Category {uuid4().hex[:8]}",
        slug=f"test-category-{uuid4().hex[:8]}",
        is_active=True
    )
    db_session.add(category)
    db_session.flush()
    
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
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock the email sending function
    with patch('app.api.routes.products.send_product_archived_email', new=AsyncMock()) as mock_send_email:
        
        # Archive the product
        result = await archive_product(product.id, db_session, admin_user)
        
        # Verify product was archived
        assert result.is_active is False
        
        # Verify NO notification email was sent
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_archive_product_with_closed_orders_no_notification(db_session: Session):
    """Test that products with only closed orders don't trigger notifications."""
    from app.api.routes.products import archive_product
    
    # Create test data but with closed order
    buyer, product, order = create_test_data(db_session)
    
    # Change order status to closed
    order.status = OrderStatus.delivered  # Closed status
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock the email sending function
    with patch('app.api.routes.products.send_product_archived_email', new=AsyncMock()) as mock_send_email:
        
        # Archive the product
        result = await archive_product(product.id, db_session, admin_user)
        
        # Verify product was archived
        assert result.is_active is False
        
        # Verify NO notification email was sent (order is closed)
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_archive_product_multiple_buyers_multiple_notifications(db_session: Session):
    """Test that multiple buyers with open orders each get notified."""
    from app.api.routes.products import archive_product
    
    # Create category and product
    category = Category(
        id=uuid4(),
        name=f"Test Category {uuid4().hex[:8]}",
        slug=f"test-category-{uuid4().hex[:8]}",
        is_active=True
    )
    db_session.add(category)
    db_session.flush()
    
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
    
    # Create two different buyers
    buyers = []
    orders = []
    
    for i in range(2):
        buyer = User(
            id=uuid4(),
            email=f"buyer{i}-{uuid4().hex[:8]}@example.com",
            hashed_password=get_password_hash("password123"),
            full_name=f"Test Buyer {i}",
            role=UserRole.buyer,
            buyer_status=BuyerStatus.approved,
            email_verified=True,
            company_name=f"Test Company {i}"
        )
        db_session.add(buyer)
        db_session.flush()
        buyers.append(buyer)
        
        # Create order for each buyer
        order = Order(
            id=uuid4(),
            buyer_id=buyer.id,
            status=OrderStatus.confirmed,  # Open status
            total_net=20.00,
            total_gross=24.60,
            shipping_address=f"Test Address {i}",
            payment_method=PaymentMethod.cod,
            company_name=f"Test Company {i}",
            recipient_name=f"Test Recipient {i}"
        )
        db_session.add(order)
        db_session.flush()
        orders.append(order)
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name_snapshot=product.name,
            pack_size_snapshot=product.pack_size,
            price_net_snapshot=product.price_net,
            price_gross_snapshot=product.price_gross,
            pack_quantity=1
        )
        db_session.add(order_item)
    
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock the email sending function
    with patch('app.api.routes.products.send_product_archived_email', new=AsyncMock()) as mock_send_email:
        
        # Archive the product (force=True to bypass warning)
        result = await archive_product(product.id, db_session, admin_user, force=True)
        
        # Verify product was archived
        assert result.is_active is False
        
        # Verify two notification emails were sent (one per buyer)
        assert mock_send_email.call_count == 2
        
        # Verify each buyer got notified
        call_args_list = mock_send_email.call_args_list
        notified_emails = {call[0][0] for call in call_args_list}  # First arg is email
        expected_emails = {buyer.email for buyer in buyers}
        assert notified_emails == expected_emails


@pytest.mark.asyncio
async def test_unarchive_product_no_notification(db_session: Session):
    """Test that unarchiving (restoring) a product doesn't send notifications."""
    from app.api.routes.products import archive_product
    
    # Create test data with archived product
    buyer, product, order = create_test_data(db_session)
    product.is_active = False  # Already archived
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock the email sending function
    with patch('app.api.routes.products.send_product_archived_email', new=AsyncMock()) as mock_send_email:
        
        # Unarchive the product (toggle back to active)
        result = await archive_product(product.id, db_session, admin_user)
        
        # Verify product was unarchived (restored)
        assert result.is_active is True
        
        # Verify NO notification email was sent (this is unarchiving, not archiving)
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_archive_product_email_failure_still_archives(db_session: Session):
    """Test that product is still archived even if notification email fails."""
    from app.api.routes.products import archive_product
    
    # Create test data
    buyer, product, order = create_test_data(db_session)
    db_session.commit()
    
    # Mock admin user
    admin_user = User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.admin,
        buyer_status=BuyerStatus.approved,
        email_verified=True
    )
    
    # Mock email sending to fail
    with patch('app.api.routes.products.send_product_archived_email', 
               new=AsyncMock(side_effect=Exception("Email service down"))):
        
        # Archive the product (force=True to bypass warning)
        result = await archive_product(product.id, db_session, admin_user, force=True)
        
        # Verify product was still archived despite email failure
        assert result.is_active is False
        
        # Verify the product is archived in the database
        db_product = db_session.query(Product).filter(Product.id == product.id).first()
        assert db_product.is_active is False