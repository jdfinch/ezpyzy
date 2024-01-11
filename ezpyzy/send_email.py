"""
Easily send emails programmatically using Python.
"""

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


def send_email(recipient, subject, message):
    """
    Send an email to the specified recipient with the specified subject and message. Create the file:

    ~/.pw/gmail.json

    {
        "smtp_server": "smtp.gmail.com",

        "smtp_port": 587,

        "sender_email": "address@gmail.com",

        "sender_password": "app_password"
    }
    """
    # Determine the user's home directory
    home_dir = os.path.expanduser("~")
    json_file_path = os.path.join(home_dir, ".pw", "gmail.json")

    # Load SMTP server settings and credentials from the JSON file
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)

        smtp_server = data['smtp_server']
        smtp_port = data['smtp_port']
        sender_email = data['sender_email']
        sender_password = data['sender_password']

    # Create a MIMEText object for the message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject

    # Attach the message to the email
    msg.attach(MIMEText(message, 'plain'))

    # Establish a connection to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Start TLS encryption (optional)

    # Login to your email account
    server.login(sender_email, sender_password)

    # Send the email
    server.sendmail(sender_email, recipient, msg.as_string())

    # Close the connection
    server.quit()



# Usage example
if __name__ == "__main__":
    subject = "Hello from Python!"
    message = "This is a test email sent from Python."
    recipient = "recipient@gmail.com"

    send_email(recipient, subject, message)
