# 🔐 Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for the AI Trip Planner application.

## 📋 Prerequisites

- Google Cloud Platform account
- Access to Google Cloud Console
- Domain name (for production) or localhost (for development)

## 🚀 Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "AI Trip Planner"
4. Click "Create"

### 2. Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API" or "Google People API"
3. Click on it and press "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" user type
   - Fill in required fields:
     - App name: "AI Trip Planner"
     - User support email: your email
     - Developer contact: your email
   - Add scopes:
     - `../auth/userinfo.email`
     - `../auth/userinfo.profile`
     - `openid`
   - Add test users (for development)

### 4. Configure OAuth Client

1. Application type: "Web application"
2. Name: "AI Trip Planner Web Client"
3. Authorized JavaScript origins:
   - `http://localhost:8501` (for development)
   - `https://yourdomain.com` (for production)
4. Authorized redirect URIs:
   - `http://localhost:8501` (for development)
   - `https://yourdomain.com` (for production)
5. Click "Create"

### 5. Get Credentials

1. After creating, you'll see a popup with:
   - Client ID
   - Client Secret
2. Copy these values

### 6. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8501

# Other configurations...
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-pro
```

### 7. Update Streamlit Secrets (Alternative)

Create `.streamlit/secrets.toml`:

```toml
GOOGLE_CLIENT_ID = "your-client-id-here"
GOOGLE_CLIENT_SECRET = "your-client-secret-here"
GOOGLE_REDIRECT_URI = "http://localhost:8501"

VERTEX_AI_PROJECT_ID = "your-project-id"
VERTEX_AI_LOCATION = "us-central1"
VERTEX_AI_MODEL = "gemini-pro"
```

## �� Testing the Setup

### 1. Start the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
streamlit run src/app.py
```

### 2. Test Google Sign-in

1. Open http://localhost:8501
2. Click "Sign in with Google"
3. Complete the OAuth flow
4. You should be logged in with your Google account

## 🚀 Production Deployment

### 1. Update OAuth Settings

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Edit your OAuth 2.0 client
3. Update authorized origins and redirect URIs:
   - `https://yourdomain.com`
   - `https://yourdomain.com/oauth/callback`

### 2. Update Environment Variables

```bash
GOOGLE_REDIRECT_URI=https://yourdomain.com
```

### 3. Configure Domain

Make sure your domain is properly configured and SSL certificate is installed.

## 🔒 Security Considerations

### 1. Environment Variables

- Never commit `.env` files to version control
- Use secure secret management in production
- Rotate credentials regularly

### 2. OAuth Scopes

The application requests minimal scopes:
- `userinfo.email` - Access to user's email
- `userinfo.profile` - Access to user's basic profile
- `openid` - OpenID Connect

### 3. State Parameter

The application uses a state parameter to prevent CSRF attacks.

## 🐛 Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Check that the redirect URI in Google Console matches your application URL
   - Ensure no trailing slashes

2. **"Access blocked"**
   - Check OAuth consent screen configuration
   - Verify test users are added (for development)

3. **"Client ID not found"**
   - Verify environment variables are set correctly
   - Check that the client ID is copied correctly

4. **"Scope not authorized"**
   - Check that required scopes are added to OAuth consent screen
   - Verify the scopes in the code match the configured scopes

### Debug Mode

Enable debug logging by setting:

```bash
export STREAMLIT_LOGGER_LEVEL=debug
```

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Streamlit Authentication Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Google Cloud Console](https://console.cloud.google.com/)

## 🆘 Support

If you encounter issues:

1. Check the application logs
2. Verify Google Cloud Console settings
3. Test with a simple OAuth flow first
4. Check network connectivity and firewall settings

---

**Happy Authenticating! 🔐**
