"""
Gmail OAuth2 Setup for Django
This is an alternative to app passwords that's more secure
"""

# Install required packages:
# pip install google-auth google-auth-oauthlib google-auth-httplib2

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Gmail API scopes
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def setup_gmail_oauth():
    """Set up Gmail OAuth2 credentials"""
    creds = None

    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds


if __name__ == "__main__":
    print("Setting up Gmail OAuth2...")
    creds = setup_gmail_oauth()
    print("OAuth2 setup complete!")
    print("You can now use these credentials in your Django settings")
