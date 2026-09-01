import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.email import EmailService, send_verification_email
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.order_item import OrderItem


class MockOrder:
    """Mock order for testing without database dependency."""
    def __init__(self):
        self.id = uuid4()
        self.status = OrderStatus.pending
        self.total_net = 150.50
        self.total_gross = 185.12
        self.payment_method = PaymentMethod.cod
        self.shipping_address = "123 Test St\nTest City, TC 12345"
        self.company_name = "Test Company Ltd"
        self.recipient_name = "John Doe"
        self.recipient_phone = "+1234567890"
        self.created_at = datetime.now(timezone.utc)
        self.items = [
            MockOrderItem("Test Product 1", 12, 2, 25.00),
            MockOrderItem("Test Product 2", 6, 3, 33.50)
        ]


class MockOrderItem:
    """Mock order item for testing."""
    def __init__(self, product_name, pack_size, quantity, price):
        self.product_name_snapshot = product_name
        self.pack_size_snapshot = pack_size
        self.pack_quantity = quantity
        self.price_net_snapshot = price


@pytest.fixture
def email_service_console():
    """EmailService instance configured for console mode."""
    with patch('app.services.email.settings.MAIL_USERNAME', ''):
        return EmailService()


@pytest.fixture  
def email_service_smtp():
    """EmailService instance configured for SMTP mode."""
    with patch('app.services.email.settings.MAIL_USERNAME', 'test@example.com'), \
         patch('app.services.email.settings.MAIL_PASSWORD', 'password'), \
         patch('app.services.email.settings.MAIL_FROM', 'noreply@test.com'), \
         patch('app.services.email.settings.MAIL_SERVER', 'smtp.test.com'), \
         patch('app.services.email.settings.MAIL_PORT', 587):
        return EmailService()


@pytest.mark.asyncio
async def test_console_mode_initialization(email_service_console):
    """Test EmailService initializes in console mode when no MAIL_USERNAME."""
    assert email_service_console.use_console is True
    assert not hasattr(email_service_console, 'fastmail')


@pytest.mark.asyncio
async def test_smtp_mode_initialization(email_service_smtp):
    """Test EmailService initializes in SMTP mode when MAIL_USERNAME provided."""
    assert email_service_smtp.use_console is False
    assert hasattr(email_service_smtp, 'fastmail')


@pytest.mark.asyncio
async def test_send_verification_email_console(email_service_console, caplog):
    """Test verification email sending in console mode."""
    with caplog.at_level("INFO"):
        result = await email_service_console.send_verification_email(
            to_email="test@example.com",
            full_name="John Doe", 
            verification_url="http://example.com/verify?token=abc123"
        )
    
    assert result is True
    # Check that email details were logged
    assert "EMAIL (CONSOLE MODE)" in caplog.text
    assert "test@example.com" in caplog.text
    assert "Verify your email address" in caplog.text
    assert "John Doe" in caplog.text
    assert "http://example.com/verify?token=abc123" in caplog.text


@pytest.mark.asyncio
async def test_send_order_confirmation_console(email_service_console, caplog):
    """Test order confirmation email in console mode."""
    mock_order = MockOrder()
    
    with caplog.at_level("INFO"):
        result = await email_service_console.send_order_confirmation(
            to_email="buyer@example.com",
            full_name="Jane Smith",
            order=mock_order
        )
    
    assert result is True
    # Check that order details were logged
    assert "Order Confirmation" in caplog.text
    assert "buyer@example.com" in caplog.text
    assert "Jane Smith" in caplog.text
    assert "Test Product 1" in caplog.text
    assert "Test Product 2" in caplog.text
    assert "150.50" in caplog.text  # total_net
    assert "185.12" in caplog.text  # total_gross


@pytest.mark.asyncio
async def test_send_product_archived_notice_console(email_service_console, caplog):
    """Test product archived notification in console mode."""
    with caplog.at_level("INFO"):
        result = await email_service_console.send_product_archived_notice(
            to_email="buyer@example.com",
            full_name="Jane Smith",
            order_id=str(uuid4()),
            product_names=["Archived Product 1", "Archived Product 2"]
        )
    
    assert result is True
    # Check that notification details were logged
    assert "Product Update" in caplog.text
    assert "buyer@example.com" in caplog.text
    assert "Jane Smith" in caplog.text
    assert "Archived Product 1" in caplog.text
    assert "Archived Product 2" in caplog.text


@pytest.mark.asyncio
async def test_send_verification_email_smtp_success(email_service_smtp):
    """Test verification email sending via SMTP (mocked)."""
    # Mock the FastMail send_message method
    email_service_smtp.fastmail.send_message = AsyncMock()
    
    result = await email_service_smtp.send_verification_email(
        to_email="test@example.com",
        full_name="John Doe",
        verification_url="http://example.com/verify?token=abc123"
    )
    
    assert result is True
    # Verify send_message was called once
    email_service_smtp.fastmail.send_message.assert_called_once()
    
    # Check the message that was sent
    call_args = email_service_smtp.fastmail.send_message.call_args[0][0]
    assert call_args.subject == "Verify your email address"
    assert "test@example.com" in call_args.recipients
    assert "John Doe" in call_args.body
    assert "http://example.com/verify?token=abc123" in call_args.body


@pytest.mark.asyncio
async def test_send_email_smtp_failure(email_service_smtp, caplog):
    """Test email sending failure handling in SMTP mode."""
    # Mock FastMail to raise an exception
    email_service_smtp.fastmail.send_message = AsyncMock(side_effect=Exception("SMTP Error"))
    
    with caplog.at_level("ERROR"):
        result = await email_service_smtp.send_verification_email(
            to_email="test@example.com",
            full_name="John Doe", 
            verification_url="http://example.com/verify"
        )
    
    assert result is False
    assert "Failed to send email" in caplog.text
    # The actual exception message should be in the log
    assert "test@example.com" in caplog.text


@pytest.mark.asyncio 
async def test_helper_function_send_verification_email():
    """Test the helper function for sending verification emails."""
    with patch('app.services.email.email_service') as mock_service, \
         patch('app.services.email.settings.FRONTEND_BASE_URL', 'http://localhost:8000'):
        
        mock_service.send_verification_email = AsyncMock(return_value=True)
        
        result = await send_verification_email(
            to_email="test@example.com",
            full_name="John Doe",
            token="abc123token"
        )
        
        assert result is True
        mock_service.send_verification_email.assert_called_once_with(
            "test@example.com", 
            "John Doe", 
            "http://localhost:8000/verify-email?token=abc123token"
        )


@pytest.mark.asyncio
async def test_email_content_structure():
    """Test that emails contain required elements."""
    service = EmailService()
    service.use_console = True  # Force console mode
    
    # Test verification email content
    with patch('app.services.email.logger') as mock_logger:
        await service.send_verification_email(
            "test@example.com", 
            "John Doe", 
            "http://example.com/verify?token=test"
        )
        
        # Check that logger.info was called with email content
        mock_logger.info.assert_called_once()
        email_content = mock_logger.info.call_args[0][0]
        
        # Verify essential email elements are present
        assert "To: test@example.com" in email_content
        assert "Subject: Verify your email address" in email_content
        assert "Hello John Doe" in email_content
        assert "http://example.com/verify?token=test" in email_content
        assert "24 hours" in email_content


def test_email_service_configuration_validation():
    """Test that EmailService correctly determines console vs SMTP mode."""
    # Test empty username -> console mode
    with patch('app.services.email.settings.MAIL_USERNAME', ''):
        service = EmailService()
        assert service.use_console is True
    
    # Test whitespace username -> console mode  
    with patch('app.services.email.settings.MAIL_USERNAME', '   '):
        service = EmailService()
        assert service.use_console is True
    
    # Test valid username -> SMTP mode
    with patch('app.services.email.settings.MAIL_USERNAME', 'test@example.com'):
        service = EmailService()
        assert service.use_console is False