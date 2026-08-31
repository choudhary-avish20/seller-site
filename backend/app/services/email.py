import logging
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service with SMTP and console fallback backends."""
    
    def __init__(self):
        self.use_console = not bool(settings.MAIL_USERNAME.strip())
        
        if not self.use_console:
            # Configure FastMail for SMTP
            self.conf = ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=settings.MAIL_PASSWORD,
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_SERVER,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=settings.MAIL_TLS,
                MAIL_SSL_TLS=settings.MAIL_SSL,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True
            )
            self.fastmail = FastMail(self.conf)
        else:
            logger.info("Email service initialized in console mode (MAIL_USERNAME not configured)")
    
    async def send_verification_email(
        self, 
        to_email: EmailStr, 
        full_name: str, 
        verification_url: str
    ) -> bool:
        """Send email verification email with verification link."""
        subject = "Verify your email address"
        
        # Plain text version
        text_body = f"""
Hello {full_name},

Welcome to Wholesale Marketplace! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
Wholesale Marketplace Team
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0f172a;">Welcome to Wholesale Marketplace!</h2>
                
                <p>Hello {full_name},</p>
                
                <p>Thank you for creating an account with us. Please verify your email address to complete your registration.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #0099cc; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>This link will expire in 24 hours.</p>
                
                <p>If you didn't create an account, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    Wholesale Marketplace Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
    
    async def send_order_confirmation(
        self, 
        to_email: EmailStr, 
        full_name: str, 
        order: "Order"  # Forward reference to avoid circular import
    ) -> bool:
        """Send order confirmation email with order details."""
        subject = f"Order Confirmation #{str(order.id)[:8]}"
        
        # Build items list for email
        items_text = []
        items_html = []
        
        for item in order.items:
            line_total = float(item.price_net_snapshot) * item.pack_quantity
            items_text.append(
                f"• {item.product_name_snapshot} (pack of {item.pack_size_snapshot}) "
                f"x{item.pack_quantity} = ${line_total:.2f}"
            )
            items_html.append(
                f"<tr>"
                f"<td>{item.product_name_snapshot}</td>"
                f"<td>Pack of {item.pack_size_snapshot}</td>"
                f"<td>{item.pack_quantity}</td>"
                f"<td>${float(item.price_net_snapshot):.2f}</td>"
                f"<td>${line_total:.2f}</td>"
                f"</tr>"
            )
        
        # Plain text version
        text_body = f"""
Order Confirmation

Hello {full_name},

Thank you for your order! Here are the details:

Order ID: {str(order.id)[:8]}
Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}
Status: {order.status.value.title()}

Items:
{chr(10).join(items_text)}

Total (Net): ${float(order.total_net):.2f}
Total (Gross): ${float(order.total_gross):.2f}

Payment Method: {order.payment_method.value.upper()}
Shipping Address:
{order.shipping_address}

Company: {order.company_name or 'N/A'}
Recipient: {order.recipient_name or 'N/A'}
Phone: {order.recipient_phone or 'N/A'}

We'll process your order and keep you updated on its status.

Best regards,
Wholesale Marketplace Team
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0f172a;">Order Confirmation</h2>
                
                <p>Hello {full_name},</p>
                
                <p>Thank you for your order! Here are the details:</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order ID:</strong> {str(order.id)[:8]}</p>
                    <p><strong>Date:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M')}</p>
                    <p><strong>Status:</strong> {order.status.value.title()}</p>
                </div>
                
                <h3>Items Ordered:</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background: #f1f5f9;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Product</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Pack Size</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Quantity</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Unit Price</th>
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Total</th>
                    </tr>
                    {''.join(items_html)}
                </table>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Total (Net):</strong> ${float(order.total_net):.2f}</p>
                    <p><strong>Total (Gross):</strong> ${float(order.total_gross):.2f}</p>
                </div>
                
                <h3>Delivery Information:</h3>
                <p><strong>Payment Method:</strong> {order.payment_method.value.upper()}</p>
                <p><strong>Shipping Address:</strong><br>{order.shipping_address.replace(chr(10), '<br>')}</p>
                <p><strong>Company:</strong> {order.company_name or 'N/A'}</p>
                <p><strong>Recipient:</strong> {order.recipient_name or 'N/A'}</p>
                <p><strong>Phone:</strong> {order.recipient_phone or 'N/A'}</p>
                
                <p style="margin-top: 30px;">We'll process your order and keep you updated on its status.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    Wholesale Marketplace Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
    
    async def send_product_archived_notice(
        self, 
        to_email: EmailStr, 
        full_name: str, 
        order_id: str, 
        product_names: List[str]
    ) -> bool:
        """Send notification when products in buyer's order are archived."""
        subject = f"Product Update for Order #{order_id[:8]}"
        
        products_list = "\n".join(f"• {name}" for name in product_names)
        products_html = "".join(f"<li>{name}</li>" for name in product_names)
        
        # Plain text version
        text_body = f"""
Product Update Notification

Hello {full_name},

We're writing to inform you about an update to your order #{order_id[:8]}.

The following product(s) in your order have been archived and are no longer available:

{products_list}

If your order status is still pending or confirmed, please contact us to discuss alternatives or modifications to your order.

We apologize for any inconvenience this may cause.

Best regards,
Wholesale Marketplace Team
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
        <head></head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc2626;">Product Update Notification</h2>
                
                <p>Hello {full_name},</p>
                
                <p>We're writing to inform you about an update to your order <strong>#{order_id[:8]}</strong>.</p>
                
                <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <p><strong>The following product(s) in your order have been archived and are no longer available:</strong></p>
                    <ul>
                        {products_html}
                    </ul>
                </div>
                
                <p>If your order status is still pending or confirmed, please contact us to discuss alternatives or modifications to your order.</p>
                
                <p>We apologize for any inconvenience this may cause.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Best regards,<br>
                    Wholesale Marketplace Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self._send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
    
    async def _send_email(
        self, 
        to_email: EmailStr, 
        subject: str, 
        text_body: str, 
        html_body: str
    ) -> bool:
        """Internal method to send email via SMTP or log to console."""
        try:
            if self.use_console:
                # Console backend for development
                logger.info(f"""
================== EMAIL (CONSOLE MODE) ==================
To: {to_email}
Subject: {subject}
---
{text_body}
===========================================================
                """)
                return True
            else:
                # SMTP backend for production
                message = MessageSchema(
                    subject=subject,
                    recipients=[to_email],
                    body=text_body,
                    html=html_body,
                    subtype=MessageType.html
                )
                
                await self.fastmail.send_message(message)
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()


async def send_verification_email(to_email: EmailStr, full_name: str, token: str) -> bool:
    """Helper function to send verification email with token URL."""
    verification_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
    return await email_service.send_verification_email(to_email, full_name, verification_url)


async def send_order_confirmation_email(to_email: EmailStr, full_name: str, order) -> bool:
    """Helper function to send order confirmation email."""
    return await email_service.send_order_confirmation(to_email, full_name, order)


async def send_product_archived_email(to_email: EmailStr, full_name: str, order_id: str, product_names: List[str]) -> bool:
    """Helper function to send product archived notification email."""
    return await email_service.send_product_archived_notice(to_email, full_name, order_id, product_names)