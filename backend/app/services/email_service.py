import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "electrohub@example.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.use_mock = not self.sender_password
    
    def send_contact_seller_email(self, to_email, from_email, from_name, subject, message, item_title=""):
        if self.use_mock:
            logger.info(f"📧 [MOCK] Email to {to_email}: {subject}")
            return True
        
        try:
            html_body = f"""<html><body><h2>New Message from {from_name}</h2><p><strong>Email:</strong> {from_email}</p>{f'<p><strong>Item:</strong> {item_title}</p>' if item_title else ''}<p>{message}</p><a href="http://localhost:3000/messages">Reply via ElectroHub</a></body></html>"""
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[ElectroHub] {subject}"
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return False
    
    def send_message_notification(self, to_email, from_name, subject, item_title):
        if self.use_mock:
            logger.info(f"📧 [MOCK] Notification to {to_email}")
            return True
        
        try:
            html_body = f"<html><body><h2>New Message</h2><p>{from_name} sent you a message about {item_title}: {subject}</p></body></html>"
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "[ElectroHub] New Message"
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return True
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return False
