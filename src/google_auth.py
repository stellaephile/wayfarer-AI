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
from database import db
from dotenv import load_dotenv

## Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Google OAuth configuration with proper error handling
try:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", st.secrets.get("GOOGLE_CLIENT_ID", ""))
except:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

try:
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", st.secrets.get("GOOGLE_CLIENT_SECRET", ""))
except:
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

try:
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", st.secrets.get("GOOGLE_REDIRECT_URI", "http://localhost:8501"))
except:
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

# OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

class GoogleAuth:
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        self.scopes = SCOPES
        
        # Check if Google OAuth is configured
        self.is_configured = bool(self.client_id and self.client_secret)
        
        if not self.is_configured:
            st.warning("⚠️ Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    
    def get_authorization_url(self):
        """Get Google OAuth authorization URL"""
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
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        st.session_state.oauth_state = state
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        return authorization_url
    
    def get_user_info(self, authorization_response):
        """Get user information from Google OAuth response"""
        if not self.is_configured:
            return None
            
        try:
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
            
            # Verify state parameter
            if 'state' in authorization_response:
                if authorization_response['state'] != st.session_state.get('oauth_state'):
                    st.error("Invalid state parameter. Please try again.")
                    return None
            
            # Exchange authorization code for tokens
            flow.fetch_token(authorization_response=authorization_response)
            
            # Get user info
            credentials = flow.credentials
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            
            return {
                'id': user_info.get('id'),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'given_name': user_info.get('given_name'),
                'family_name': user_info.get('family_name'),
                'picture': user_info.get('picture'),
                'verified_email': user_info.get('verified_email', False)
            }
            
        except Exception as e:
            st.error(f"Error during Google authentication: {str(e)}")
            return None
    
    def create_or_get_user(self, google_user_info):
        """Create or get user from Google OAuth info"""
        if not google_user_info:
            return None
            
        email = google_user_info['email']
        name = google_user_info['name']
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return existing_user
        
        # Create new user with Google info
        username = self._generate_username_from_email(email)
        success, message = db.create_google_user(
            username=username,
            email=email,
            name=name,
            google_id=google_user_info['id'],
            picture=google_user_info.get('picture', ''),
            verified_email=google_user_info.get('verified_email', False)
        )
        
        if success:
            return db.get_user_by_email(email)
        else:
            st.error(f"Error creating user: {message}")
            return None
    
    def _generate_username_from_email(self, email):
        """Generate username from email"""
        local_part = email.split('@')[0]
        # Remove special characters and make it unique
        username = ''.join(c for c in local_part if c.isalnum() or c in '._-')
        # Add random suffix to ensure uniqueness
        random_suffix = secrets.token_hex(4)
        return f"{username}_{random_suffix}"

def show_google_signin_button():
    """Show Google sign-in button"""
    google_auth = GoogleAuth()
    
    if not google_auth.is_configured:
        st.info("Google sign-in is not configured. Please contact administrator.")
        return False
    
    # Create Google sign-in button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔐 Sign in with Google", use_container_width=True, type="primary"):
            auth_url = google_auth.get_authorization_url()
            if auth_url:
                st.markdown(f"""
                <script>
                    window.open('{auth_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)
                st.info("Please complete the Google sign-in in the popup window.")
    
    return True

def handle_google_callback():
    """Handle Google OAuth callback"""
    google_auth = GoogleAuth()
    
    if not google_auth.is_configured:
        return False
    
    # Check if we have authorization response in URL
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        authorization_response = {
            'code': query_params['code'],
            'state': query_params['state']
        }
        
        # Get user info from Google
        google_user_info = google_auth.get_user_info(authorization_response)
        
        if google_user_info:
            # Create or get user
            user = google_auth.create_or_get_user(google_user_info)
            
            if user:
                st.session_state.user = user
                st.session_state.logged_in = True
                st.session_state.login_method = 'google'
                st.success(f"Welcome, {user['name']}!")
                st.rerun()
            else:
                st.error("Failed to create or retrieve user account.")
        else:
            st.error("Failed to authenticate with Google.")
    
    return False

# Initialize Google Auth
google_auth = GoogleAuth()
