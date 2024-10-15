import smtplib
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import email.utils as utils
import random
import string
# Setup logging to both file and console
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs.txt"),
                        logging.StreamHandler()
                    ])

# Function to get MX records for a domain
def get_mx_records(domain):
    records = dns.resolver.resolve(domain, 'MX')
    mx_records = sorted(records, key=lambda record: record.preference)
    return [str(record.exchange) for record in mx_records]

# Function to send email via MX record with BCC
def send_email_via_mx(to_emails, from_email, from_name, subject, html_body,mx_records):
    if not to_emails:
        return

    # Extract domain from the first email (assuming all emails are from the same domain)
    domain = to_emails[0].split('@')[1]
    #mx_records = get_mx_records(domain)
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    html_body = html_body.replace('{{random}}', random_string)
    from_email=f"{random_string}{from_email}"
    print(from_email)
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = from_email  # To field can be any valid email address
    msg['Bcc'] = ', '.join(to_emails)
    msg['message-id'] = utils.make_msgid(domain='nike.org')
    msg.attach(MIMEText(html_body, 'html'))

    for mx in mx_records:
        try:
            with smtplib.SMTP(mx) as server:
                server.sendmail(from_email, to_emails, msg.as_string())
                logging.info(f"Batch of {len(to_emails)} emails sent successfully via {mx}")
                break
        except Exception as e:
            logging.error(f"Failed to send batch of {len(to_emails)} emails via {mx}: {e}")

# Function to read email list from a file
def read_email_list(file_path):
    with open(file_path, 'r') as file:
        emails = [line.strip() for line in file if line.strip()]
    return emails

# Function to batch the email list
def batch_email_list(email_list, batch_size):
    for i in range(0, len(email_list), batch_size):
        yield email_list[i:i + batch_size]

# Function to read HTML content from a file
def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Email details
from_email = "info@nike.org"
from_name = "8 kg weniger in 1 Woche!"
subject = "DIE WISSENSCHAFT HAT HERAUSGEFUNDEN, WARUM SIE DICK WERDEN!!"

# Read HTML content from file
html_body = read_html_file('insta.html')

# Read email list from file
email_list = read_email_list('mails-insta.txt')
domain="lycos.com"
mx_records = get_mx_records(domain)
# Send email in batches of 100
batch_size = 100
batches = list(batch_email_list(email_list, batch_size))

# Use ThreadPoolExecutor to send emails concurrently
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    for batch in batches:
        futures.append(executor.submit(send_email_via_mx, batch, from_email, from_name, subject, html_body,mx_records))
        time.sleep(3)  # Sleep for 3 seconds between sending each batch

    for future in as_completed(futures):
        try:
            future.result()
        except Exception as exc:
            logging.error(f"Batch generated an exception: {exc}")
