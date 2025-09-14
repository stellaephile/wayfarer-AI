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
        
        # Store state in session state
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
            # Verify state parameter (with debugging)
            if 'state' in authorization_response:
                stored_state = st.session_state.get('oauth_state')
                received_state = authorization_response['state']
                
                # Debug information
                st.write(f"🔍 Debug: Stored state: {stored_state[:10] if stored_state else 'None'}...")
                st.write(f"🔍 Debug: Received state: {received_state[:10]}...")
                
                if not stored_state:
                    st.warning("⚠️ No stored state found. This might be a new session or the state was lost.")
                    st.info("ℹ️ Continuing with authentication (state validation skipped for new sessions)")
                elif stored_state != received_state:
                    st.error(f"❌ State parameter mismatch!")
                    st.error(f"Expected: {stored_state[:10]}...")
                    st.error(f"Received: {received_state[:10]}...")
                    st.error("Please try signing in again.")
                    # Clear the invalid state
                    if 'oauth_state' in st.session_state:
                        del st.session_state['oauth_state']
                    return None
                else:
                    st.success("✅ State parameter validated successfully!")
            
            # Use requests to exchange code for tokens directly
            import requests
            
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_response['code'],
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            st.write(f"🔍 Debug: Token request data: {token_data}")
            
            # Exchange code for tokens
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            st.write(f"🔍 Debug: Token response: {list(tokens.keys())}")
            
            # Get user info using the access token
            access_token = tokens['access_token']
            user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            
            user_response = requests.get(user_info_url)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            st.write(f"🔍 Debug: User info: {list(user_info.keys())}")
            
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
            st.write(f"🔍 Full error details: {type(e).__name__}: {str(e)}")
            import traceback
            st.write(f"🔍 Traceback: {traceback.format_exc()}")
            return None
    
    def create_or_get_user(self, google_user_info):
        """Create or get user from Google OAuth info"""
        if not google_user_info:
            return None
            
        email = google_user_info['email']
        name = google_user_info['name']
        google_id = google_user_info['id']
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            # If user exists, check if it's already a Google user
            if existing_user.get('login_method') == 'google':
                st.success(f"Welcome back, {existing_user['name']}!")
                return existing_user
            else:
                # User exists but with different login method
                st.warning(f"⚠️ An account with email {email} already exists with {existing_user.get('login_method', 'email')} login.")
                st.info("🔄 Linking your Google account to the existing account...")
                
                # Update existing user to include Google info
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE users 
                        SET google_id = ?, picture = ?, verified_email = ?, login_method = 'google'
                        WHERE email = ?
                    """, (google_id, google_user_info.get('picture', ''), 
                          google_user_info.get('verified_email', False), email))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Google account linked successfully! Welcome, {name}!")
                    return db.get_user_by_email(email)
                except Exception as e:
                    st.error(f"❌ Error linking Google account: {str(e)}")
                    return None
        
        # Create new user with Google info
        username = self._generate_username_from_email(email)
        success, message = db.create_google_user(
            username=username,
            email=email,
            name=name,
            google_id=google_id,
            picture=google_user_info.get('picture', ''),
            verified_email=google_user_info.get('verified_email', False)
        )
        
        if success:
            st.success(f"✅ New Google account created! Welcome, {name}!")
            return db.get_user_by_email(email)
        else:
            st.error(f"❌ Error creating user: {message}")
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
    
    # Get authorization URL
    auth_url = google_auth.get_authorization_url()
    if not auth_url:
        st.error("Failed to generate Google OAuth URL")
        return False
    
    # Create Google sign-in button using st.link_button (more reliable)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button(
            "🔐 Sign in with Google", 
            auth_url, 
            use_container_width=True,
            type="primary"
        )
    
    st.info("Click the button above to sign in with Google. You'll be redirected to Google's authentication page.")
    
    return True

def handle_google_callback():
    """Handle Google OAuth callback"""
    google_auth = GoogleAuth()
    
    if not google_auth.is_configured:
        return False
    
    # Check if we have authorization response in URL
    query_params = st.query_params
    
    if 'code' in query_params:
        try:
            # Create authorization response with or without state
            authorization_response = {
                'code': query_params['code']
            }
            
            # Add state if present
            if 'state' in query_params:
                authorization_response['state'] = query_params['state']
            
            st.info("🔄 Processing Google authentication...")
            
            # Get user info from Google
            google_user_info = google_auth.get_user_info(authorization_response)
            
            if google_user_info:
                # Create or get user
                user = google_auth.create_or_get_user(google_user_info)
                
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.session_state.login_method = 'google'
                    st.success(f"🎉 Welcome, {user['name']}!")
                    # Clear the URL parameters after successful login
                    st.query_params.clear()
                    # Clear OAuth state
                    if 'oauth_state' in st.session_state:
                        del st.session_state['oauth_state']
                    st.rerun()
                else:
                    st.error("❌ Failed to create or retrieve user account.")
            else:
                st.error("❌ Failed to authenticate with Google.")
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")
            st.write(f"🔍 Error details: {type(e).__name__}: {str(e)}")
    
    # Check for error in OAuth response
    elif 'error' in query_params:
        error = query_params.get('error', 'Unknown error')
        error_description = query_params.get('error_description', '')
        st.error(f"❌ Google OAuth Error: {error}")
        if error_description:
            st.error(f"Description: {error_description}")
        # Clear error parameters from URL
        st.query_params.clear()
    
    return False

# Initialize Google Auth
google_auth = GoogleAuth()
