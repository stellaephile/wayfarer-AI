import streamlit as st

# Configure page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import other modules
from misc.auth import show_auth_pages, check_auth
from trip_planner import show_trip_planner
from credit_widget import credit_widget

def main():
    """Main application entry point"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Root variables */
    :root {
        --primary-color: #00A4D4;
        --accent-color: #F7F052;
        --text-primary: #293162;
        --text-secondary: #4F5165;
        --background: #fafafa;
        --card-background: #ffffff;
        --muted-background: #f1f3f4;
        --border-color: rgba(79, 81, 101, 0.15);
    }

    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--card-background);
        border-right: 1px solid var(--border-color);
    }

    .css-1d391kg .css-1v3fvcr {
        background-color: var(--card-background);
    }

    /* Wayfarer brand in sidebar */
    .wayfarer-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 24px 16px;
        margin-bottom: 20px;
        background: var(--card-background);
        border-radius: 8px;
    }

    .wayfarer-icon {
        background: var(--primary-color);
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }


    /* User card styling */
    .user-card {
        background: var(--muted-background);
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--primary-color);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 16px;
    }

    .user-info h4 {
        margin: 0;
        color: var(--text-primary);
        font-weight: 500;
    }

    .user-info p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 14px;
    }

    /* Animated gradient button */
    .animated-gradient-button {
        background: var(--primary-color);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        text-decoration: none;
        display: inline-block;
        margin: 8px 0;
    }

    .animated-gradient-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--accent-color) 50%, var(--primary-color) 100%);
        background-size: 200% 100%;
        background-position: 100% 0;
        transition: background-position 0.6s ease;
        z-index: 1;
    }

    .animated-gradient-button::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
        transform: translateX(-100%);
        transition: transform 0.6s ease;
        z-index: 2;
    }

    .animated-gradient-button:hover::before {
        background-position: -100% 0;
    }

    .animated-gradient-button:hover::after {
        transform: translateX(100%);
    }

    .animated-gradient-button span {
        position: relative;
        z-index: 3;
    }

    /* Card styling */
    .metric-card {
        background: var(--card-background);
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid var(--border-color);
        margin-bottom: 16px;
    }

    .metric-card h3 {
        margin: 0 0 8px 0;
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
    }

    .metric-card .metric-value {
        font-size: 32px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .metric-card .metric-change {
        font-size: 14px;
        margin: 8px 0 0 0;
    }

    .metric-change.positive {
        color: #10b981;
    }

    .metric-change.negative {
        color: #ef4444;
    }

    /* Trip card styling */
    .trip-card {
        background: var(--card-background);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid var(--border-color);
        margin-bottom: 16px;
    }

    .trip-card h3 {
        margin: 0 0 8px 0;
        color: var(--text-primary);
        font-weight: 600;
    }

    .trip-card .trip-meta {
        color: var(--text-secondary);
        font-size: 14px;
        margin-bottom: 12px;
    }

    .trip-status {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 500;
    }

    .status-planned {
        background: #fef3c7;
        color: #92400e;
    }

    .status-completed {
        background: #d1fae5;
        color: #065f46;
    }

    .status-in-progress {
        background: #dbeafe;
        color: #1e40af;
    }

    /* Form styling */
    .stSelectbox > div > div {
        background-color: var(--muted-background);
        border: 1px solid var(--border-color);
    }

    .stTextInput > div > div > input {
        background-color: var(--muted-background);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }

    .stTextArea > div > div > textarea {
        background-color: var(--muted-background);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
    }


    .welcome-section {
        background: linear-gradient(135deg, var(--primary-color), #0088cc);
        color: white;
        padding: 10px;
        border-radius: 16px;
        margin-bottom: 32px;
    }

    .recent-trips {
        background: var(--card-background);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid var(--border-color);
    }

    /* Currency symbols */
    .currency-symbol {
        font-weight: 600;
        color: var(--primary-color);
    }
            .login-container {
            background: #ffffff;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
        }
        /* Full page */
        .login-page {
            height: 100vh; /* Take full screen */
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f7f9fc;
        }

        /* Centered container */
        .login-container {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            width: 100%;
            max-width: 400px;
            max-height: 90vh; /* Prevent overflow */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        /* Header */
        .login-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }

/* Icon */
.login-icon {
    background: var(--primary-color);
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    box-shadow: 0 4px 10px rgba(0, 164, 212, 0.3);
}

/* Title and subtitle */
.wayfarer-title {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 0.5rem 0;
    color: var(--text-primary);
}

.login-subtitle {
    font-size: 1rem;
    color: var(--text-secondary);
    margin: 0;
}

    /* Accent button */
    .accent-btn {
        background-color: var(--accent-color);
        color: var(--text-primary);
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: 0.3s;
        width: 100%;
        margin-top: 1rem;
    }
    .accent-btn:hover {
        background-color: #e6e04d;
    }


    .wayfarer-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0 0 0;
        color: #293132;
    }



    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Check if user is authenticated
    if not check_auth():
        # Show authentication pages
        #st.markdown('<h1 class="main-header">🗺️ AI Trip Planner</h1>', unsafe_allow_html=True)
        #st.markdown('<p class="welcome-message">Plan your perfect trip with AI-powered suggestions</p>', unsafe_allow_html=True)
        show_auth_pages()
    else:
        # Show credit widget in sidebar
        if 'user' in st.session_state:
            credit_widget.show_credit_sidebar(st.session_state.user['id'])
        
        # Show main application
        show_trip_planner()

if __name__ == "__main__":
    main()
