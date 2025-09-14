# trip_planner.py
import streamlit as st
import json
from datetime import datetime, timedelta
from database import db
from vertex_ai_utils import VertexAITripPlanner
from maps_utils import fetch_place_details
from exports import generate_pdf, generate_ics
from emt_utils import EMTSearchGenerator

# Initialize components
planner = VertexAITripPlanner()
emt_generator = EMTSearchGenerator()

def logout():
    """Logout user and clear session state"""
    keys_to_clear = [
        'logged_in', 'user', 'current_trip', 'trip_id', 
        'active_profile_tab', 'trip_planner_page', 'form_data'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear Google OAuth related session state
    google_keys = [key for key in st.session_state.keys() if key.startswith('google_')]
    for key in google_keys:
        del st.session_state[key]
    
    st.success("✅ Successfully logged out!")
    st.rerun()

def check_auth():
    """Check if user is authenticated"""
    return 'logged_in' in st.session_state and st.session_state.logged_in

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
    user_trips = db.get_user_trips(user['id'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="📅 Total Trips",
            value=len(user_trips),
            delta=None
        )
    with col2:
        active_trips = len([trip for trip in user_trips if trip.get('status') == 'active'])
        st.metric(
            label="🗺️ Active Trips",
            value=active_trips,
            delta=None
        )
    with col3:
        completed_trips = len([trip for trip in user_trips if trip.get('status') == 'completed'])
        st.metric(
            label="✅ Completed Trips",
            value=completed_trips,
            delta=None
        )
    with col4:
        total_budget = sum(trip.get('budget', 0) for trip in user_trips)
        st.metric(
            label="💰 Total Budget",
            value=f"${total_budget:,.0f}",
            delta=None
        )
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗺️ Plan New Trip", type="primary", use_container_width=True):
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
    if user_trips:
        for trip in user_trips[:3]:  # Show last 3 trips
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{trip['destination']}**")
                    st.write(f"📅 {trip['start_date']} to {trip['end_date']}")
                    st.write(f"💰 ${trip['budget']:,.2f}")
                with col2:
                    st.write(f"Status: {trip.get('status', 'planned').title()}")
                with col3:
                    if st.button("View", key=f"view_{trip.get('id', 'unknown')}"):
                        st.session_state.selected_trip = trip
                        st.session_state.navigation_target = "📚 My Trips"
                        st.rerun()
            st.divider()
    else:
        st.info("No trips found. Start planning your first trip!")

def show_trip_planner_form():
    """Show the main trip planning form"""
    st.title("🗺️ AI Trip Planner")
    st.markdown("Plan your perfect trip with AI-powered suggestions and sustainable travel options")
    
    user = st.session_state.user
    
    # Trip planning form
    with st.form("trip_form"):
        st.subheader("✈️ Trip Details")
        
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input(
                "🎯 Destination(s)", 
                placeholder="e.g., Paris, France or Mumbai, Delhi, Goa"
            )
            start_date = st.date_input(
                "📅 Start Date",
                min_value=datetime.now().date()
            )
            budget = st.number_input(
                "💰 Budget (USD)", 
                min_value=0.0, 
                value=1000.0,
                step=100.0
            )
        
        with col2:
            travelers = st.number_input(
                "👥 Number of Travelers",
                min_value=1,
                value=1,
                max_value=10
            )
            end_date = st.date_input(
                "📅 End Date",
                min_value=start_date if 'start_date' in locals() else datetime.now().date()
            )
            optimize = st.selectbox(
                "🎯 Optimize for",
                ["Cost-Efficient", "Time-Efficient"],
                help="Choose whether to prioritize saving money or time"
            )
        
        interests = st.text_area(
            "🎨 Interests / Themes", 
            placeholder="e.g., adventure, culture, food, nature, history, nightlife"
        )
        
        # Origin city for flight/train search
        origin_city = st.text_input(
            "🏠 Your Departure City",
            placeholder="e.g., New York, Mumbai, London",
            help="This helps us find flights and trains from your location"
        )
        
        submitted = st.form_submit_button("🚀 Generate Itinerary", type="primary")
    
    if submitted and destination:
        with st.spinner("🔍 Searching EaseMyTrip for best deals and generating your perfect itinerary..."):
            # Generate AI itinerary with EaseMyTrip integration
            itinerary = planner.generate_trip_suggestions(
                destination=destination,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                budget=budget,
                preferences=interests,
                optimize_for=optimize,
                origin_city=origin_city,
                travelers=travelers
            )
        
        # Save to chat history
        query_params = f"{destination}|{start_date}|{end_date}|${budget}|{interests}|{optimize}|{travelers} travelers"
        db.save_chat(user["id"], query_params, json.dumps(itinerary))
        
        # Display results
        display_itinerary_results(itinerary, user)
        
        # Save as trip option
        if st.button("💾 Save This Trip"):
            success, message = db.create_trip(
                user_id=user["id"],
                destination=destination,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                budget=budget,
                preferences=interests,
                ai_suggestions=json.dumps(itinerary)
            )
            if success:
                st.success("✅ Trip saved successfully!")
            else:
                st.error(f"❌ Error saving trip: {message}")

def display_itinerary_results(itinerary, user):
    """Display the generated itinerary with EaseMyTrip bookings"""
    
    st.success("🌱 Your sustainable, AI-optimized itinerary is ready!")
    
    # Display EaseMyTrip booking options first
    if "easemytrip_bookings" in itinerary:
        st.subheader("🔗 Book on EaseMyTrip")
        st.markdown("*Click any link below to book directly on EaseMyTrip*")
        
        bookings = itinerary["easemytrip_bookings"]
        
        # Sustainable transport options (trains/buses) first
        if "trains" in bookings and bookings["trains"]:
            st.markdown("### 🌱 Sustainable Transport (Recommended)")
            for train in bookings["trains"]:
                with st.container():
                    st.markdown(f"""
                    <div class="sustainable-option">
                        <strong>🚆 {train.get('route', 'Train Journey')}</strong> - {train.get('train', 'Railway Service')}<br>
                        💰 Price: {train.get('price_range', 'Check website')}<br>
                        ⏱️ Duration: {train.get('duration', 'Varies')}<br>
                        🌱 <em>Eco-friendly option - Lower carbon footprint</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"[🚆 Book Train on EaseMyTrip →]({train.get('booking_url', '#')})")
                st.divider()
        
        if "buses" in bookings and bookings["buses"]:
            for bus in bookings["buses"]:
                with st.container():
                    st.markdown(f"""
                    <div class="sustainable-option">
                        <strong>🚌 {bus.get('route', 'Bus Journey')}</strong> - {bus.get('operator', 'Bus Service')}<br>
                        💰 Price: {bus.get('price_range', 'Check website')}<br>
                        ⏱️ Duration: {bus.get('duration', 'Varies')}<br>
                        🌱 <em>Eco-friendly option - Shared transport</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"[🚌 Book Bus on EaseMyTrip →]({bus.get('booking_url', '#')})")
                st.divider()
        
        # Flights section
        if "flights" in bookings and bookings["flights"]:
            st.markdown("### ✈️ Flight Options")
            for flight in bookings["flights"]:
                sustainability_icon = "🌱" if flight.get("sustainable") else "✈️"
                with st.container():
                    st.markdown(f"""
                    <div class="booking-card">
                        <strong>{sustainability_icon} {flight.get('route', 'Flight Route')}</strong> - {flight.get('airline', 'Airline')}<br>
                        💰 Price: {flight.get('price_range', 'Check website')}<br>
                        📅 Date: {flight.get('date', 'Check website')}<br>
                        ⏱️ Duration: {flight.get('duration', 'Direct/Connect')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"[✈️ Book Flight on EaseMyTrip →]({flight.get('booking_url', '#')})")
                st.divider()
        
        # Hotels section
        if "hotels" in bookings and bookings["hotels"]:
            st.markdown("### 🏨 Accommodation Options")
            for hotel in bookings["hotels"]:
                with st.container():
                    st.markdown(f"""
                    <div class="booking-card">
                        <strong>🏨 {hotel.get('name', 'Hotel')}</strong> - {hotel.get('location', 'City Center')}<br>
                        💰 Price: {hotel.get('price_range', 'Check website')}<br>
                        ⭐ Rating: {hotel.get('rating', 'N/A')}/5<br>
                        🏢 Type: {hotel.get('type', 'Hotel')}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"[🏨 Book Hotel on EaseMyTrip →]({hotel.get('booking_url', '#')})")
                st.divider()
    
    # Display detailed itinerary
    if "itinerary" in itinerary:
        st.subheader("📋 Daily Itinerary")
        for day in itinerary["itinerary"]:
            with st.expander(f"Day {day.get('day', 'X')} - {day.get('day_name', 'Date')} ({day.get('date', '')})"):
                st.markdown("**🎯 Activities:**")
                for activity in day.get("activities", []):
                    st.markdown(f"• {activity}")
                
                st.markdown("**🍽️ Meals:**")
                meals = day.get("meals", {})
                st.markdown(f"• **Breakfast:** {meals.get('breakfast', 'Local café')}")
                st.markdown(f"• **Lunch:** {meals.get('lunch', 'Local restaurant')}")
                st.markdown(f"• **Dinner:** {meals.get('dinner', 'Recommended restaurant')}")
    
    # Export options
    st.subheader("📤 Export Your Itinerary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download PDF", type="primary"):
            try:
                from exports import generate_pdf
                
                # Generate PDF as bytes
                pdf_bytes = generate_pdf(itinerary, form_data["destination"])
                
                # Create filename
                destination_clean = form_data["destination"].replace(" ", "_").replace("/", "_")
                filename = f"trip_plan_{destination_clean}.pdf"
                
                # Download button with correct data type
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,  # Pass bytes directly, NOT base64 encoded
                    file_name=filename,
                    mime="application/pdf"  # Correct MIME type
                )
                st.success("✅ PDF ready for download!")
                
            except Exception as e:
                st.error(f"❌ PDF generation failed: {str(e)}")
                print(f"PDF Error: {e}")  # For debugging
    
    with col2:
        if st.button("📅 Add to Calendar", type="secondary"):
            try:
                from exports import generate_ics
                ics_data = generate_ics(itinerary)
                
                destination_clean = form_data["destination"].replace(" ", "_").replace("/", "_")
                filename = f"trip_{destination_clean}.ics"
                
                st.download_button(
                    label="📥 Download .ics",
                    data=ics_data,
                    file_name=filename,
                    mime="text/calendar"
                )
                st.success("✅ Calendar file ready!")
                
            except Exception as e:
                st.error(f"❌ Calendar export failed: {str(e)}")
    
    with col3:
        if st.button("📧 Share via Email", type="secondary"):
            # Create shareable summary
            summary = create_trip_summary(itinerary, form_data)
            st.text_area(
                "Copy this summary to share:",
                value=summary,
                height=200,
                help="Copy and paste this summary into your email"
            )

def show_trip_history():
    """Show user's trip history and chat logs"""
    st.title("📚 My Trips & Chat History")
    
    user = st.session_state.user
    
    # Tabs for trips and chat history
    tab1, tab2 = st.tabs(["🗺️ Saved Trips", "💬 Chat History"])
    
    with tab1:
        trips = db.get_user_trips(user['id'])
        if trips:
            for trip in trips:
                with st.expander(f"🗺️ {trip['destination']} - {trip['start_date']} to {trip['end_date']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Budget:** ${trip['budget']:,.2f}")
                        st.write(f"**Status:** {trip.get('status', 'planned').title()}")
                        st.write(f"**Created:** {trip.get('created_at', 'Unknown')}")
                    with col2:
                        st.write(f"**Preferences:** {trip.get('preferences', 'None specified')}")
                    
                    if trip.get('ai_suggestions'):
                        try:
                            suggestions = json.loads(trip['ai_suggestions'])
                            st.json(suggestions)
                        except:
                            st.write(trip['ai_suggestions'])
        else:
            st.info("No saved trips yet. Create your first itinerary!")
    
    with tab2:
        chats = db.get_user_chats(user['id'])
        if chats:
            for chat in chats:
                timestamp = chat.get('timestamp', datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                with st.expander(f"💬 {timestamp} - {chat.get('message', '')[:50]}..."):
                    st.markdown(f"**Query:** {chat.get('message', 'No query')}")
                    st.markdown("**AI Response:**")
                    try:
                        response_data = json.loads(chat.get('response', '{}'))
                        st.json(response_data)
                    except:
                        st.write(chat.get('response', 'No response'))
        else:
            st.info("No chat history yet. Start planning a trip!")

def show_trip_planner():
    """Main trip planner interface with sidebar navigation"""
    
    # Check for navigation target from dashboard
    if 'navigation_target' in st.session_state:
        target = st.session_state.navigation_target
        del st.session_state.navigation_target
        st.session_state.trip_planner_page = target
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🗺️ AI Trip Planner")
        st.markdown("---")
        
        # User info
        user = st.session_state.user
        st.markdown(f"👋 **{user.get('name', user.get('username', 'User'))}**")
        st.markdown(f"📧 {user.get('email', '')}")
        
        st.markdown("---")
        
        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["🏠 Dashboard", "🗺️ Plan Trip", "📚 My Trips", "👤 Profile"],
            key="trip_planner_page"
        )
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🗺️ Plan Trip":
        show_trip_planner_form()
    elif page == "📚 My Trips":
        show_trip_history()
    elif page == "👤 Profile":
        st.title("👤 Profile")
        st.info("Profile management coming soon!")
        
        # Basic profile info
        user = st.session_state.user
        st.write(f"**Name:** {user.get('name', 'Not set')}")
        st.write(f"**Email:** {user.get('email', 'Not set')}")
        st.write(f"**Username:** {user.get('username', 'Not set')}")
        st.write(f"**Login Method:** {user.get('login_method', 'Unknown')}")
        st.write(f"**Member Since:** {user.get('created_at', 'Unknown')}")