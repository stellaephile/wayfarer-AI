import streamlit as st
from css_styles import inject_css
import os

# Configure page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="Wayfarer AI",
    page_icon="ᨒ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from auth import  check_auth,login_page,signup_page
from trip_planner import show_trip_planner

def display_background_image():
    """Display background image using base64 encoding in CSS"""
    background_image_path = os.path.join("misc", "login_page_background.jpeg")
    if os.path.exists(background_image_path):
        import base64
        with open(background_image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
            img_url = f"data:image/jpeg;base64,{img_data}"
        
        st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(135deg, rgba(240, 249, 255, 0.4) 0%, rgba(224, 231, 255, 0.4) 100%), 
                       url('{img_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)


def main():
    inject_css()
    
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    
    
    # Check authentication
    if check_auth():
        st.session_state.show_login = False
        show_trip_planner()
        
    else:
        display_background_image()
        col1,col2,col3 =st.columns([1,2,1])
        # Gradient Header
        
        # Auth page container
        with col2:
            st.markdown("""
            <div class="auth-header">
                <h1>ᨒ Wayfarer</h1>
                <p>Reimagine Travel with AI</p>
            </div>
    """, unsafe_allow_html=True)
            with st.container():
                #st.markdown(
                #    """
                #    <div style="background:white; padding:2rem; border-radius:12px;
                #                box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                #    """,
                #    unsafe_allow_html=True
                #)

                # Show login or signup page based on session state
                if st.session_state.get('show_login', True):
                    # Show login page with option to switch to signup
                    login_page()
                else:
                    # Show signup page with option to switch to login
                    signup_page()
                
                

if __name__ == "__main__":
    main()
