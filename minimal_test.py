import streamlit as st

st.set_page_config(page_title="Minimal Test")

st.title("Minimal Form Test")

# Check if user is logged in
if 'user' not in st.session_state:
    st.error("❌ Please log in first!")
    st.stop()

st.success(f"✅ Logged in as: {st.session_state.user['name'] or st.session_state.user['username']}")

# Very simple form
with st.form("minimal_form"):
    destination = st.text_input("Destination")
    submitted = st.form_submit_button("Test", type="primary")

if submitted:
    st.write("FORM SUBMITTED!")
    st.write(f"Destination: {destination}")
    
    if destination:
        st.success("SUCCESS!")
    else:
        st.error("Please enter destination")

# Show session state
st.write("Session state:")
st.write(st.session_state)
