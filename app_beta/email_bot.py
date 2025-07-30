#email_bot.py

import imaplib
import email
import re

def extract_interac_transfers(gmail_user, gmail_password):
    """
    Connects to Gmail and looks for 'Virement Interac' subject lines.
    Extracts name and amount from matching emails.
    
    Returns a list of dictionaries like:
    [{"name": "FREDERIC MORIN", "amount": 15.00}]
    """

    results = []

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_password)
        mail.select("inbox")

        # Search for emails with the target subject pattern
        status, data = mail.search(None, 'SUBJECT "Virement Interac :"')
        if status != "OK":
            print("No matching Interac emails found.")
            return results

        for num in data[0].split():
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject = email.header.decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # Match full subject pattern
            if not subject.lower().startswith("virement interac"):
                continue

            # Extract amount and name
            amount_match = re.search(r"reçu\s([\d,]+)\s*\$\s*de", subject)
            name_match = re.search(r"de\s(.+?)\set ce montant", subject)

            if amount_match and name_match:
                amt_str = amount_match.group(1).replace(",", ".")
                name = name_match.group(1).strip()
                try:
                    amount = float(amt_str)
                except ValueError:
                    continue

                results.append({
                    "bank_info_name": name,
                    "bank_info_amt": amount
                })

        mail.logout()

    except Exception as e:
        print(f"❌ Error reading Gmail: {e}")

    return results
