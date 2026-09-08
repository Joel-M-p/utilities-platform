import smtplib
from email.message import EmailMessage
import os

# --- TWILIO SMS SETUP ---
try:
    from twilio.rest import Client
    # Leave these as dummy values for now. When you go live, replace them with your real Twilio keys.
    TWILIO_ACCOUNT_SID = "your_account_sid"
    TWILIO_AUTH_TOKEN = "your_auth_token"
    TWILIO_PHONE_NUMBER = "+1234567890"
    
    if "your_account_sid" in TWILIO_ACCOUNT_SID:
        twilio_client = None
    else:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except ImportError:
    twilio_client = None
    print("Twilio not installed. SMS will be simulated.")

# --- EMAIL SMTP SETUP ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# Leave these as dummy values. When you go live, put your real email and app password here.
SMTP_EMAIL = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"

def send_email(to_email, subject, body):
    if "your_email" in SMTP_EMAIL:
        print(f"[SIMULATED EMAIL] To: {to_email} | Subject: {subject} | Body: {body}")
        return
        
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        msg.set_content(body)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def send_sms(to_phone, body):
    if not twilio_client:
        print(f"[SIMULATED SMS] To: {to_phone} | Body: {body}")
        return
        
    try:
        message = twilio_client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        print(f"✅ SMS sent to {to_phone}: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")

# --- MASTER NOTIFICATION FUNCTION ---
def send_notification(tenant_name, contact_info, message, subject="Utilities Platform Notification"):
    print("\n" + "="*50)
    print("📱 NOTIFICATION MODULE")
    print(f"To: {tenant_name} ({contact_info})")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print("="*50 + "\n")
    
    # If contact_info contains '@', treat as email
    if '@' in contact_info:
        send_email(contact_info, subject, message)
    else:
        # Assume it's a phone number
        send_sms(contact_info, message)