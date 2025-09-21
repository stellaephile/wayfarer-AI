import streamlit as st
import re,time
from cloudsql_database_config import get_database
db = get_database()
from google_auth import show_google_signin_button, handle_google_callback

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""

def validate_username(username):
    """Validate username format"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""



def login_page():
    """Display login page with enhanced UI and Google OAuth"""
    # Handle Google OAuth callback
    if handle_google_callback():
        return
    
    
    st.markdown("### 🔐 Welcome Back!")
    st.markdown("Sign in to access your personalized trip planner")
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit_button = st.form_submit_button("Login", use_container_width=True)
        
        with col2:
            #st.markdown("### Or continue with")
            show_google_signin_button()
        if submit_button:
            if not username or not password:
                st.error("Please fill in all fields")
                return
            
            with st.spinner("Authenticating..."):
                time.sleep(1)  # Simulate API call
                user = db.authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.session_state.login_method = 'email'
                    st.success(f"Welcome back, {user['username']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    
    # Google Sign In Button
    
    
    
    
    if st.button("Don't have an account? Sign Up", use_container_width=True, key="show_signup"):
        st.session_state.show_login = False
        st.rerun()
    

def signup_page():
    """Display signup page with enhanced validation and Google OAuth"""
    """Display signup form"""
    if handle_google_callback():
        return
    
    st.markdown("### 📝 Create Your Account")
    st.markdown("Join thousands of travelers planning amazing trips with AI")
    
    with st.form("signup_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        #agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        submit_button = st.form_submit_button("Create Account", use_container_width=True)
        show_google_signin_button
        if submit_button:
            # Validation
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return
            
            #if not agree_terms:
            #    st.error("Please agree to the Terms of Service and Privacy Policy")
            #    return
            
            # Validate username
            is_valid_username, username_error = validate_username(username)
            if not is_valid_username:
                st.error(username_error)
                return
            
            # Validate email
            if not validate_email(email):
                st.error("Please enter a valid email address")
                return
            
            # Validate password
            is_valid_password, password_error = validate_password(password)
            if not is_valid_password:
                st.error(password_error)
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            # Create user
            with st.spinner("Creating your account..."):
                time.sleep(1)  # Simulate API call
                success, message = db.create_user(username, email, password)
                if success:
                    st.success("Account created successfully! Please login.")
                    time.sleep(2)
                    st.session_state.show_login = True
                    st.rerun()
                else:
                    st.error(message)
    
    # Google Sign In Button
    #st.markdown("---")
    #st.markdown("### Or continue with")
    
    
    
    #st.markdown("---")
    if st.button("Already have an account? Log In", use_container_width=True):
        st.session_state.show_login = True
        st.rerun()
    

def logout():
    """Logout user and clear session"""
    for key in ['user', 'logged_in', 'current_trip', 'trip_id', 'login_method', 'oauth_state']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def check_auth():
    """Check if user is authenticated"""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        return False
    return True
