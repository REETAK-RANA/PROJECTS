import smtplib
import ssl

# SMTP server configuration for Gmail
smtp_server = "smtp.gmail.com"
port = 587  # TLS port
sender_email = "rajputpraful791@gmail.com"
receiver_email = "reetakrana65@gmail.com"
password = "tehj edww iiqu cwgy"

# Email message
message = """\
Subject: Test Email from Python

Hello,
This is a test email sent from a Python script."""

# Create a secure SSL context
context = ssl.create_default_context()

# Sending email
with smtplib.SMTP(smtp_server, port) as server:
    server.starttls(context=context)  # Secure the connection
    server.login(sender_email, password)  # Login to email account
    server.sendmail(sender_email, receiver_email, message)  # Send email

print("Email sent successfully!")
