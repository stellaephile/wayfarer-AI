import streamlit as st
import json
from datetime import datetime, timedelta
from src.database import db
from src.vertex_ai_utils import VertexAITripPlanner

st.set_page_config(page_title="Simple Trip Test", layout="wide")

st.title("🗺️ Simple Trip Planner Test")

# Check if user is logged in
if 'user' not in st.session_state:
    st.error("Please log in first!")
    st.stop()

st.write(f"Welcome, {st.session_state.user['name'] or st.session_state.user['username']}!")

# Simple form
with st.form("simple_trip_form"):
    destination = st.text_input("Destination", placeholder="e.g., Paris, France")
    start_date = st.date_input("Start Date", value=datetime.now().date())
    end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
    budget = st.number_input("Budget (USD)", min_value=0, value=1000, step=100)
    
    submitted = st.form_submit_button("Generate Trip Plan", type="primary")

if submitted:
    st.write("🔍 Form submitted!")
    
    if not destination:
        st.error("Please enter a destination")
    elif start_date >= end_date:
        st.error("End date must be after start date")
    else:
        st.write("🔍 Form validation passed!")
        
        # Generate suggestions
        vertex_ai = VertexAITripPlanner()
        
        with st.spinner("🤖 Generating trip suggestions..."):
            suggestions = vertex_ai.generate_trip_suggestions(
                destination=destination,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                budget=budget,
                preferences="Test preferences"
            )
        
        st.write("🔍 Suggestions generated!")
        st.write(f"Suggestions type: {type(suggestions)}")
        st.write(f"Suggestions keys: {list(suggestions.keys()) if suggestions else 'None'}")
        
        # Save to database
        success, message = db.create_trip(
            st.session_state.user['id'],
            destination,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            budget,
            "Test preferences",
            json.dumps(suggestions)
        )
        
        st.write(f"🔍 Database save: {success} - {message}")
        
        if success:
            st.success("Trip generated and saved successfully!")
            
            # Show some suggestions
            if suggestions:
                st.subheader("Trip Suggestions")
                st.json(suggestions)
        else:
            st.error(f"Failed to save trip: {message}")
