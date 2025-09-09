import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Debug Form", layout="wide")

st.title("🔍 Debug Form Test")

# Check if user is logged in
if 'user' not in st.session_state:
    st.error("❌ Please log in first!")
    st.info("Go to the main app and log in, then come back here.")
    st.stop()

st.success(f"✅ Logged in as: {st.session_state.user['name'] or st.session_state.user['username']}")

# Simple form
with st.form("debug_form"):
    st.subheader("Test Form")
    
    destination = st.text_input("Destination", placeholder="e.g., Paris, France")
    start_date = st.date_input("Start Date", value=datetime.now().date())
    end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
    budget = st.number_input("Budget (USD)", min_value=0, value=1000, step=100)
    
    submitted = st.form_submit_button("Test Submit", type="primary")

# Handle form submission
if submitted:
    st.write("🔍 Form submitted!")
    st.write(f"Destination: {destination}")
    st.write(f"Start Date: {start_date}")
    st.write(f"End Date: {end_date}")
    st.write(f"Budget: {budget}")
    
    if destination:
        st.success("✅ Form validation passed!")
        
        # Test the actual trip generation
        try:
            from src.vertex_ai_utils import VertexAITripPlanner
            from src.database import db
            import json
            
            st.write("🔍 Testing trip generation...")
            
            vertex_ai = VertexAITripPlanner()
            suggestions = vertex_ai.generate_trip_suggestions(
                destination=destination,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                budget=budget,
                preferences="Test preferences"
            )
            
            st.success("✅ Trip generation successful!")
            st.write(f"Suggestions keys: {list(suggestions.keys())}")
            
            # Test database save
            success, message = db.create_trip(
                st.session_state.user['id'],
                destination,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                budget,
                "Test preferences",
                json.dumps(suggestions)
            )
            
            if success:
                st.success("✅ Database save successful!")
                trip_id = int(message.split("ID: ")[1])
                st.write(f"Trip ID: {trip_id}")
                
                # Clean up
                db.delete_trip(trip_id, st.session_state.user['id'])
                st.info("Test trip cleaned up")
            else:
                st.error(f"❌ Database save failed: {message}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error("❌ Please enter a destination")

# Show session state
with st.expander("Debug: Session State"):
    st.write(st.session_state)
