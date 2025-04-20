"""
Email utility functions for sending reflection reports.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get SMTP settings from environment variables
SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')

# Recipients for reflection reports
RECIPIENTS = [
    'aturan@asu.edu',
    'kobowood1@gmail.com',
    'JANEL.WHITE@asu.edu'
]

def send_reflection_report(participant_info, report_content, participant_id):
    """
    Send the reflection report to all specified recipients.
    
    Args:
        participant_info (dict): Participant details
        report_content (str): The report content in markdown format
        participant_id (str): Unique identifier for the participant
        
    Returns:
        bool: True if all emails were sent successfully, False otherwise
    """
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        logger.error("SMTP configuration is incomplete. Cannot send emails.")
        return False
    
    # Create a timestamp-based filename for the report
    filename = f"reflection_report_{participant_id}.txt"
    
    # Basic info about the participant for the email subject
    if participant_info:
        subject = f"Refugee Policy Reflection Report - {participant_info.get('occupation', 'Participant')}"
    else:
        subject = f"Refugee Policy Reflection Report - {participant_id}"
    
    # Email body
    email_body = """
    A new reflection report has been submitted from the Republic of Bean policy simulation.
    
    The report is attached as a text file.
    
    This is an automated message from the AI CHALLENGE policy simulation platform.
    """
    
    success = True
    
    try:
        for recipient in RECIPIENTS:
            # Create message
            message = MIMEMultipart()
            message['From'] = SMTP_USER
            message['To'] = recipient
            message['Subject'] = subject
            
            # Attach the body text
            message.attach(MIMEText(email_body, 'plain'))
            
            # Attach the report as a text file
            attachment = MIMEApplication(report_content.encode('utf-8'))
            attachment['Content-Disposition'] = f'attachment; filename="{filename}"'
            message.attach(attachment)
            
            # Send the email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(message)
                logger.info(f"Reflection report sent to {recipient}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        success = False
    
    return success