import streamlit as st
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64
import hashlib
import secrets
import sqlalchemy,requests
from cloudsql_database_config import get_database
db = get_database()
from dotenv import load_dotenv

## Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Google OAuth configuration with proper error handling
def get_config_value(env_key, secrets_key=None, default=""):
    """Get configuration value from environment or secrets with fallback"""
    # Try environment variable first
    value = os.getenv(env_key, "")
    if value:
        return value
    
    # Try secrets if available
    try:
        if secrets_key and hasattr(st, 'secrets') and st.secrets:
            return st.secrets.get(secrets_key, default)
    except:
        pass
    
    return default

GOOGLE_CLIENT_ID = get_config_value("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = get_config_value("GOOGLE_CLIENT_SECRET", "GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = get_config_value("GOOGLE_REDIRECT_URI", "GOOGLE_REDIRECT_URI", "http://localhost:8501")

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]


db = get_database()

class GoogleAuth:

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
        self.is_configured = bool(self.client_id and self.client_secret)
        self.scopes = SCOPES
        if not self.is_configured:
            st.warning("⚠️ Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")

    def get_authorization_url(self):
        """Return Google OAuth URL with state"""
        if not self.is_configured:
            return None

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri

        # Secure random state
        state = secrets.token_urlsafe(32)
        st.session_state.oauth_state = state

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state
        )
        return auth_url

    def exchange_code_for_userinfo(self, code):
        """Exchange authorization code for user info"""
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]

        user_info_response = requests.get(
            f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        )
        user_info_response.raise_for_status()
        return user_info_response.json()

    def create_or_get_user(self, user_info):
        """Create or retrieve user in DB"""
        email = user_info["email"]
        google_id = user_info["id"]
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        verified = user_info.get("verified_email", False)

        # Check existing user
        user = db.get_user_by_email(email)
        if user:
            # Update Google info if needed
            if user.get("login_method") != "google":
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users
                    SET google_id = %s, picture = %s, verified_email = %s, login_method = 'google'
                    WHERE email = %s
                """, (google_id, picture, verified, email))
                conn.commit()
                conn.close()
            return db.get_user_by_email(email)

        # New user creation
        username = self._generate_username_from_email(email)
        success, _ = db.create_google_user(
            username=username, email=email, name=name, google_id=google_id,
            picture=picture, verified_email=verified
        )
        if success:
            return db.get_user_by_email(email)
        return None

    def _generate_username_from_email(self, email):
        local = ''.join(c for c in email.split('@')[0] if c.isalnum() or c in '._-')
        return f"{local}_{secrets.token_hex(4)}"


def show_google_signin_button():
    auth = GoogleAuth()
    if not auth.is_configured:
        st.info("Google sign-in not configured.")
        return False
    url = auth.get_authorization_url()
    st.link_button("🔐 Sign in with Google", url, use_container_width=True)
    return True




def handle_google_callback():
    """Handle OAuth callback and log in user"""
    auth = GoogleAuth()
    if not auth.is_configured:
        return False

    params = st.query_params

    # OAuth error
    if "error" in params:
        st.error(f"Google OAuth error: {params['error']}")
        st.query_params.clear()
        return False

    #if "code" not in params:
    #    st.info("Click the Google sign-in button to continue.")
    #    return False

    # Validate state
    #if "state" not in params or params["state"] != st.session_state.get("oauth_state"):
    #    st.error("OAuth state mismatch. Please try signing in again.")
    #    return False

    try:
        user_info = auth.exchange_code_for_userinfo(params["code"])
        user = auth.create_or_get_user(user_info)
        if user:
            st.session_state.user = user
            st.session_state.logged_in = True
            st.session_state.login_method = "google"
            st.query_params.clear()
            st.session_state.pop("oauth_state", None)
            st.success(f"Welcome, {user['name']}!")
            st.rerun()
        else:
            st.error("Failed to log in user.")
            return False
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return False


# Initialize Google Auth
google_auth = GoogleAuth()
