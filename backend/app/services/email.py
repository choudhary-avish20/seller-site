import logging
from typing import List

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Shared HTML wrapper ────────────────────────────────────────────────────

def _html_wrap(title: str, body_html: str, accent: str = "#0099cc") -> str:
    return f"""<!DOCTYPE html>
<html lang="pl">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif">
<div style="max-width:600px;margin:32px auto;background:#fff;border:1px solid #ddd">
  <div style="background:{accent};padding:14px 20px">
    <span style="color:#fff;font-size:16px;font-weight:bold">WolkaGo</span>
  </div>
  <div style="padding:24px 20px;font-size:13px;color:#333;line-height:1.6">
    <h2 style="margin:0 0 16px;font-size:16px;color:#222">{title}</h2>
    {body_html}
  </div>
  <div style="background:#f5f5f5;border-top:1px solid #ddd;padding:10px 20px;font-size:11px;color:#888">
    WolkaGo &bull; Wólka Kosowska &bull; +48 579 383 945
  </div>
</div>
</body>
</html>"""


class EmailService:
    """Email service — SMTP when MAIL_USERNAME is set, console fallback for dev."""

    def __init__(self):
        self.use_console = not bool(settings.MAIL_USERNAME.strip())

        if not self.use_console:
            import sys
            print(
                f"[EMAIL] Initialising SMTP: server={settings.MAIL_SERVER} "
                f"port={settings.MAIL_PORT} username={settings.MAIL_USERNAME} "
                f"from={settings.MAIL_FROM} tls={settings.MAIL_TLS} ssl={settings.MAIL_SSL}",
                file=sys.stderr, flush=True,
            )
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
                VALIDATE_CERTS=True,
                TIMEOUT=10,  # fail fast — surface errors instead of hanging
            )
            self.fastmail = FastMail(self.conf)
        else:
            import sys
            print("[EMAIL] MAIL_USERNAME is not set — running in CONSOLE MODE (no real emails sent)", file=sys.stderr, flush=True)
            logger.info("Email service: tryb konsolowy (MAIL_USERNAME nie ustawiony)")

    # ── Public methods ─────────────────────────────────────────────────────

    async def send_verification_email(
        self,
        to_email: EmailStr,
        full_name: str,
        verification_url: str,
    ) -> bool:
        subject = "Potwierdź swój adres e-mail — WolkaGo"

        text_body = f"""Witaj {full_name},

Dziękujemy za rejestrację w WolkaGo!
Kliknij poniższy link, aby potwierdzić swój adres e-mail:

{verification_url}

Link jest ważny przez 24 godziny.

Jeśli nie zakładałeś(-aś) konta, zignoruj tę wiadomość.

Pozdrawiamy,
Zespół WolkaGo"""

        body_html = f"""
<p>Witaj <strong>{full_name}</strong>,</p>
<p>Dziękujemy za rejestrację w WolkaGo! Kliknij przycisk poniżej, aby potwierdzić swój adres e-mail.</p>
<div style="text-align:center;margin:28px 0">
  <a href="{verification_url}"
     style="background:#0099cc;color:#fff;padding:12px 28px;text-decoration:none;font-weight:bold;font-size:14px;display:inline-block">
    Potwierdź adres e-mail
  </a>
</div>
<p style="font-size:12px;color:#666">Link jest ważny przez <strong>24 godziny</strong>.<br>
Jeśli nie zakładałeś(-aś) konta, zignoruj tę wiadomość.</p>"""

        return await self._send(
            to_email, subject, text_body,
            _html_wrap("Potwierdź swój adres e-mail", body_html),
        )

    async def send_order_confirmation(
        self,
        to_email: EmailStr,
        full_name: str,
        order,
    ) -> bool:
        order_short = str(order.id)[:8].upper()
        subject = f"Potwierdzenie zamówienia #{order_short} — WolkaGo"

        # Build rows
        rows_text = []
        rows_html = []
        for item in order.items:
            line_net = float(item.price_net_snapshot) * item.pack_quantity
            rows_text.append(
                f"  • {item.product_name_snapshot} "
                f"(pak {item.pack_size_snapshot} szt.) "
                f"× {item.pack_quantity} = {line_net:.2f} zł netto"
            )
            rows_html.append(
                f"<tr>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee'>{item.product_name_snapshot}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:center'>{item.pack_size_snapshot}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:center'>{item.pack_quantity}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:right'>{float(item.price_net_snapshot):.2f} zł</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:right'><strong>{line_net:.2f} zł</strong></td>"
                f"</tr>"
            )

        items_text = "\n".join(rows_text)
        items_html = "".join(rows_html)

        text_body = f"""Potwierdzenie zamówienia #{order_short}

Witaj {full_name},

Twoje zamówienie zostało przyjęte. Szczegóły poniżej.

Nr zamówienia : {order_short}
Data          : {order.created_at.strftime('%d.%m.%Y %H:%M')}
Status        : Przyjęte

Zamówione produkty:
{items_text}

Razem netto : {float(order.total_net):.2f} zł
Razem brutto: {float(order.total_gross):.2f} zł

Płatność     : Za pobraniem (COD)
Adres dostawy: {order.shipping_address}
Firma        : {order.company_name or '—'}
Odbiorca     : {order.recipient_name or '—'}
Telefon      : {order.recipient_phone or '—'}

Skontaktujemy się w razie pytań.

Pozdrawiamy,
Zespół WolkaGo"""

        body_html = f"""
<p>Witaj <strong>{full_name}</strong>,</p>
<p>Twoje zamówienie zostało przyjęte. Szczegóły poniżej.</p>

<table style="width:100%;border-collapse:collapse;font-size:12px;margin:16px 0">
  <tr style="background:#f0f0f0">
    <th style="padding:7px 10px;text-align:left">Nr zamówienia</th>
    <th style="padding:7px 10px;text-align:left">Data</th>
    <th style="padding:7px 10px;text-align:left">Status</th>
  </tr>
  <tr>
    <td style="padding:7px 10px;border-bottom:1px solid #eee;font-family:monospace">{order_short}</td>
    <td style="padding:7px 10px;border-bottom:1px solid #eee">{order.created_at.strftime('%d.%m.%Y %H:%M')}</td>
    <td style="padding:7px 10px;border-bottom:1px solid #eee">
      <span style="background:#dcfce7;color:#166534;padding:2px 8px;font-size:11px;font-weight:bold">Przyjęte</span>
    </td>
  </tr>
</table>

<h3 style="font-size:13px;margin:20px 0 8px">Zamówione produkty</h3>
<table style="width:100%;border-collapse:collapse;font-size:12px">
  <tr style="background:#f0f0f0">
    <th style="padding:7px 10px;text-align:left">Produkt</th>
    <th style="padding:7px 10px;text-align:center">Pak</th>
    <th style="padding:7px 10px;text-align:center">Ilość</th>
    <th style="padding:7px 10px;text-align:right">Cena netto</th>
    <th style="padding:7px 10px;text-align:right">Razem</th>
  </tr>
  {items_html}
</table>

<table style="width:100%;border-collapse:collapse;font-size:13px;margin:12px 0">
  <tr>
    <td style="padding:6px 10px;font-weight:bold">Razem netto</td>
    <td style="padding:6px 10px;text-align:right;font-weight:bold">{float(order.total_net):.2f} zł</td>
  </tr>
  <tr style="background:#f5f5f5">
    <td style="padding:6px 10px">Razem brutto</td>
    <td style="padding:6px 10px;text-align:right">{float(order.total_gross):.2f} zł</td>
  </tr>
</table>

<h3 style="font-size:13px;margin:20px 0 8px">Dane dostawy</h3>
<table style="font-size:12px;border-collapse:collapse;width:100%">
  <tr><td style="color:#666;padding:3px 10px 3px 0;white-space:nowrap">Płatność:</td><td><strong>Za pobraniem (COD)</strong></td></tr>
  <tr><td style="color:#666;padding:3px 10px 3px 0;white-space:nowrap">Adres:</td><td>{order.shipping_address.replace(chr(10), ', ')}</td></tr>
  <tr><td style="color:#666;padding:3px 10px 3px 0;white-space:nowrap">Firma:</td><td>{order.company_name or '—'}</td></tr>
  <tr><td style="color:#666;padding:3px 10px 3px 0;white-space:nowrap">Odbiorca:</td><td>{order.recipient_name or '—'}</td></tr>
  <tr><td style="color:#666;padding:3px 10px 3px 0;white-space:nowrap">Telefon:</td><td>{order.recipient_phone or '—'}</td></tr>
</table>

<p style="margin-top:20px;font-size:12px;color:#555">Skontaktujemy się w razie pytań.</p>"""

        return await self._send(
            to_email, subject, text_body,
            _html_wrap(f"Potwierdzenie zamówienia #{order_short}", body_html),
        )

    async def send_order_cancellation(
        self,
        to_email: EmailStr,
        full_name: str,
        order,
    ) -> bool:
        """Dedicated cancellation email — includes the full item list and totals
        so the buyer can see exactly what was cancelled."""
        order_short = str(order.id)[:8].upper()
        subject = f"Zamówienie anulowane #{order_short} — WolkaGo"

        rows_text = []
        rows_html = []
        for item in order.items:
            line_net = float(item.price_net_snapshot) * item.pack_quantity
            rows_text.append(
                f"  • {item.product_name_snapshot} "
                f"(pak {item.pack_size_snapshot} szt.) "
                f"× {item.pack_quantity} = {line_net:.2f} zł netto"
            )
            rows_html.append(
                f"<tr>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee'>{item.product_name_snapshot}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:center'>{item.pack_size_snapshot}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:center'>{item.pack_quantity}</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:right'>{float(item.price_net_snapshot):.2f} zł</td>"
                f"<td style='padding:7px 10px;border-bottom:1px solid #eee;text-align:right'><strong>{line_net:.2f} zł</strong></td>"
                f"</tr>"
            )

        items_text = "\n".join(rows_text)
        items_html = "".join(rows_html)

        text_body = f"""Zamówienie anulowane #{order_short}

Witaj {full_name},

Twoje zamówienie #{order_short} zostało anulowane.

Anulowane produkty:
{items_text}

Razem netto : {float(order.total_net):.2f} zł
Razem brutto: {float(order.total_gross):.2f} zł

Jeśli uważasz, że to pomyłka lub masz pytania, skontaktuj się z nami:
📞 +48 579 383 945

Pozdrawiamy,
Zespół WolkaGo"""

        body_html = f"""
<p>Witaj <strong>{full_name}</strong>,</p>
<p>Informujemy, że Twoje zamówienie zostało <strong style="color:#991b1b">anulowane</strong>.</p>

<div style="background:#fef2f2;border-left:4px solid #991b1b;padding:10px 16px;margin:16px 0;font-size:13px">
  Nr zamówienia: <strong style="font-family:monospace">{order_short}</strong>
</div>

<h3 style="font-size:13px;margin:20px 0 8px">Anulowane produkty</h3>
<table style="width:100%;border-collapse:collapse;font-size:12px">
  <tr style="background:#f0f0f0">
    <th style="padding:7px 10px;text-align:left">Produkt</th>
    <th style="padding:7px 10px;text-align:center">Pak</th>
    <th style="padding:7px 10px;text-align:center">Ilość</th>
    <th style="padding:7px 10px;text-align:right">Cena netto</th>
    <th style="padding:7px 10px;text-align:right">Razem</th>
  </tr>
  {items_html}
</table>

<table style="width:100%;border-collapse:collapse;font-size:13px;margin:12px 0">
  <tr>
    <td style="padding:6px 10px;font-weight:bold">Razem netto</td>
    <td style="padding:6px 10px;text-align:right;font-weight:bold">{float(order.total_net):.2f} zł</td>
  </tr>
  <tr style="background:#f5f5f5">
    <td style="padding:6px 10px">Razem brutto</td>
    <td style="padding:6px 10px;text-align:right">{float(order.total_gross):.2f} zł</td>
  </tr>
</table>

<p style="font-size:12px;color:#555;margin-top:20px">
  Jeśli uważasz, że to pomyłka lub masz pytania, zadzwoń do nas:<br>
  <strong>+48 579 383 945</strong>
</p>"""

        return await self._send(
            to_email, subject, text_body,
            _html_wrap(f"Zamówienie anulowane #{order_short}", body_html, "#991b1b"),
        )

    async def send_order_status_email(
        self,
        to_email: EmailStr,
        full_name: str,
        order_id: str,
        new_status: str,
    ) -> bool:
        """Notify buyer when seller changes order status to 'delivered' or 'cancelled'."""
        order_short = order_id[:8].upper()

        status_labels = {
            "delivered": ("Zamówienie zrealizowane", "#166534", "#dcfce7"),
            "cancelled": ("Zamówienie anulowane",    "#991b1b", "#fef2f2"),
            "confirmed": ("Zamówienie potwierdzone", "#1e40af", "#dbeafe"),
            "shipped":   ("Zamówienie wysłane",      "#92400e", "#fef3c7"),
            "out_for_delivery": ("Zamówienie w dostawie", "#0e7490", "#ecfeff"),
        }
        label, text_color, bg_color = status_labels.get(
            new_status, ("Zmiana statusu zamówienia", "#333", "#f5f5f5")
        )

        subject = f"{label} #{order_short} — WolkaGo"

        status_notes = {
            "delivered": "Twoje zamówienie zostało oznaczone jako zrealizowane. Jeśli masz jakiekolwiek pytania, skontaktuj się z nami.",
            "cancelled": "Twoje zamówienie zostało anulowane. Jeśli uważasz, że to pomyłka, skontaktuj się z nami pod numerem +48 579 383 945.",
            "confirmed": "Twoje zamówienie zostało potwierdzone i jest w trakcie realizacji.",
            "shipped":   "Twoje zamówienie zostało wysłane. Wkrótce do Ciebie dotrze.",
            "out_for_delivery": "Twój kurier jest już w drodze — zamówienie dotrze do Ciebie już dziś.",
        }
        note = status_notes.get(new_status, "Status Twojego zamówienia uległ zmianie.")

        text_body = f"""{label} #{order_short}

Witaj {full_name},

{note}

Nr zamówienia: {order_short}

W razie pytań zadzwoń: +48 579 383 945

Pozdrawiamy,
Zespół WolkaGo"""

        body_html = f"""
<p>Witaj <strong>{full_name}</strong>,</p>
<p>{note}</p>

<div style="background:{bg_color};border-left:4px solid {text_color};padding:12px 16px;margin:20px 0;font-size:13px">
  Nr zamówienia: <strong style="font-family:monospace">{order_short}</strong><br>
  Nowy status: <strong style="color:{text_color}">{label}</strong>
</div>

<p style="font-size:12px;color:#555">W razie pytań zadzwoń: <strong>+48 579 383 945</strong></p>"""

        return await self._send(
            to_email, subject, text_body,
            _html_wrap(label, body_html, text_color),
        )

    async def send_product_archived_notice(
        self,
        to_email: EmailStr,
        full_name: str,
        order_id: str,
        product_names: List[str],
    ) -> bool:
        order_short = order_id[:8].upper()
        subject = f"Informacja o zamówieniu #{order_short} — WolkaGo"

        products_text = "\n".join(f"  • {n}" for n in product_names)
        products_html = "".join(f"<li>{n}</li>" for n in product_names)

        text_body = f"""Informacja o zamówieniu #{order_short}

Witaj {full_name},

Informujemy, że następujące produkty z Twojego zamówienia #{order_short} zostały wycofane ze sprzedaży:

{products_text}

Jeśli Twoje zamówienie jest w toku (oczekujące lub potwierdzone), skontaktuj się z nami, abyśmy mogli omówić dostępne opcje.

Przepraszamy za utrudnienia.

Pozdrawiamy,
Zespół WolkaGo"""

        body_html = f"""
<p>Witaj <strong>{full_name}</strong>,</p>
<p>Informujemy, że następujące produkty z Twojego zamówienia <strong>#{order_short}</strong> zostały wycofane ze sprzedaży:</p>

<div style="background:#fef2f2;border-left:4px solid #dc2626;padding:12px 16px;margin:16px 0">
  <ul style="margin:0;padding-left:18px">
    {products_html}
  </ul>
</div>

<p>Jeśli Twoje zamówienie jest w toku, skontaktuj się z nami pod numerem <strong>+48 579 383 945</strong>, abyśmy mogli omówić dostępne opcje.</p>
<p style="font-size:12px;color:#555">Przepraszamy za utrudnienia.</p>"""

        return await self._send(
            to_email, subject, text_body,
            _html_wrap(f"Informacja o zamówieniu #{order_short}", body_html, "#dc2626"),
        )

    # ── Internal ───────────────────────────────────────────────────────────

    async def _send(
        self,
        to_email: EmailStr,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> bool:
        try:
            if self.use_console:
                logger.info(
                    "\n================== EMAIL (TRYB KONSOLOWY) ==================\n"
                    f"Do     : {to_email}\n"
                    f"Temat  : {subject}\n"
                    "------------------------------------------------------------\n"
                    f"{text_body}\n"
                    "============================================================"
                )
                return True

            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=text_body,
                html=html_body,
                subtype=MessageType.html,
            )
            await self.fastmail.send_message(message)
            logger.info(f"E-mail wysłany do {to_email}: {subject}")
            return True

        except Exception as e:
            import sys, traceback
            print(f"[EMAIL ERROR] Failed to send to {to_email}: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            logger.exception(f"Błąd wysyłki e-mail do {to_email}: {e}")
            return False


# ── Module-level helpers ───────────────────────────────────────────────────

email_service = EmailService()


async def send_verification_email(to_email: EmailStr, full_name: str, token: str) -> bool:
    """Send email-verification link. Points at the backend endpoint which consumes
    the token server-side and then redirects the browser to the frontend result page.
    This avoids the frontend needing to know the backend URL or call the API itself."""
    verification_url = (
        f"{settings.BACKEND_BASE_URL.rstrip('/')}"
        f"/api/v1/auth/verify-email?token={token}"
    )
    return await email_service.send_verification_email(to_email, full_name, verification_url)


async def send_order_confirmation_email(to_email: EmailStr, full_name: str, order) -> bool:
    return await email_service.send_order_confirmation(to_email, full_name, order)


async def send_order_status_email(to_email: EmailStr, full_name: str, order_id: str, new_status: str) -> bool:
    return await email_service.send_order_status_email(to_email, full_name, order_id, new_status)


async def send_order_cancellation_email(to_email: EmailStr, full_name: str, order) -> bool:
    return await email_service.send_order_cancellation(to_email, full_name, order)


async def send_product_archived_email(
    to_email: EmailStr, full_name: str, order_id: str, product_names: List[str]
) -> bool:
    return await email_service.send_product_archived_notice(to_email, full_name, order_id, product_names)
