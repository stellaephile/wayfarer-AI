#!/usr/bin/env python3
"""
Google OAuth Setup Helper Script
This script helps you set up Google OAuth for the AI Trip Planner application.
"""

import os
import webbrowser
from urllib.parse import urlencode

def print_banner():
    print("=" * 60)
    print("🔐 Google OAuth Setup Helper")
    print("=" * 60)
    print()

def print_step(step_num, title):
    print(f"Step {step_num}: {title}")
    print("-" * 40)

def main():
    print_banner()
    
    print("This script will help you set up Google OAuth authentication.")
    print("You'll need a Google Cloud Platform account.\n")
    
    # Step 1: Google Cloud Console
    print_step(1, "Open Google Cloud Console")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable the Google+ API or Google People API")
    print()
    
    # Step 2: OAuth Consent Screen
    print_step(2, "Configure OAuth Consent Screen")
    print("1. Go to APIs & Services → OAuth consent screen")
    print("2. Choose 'External' user type")
    print("3. Fill in required information:")
    print("   - App name: AI Trip Planner")
    print("   - User support email: your email")
    print("   - Developer contact: your email")
    print("4. Add scopes:")
    print("   - ../auth/userinfo.email")
    print("   - ../auth/userinfo.profile")
    print("   - openid")
    print("5. Add test users (for development)")
    print()
    
    # Step 3: Create Credentials
    print_step(3, "Create OAuth 2.0 Credentials")
    print("1. Go to APIs & Services → Credentials")
    print("2. Click 'Create Credentials' → 'OAuth 2.0 Client IDs'")
    print("3. Application type: Web application")
    print("4. Name: AI Trip Planner Web Client")
    print("5. Authorized JavaScript origins:")
    print("   - http://localhost:8501")
    print("6. Authorized redirect URIs:")
    print("   - http://localhost:8501")
    print("7. Click 'Create'")
    print()
    
    # Step 4: Get Credentials
    print_step(4, "Get Your Credentials")
    print("After creating, you'll get:")
    print("- Client ID")
    print("- Client Secret")
    print("Copy these values!")
    print()
    
    # Step 5: Configure Environment
    print_step(5, "Configure Environment Variables")
    print("Create a .env file with:")
    print("GOOGLE_CLIENT_ID=your-client-id-here")
    print("GOOGLE_CLIENT_SECRET=your-client-secret-here")
    print("GOOGLE_REDIRECT_URI=http://localhost:8501")
    print()
    
    # Step 6: Test
    print_step(6, "Test the Setup")
    print("1. Run: streamlit run src/app.py")
    print("2. Open: http://localhost:8501")
    print("3. Click 'Sign in with Google'")
    print("4. Complete the OAuth flow")
    print()
    
    print("🎉 You're all set! Google OAuth is now integrated.")
    print()
    print("For detailed instructions, see: GOOGLE_OAUTH_SETUP.md")
    print("=" * 60)

if __name__ == "__main__":
    main()
