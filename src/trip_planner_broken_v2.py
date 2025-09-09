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
    
    # Create form
    with st.form("trip_planning_form", clear_on_submit=False):
        st.subheader("Trip Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "Destination *", 
                placeholder="e.g., Paris, France",
                help="Enter your travel destination"
            )
            start_date = st.date_input(
                "Start Date *", 
                value=datetime.now().date(),
                help="When does your trip start?"
            )
            end_date = st.date_input(
                "End Date *", 
                value=datetime.now().date() + timedelta(days=7),
                help="When does your trip end?"
            )
            budget = st.number_input(
                "Budget (USD) *", 
                min_value=0, 
                value=1000, 
                step=100,
                help="Your total trip budget"
            )
        
        with col2:
            travel_type = st.selectbox(
                "Travel Type",
                ["Solo", "Couple", "Family", "Friends", "Business"],
                help="Who are you traveling with?"
            )
            
            preferences = st.multiselect(
                "Interests",
                ["Adventure", "Culture", "Food", "History", "Nature", "Nightlife", "Shopping", "Relaxation"],
                help="Select your interests"
            )
            
            accommodation_type = st.selectbox(
                "Accommodation Preference",
                ["Budget", "Mid-range", "Luxury", "Hostel", "Airbnb"],
                help="What type of accommodation do you prefer?"
            )
        
        # Additional preferences
        additional_preferences = st.text_area(
            "Additional Preferences",
            placeholder="Any specific requirements or interests...",
            help="Any other preferences or special requirements"
        )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🤖 Generate Trip Plan", 
                type="primary",
                use_container_width=True
            )
    
    # Handle form submission
    if submitted:
        st.write("🔍 Processing your request...")
        
        # Validation
        if not destination or not destination.strip():
            st.error("❌ Please enter a destination")
            return
        
        if start_date >= end_date:
            st.error("❌ End date must be after start date")
            return
        
        if budget <= 0:
            st.error("❌ Please enter a valid budget")
            return
        
        st.success("✅ Form validation passed!")
        
        # Prepare preferences string
        preferences_str = ", ".join(preferences) if preferences else "General travel"
        if additional_preferences and additional_preferences.strip():
            preferences_str += f" | Additional: {additional_preferences.strip()}"
        
        st.write(f"📍 Destination: {destination}")
        st.write(f"📅 Dates: {start_date} to {end_date}")
        st.write(f"💰 Budget: ${budget:,}")
        st.write(f"🎯 Preferences: {preferences_str}")
        
        # Generate suggestions
        try:
            with st.spinner("�� AI is planning your perfect trip... This may take a moment."):
                suggestions = vertex_ai.generate_trip_suggestions(
                    destination=destination.strip(),
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    budget=float(budget),
                    preferences=preferences_str
                )
            
            if not suggestions:
                st.error("❌ Failed to generate trip suggestions. Please try again.")
                return
            
            st.success("✅ Trip suggestions generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating suggestions: {str(e)}")
            return
        
        # Save trip to database
        try:
            success, message = db.create_trip(
                st.session_state.user['id'],
                destination.strip(),
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                float(budget),
                preferences_str,
                json.dumps(suggestions)
            )
            
            if success:
                # Extract trip_id from message
                trip_id = int(message.split("ID: ")[1])
                st.session_state.current_trip = suggestions
                st.session_state.trip_id = trip_id
                st.success("🎉 Trip plan generated and saved successfully!")
                
                # Show a preview
                st.subheader("📋 Trip Preview")
                if 'itinerary' in suggestions and suggestions['itinerary']:
                    st.write("**Daily Itinerary:**")
                    # Handle itinerary as list of dictionaries
                    if isinstance(suggestions['itinerary'], list):
                        for day_info in suggestions['itinerary'][:3]:  # Show first 3 days
                            with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')}"):
                                if 'activities' in day_info:
                                    for activity in day_info['activities']:
                                        st.write(f"• {activity}")
                                if 'meals' in day_info:
                                    st.write("**Meals:**")
                                    for meal in day_info['meals']:
                                        st.write(f"🍽️ {meal}")
                    else:
                        # Fallback for dictionary format
                        for day, activities in list(suggestions['itinerary'].items())[:3]:
                            with st.expander(f"Day {day}"):
                                for activity in activities:
                                    st.write(f"• {activity}")
                
                if 'accommodations' in suggestions and suggestions['accommodations']:
                    st.write("**Recommended Accommodations:**")
                    for hotel in suggestions['accommodations'][:2]:  # Show first 2
                        st.write(f"🏨 **{hotel['name']}** - ${hotel['price']}/night")
                
                st.info("💡 Go to 'My Trips' to view the complete trip plan!")
                st.rerun()
            else:
                st.error(f"❌ Failed to save trip: {message}")
                
        except Exception as e:
            st.error(f"❌ Error saving trip: {str(e)}")
            st.write(f"Debug info: {str(e)}")

def show_trip_details(trip_data):
    """Display detailed trip information"""
    try:
        suggestions = json.loads(trip_data['ai_suggestions']) if isinstance(trip_data['ai_suggestions'], str) else trip_data['ai_suggestions']
    except Exception as e:
        st.error(f"Error loading trip details: {str(e)}")
        return
    
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
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("📅 Daily Itinerary")
            # Handle itinerary as list of dictionaries
            if isinstance(suggestions['itinerary'], list):
                for day_info in suggestions['itinerary']:
                    with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')} ({day_info.get('date', '')})"):
                        if 'activities' in day_info:
                            st.write("**Activities:**")
                            for activity in day_info['activities']:
                                st.write(f"• {activity}")
                        if 'meals' in day_info:
                            st.write("**Meals:**")
                            for meal in day_info['meals']:
                                st.write(f"🍽️ {meal}")
            else:
                # Fallback for dictionary format
                for day, activities in suggestions['itinerary'].items():
                    with st.expander(f"Day {day}"):
                        for activity in activities:
                            st.write(f"• {activity}")
        
        # Accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
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
        if 'activities' in suggestions and suggestions['activities']:
            st.subheader("🎯 Activities")
            for activity in suggestions['activities']:
                with st.container():
                    st.write(f"**{activity['name']}**")
                    st.write(f"📍 {activity['location']}")
                    st.write(f"💰 ${activity['cost']}")
                    st.write(f"⏰ {activity['duration']}")
                    st.write("---")
        
        # Restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
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
        if 'transportation' in suggestions and suggestions['transportation']:
            st.subheader("🚗 Transportation")
            for transport in suggestions['transportation']:
                with st.container():
                    st.write(f"**{transport['type']}**")
                    st.write(f"📍 {transport['route']}")
                    st.write(f"💰 ${transport['cost']}")
                    st.write("---")
        
        # Tips
        if 'tips' in suggestions and suggestions['tips']:
            st.subheader("💡 Travel Tips")
            for tip in suggestions['tips']:
                st.write(f"• {tip}")
        
        # Weather
        if 'weather' in suggestions and suggestions['weather']:
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

# Initialize the trip planner
if __name__ == "__main__":
    show_trip_planner()
