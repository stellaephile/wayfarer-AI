import streamlit as st
from datetime import datetime, timedelta

st.title("Test Form")

with st.form("test_form"):
    destination = st.text_input("Destination", placeholder="e.g., Paris, France")
    start_date = st.date_input("Start Date", value=datetime.now().date())
    end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
    budget = st.number_input("Budget (USD)", min_value=0, value=1000, step=100)
    
    submitted = st.form_submit_button("Test Submit", type="primary")
    
    if submitted:
        st.write("Form submitted!")
        st.write(f"Destination: {destination}")
        st.write(f"Start Date: {start_date}")
        st.write(f"End Date: {end_date}")
        st.write(f"Budget: {budget}")
        
        if destination:
            st.success("Form validation passed!")
        else:
            st.error("Please enter a destination")
