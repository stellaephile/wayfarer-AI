import streamlit as st

def inject_css():
    """Inject custom CSS for Wayfarer styling"""
    st.markdown("""
<style>
/* Root variables */
:root {
    --wayfarer-blue: #00A4D4;
    --wayfarer-blue-dark: #008bb5;
    --wayfarer-gray: #f8f9fa;
    --wayfarer-text: #293132;
    --wayfarer-muted: #6b7280;
}

/* Reset Streamlit UI elements */
#MainMenu, footer, header {visibility: hidden;}

/* Main app container */
.main .block-container {
    padding-top: 0 !important;
        padding-bottom: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
}

/* Fullscreen auth page */
.auth-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%);
    padding: 1rem;
}

/* Auth container */
.auth-container {
    background: #fff;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    max-width: 420px;
    width: 100%;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12);
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
}


/* Inputs */
.stTextInput input {
    border-radius: 8px !important;
    border: 1.5px solid #e5e7eb !important;
    padding: 0.75rem !important;
    font-size: 1rem !important;
}
.stTextInput input:focus {
    border-color: var(--wayfarer-blue) !important;
    box-shadow: 0 0 0 3px rgba(0,164,212,0.2) !important;
}

/* Buttons */
.stButton button {
    background: var(--wayfarer-blue) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.8rem 1.2rem !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
}
.stButton button:hover {
    background: var(--wayfarer-blue-dark) !important;
    transform: translateY(-2px) !important;
}

/* Divider */
.divider {
    margin: 1.5rem 0;
    text-align: center;
    position: relative;
    color: var(--wayfarer-muted);
    font-size: 0.9rem;
}
.divider::before, .divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: #e5e7eb;
}
.divider::before { left: 0; }
.divider::after { right: 0; }

/* Google button */
.google-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 0.75rem;
    border: 1.5px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    color: #374151;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    font-size: 0.95rem;
}
.google-btn:hover {
    border-color: #d1d5db;
    background: #f9fafb;
}
.google-icon {
    width: 20px;
    height: 20px;
    margin-right: 8px;
}
.wayfarer-header {
    text-align: center;
    margin-bottom: 2rem;
}

.wayfarer-icon {
    background: var(--wayfarer-blue);
    width: 70px;
    height: 70px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    font-size: 28px;
    color: white;
    box-shadow: 0 4px 12px rgba(0,164,212,0.3);
}

.wayfarer-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--wayfarer-text);
    margin: 0.5rem 0 0 0;
}

.wayfarer-subtitle {
    font-size: 1rem;
    color: var(--wayfarer-muted);
    margin-top: 0.3rem;
}
.gradient-bg {
    background: linear-gradient(135deg, #00A4D4 0%, #008bb5 100%);
    padding: 2rem 1rem;
    border-radius: 16px;
    color: white;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.gradient-bg .wayfarer-icon {
    background: rgba(255, 255, 255, 0.15);
    width: 70px;
    height: 70px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    font-size: 28px;
    color: white;
}

.gradient-bg .wayfarer-title {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.5rem 0 0 0;
    color: white;
}

.gradient-bg .wayfarer-subtitle {
    font-size: 1rem;
    color: rgba(255,255,255,0.8);
    margin-top: 0.3rem;
}

</style>

    """, unsafe_allow_html=True)