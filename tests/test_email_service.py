import email as email_lib
from unittest.mock import MagicMock, patch

from app.services.email_service import send_payment_confirmation


def _make_smtp_mock() -> tuple[MagicMock, MagicMock]:
    mock_server = MagicMock()
    mock_smtp_class = MagicMock()
    mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
    return mock_smtp_class, mock_server


def _get_html_body(message_str: str) -> str:
    """Extrait et décode le body HTML du message MIME (base64 ou quoted-printable)."""
    msg = email_lib.message_from_string(message_str)
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True)
            return payload.decode("utf-8")
    return ""


def test_send_payment_confirmation_monthly():
    mock_smtp_class, mock_server = _make_smtp_mock()

    with patch("smtplib.SMTP", mock_smtp_class):
        send_payment_confirmation(to_email="client@example.com", billing_period="monthly")

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once()
    mock_server.sendmail.assert_called_once()

    _, _, message_str = mock_server.sendmail.call_args[0]
    html = _get_html_body(message_str)
    assert "mensuel" in html


def test_send_payment_confirmation_annual():
    mock_smtp_class, mock_server = _make_smtp_mock()

    with patch("smtplib.SMTP", mock_smtp_class):
        send_payment_confirmation(to_email="client@example.com", billing_period="annual")

    mock_server.sendmail.assert_called_once()
    _, _, message_str = mock_server.sendmail.call_args[0]
    html = _get_html_body(message_str)
    assert "annuel" in html
