import streamlit as st
from auth import show_auth_pages, check_auth
from trip_planner import show_trip_planner

# Configure page
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check if user is authenticated
    if not check_auth():
        # Show authentication pages
        st.markdown('<h1 class="main-header">🗺️ AI Trip Planner</h1>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-message">Plan your perfect trip with AI-powered suggestions</p>', unsafe_allow_html=True)
        show_auth_pages()
    else:
        # Show main application
        show_trip_planner()

if __name__ == "__main__":
    main()
