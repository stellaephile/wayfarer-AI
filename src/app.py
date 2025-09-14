# app.py
import streamlit as st
import os

# Configure page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from auth import show_auth_pages, check_auth
from trip_planner import show_trip_planner

def main():
    """Main application entry point"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .welcome-message {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0d5a8a;
        color: white;
    }
    .sustainable-option {
        border-left: 4px solid #28a745;
        padding-left: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .booking-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check if user is authenticated
    if not check_auth():
        # Show authentication pages
        st.markdown('<h1 class="main-header">🗺️ AI Trip Planner</h1>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-message">Plan your perfect trip with AI-powered suggestions and sustainable travel options</p>', unsafe_allow_html=True)
        show_auth_pages()
    else:
        # Show main application
        show_trip_planner()

if __name__ == "__main__":
    main()