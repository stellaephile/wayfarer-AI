import streamlit as st
import json
from datetime import datetime, timedelta
from database import db
from vertex_ai_utils import VertexAITripPlanner

# # Configure page FIRST - before any other Streamlit commands
# st.set_page_config(
#     page_title="AI Trip Planner",
#     page_icon="🗺️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Now import other modules
from auth import show_auth_pages, check_auth
# from trip_planner import show_trip_planner

def logout():
    """Logout user and clear session state"""
    # Clear all session state variables
    keys_to_clear = [
        'logged_in', 'user', 'current_trip', 'trip_id', 
        'active_profile_tab', 'trip_planner_page', 'form_data'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any Google OAuth related session state
    google_keys = [key for key in st.session_state.keys() if key.startswith('google_')]
    for key in google_keys:
        del st.session_state[key]
    
    st.success("✅ Successfully logged out!")
    st.rerun()

def check_auth():
    """Check if user is authenticated"""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        return False
    return True

def show_dashboard():
    """Show user dashboard with overview"""
    st.title("🏠 Dashboard")
    
    if 'user' not in st.session_state:
        st.error("❌ Please log in to view dashboard!")
        return
    
    user = st.session_state.user
    
    # Welcome message
    st.markdown(f"### 👋 Welcome back, {user['name'] or user['username']}!")
    st.markdown("Here's your trip planning overview")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📅 Total Trips",
            value=len(db.get_user_trips(user['id'])),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🗺️ Active Trips",
            value=len([trip for trip in db.get_user_trips(user['id']) if trip['status'] == 'active']),
            delta=None
        )
    
    with col3:
        st.metric(
            label="✅ Completed Trips",
            value=len([trip for trip in db.get_user_trips(user['id']) if trip['status'] == 'completed']),
            delta=None
        )
    
    with col4:
        st.metric(
            label="💰 Total Budget",
            value=f"${sum(trip['budget'] for trip in db.get_user_trips(user['id'])):,.0f}",
            delta=None
        )
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗺️ Plan New Trip", type="primary", use_container_width=True):
            # Set navigation target and rerun
            st.session_state.navigation_target = "🗺️ Plan Trip"
            st.rerun()
    
    with col2:
        if st.button("📚 View My Trips", type="secondary", use_container_width=True):
            st.session_state.navigation_target = "📚 My Trips"
            st.rerun()
    
    with col3:
        if st.button("👤 Edit Profile", type="secondary", use_container_width=True):
            st.session_state.navigation_target = "👤 Profile"
            st.rerun()
    
    # Recent trips
    st.subheader("📜 Recent Trips")
    trips = db.get_user_trips(user['id'])
    
    if trips:
        # Show last 3 trips
        for trip in trips[:3]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{trip['destination']}**")
                    st.write(f"📅 {trip['start_date']} to {trip['end_date']}")
                    st.write(f"💰 ${trip['budget']:,.2f}")
                
                with col2:
                    st.write(f"Status: {trip['status'].title()}")
                
                with col3:
                    if st.button("View", key=f"view_{trip['id']}"):
                        st.session_state.selected_trip = trip
                        st.session_state.navigation_target = "📚 My Trips"
                        st.rerun()
                
                st.divider()
    else:
        st.info("No trips found. Start planning your first trip!")
    
    # Tips and suggestions
    st.subheader("💡 Tips & Suggestions")
    
    tips = [
        "🗺️ Use the AI trip planner to get personalized recommendations",
        "📚 Save your favorite trips for future reference",
        "📊 Check your analytics to see your travel patterns",
        "👤 Keep your profile updated for better recommendations"
    ]
    
    for tip in tips:
        st.write(tip)

def show_trip_planner():
    """Main trip planner interface with optimized sidebar"""
    
    # Check for navigation target from dashboard
    if 'navigation_target' in st.session_state:
        target = st.session_state.navigation_target
        del st.session_state.navigation_target
        st.session_state.trip_planner_page = target
    
    # Optimized sidebar
    with st.sidebar:
        # Compact header with app name and icon
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem; margin-right: 0.5rem;">🗺️</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #1e293b;">Trip Planner</h1>
            </div>
            <div style="width: 100%; height: 2px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 1px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Compact user info
        if 'user' in st.session_state:
            user = st.session_state.user
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: center;">
                    <div style="width: 35px; height: 35px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 0.75rem; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);">
                        <span style="color: white; font-weight: 600; font-size: 0.9rem;">{(user['name'] or user['username'])[0].upper()}</span>
                    </div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: #1e293b; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user['name'] or user['username']}</div>
                        <div style="font-size: 0.8rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">@{user['username']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Please log in first!")
            return
        
        # Compact navigation menu
        st.markdown("### 🎯 Menu")
        page = st.radio(
            "",
            [
                "🏠 Dashboard", 
                "🗺️ Plan Trip", 
                "📚 My Trips", 
                "📊 Analytics", 
                "👤 Profile"
            ],
            key="trip_planner_page",
            label_visibility="collapsed"
        )
        
        # Compact divider
        st.markdown("---")
        
        # Compact logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True, key="logout_btn"):
            logout()
    
    # Main content area
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🗺️ Plan Trip":
        plan_new_trip()
    elif page == "📚 My Trips":
        show_my_trips()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "👤 Profile":
        show_profile()

def plan_new_trip():
    """Plan a new trip with AI assistance"""
    st.title("🗺️ Plan Your Perfect Trip")
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        st.error("❌ Please log in to plan a trip!")
        return
    
    # Initialize Vertex AI
    vertex_ai = VertexAITripPlanner()
    
    # Check if we have a trip to display
    if 'current_trip' in st.session_state and st.session_state.current_trip:
        # Display the generated trip
        suggestions = st.session_state.current_trip
        trip_id = st.session_state.get('trip_id', 'Unknown')
        
        st.success("🎉 Trip plan generated successfully!")
        st.subheader("📋 Your Trip Plan")
        
        # Show trip details
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Destination:** {suggestions.get('destination', 'N/A')}")
            st.write(f"**Duration:** {suggestions.get('duration', 'N/A')} days")
        with col2:
            st.write(f"**Budget:** ${suggestions.get('budget', 'N/A')}")
            st.write(f"**Trip ID:** {trip_id}")
        
        # Show itinerary
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("📅 Daily Itinerary")
            if isinstance(suggestions['itinerary'], list):
                for day_info in suggestions['itinerary']:
                    with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')}"):
                        if 'activities' in day_info:
                            st.write("**Activities:**")
                            for activity in day_info['activities']:
                                st.write(f"• {activity}")
                        if 'meals' in day_info:
                            st.write("**Meals:**")
                            for meal in day_info['meals']:
                                st.write(f"🍽️ {meal}")
            else:
                for day, activities in suggestions['itinerary'].items():
                    with st.expander(f"Day {day}"):
                        for activity in activities:
                            st.write(f"• {activity}")
        
        # Show accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
            st.subheader("🏨 Recommended Accommodations")
            for hotel in suggestions['accommodations']:
                price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                st.write(f"**{hotel['name']}** - {price_info}")
                if 'description' in hotel:
                    st.write(f"*{hotel['description']}*")
        
        # Show additional info
        if 'additional_info' in suggestions and suggestions['additional_info']:
            st.subheader("ℹ️ Additional Information")
            st.write(suggestions['additional_info'])
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Generate New Trip", type="secondary"):
                # Clear current trip and show form again
                if 'current_trip' in st.session_state:
                    del st.session_state.current_trip
                if 'trip_id' in st.session_state:
                    del st.session_state.trip_id
                st.rerun()
        
        with col2:
            if st.button("👁️ View in My Trips", type="primary"):
                st.session_state.page = "my_trips"
                st.rerun()
        
        with col3:
            if st.button("💾 Save & Continue", type="secondary"):
                st.success("✅ Trip saved! You can view it in 'My Trips' anytime.")
        
        return
    
    # Create form for new trip planning
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
        submitted = st.form_submit_button(
            "🤖 Generate Trip Plan", 
            type="primary",
            use_container_width=True
        )
        
        # Handle form submission INSIDE the form context
        if submitted:
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
            
            # Store form data in session state
            st.session_state.form_data = {
                'destination': destination.strip(),
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'budget': float(budget),
                'preferences': preferences_str,
                'travel_type': travel_type,
                'accommodation_type': accommodation_type
            }
            
            # Generate suggestions
            try:
                with st.spinner("🤖 AI is planning your perfect trip... This may take a moment."):
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
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save trip: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error saving trip: {str(e)}")
                st.write(f"Debug info: {str(e)}")

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
        st.subheader("📋 AI Recommendations")
        
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
                    st.write(f"📍 {hotel.get('location', 'Location not specified')}")
                    # Use price_range instead of price
                    price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                    st.write(f"💰 {price_info}")
                    if 'rating' in hotel:
                        st.write(f"⭐ {hotel['rating']}/5")
                    if 'type' in hotel:
                        st.write(f"🏷️ {hotel['type']}")
                    if 'amenities' in hotel:
                        st.write(f"✨ Amenities: {', '.join(hotel['amenities'])}")
                    st.write("---")
        
        # Activities
        if 'activities' in suggestions and suggestions['activities']:
            st.subheader("🎯 Activities")
            for activity in suggestions['activities']:
                with st.container():
                    st.write(f"**{activity['name']}**")
                    st.write(f"📍 {activity.get('location', 'Location not specified')}")
                    st.write(f"💰 {activity.get('cost', 'Cost not specified')}")
                    st.write(f"⏰ {activity.get('duration', 'Duration not specified')}")
                    if 'description' in activity:
                        st.write(f"📝 {activity['description']}")
                    st.write("---")
        
        # Restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
            st.subheader("🍽️ Restaurants")
            for restaurant in suggestions['restaurants']:
                with st.container():
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"📍 {restaurant.get('location', 'Location not specified')}")
                    st.write(f"💰 {restaurant.get('price_range', 'Price not available')}")
                    if 'cuisine' in restaurant:
                        st.write(f"🍴 {restaurant['cuisine']}")
                    st.write("---")
        
        # Transportation
        if 'transportation' in suggestions and suggestions['transportation']:
            st.subheader("🚗 Transportation")
            for transport in suggestions['transportation']:
                with st.container():
                    st.write(f"**{transport['type']}**")
                    st.write(f"📍 {transport.get('route', 'Route not specified')}")
                    st.write(f"💰 ${transport.get('cost', 'Cost not specified')}")
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
    """Show user profile and settings with edit functionality"""
    st.title("👤 Profile")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view profile")
        return
    
    user = st.session_state.user
    
    # Initialize active tab in session state
    if 'active_profile_tab' not in st.session_state:
        st.session_state.active_profile_tab = 0  # 0 = View Profile, 1 = Edit Profile
    
    # Create tabs for viewing and editing profile
    tab1, tab2 = st.tabs(["👀 View Profile", "✏️ Edit Profile"])
    
    # Use session state to control which tab content is shown
    if st.session_state.active_profile_tab == 0:
        # View Profile Tab
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
        
        # Contact Information
        st.subheader("📞 Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Personal Number:** {user.get('personal_number', 'Not provided')}")
            st.write(f"**Alternate Number:** {user.get('alternate_number', 'Not provided')}")
        with col2:
            st.write(f"**Address:** {user.get('address', 'Not provided')}")
            st.write(f"**Pincode:** {user.get('pincode', 'Not provided')}")
            st.write(f"**State:** {user.get('state', 'Not provided')}")
        
        # Button to switch to edit tab
        if st.button("✏️ Edit Profile", type="primary"):
            st.session_state.active_profile_tab = 1
            st.rerun()
    
    else:
        # Edit Profile Tab
        st.subheader("Edit Profile Information")
        st.info("💡 You can update your personal information below. Fields marked with * are required.")
        
        with st.form("edit_profile_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basic Information**")
                name = st.text_input(
                    "Full Name *",
                    value=user.get('name', ''),
                    help="Enter your full name"
                )
                
                personal_number = st.text_input(
                    "Personal Number",
                    value=user.get('personal_number', ''),
                    help="Your primary contact number"
                )
                
                alternate_number = st.text_input(
                    "Alternate Number",
                    value=user.get('alternate_number', ''),
                    help="Secondary contact number (optional)"
                )
            
            with col2:
                st.write("**Address Information**")
                address = st.text_area(
                    "Address",
                    value=user.get('address', ''),
                    help="Your complete address",
                    height=100
                )
                
                pincode = st.text_input(
                    "Pincode",
                    value=user.get('pincode', ''),
                    help="Postal/ZIP code"
                )
                
                state = st.text_input(
                    "State",
                    value=user.get('state', ''),
                    help="State or Province"
                )
            
            # Submit button
            submitted = st.form_submit_button(
                "💾 Update Profile",
                type="primary",
                use_container_width=True
            )
            
            # Handle form submission
            if submitted:
                # Validation
                if not name or not name.strip():
                    st.error("❌ Please enter your full name")
                else:
                    # Prepare update data
                    update_data = {
                        'name': name.strip(),
                        'personal_number': personal_number.strip() if personal_number else None,
                        'address': address.strip() if address else None,
                        'pincode': pincode.strip() if pincode else None,
                        'state': state.strip() if state else None,
                        'alternate_number': alternate_number.strip() if alternate_number else None
                    }
                    
                    # Update profile in database
                    try:
                        success, message = db.update_user_profile(user['id'], **update_data)
                        
                        if success:
                            # Update session state with new data
                            st.session_state.user.update(update_data)
                            
                            # Refresh user data from database
                            updated_user = db.get_user_by_id(user['id'])
                            if updated_user:
                                st.session_state.user = updated_user
                            
                            # Switch to view profile tab
                            st.session_state.active_profile_tab = 0
                            st.success("✅ Profile updated successfully! Redirecting to view profile...")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update profile: {message}")
                    
                    except Exception as e:
                        st.error(f"❌ Error updating profile: {str(e)}")
        
        # Button to switch back to view tab
        if st.button("👀 View Profile", type="secondary"):
            st.session_state.active_profile_tab = 0
            st.rerun()
    
    # Account Actions (removed logout button)
    st.subheader("👥 Account Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Profile", type="secondary"):
            # Refresh user data from database
            updated_user = db.get_user_by_id(user['id'])
            if updated_user:
                st.session_state.user = updated_user
                st.success("✅ Profile refreshed!")
                st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", type="secondary"):
            st.session_state.trip_planner_page = "📊 Analytics"
            st.rerun()
    
    with col3:
        if st.button("🗺️ Plan New Trip", type="secondary"):
            st.session_state.trip_planner_page = "🗺️ Plan New Trip"
            st.rerun()
    
    # Security Information
    with st.expander("🔒 Security Information"):
        st.write("**Account Security:**")
        st.write(f"• Login Method: {user.get('login_method', 'email').title()}")
        st.write(f"• Email Verified: {'Yes' if user.get('verified_email') else 'No'}")
        st.write(f"• Account Status: {'Active' if user.get('is_active', True) else 'Inactive'}")
        st.write(f"• Last Login: {user.get('last_login', 'Unknown')}")
        
        if user.get('login_method') == 'google':
            st.info("🔐 This account is secured with Google OAuth. Your password is managed by Google.")
        else:
            st.info("🔐 This account uses email/password authentication. Keep your password secure.")

# Initialize the trip planner
if __name__ == "__main__":
    show_trip_planner()
