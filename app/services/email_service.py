import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.logger import logger
from config.settings import settings


def send_payment_confirmation(to_email: str) -> None:
    html_body = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 24px;">
        <h1 style="color: #10b981;">Bienvenue dans voclaire Pro !</h1>
        <p>Bonjour,</p>
        <p>Votre abonnement <strong>voclaire Pro</strong> est maintenant actif. Vous avez accès à toutes les fonctionnalités premium :</p>
        <ul>
            <li>Transcription audio illimitée</li>
            <li>Post-traitement LLM illimité (correction, reformulation, résumé)</li>
            <li>Export de documents (DOCX, PDF, PPTX)</li>
            <li>Modèle Whisper fine-tuné pour le français</li>
        </ul>
        <p>
            <a href="http://localhost:5173/app"
               style="display: inline-block; background-color: #10b981; color: white;
                      padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                Accéder à mon espace
            </a>
        </p>
        <p style="color: #888; font-size: 0.9em; margin-top: 32px;">
            Merci de faire confiance à voclaire.
        </p>
    </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Bienvenue dans voclaire Pro !"
    message["From"] = settings.SMTP_USER
    message["To"] = to_email
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, message.as_string())

    logger.info(f"Email de confirmation envoyé à {to_email}")
