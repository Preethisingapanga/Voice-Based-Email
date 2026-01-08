
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import os
import schedule
from google.oauth2 import service_account
import pyttsx3
import speech_recognition as sr
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64
from datetime import datetime
import time
time.sleep(1)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.modify']
listener = sr.Recognizer()
engine = pyttsx3.init()


def talk(text):
    engine.say(text)
    engine.runAndWait()


def get_audio(command=None, retries=3):
    """Function to listen for audio input with retries."""
    r = sr.Recognizer()
    attempts = 0

    while attempts < retries:
        with sr.Microphone() as source:
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"Listening for command:")
            if command:
                talk(command)  # Prompt the user with the command (optional)
            audio = r.listen(source)
            said = ""

        try:
            said = r.recognize_google(audio).lower()  # Recognize speech and convert to lowercase
            print(f"Recognized: {said}")
            return said  # Return the recognized command if successful
        except sr.UnknownValueError:
            talk("Sorry, I didn't catch that. Please try again.")
            print("Didn't get that.")
        except sr.RequestError:
            talk("Sorry, I'm having trouble reaching the speech recognition service. Please try again later.")
            print("Speech recognition service error.")

        attempts += 1

    talk("I could not hear your response after several attempts. Please check your microphone.")
    print("Could not hear your response after several attempts.")
    return ""


def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                print("Failed to refresh credentials Reauthenticating")
                creds = None
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def read_mails(service):
    while True:
        talk("What would you like to do? Say 'read by count', 'read by recipient', 'read by date','read from draft' or 'read from trash' or 'read from starred' or 'exit'.")
        print("What would you like to do? Say 'read some', 'read by recipient', 'read by date','read from draft' or 'read from trash' or 'read from starred'  or 'exit'.")
        command = get_audio().lower()
        print(command)
        talk("u said {command}")
        if "read some" in command or "count" in command:
            talk("How many emails do you want to read?")
            print("How many emails do you want to read?")

            try:
                user_limit = get_audio()
                limit = int(user_limit)
                read_some_mails(service, limit)
            except ValueError:
                talk("Sorry, I could not understand the number. Please try again.")
                print("Sorry, I could not understand the number. Please try again.")
        elif "recipient" in command:
            recipient = trimming_recepient(service)
            read_mails_by_recipient(service, recipient)
        elif "starred" in command or "star" in command:
            read_starred_mails(service)
        elif "spam" in command:
            read_spam_mails(service)
        elif "trash" in command:
            read_trash_mails(service)
        elif "draft" in command or "drought" in command or "draught" in command:
            read_draft_mails(service)
        elif "exit" in command:
            talk("Exiting from reading emails.")
            return
        else:
            talk("Invalid choice. Please try again.")
            print("Invalid choice. Please try again.")

def trimming_recepient(service):
    for _ in range(5):
       talk("Please say the recipient's email address.")
       print("Please say the recipient's email address.")
       rec=get_audio()
       rec=rec.replace(" at the rate ","@").replace(" ","").replace("dot",".")
       print(rec)
       talk(rec)
       print("is it correct? say yes or no")
       talk("is it correct,say yes or no")
       info=get_audio()
       if "yes" in info or "s" in info:
          return rec
    print("too many incorect attempts")
    talk("too many incorect attempts")
    read_mails(service)


def read_some_mails(service, limit):
    """Read a specific number of emails."""
    results = service.users().messages().list(
        userId='me',
        labelIds=["INBOX", "UNREAD"],
        maxResults=limit
    ).execute()
    messages = results.get('messages', [])
    if not messages:
        talk('No unread messages found.')
        print('No unread messages found.')
    else:
        talk(f"{len(messages)} unread emails found.")
        print(f"{len(messages)} unread emails found.")

        for message in messages:
            process_email(service, message)

def read_mails_by_recipient(service, recipient):
    """Read emails from a specific recipient."""
    query = f"from:{recipient}"
    results = service.users().messages().list(
        userId='me',
        q=query,
        labelIds=["INBOX"]
    ).execute()
    messages = results.get('messages', [])
    if not messages:
        talk(f'No emails found from {recipient}.')
        print(f'No emails found from {recipient}.')
    else:
        talk(f"{len(messages)} emails found from {recipient}.")
        print(f"{len(messages)} emails found from {recipient}.")

        for message in messages:
            process_email(service, message)


def read_starred_mails(service):
    results = service.users().messages().list(
        userId="me", labelIds=["STARRED"]
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        talk("No starred emails found.")
        print("No starred emails found.")
    else:
        talk(f"{len(messages)} emails found from starred.")
        print(f"{len(messages)} emails found from starred.")
        for message in messages:
            process_email(service, message)
            talk("Would you like to read to another email? If yes, say 'yes'. If no, say 'no'.")
            if "no" in get_audio():
                break

def read_trash_mails(service):
    results = service.users().messages().list(
        userId="me", labelIds=["TRASH"]
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        talk("No spam emails found.")
        print("No spam emails found.")
    else:
        talk(f"{len(messages)} emails found from trash.")
        print(f"{len(messages)} emails found from trash.")
        for message in messages:
            process_email(service, message, folder="Trash")
            talk("Would you like to read to another email? If yes, say 'yes'. If no, say 'no'.")
            if "no" in get_audio():
                break

def read_spam_mails(service):
    results = service.users().messages().list(
        userId="me", labelIds=["SPAM"]
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        talk("No spam emails found.")
        print("no spam emails found")
    else:
        talk(f"{len(messages)} emails found from spam.")
        print(f"{len(messages)} emails found from spam.")
        for message in messages:
            process_email(service, message, folder="Spam")
            talk("Would you like to reply to another email? If yes, say 'yes'. If no, say 'no'.")
            if "no" in get_audio():
                break
def read_draft_mails(service):
    results = service.users().messages().list(
        userId="me", labelIds=["DRAFT"]
    ).execute()
    messages = results.get("messages", [])
    if not messages:
        talk("No draft emails found.")
        print("no draft mails found")
    else:
        talk(f"{len(messages)} emails found from draft.")
        print(f"{len(messages)} emails found from draft.")
        for message in messages:
            draft = service.users().messages().get(userId="me", id=message['id']).execute()

            # Extract recipient email
            headers = draft.get("payload", {}).get("headers", [])
            recipient = next((header["value"] for header in headers if header["name"] == "To"), "Unknown recipient")

            # Extract existing email body (snippet)
            snippet = draft.get("snippet", "No snippet available")

            talk(f"Recipient: {recipient}. Email snippet: {snippet}.")
            print(f"Recipient: {recipient}, Email snippet: {snippet}")


            talk("Would you like to continue reading other drafts? If yes, say 'yes'. If no, say 'no'.")
            print("Would you like to continue reading other drafts? If yes, say 'yes'. If no, say 'no'.")
            continue_response = get_audio().lower()
            if "no" in continue_response:
              break

def process_email(service, message,folder=None):
    msg = service.users().messages().get(
        userId='me',
        id=message['id'],
        format='metadata'
    ).execute()

    sender = "Unknown sender"
    for header in msg['payload']['headers']:
        if header['name'] == "From":
            sender = header['value']
            break

    talk(f"Email from {sender}. Would you like to read it?")
    print(f"Email from {sender}. Would you like to read it?")
    response = get_audio()

    if "read" in response or "narrate" in response:
        talk(msg['snippet'])
        print(msg['snippet'])

        # Mark the email as read
        print("do u wnt to make it as read")
        talk("do u want to make it as read")
        x=get_audio()
        if "Yes" in x or "read" in x or "yes" in x:

            service.users().messages().modify(
            userId='me',
            id=message['id'],
            body={'removeLabelIds': ['UNREAD']}
            ).execute()

            talk("Email marked as read")
            print("Email marked as read")
        else:
            talk("Email not marked as read.")
            print("Email not marked as read.")

        # Ask if the user wants to star the email
        talk("Would you like to star this email?")
        print("Would you like to star this email?")
        star_response = get_audio()
        if "yes" in star_response or "starr" in star_response or "star" in star_response:
            service.users().messages().modify(
                userId='me',
                id=message['id'],
                body={'addLabelIds': ['STARRED']}
            ).execute()
            talk("Email has been starred.")
            print("Email has been starred.")
        else:
            talk("Email not starred.")
            print("Email not starred.")

        # Ask if the user wants to reply to the email
        talk("Would you like to reply to this email?")
        print("Would you like to reply to this email?")
        reply_response = get_audio()
        if "yes" in reply_response or "reply" in reply_response:

                recipient_email = extract_recipient_email(msg)
                if recipient_email:
                    composing_email(recipient_email,service)

                else:
                    talk("Could not identify the recipient. Reply not sent.")
                    print("Could not identify the recipient. Reply not sent.")
            
    else:
        talk("Email skipped.")
        print("Email skipped.")

def extract_recipient_email(msg):
    """Extracts the sender's email address from the message headers."""
    for header in msg['payload']['headers']:
        if header['name'] == "From":
            return header['value'].split("<")[-1].strip(">")
    return ""

def get_cc_bcc(service):
    email_address = []  # List to store valid email addresses

    while True:
        print("Please say the email address:")
        talk("Please say the email address:")
        recipient = get_audio().lower().strip()
        print(f"You said: {recipient}")
        talk(f"You said: {recipient}")

        # Process the recipient for corrections
        recipient = recipient.replace(" dot ", ".")
        recipient = recipient.replace(" ", "")
        recipient = recipient.replace("attherate", "@")
        print(f"Processed email address: {recipient}")

        # Validate the recipient
        if "@" in recipient and "." in recipient:
            while True:
                print(f"Is '{recipient}' correct? Please say yes/correct or no/wrong")
                talk(f"Is '{recipient}' correct? Please say yes/correct or no/wrong")
                confirmation = get_audio().lower()

                if "yes" in confirmation or "correct" in confirmation:
                    email_address.append(recipient)
                    print(f"Recipient '{recipient}' added.")
                    talk(f"Recipient '{recipient}' added.")

                    print("Do you want to add more recipients? Please say yes or no.")
                    talk("Do you want to add more recipients? Please say yes or no.")
                    more_recipients = get_audio().lower()

                    if "yes" in more_recipients:
                        break  # Go back to the start of the loop to add another recipient
                    else:
                        print("Recipient collection complete.")
                        talk("Recipient collection complete.")
                        print(f"Final List of Recipients: {email_address}")
                        return email_address

                elif "no" in confirmation or "wrong" in confirmation:
                    print("Please say the email address again.")
                    talk("Please say the email address again.")
                    break  # Go back to the start of the loop to get a new recipient

                else:
                    print("Invalid response. Please confirm with yes or no.")
                    talk("Invalid response. Please confirm with yes or no.")

        else:
            print("Invalid email address. Please say the email address again.")
            talk("Invalid email address. Please say the email address again.")



def get_recipient_email(service):

        talk("Please say the recipient's email address.")
        print("Please say the recipient's email address.")
        while True:
            recipient_email = get_audio().lower()
            print(f"You said (raw): {recipient_email}")

            # Preprocessing to handle common issues
            recipient_email = recipient_email.replace(" ", "")  # Remove spaces
            recipient_email = recipient_email.replace("attherate", "@")  # Replace "atherate" with "@"

            print(f"Processed email address: {recipient_email}")
            if "@" in recipient_email and "." in recipient_email:
                talk(f"Is {recipient_email} correct? Please say yes/correct or no/wrong")
                print(f"Is {recipient_email} correct? Please say yes/correct or no/wrong")
                confirmation = get_audio().lower()
                if "yes" in confirmation or "correct" in confirmation:
                    composing_email(recipient_email,service)

                elif "no" in confirmation or "wrong" in confirmation:
                    talk("Please say the email address again.")
                    print("Please say the email address again.")
                    return
                else:
                    talk("Invalid response. Let's try again.")
                    print("Invalid response. Let's try again.")
            else:
                talk("That doesn't seem to be a valid email address. Please try again.")
                print("That doesn't seem to be a valid email address. Please try again.")

            # Basic email format validation

def save_draft(email_data):
    """Save email data as a draft."""
    draft_folder = "drafts"
    os.makedirs(draft_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{draft_folder}/draft_{timestamp}.txt"
    with open(file_name, "w") as draft_file:
        draft_file.write(str(email_data))
    talk("Your email has been saved as a draft.")


def composing_email(recipient_email,service):
    """Function to compose an email."""
    email_data = {
      "recipient":recipient_email,
      "subject": "",
      "body": "",
      "attachments": []
    }
    if recipient_email:
        talk("What is the subject of the email?")
        print("What is the subject of the email?")
        email_subject = get_audio()
        talk("Please dictate the content of the email.")
        print("Please dictate the content of the email.")
        email_content = get_audio()

        message = MIMEText(email_content)
        message['to'] = recipient_email
        message['subject'] = email_subject

        talk("Here is the email you're about to send:")
        print("Here is the email you're about to send:")
        talk(f"Subject: {email_subject}")
        print(f"Subject: {email_subject}")
        talk(f"Body: {email_content}")
        print(f"Body: {email_content}")

    # Get subject
        email_data["subject"] =email_subject
        email_data["body"] =email_content

    # Attach files
    #     talk("Do you want to attach any files? Say 'yes' or 'no'.")
    #     print("Do you want to attach any files? Say 'yes' or 'no'.")
    #     attach_files_response = get_audio()
    #     if "attach" in attach_files_response or "yes" in attach_files_response or "s" in attach_files_response:
    #         base_path = r"C:\Users\MAMATHA\Pictures"
    #
    #         for _ in range(5):
    #
    #              talk("Please provide the filename.")
    #              print("Please provide the filename.")
    #              filename = get_audio()
    #              filename=filename.replace("dot",".").replace(" ","")
    #
    #              # Construct the full file path by appending the filename to the base path
    #              file_path = os.path.join(base_path, filename)
    #
    #                       # Check if the file exists at the specified path
    #              if os.path.exists(file_path):
    #                 email_data["attachments"].append(file_path)
    #                 talk(f"File {file_path} has been attached.")
    #                 break  # Exit the loop after successful attachment
    #              else:
    #                 talk("The file does not exist in the specified directory. Please try again.")
    #                 print("The file does not exist in the specified directory. Please try again.")
    #
        # Choose action: draft, send, or schedule
        talk("Do you want to send or save as a draft this email? Say 'send the mail', 'draft the mail'.")
        print("Do you want to send or save as a draft this email? Say 'send the mail', 'draft the mail'.")
        action = get_audio()
        print(action)
    if action:
        action = action.lower()
        print("action checking : ",action)
        if "send" in action:
            for _ in range(2):
                talk("Do you want to send this email?")
                print("Do you want to send this email?")
                confirmation = get_audio().lower()

                if "yes" in confirmation or "send" in confirmation or "compose" in confirmation:
                    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
                    body = {'raw': raw_message}

                    try:
                        sent_message = service.users().messages().send(userId='me', body=body).execute()
                        talk("Email sent successfully!")
                        print("EMAIL SENT SUCCESSFULLY")
                        break
                    except Exception as e:
                        print(f"An error occurred: {e}")
                        talk("Email could not be sent. Please check the console for details.")
                        print("Email could not be sent. Please check the console for details.")
                    break
                elif "no" in confirmation or "cancel" in confirmation:
                    talk("Email sending canceled.")
                    print("Email sending canceled.")

            # Simulate sending email (implement actual email sending functionality)
        elif  "draft" in action:
            save_draft(email_data)
        else:
            talk("Invalid action. Please try again.")
    else:
        talk("No action selected. Please try composing the email again.")

def compose_email(service,a=0):
    if a>3:
      print("Too many invalid attempts.Exiting composing email.")
      talk("Too many invalid attempts.Exiting composing email.")
      return



    # Ask for the type of recipient (single, group, cc, bcc)
    talk("Please select the recipient label. Say 'single' for one recipient, 'group' for multiple recipients, 'cc' for carbon copy, or 'bcc' for blind carbon copy.")
    print("Please select the recipient label. Say 'single' for one recipient, 'group' for multiple recipients, 'cc' for carbon copy, or 'bcc' for blind carbon copy.")
    label = get_audio()  # Get audio input from user
    to_recipients = []
    cc_recipients = []
    bcc_recipients = []
    if  "single" in label:
        recipient_email=get_recipient_email(service)
        composing_email(recipient_email,service)

    elif  "cc" in label:

        cc_workflow(service)
        # Add to CC list

    elif  "bcc" in label:
       bcc_workflow(service)
    else:
        print("invalid response")
        talk("invalid response,try again")
        compose_email(service,a+1)




# Function to send an email with CC
def send_email_with_cc(service,recipients, cc_recipients, subject, body,file_path=None):
    try:
        msg = MIMEMultipart()
        msg['To'] = ", ".join(recipients)
        msg['CC'] = ", ".join(cc_recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if os.path.exists(file_path):
                    # email_data["attachments"].append(file_path)
            talk(f"File {file_path} has been attached.")

        else:
            talk("The file does not exist in the specified directory. Please try again.")
            print("The file does not exist in the specified directory. Please try again.")
                # Check if the file exists at the specified path

        # Handle attachments
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as attachment:
                mime_base = MIMEBase('application', 'octet-stream')
                mime_base.set_payload(attachment.read())
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                msg.attach(mime_base)

        # Encode message for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        message_body = {'raw': raw_message}

        # Send email using Gmail API
        sent_message = service.users().messages().send(userId='me', body=message_body).execute()

        print("Email sent successfully!", sent_message)

    except Exception as e:
        talk(f"Failed to send email. Error: {e}")
        print(f"Failed to send email. Error: {e}")


# Draft Email
def draft_email_cc(service,recipients, cc_recipients, subject, body,file_path=None):
    try:
        msg = MIMEMultipart()
        msg['To'] = ", ".join(recipients)
        msg['CC'] = ", ".join(cc_recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body,'plain'))
        if os.path.exists(file_path):
            # email_data["attachments"].append(file_path)
            talk(f"File {file_path} has been attached.")

        else:
            talk("The file does not exist in the specified directory. Please try again.")
            print("The file does not exist in the specified directory. Please try again.")
            # Check if the file exists at the specified path

        # Handle attachments
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as attachment:
                mime_base = MIMEBase('application', 'octet-stream')
                mime_base.set_payload(attachment.read())
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                msg.attach(mime_base)
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        message_body = {'message':{'raw': raw_message}}
        draft=service.users().drafts().create(userId="me",body=message_body).execute()

        talk(" email drafted")
        print("email drafted")
    except Exception as e:
        talk(f"Failed to draft email. Error: {e}")
        print(f"Failed to draft email. Error: {e}")



# Compose Email (CC Workflow)
def cc_workflow(service):
    # Get main recipients
    recipients = get_cc_bcc("To")

    # Get CC recipients
    cc_recipients = get_cc_bcc("Cc")

    # Get subject
    if recipients:
        talk("What is the subject of the email?")
        print("What is the subject of the email?")
        email_subject = get_audio()
        talk("Please dictate the content of the email.")
        print("Please dictate the content of the email.")
        email_content = get_audio()



        talk("Here is the email you're about to send:")
        print("Here is the email you're about to send:")
        talk(f"Subject: {email_subject}")
        print(f"Subject: {email_subject}")
        talk(f"Body: {email_content}")
        print(f"Body: {email_content}")
        talk("Do you want to attach any files? Say 'yes' or 'no'.")
        print("Do you want to attach any files? Say 'yes' or 'no'.")
        attach_files_response = get_audio()
        if "attach" in attach_files_response or "yes" in attach_files_response or "s" in attach_files_response:
            base_path = r"C:\Users\MAMATHA\Pictures"

            for _ in range(5):
                talk("Please provide the filename.")
                print("Please provide the filename.")
                filename = get_audio()
                filename = filename.replace("dot", ".").replace(" ", "")

                # Construct the full file path by appending the filename to the base path
                file_path = os.path.join(base_path, filename)
    for _ in range(5):
    # Ask for next step
      talk("Do you want to  Save as Draft, or Compose now? Please say , draft, or compose.")
      choice = get_audio()


      if 'draft' in choice or 'draught' in choice:
        draft_email_cc(service,recipients, cc_recipients, email_subject, email_content,file_path)
        break
      elif 'compose' in choice:
        send_email_with_cc(service,recipients, cc_recipients, email_subject, email_content,file_path)
        break
      else:
        talk("Invalid choice. Returning to main menu.")

def draft_bcc(service,bcc_recipients,recipients, subject, body, file_path=None):
    try:
        msg = MIMEMultipart()
        msg['To'] = ", ".join(recipients)
        msg['Bcc'] = ", ".join(bcc_recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body,'plain'))
        if os.path.exists(file_path):
            # email_data["attachments"].append(file_path)
            talk(f"File {file_path} has been attached.")

        else:
            talk("The file does not exist in the specified directory. Please try again.")
            print("The file does not exist in the specified directory. Please try again.")
            # Check if the file exists at the specified path

        # Handle attachments
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as attachment:
                mime_base = MIMEBase('application', 'octet-stream')
                mime_base.set_payload(attachment.read())
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                msg.attach(mime_base)
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        message_body = {'message':{'raw': raw_message}}
        draft=service.users().drafts().create(userId="me",body=message_body).execute()

        talk(" email drafted")
        print("email drafted")
    except Exception as e:
        talk(f"Failed to draft email. Error: {e}")
        print(f"Failed to draft email. Error: {e}")


def send_bcc(service,recipients,bcc_recipients, subject, body,attachment_path=None):
    try:

        msg = MIMEMultipart()
        msg['To'] = ", ".join(recipients)  # Main recipients
        msg['Bcc'] = ", ".join(bcc_recipients)  # BCC recipients (hidden)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path:
            with open(attachment_path, 'rb') as attachment:
                mime_base = MIMEBase('application', 'octet-stream')
                mime_base.set_payload(attachment.read())
                encoders.encode_base64(mime_base)
                mime_base.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(mime_base)

        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        message_body = {'raw': raw_message}

    # Send email using Gmail API
        sent_message = service.users().messages().send(userId='me', body=message_body).execute()

        print("Email sent successfully!", sent_message)

    except Exception as e:
        talk(f"Failed to send email. Error: {e}")
        print(f"Failed to send email. Error: {e}")


# Compose Email (BCC Workflow)
def bcc_workflow(service):
    recipients = get_cc_bcc("To")

    # Get CC recipients
    bcc_recipients = get_cc_bcc("Bcc")
    if recipients:
        talk("What is the subject of the email?")
        print("What is the subject of the email?")
        subject = get_audio()
        talk("Please dictate the content of the email.")
        print("Please dictate the content of the email.")
        body = get_audio()



        talk("Here is the email you're about to send:")
        print("Here is the email you're about to send:")
        talk(f"Subject: {subject}")
        print(f"Subject: {subject}")
        talk(f"Body: {body}")
        print(f"Body: {body}")
        talk("Do you want to attach any files? Say 'yes' or 'no'.")
        print("Do you want to attach any files? Say 'yes' or 'no'.")
        attach_files_response = get_audio()
        if "attach" in attach_files_response or "yes" in attach_files_response or "s" in attach_files_response:
            base_path = r"C:\Users\MAMATHA\Pictures"

            for _ in range(5):
                talk("Please provide the filename.")
                print("Please provide the filename.")
                filename = get_audio()
                filename = filename.replace("dot", ".").replace(" ", "")

                # Construct the full file path by appending the filename to the base path
                file_path = os.path.join(base_path, filename)

    talk("Do you want to Schedule, Save as Draft, or Compose now? Please say schedule, draft, or compose.")
    choice = get_audio()

    for _ in range(5):
      if 'draft' in choice or 'draught' in choice:
        draft_bcc(service,recipients,bcc_recipients, subject, body, file_path)
        break
      elif 'compose' in choice or 'send' in choice:
        send_bcc(service,recipients,bcc_recipients, subject, body, file_path)
        break
      else:
        talk("Invalid choice. Returning to main menu.")

def main():
    talk("Welcome to voice mail service")
    print("Welcome to voice mail service")
    SERVICE2 = authenticate_gmail()

    while True:
        talk("Do you want to read an email or send an email or exit?")
        print("Do you want to read an email or send an email or exit?")
        choice = get_audio().lower()

        if "read" in choice or "narrate" in choice:
            read_mails(SERVICE2)
        elif "send" in choice or "end" in choice or "compose" in choice:
            compose_email(SERVICE2)
        elif "stop" in choice or "exit" in choice:
            exit(0)
        else:
            talk("Invalid choice. Please say 'read' or 'send' or 'exit' ")
            print("Invalid choice. Please say 'read' or 'send' or 'exit' ")


if __name__ == "__main__":
    main()
