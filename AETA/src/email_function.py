# Function to send email with the summary of the transcript

import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Function to send email
def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path):
    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Open ZIP file in binary mode
    with open(attachment_path, "rb") as attachment:
        # Add file as application/octet-stream
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {os.path.basename(attachment_path)}",
    )

    # Add attachment to message
    message.attach(part)

    # Convert message to string
    text = message.as_string()

    # Log in to server using secure context and send email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, text)

def send_summary_email(company: str, year: str, quarter: str):
    # file path
    file_path = f"summary/{company}-{year}-Q{quarter}-transcript-summary.txt" 

    # Email details

    # Fetching sender email and password from .env file
    sender_email = "sender_email"
    sender_password = "sender_password"

    # Take input from user for stakeholder email
    # stakeholder_email = input("Enter the stakeholder email: ")

    stakeholders = [
    "bhagyarana2001@gmail.com",
        # Add more stakeholder emails as needed
    ]

    # add_stakeholder_email = input("Do you want to add more stakeholder emails? (y/n): ")
    # if add_stakeholder_email == "y":
    #     stakeholder_email = input("Enter the stakeholder email: ")
    #     stakeholders.append(stakeholder_email)

    subject = f"Transcript Summary - {company} - {year} Q{quarter}"
    body = f"Dear Stakeholder, \n\nPlease find attached the transcript summary for {company} - {year} Q{quarter} \n\nBest regards, \nFinSolve-Team 10"

    # Send email to each stakeholder
    for stakeholder_email in stakeholders:
        try:
            send_email(sender_email, sender_password, stakeholder_email, subject, body, file_path)
            print(f"Email sent successfully to {stakeholder_email}\n")
        except Exception as e:
            print(f"Failed to send email to {stakeholder_email}. Error: {str(e)}")

    print("Email sent to all stakeholders successfully!")
