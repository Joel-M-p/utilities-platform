import os

def send_notification(to_name, to_email, to_cellphone, message, subject="Utilities Notification"):
    # 1. Simulate Email
    if to_email:
        print(f"[SIMULATED EMAIL] To: {to_email} | Subject: {subject} | Body: {message}")
    
    # 2. Simulate SMS
    if to_cellphone:
        print(f"[SIMULATED SMS] To: {to_cellphone} | Body: {message}")

    # 3. Real Twilio Integration (For later when you are ready)
    """
    if to_cellphone and os.getenv("TWILIO_ACCOUNT_SID"):
        from twilio.rest import Client
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_cellphone
        )
    """