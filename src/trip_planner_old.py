import streamlit as st
import json
from datetime import datetime, timedelta
from database import db
from vertex_ai_utils import VertexAITripPlanner

def show_trip_planner():
    """Main trip planner interface"""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🗺️ Trip Planner")
        
        # User info
        if 'user' in st.session_state:
            st.write(f"Welcome, {st.session_state.user['name'] or st.session_state.user['username']}!")
        
        # Navigation
        page = st.radio(
            "Choose an option:",
            ["Plan New Trip", "My Trips", "Analytics", "Profile"],
            key="trip_planner_page"
        )
    
    # Main content area
    if page == "Plan New Trip":
        plan_new_trip()
    elif page == "My Trips":
        show_my_trips()
    elif page == "Analytics":
        show_analytics()
    elif page == "Profile":
        show_profile()

def plan_new_trip():
    """Plan a new trip with AI assistance"""
    st.title("🗺️ Plan Your Perfect Trip")
    
    # Initialize Vertex AI
    vertex_ai = VertexAITripPlanner()
    
    with st.form("trip_planning_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input("Destination", placeholder="e.g., Paris, France")
            start_date = st.date_input("Start Date", value=datetime.now().date())
            end_date = st.date_input("End Date", value=datetime.now().date() + timedelta(days=7))
            budget = st.number_input("Budget (USD)", min_value=0, value=1000, step=100)
        
        with col2:
            travel_type = st.selectbox(
                "Travel Type",
                ["Solo", "Couple", "Family", "Friends", "Business"]
            )
            
            preferences = st.multiselect(
                "Interests",
                ["Adventure", "Culture", "Food", "History", "Nature", "Nightlife", "Shopping", "Relaxation"]
            )
            
            accommodation_type = st.selectbox(
                "Accommodation Preference",
                ["Budget", "Mid-range", "Luxury", "Hostel", "Airbnb"]
            )
        
        # Additional preferences
        additional_preferences = st.text_area(
            "Additional Preferences",
            placeholder="Any specific requirements or interests..."
        )
        
        submitted = st.form_submit_button("Generate Trip Plan", type="primary")
        
        if submitted:
            if not destination:
                st.error("Please enter a destination")
                return
            
            if start_date >= end_date:
                st.error("End date must be after start date")
                return
            
            # Prepare preferences string
            preferences_str = ", ".join(preferences)
            if additional_preferences:
                preferences_str += f" | Additional: {additional_preferences}"
            
            # Show loading
            with st.spinner("🤖 AI is planning your perfect trip..."):
                suggestions = vertex_ai.generate_trip_suggestions(
                    destination=destination,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    budget=budget,
                    preferences=preferences_str
                )
            
            # Save trip to database
            success, message = db.create_trip(
                st.session_state.user['id'],
                destination,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                budget,
                preferences_str,
                json.dumps(suggestions)
            )
            
            if success:
                # Extract trip_id from message
                trip_id = int(message.split("ID: ")[1])
                st.session_state.current_trip = suggestions
                st.session_state.trip_id = trip_id
                st.success("Trip plan generated successfully!")
                st.rerun()
            else:
                st.error(f"Failed to save trip: {message}")

def show_trip_details(trip_data):
    """Display detailed trip information"""
    suggestions = json.loads(trip_data['ai_suggestions']) if isinstance(trip_data['ai_suggestions'], str) else trip_data['ai_suggestions']
    
    st.subheader(f"🗺️ {trip_data['destination']}")
    
    # Trip overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Duration", f"{trip_data['start_date']} to {trip_data['end_date']}")
    with col2:
        st.metric("Budget", f"${trip_data['budget']:,.2f}")
    with col3:
        st.metric("Status", trip_data['status'].title())
    
    # AI suggestions
    if suggestions:
        st.subheader("🤖 AI Recommendations")
        
        # Itinerary
        if 'itinerary' in suggestions:
            st.subheader("📅 Daily Itinerary")
            for day, activities in suggestions['itinerary'].items():
                with st.expander(f"Day {day}"):
                    for activity in activities:
                        st.write(f"• {activity}")
        
        # Accommodations
        if 'accommodations' in suggestions:
            st.subheader("🏨 Accommodations")
            for hotel in suggestions['accommodations']:
                with st.container():
                    st.write(f"**{hotel['name']}**")
                    st.write(f"📍 {hotel['location']}")
                    st.write(f"💰 ${hotel['price']}/night")
                    if 'rating' in hotel:
                        st.write(f"⭐ {hotel['rating']}/5")
                    st.write("---")
        
        # Activities
        if 'activities' in suggestions:
            st.subheader("🎯 Activities")
            for activity in suggestions['activities']:
                with st.container():
                    st.write(f"**{activity['name']}**")
                    st.write(f"📍 {activity['location']}")
                    st.write(f"💰 ${activity['cost']}")
                    st.write(f"⏰ {activity['duration']}")
                    st.write("---")
        
        # Restaurants
        if 'restaurants' in suggestions:
            st.subheader("🍽️ Restaurants")
            for restaurant in suggestions['restaurants']:
                with st.container():
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"📍 {restaurant['location']}")
                    st.write(f"💰 {restaurant['price_range']}")
                    if 'cuisine' in restaurant:
                        st.write(f"🍴 {restaurant['cuisine']}")
                    st.write("---")
        
        # Transportation
        if 'transportation' in suggestions:
            st.subheader("🚗 Transportation")
            for transport in suggestions['transportation']:
                with st.container():
                    st.write(f"**{transport['type']}**")
                    st.write(f"📍 {transport['route']}")
                    st.write(f"💰 ${transport['cost']}")
                    st.write("---")
        
        # Tips
        if 'tips' in suggestions:
            st.subheader("💡 Travel Tips")
            for tip in suggestions['tips']:
                st.write(f"• {tip}")
        
        # Weather
        if 'weather' in suggestions:
            st.subheader("🌤️ Weather Information")
            weather = suggestions['weather']
            st.write(f"**Temperature:** {weather.get('temperature', 'N/A')}")
            st.write(f"**Conditions:** {weather.get('conditions', 'N/A')}")
            st.write(f"**Packing:** {weather.get('packing', 'N/A')}")

def show_my_trips():
    """Display user's saved trips"""
    st.title("🗺️ My Trips")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view your trips")
        return
    
    user_id = st.session_state.user['id']
    trips = db.get_user_trips(user_id)
    
    if not trips:
        st.info("No trips found. Start planning your first trip!")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "planned", "booked", "completed", "cancelled"])
    with col2:
        sort_by = st.selectbox("Sort by", ["Date Created", "Start Date", "Destination", "Budget"])
    
    # Filter trips
    if status_filter != "All":
        trips = [trip for trip in trips if trip['status'] == status_filter]
    
    # Sort trips
    if sort_by == "Date Created":
        trips.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Start Date":
        trips.sort(key=lambda x: x['start_date'] or "", reverse=True)
    elif sort_by == "Destination":
        trips.sort(key=lambda x: x['destination'])
    elif sort_by == "Budget":
        trips.sort(key=lambda x: x['budget'] or 0, reverse=True)
    
    # Display trips
    for trip in trips:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(f"🗺️ {trip['destination']}")
                st.write(f"📅 {trip['start_date']} to {trip['end_date']}")
                st.write(f"💰 Budget: ${trip['budget']:,.2f}")
                st.write(f"📊 Status: {trip['status'].title()}")
            
            with col2:
                if st.button("View Details", key=f"view_{trip['id']}"):
                    st.session_state.selected_trip = trip
                    st.rerun()
            
            with col3:
                if st.button("Delete", key=f"delete_{trip['id']}"):
                    success, message = db.delete_trip(trip['id'], user_id)
                    if success:
                        st.success("Trip deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error deleting trip: {message}")
            
            st.write("---")
    
    # Show selected trip details
    if 'selected_trip' in st.session_state:
        st.subheader("Trip Details")
        show_trip_details(st.session_state.selected_trip)
        
        if st.button("Close Details"):
            del st.session_state.selected_trip
            st.rerun()

def show_analytics():
    """Show trip analytics and statistics"""
    st.title("📊 Trip Analytics")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view analytics")
        return
    
    user_id = st.session_state.user['id']
    stats = db.get_user_stats(user_id)
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trips", stats['trip_count'])
    with col2:
        st.metric("Total Budget", f"${stats['total_budget']:,.2f}")
    with col3:
        st.metric("Favorite Destination", stats['popular_destination'])
    
    # Trip history
    trips = db.get_user_trips(user_id)
    if trips:
        st.subheader("Trip History")
        
        # Create a simple chart
        import pandas as pd
        df = pd.DataFrame(trips)
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Monthly trip count
        monthly_trips = df.groupby(df['created_at'].dt.to_period('M')).size()
        st.subheader("Trips by Month")
        st.bar_chart(monthly_trips)
        
        # Budget distribution
        if 'budget' in df.columns:
            st.subheader("Budget Distribution")
            st.bar_chart(df.set_index('destination')['budget'])

def show_profile():
    """Show user profile and settings"""
    st.title("👤 Profile")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view profile")
        return
    
    user = st.session_state.user
    
    # Profile information
    st.subheader("Profile Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Name:** {user.get('name', 'Not set')}")
        st.write(f"**Login Method:** {user.get('login_method', 'email').title()}")
    
    with col2:
        st.write(f"**Member Since:** {user.get('created_at', 'Unknown')}")
        st.write(f"**Last Login:** {user.get('last_login', 'Unknown')}")
        st.write(f"**Status:** {'Active' if user.get('is_active', True) else 'Inactive'}")
    
    # Profile update form
    st.subheader("Update Profile")
    
    with st.form("profile_update_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Full Name", value=user.get('name', ''))
            personal_number = st.text_input("Personal Number", value=user.get('personal_number', ''))
            address = st.text_area("Address", value=user.get('address', ''))
        
        with col2:
            pincode = st.text_input("Pincode", value=user.get('pincode', ''))
            state = st.text_input("State", value=user.get('state', ''))
            alternate_number = st.text_input("Alternate Number", value=user.get('alternate_number', ''))
        
        if st.form_submit_button("Update Profile"):
            # Update profile
            success, message = db.update_user_profile(
                user['id'],
                name=new_name,
                personal_number=personal_number,
                address=address,
                pincode=pincode,
                state=state,
                alternate_number=alternate_number
            )
            
            if success:
                st.success("Profile updated successfully!")
                # Update session state
                st.session_state.user.update({
                    'name': new_name,
                    'personal_number': personal_number,
                    'address': address,
                    'pincode': pincode,
                    'state': state,
                    'alternate_number': alternate_number
                })
                st.rerun()
            else:
                st.error(f"Error updating profile: {message}")
    
    # Account actions
    st.subheader("Account Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Change Password"):
            st.info("Password change functionality coming soon!")
    
    with col2:
        if st.button("Delete Account", type="secondary"):
            st.warning("Account deletion functionality coming soon!")

# Initialize the trip planner
if __name__ == "__main__":
    show_trip_planner()
