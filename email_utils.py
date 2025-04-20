"""
Email utility functions for sending reflection reports using SendGrid.
"""
import os
import sys
import base64
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, 
    FileType, Disposition, ContentId, 
    Email, To, Content, MailSettings, SandBoxMode
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get SendGrid API key from environment variable
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

# Default from email - must be a verified sender in SendGrid for production use
# This must match exactly with your verified sender in SendGrid
FROM_EMAIL = "YOUR_VERIFIED_EMAIL@DOMAIN.COM"  # Replace this with your actual verified sender email

# Recipients for reflection reports
RECIPIENTS = [
    'aturan@asu.edu',
    'kobowood1@gmail.com',
    'JANEL.WHITE@asu.edu'
]

def send_reflection_report(participant_info, report_content, participant_id):
    """
    Send the reflection report to all specified recipients using SendGrid.
    
    Args:
        participant_info (dict): Participant details
        report_content (str): The report content in markdown format
        participant_id (str): Unique identifier for the participant
        
    Returns:
        bool: True if all emails were sent successfully, False otherwise
    """
    # Check if we have a valid SendGrid API key
    if not SENDGRID_API_KEY:
        logger.error("SendGrid API key is missing. Cannot send emails.")
        logger.warning("Email requires a valid SENDGRID_API_KEY environment variable.")
        return False
    
    # Create a meaningful filename for the report with participant info if available
    if participant_info and participant_info.get('occupation'):
        occupation = participant_info.get('occupation', '').replace(' ', '_').lower()
        filename = f"refugee_policy_reflection_{occupation}_{participant_id}.md"
    else:
        filename = f"refugee_policy_reflection_{participant_id}.md"
    
    # Basic info about the participant for the email subject
    if participant_info:
        subject = f"Refugee Policy Reflection Report - {participant_info.get('occupation', 'Participant')}"
    else:
        subject = f"Refugee Policy Reflection Report - {participant_id}"
    
    # Email body with HTML formatting
    email_body = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 5px;">
            <h2 style="color: #2a5885;">New Reflection Report Submission</h2>
            <p>A new reflection report has been submitted from the Republic of Bean policy simulation.</p>
            <p>The report is attached as a text file. It contains participant information, policy selections, and reflection responses.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #777; font-size: 12px;">This is an automated message from the AI CHALLENGE policy simulation platform.</p>
        </div>
    </body>
    </html>
    """
    
    success = True
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        for recipient in RECIPIENTS:
            # Create a Mail message
            message = Mail(
                from_email=Email(FROM_EMAIL),
                to_emails=To(recipient),
                subject=subject,
                html_content=Content("text/html", email_body)
            )
            
            # In production mode, emails will actually be delivered
            # Note: The FROM_EMAIL must be a verified sender in SendGrid
            # No sandbox mode, emails will be delivered to recipients
            
            # Encode report content as base64
            encoded_content = base64.b64encode(report_content.encode()).decode()
            
            # Create attachment
            attachment = Attachment()
            attachment.file_content = FileContent(encoded_content)
            attachment.file_name = FileName(filename)
            attachment.file_type = FileType('text/markdown')
            attachment.disposition = Disposition('attachment')
            attachment.content_id = ContentId('Report')
            
            # Add attachment to message
            message.attachment = attachment
            
            # Send message
            response = sg.send(message)
            status_code = response.status_code
            
            # Status code 202 is the standard success code for SendGrid API
            if status_code in [200, 202]:
                logger.info(f"Email sent successfully to {recipient} with status code {status_code}")
                # In production mode, emails are actually delivered to recipients
            else:
                logger.warning(f"SendGrid returned status code {status_code}")
                success = False
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to send email via SendGrid: {str(e)}")
        return False