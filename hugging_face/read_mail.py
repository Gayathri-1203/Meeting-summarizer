import re
from pymongo import MongoClient
from datetime import datetime
from dateutil import parser
import imaplib
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import os

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
EMAIL_ACCOUNT = 'mail'
EMAIL_PASSWORD = 'password'

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = EMAIL_ACCOUNT
SENDER_PASSWORD = EMAIL_PASSWORD

MONGODB_URI = 'URI'
DB_NAME = 'meetings'
COLLECTION_NAME = 'meeting_details'

NON_PERSON_NAMES = {'Google Calendar', 'More phone numbers', 'View all guest info'}

def connect_to_gmail():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        return mail
    except imaplib.IMAP4.error as e:
        print(f"Failed to connect to Gmail: {e}")
        return None

def fetch_unread_emails(mail):
    mail.select('inbox')
    result, data = mail.search(None, 'UNSEEN SUBJECT "Invitation"')
    if result != 'OK':
        print("No unread messages found.")
        return []

    email_ids = data[0].split()
    return email_ids

def decode_subject(subject):
    decoded_header = decode_header(subject)
    subject, encoding = decoded_header[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else 'utf-8')
    return subject

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode()
                return body
    else:
        body = msg.get_payload(decode=True).decode()
        return body

def process_emails(mail, email_ids):
    if not email_ids:
        print("No mails found.")
        return
    
    for email_id in email_ids:
        result, msg_data = mail.fetch(email_id, '(RFC822)')
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        subject = decode_subject(msg['Subject'])
        meeting_title = extract_meeting_title(subject)
        body = get_email_body(msg)

        date, time, url = extract_details_from_body(body)
        names_emails = extract_names_and_emails_from_body(body)

        print(f"Meeting Title: {meeting_title}")
        print(f"Date: {date}")
        print(f"Time: {time}")
        print(f"URL: {url}")
        print(f"Names and Emails: {names_emails}")
        print("="*50)

        store_in_mongodb(date, time, url, meeting_title, names_emails)
        # send_reply_to_participants(date, time, url, names_emails)

def extract_meeting_title(subject):
    title_pattern = r'Invitation: (.+?) @'
    title_match = re.search(title_pattern, subject)
    if title_match:
        return title_match.group(1)
    return None

def extract_details_from_body(body):
    url_pattern = r'(https://meet\.google\.com/\S+|https://\S+.zoom.us/j/\S+)'
    time_pattern = r'\b\d{1,2}[:.]\d{2}\s?[APap][Mm]?\b|\b\d{1,2}\s?[APap][Mm]\b'
    date_pattern = r'\b\w+\s+\d{1,2},\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b'

    url_match = re.search(url_pattern, body)
    url = url_match.group(1) if url_match else None

    date = None
    time = None

    for line in body.splitlines():
        time_match = re.search(time_pattern, line, re.IGNORECASE)
        date_match = re.search(date_pattern, line, re.IGNORECASE)

        if time_match and not time:
            time_str = time_match.group()
            try:
                parsed_time = parser.parse(time_str, fuzzy=True).time()
                time = parsed_time.strftime('%I:%M %p')
            except ValueError as e:
                print("Error parsing time:", e)

        if date_match and not date:
            date_str = date_match.group()
            try:
                parsed_date = parser.parse(date_str, fuzzy=True)
                date = parsed_date.strftime('%Y-%m-%d')
            except ValueError as e:
                print("Error parsing date:", e)

    return date, time, url

def extract_names_and_emails_from_body(body):
    guests_pattern = re.compile(r'Guests[:\s]*([\s\S]*?)(?:\n\n|\n$)', re.IGNORECASE)
    name_email_pattern = re.compile(r'\b([A-Z][a-zA-Z]*\s[A-Z][a-zA-Z]*)(?:\s-\s[^\n]*\n)?\s?([\w\.-]+@[\w\.-]+)?\b')

    names_emails = []

    guests_match = guests_pattern.search(body)
    if guests_match:
        guests_section = guests_match.group(1)
        found_names_emails = name_email_pattern.findall(guests_section)
        for name, email in found_names_emails:
            if name not in NON_PERSON_NAMES:
                if not email:
                    email = find_email_for_name(name, body)
                names_emails.append({'name': name, 'email': email})
    
    return names_emails

def find_email_for_name(name, body):
    email_pattern = re.compile(r'([\w\.-]+@[\w\.-]+)')
    potential_emails = email_pattern.findall(body)
    for email in potential_emails:
        if name.split()[0].lower() in email.lower():
            return email
    return None

def store_in_mongodb(date, time, url, meeting_title, names_emails):
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        existing_meeting = collection.find_one({'date': date, 'time': time, 'url': url})
        
        if existing_meeting:
            print(f"Meeting already exists: {existing_meeting}")
        else:
            meeting_details = {
                'date': date,
                'time': time,
                'url': url,
                'meeting_title': meeting_title,
                'names_emails': names_emails,
                'timestamp': datetime.now()
            }
            print(f"Storing new meeting details: {meeting_details}")
            result = collection.insert_one(meeting_details)
            print(f"Stored new meeting details with id: {result.inserted_id}")
    except Exception as e:
        print(f"Failed to store meeting details: {e}")
    finally:
        client.close()

def get_interview_data():
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    interview_data = list(collection.find())
    client.close()
    return interview_data

def send_email(to_email, html_content, pdf_path=None):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = 'Meeting Summary and Action Items'

    msg.attach(MIMEText(html_content, 'html'))
    
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
            msg.attach(part)
    
    SERVER = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    SERVER.starttls()
    SERVER.login(SENDER_EMAIL, SENDER_PASSWORD)

    try:
        SERVER.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
    finally:
        SERVER.quit()

def send_reply_to_participants(html_content, participants, pdf_path=None):
    for participant in participants:
        if 'email' in participant and participant['email']:
            send_email(participant['email'], html_content, pdf_path)

def mail():
    mail = connect_to_gmail()
    if mail:
        email_ids = fetch_unread_emails(mail)
        process_emails(mail, email_ids)
        mail.logout()

if __name__ == "__main__":
    mail()
