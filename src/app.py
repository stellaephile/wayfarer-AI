import streamlit as st
from css_styles import inject_css
# Configure page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from auth import  check_auth,login_page,signup_page
from trip_planner import show_trip_planner

def main():
    inject_css()
    
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    
    
    # Check authentication
    if check_auth():
        st.session_state.show_login = False
        show_trip_planner()
        
    else:
        
        col1,col2,col3 =st.columns([1,2,1])
        # Gradient Header
        
        # Auth page container
        with col2:
            st.markdown("""
            <style>
                .auth-header {
                    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                    padding: 0rem;
                    border-radius: 12px;
                    text-align: center;
                    margin-bottom: 1rem;
                }
                .auth-header h1 {
                    color: white;
                    margin: 0;
                    font-size: 2rem;
                    font-family: 'Space Grotesk', sans-serif;
                }
                .auth-header p {
                    color: rgba(255,255,255,0.9);
                    margin: 0rem 0 0 0;
                    font-size: 1rem;
                }
            </style>

            <div class="auth-header">
                <h1>🌍 Wayfarer</h1>
                <p>Your AI-powered travel companion</p>
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

                # Tabs for login/signup
                tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

                with tab1:
                        login_page()
                with tab2:
                        signup_page()
                
                

if __name__ == "__main__":
    main()
