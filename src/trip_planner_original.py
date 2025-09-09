import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from database import db
from vertex_ai_utils import trip_planner
from auth import logout
import json

def show_trip_planner():
    """Main trip planner interface with enhanced UI"""
    st.title("🗺️ AI-Powered Trip Planner")
    
    # User info in sidebar
    with st.sidebar:
        st.success(f"Welcome, {st.session_state.user['username']}!")
        if st.button("Logout", use_container_width=True):
            logout()
        st.markdown("---")
        
        # Navigation
        page = st.selectbox(
            "Navigate",
            ["Plan New Trip", "My Trips", "Profile", "Analytics"],
            key="nav_select"
        )
    
    if page == "Plan New Trip":
        plan_new_trip()
    elif page == "My Trips":
        show_my_trips()
    elif page == "Profile":
        show_profile()
    elif page == "Analytics":
        show_analytics()

def plan_new_trip():
    """Plan a new trip interface with enhanced UI"""
    st.header("🎯 Plan Your Perfect Trip")
    st.markdown("Let AI help you create the perfect travel experience!")
    
    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "Destination", 
                placeholder="e.g., Paris, Tokyo, New York",
                help="Enter the city or country you want to visit"
            )
            start_date = st.date_input(
                "Start Date",
                value=date.today(),
                min_value=date.today(),
                help="When does your trip start?"
            )
            budget = st.number_input(
                "Budget (USD)",
                min_value=100,
                max_value=50000,
                value=2000,
                step=100,
                help="Your total budget for the trip"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today(),
                min_value=date.today(),
                help="When does your trip end?"
            )
            preferences = st.text_area(
                "Travel Preferences",
                placeholder="e.g., adventure, culture, food, relaxation, family-friendly",
                help="Describe what you're interested in during your trip"
            )
            
            # Travel type selection
            travel_type = st.selectbox(
                "Travel Type",
                ["Solo", "Couple", "Family", "Friends", "Business"],
                help="What type of trip is this?"
            )
        
        submit_button = st.form_submit_button("🤖 Generate AI Trip Plan", use_container_width=True)
        
        if submit_button:
            if not destination:
                st.error("Please enter a destination")
                return
            
            if start_date >= end_date:
                st.error("End date must be after start date")
                return
            
            # Generate AI suggestions
            with st.spinner("🤖 AI is planning your perfect trip..."):
                suggestions = trip_planner.generate_trip_suggestions(
                    destination, 
                    start_date.strftime("%Y-%m-%d"), 
                    end_date.strftime("%Y-%m-%d"),
                    budget,
                    preferences
                )
            
            # Save trip to database
            trip_id = db.create_trip(
                st.session_state.user['id'],
                destination,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                budget,
                preferences,
                suggestions
            )
            
            if trip_id:
                st.session_state.current_trip = suggestions
                st.session_state.trip_id = trip_id
                st.success("Trip plan generated successfully!")
                st.rerun()
            else:
                st.error("Failed to save trip. Please try again.")
    
    # Display current trip if available
    if 'current_trip' in st.session_state:
        display_trip_plan(st.session_state.current_trip)

def display_trip_plan(suggestions):
    """Display the AI-generated trip plan with enhanced UI"""
    st.header(f"🎯 Your Trip to {suggestions['destination']}")
    
    # Trip overview with metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", suggestions['duration'])
    with col2:
        st.metric("Total Budget", f"${suggestions['budget']:,.0f}")
    with col3:
        st.metric("Days", len(suggestions['itinerary']))
    with col4:
        if 'weather' in suggestions:
            st.metric("Weather", suggestions['weather']['temperature'])
    
    # Budget breakdown chart
    if 'budget_breakdown' in suggestions:
        st.subheader("💰 Budget Breakdown")
        budget_data = suggestions['budget_breakdown']
        
        fig = px.pie(
            values=list(budget_data.values()),
            names=list(budget_data.keys()),
            title="Budget Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📅 Itinerary", "🏨 Accommodations", "�� Activities", 
        "🍽️ Restaurants", "🚗 Transportation", "💡 Tips", "🌤️ Weather", "🎒 Packing"
    ])
    
    with tab1:
        st.subheader("Daily Itinerary")
        for day in suggestions['itinerary']:
            with st.expander(f"Day {day['day']} - {day['date']} ({day.get('day_name', '')})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write("**Activities:**")
                    for activity in day['activities']:
                        st.write(f"• {activity}")
                with col2:
                    if 'meals' in day:
                        st.write("**Meals:**")
                        for meal_type, meal_desc in day['meals'].items():
                            st.write(f"**{meal_type.title()}:** {meal_desc}")
    
    with tab2:
        st.subheader("Recommended Accommodations")
        for i, acc in enumerate(suggestions['accommodations']):
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{acc['name']}** ({acc['type']})")
                    st.write(f"📍 {acc.get('location', 'Location not specified')}")
                    st.write(f"💰 {acc['price_range']}")
                    st.write(f"⭐ {acc['rating']}/5")
                    if 'description' in acc:
                        st.write(f"📝 {acc['description']}")
                with col2:
                    st.write("**Amenities:**")
                    for amenity in acc['amenities']:
                        st.write(f"• {amenity}")
                if i < len(suggestions['accommodations']) - 1:
                    st.markdown("---")
    
    with tab3:
        st.subheader("Activities & Attractions")
        for activity in suggestions['activities']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{activity['name']}**")
                    st.write(f"📝 {activity['description']}")
                    st.write(f"🏷️ {activity['type']}")
                with col2:
                    st.write(f"⏱️ {activity['duration']}")
                    st.write(f"💰 {activity['cost']}")
                    if 'rating' in activity:
                        st.write(f"⭐ {activity['rating']}/5")
                    if 'best_time' in activity:
                        st.write(f"🕐 Best time: {activity['best_time']}")
                st.markdown("---")
    
    with tab4:
        st.subheader("Restaurant Recommendations")
        for restaurant in suggestions['restaurants']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"🍽️ {restaurant['cuisine']}")
                    st.write(f"💰 {restaurant['price_range']}")
                    st.write(f"⭐ {restaurant['rating']}/5")
                    if 'location' in restaurant:
                        st.write(f"📍 {restaurant['location']}")
                with col2:
                    st.write("**Specialties:**")
                    for specialty in restaurant['specialties']:
                        st.write(f"• {specialty}")
                    if 'reservation_required' in restaurant:
                        if restaurant['reservation_required']:
                            st.write("📞 Reservation required")
                        else:
                            st.write("🚶 Walk-ins welcome")
                st.markdown("---")
    
    with tab5:
        st.subheader("Transportation Options")
        for transport in suggestions['transportation']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{transport['type']}**")
                    st.write(f"🚗 {transport['option']}")
                    st.write(f"💰 {transport['cost']}")
                    st.write(f"⏱️ {transport['duration']}")
                    if 'description' in transport:
                        st.write(f"📝 {transport['description']}")
                with col2:
                    if 'booking_required' in transport:
                        if transport['booking_required']:
                            st.write("📞 Booking required")
                        else:
                            st.write("🚶 No booking needed")
                st.markdown("---")
    
    with tab6:
        st.subheader("Travel Tips")
        for i, tip in enumerate(suggestions['tips'], 1):
            st.write(f"{i}. 💡 {tip}")
    
    with tab7:
        st.subheader("Weather Information")
        if 'weather' in suggestions:
            weather = suggestions['weather']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Temperature", weather['temperature'])
            with col2:
                st.metric("Conditions", weather['conditions'])
            with col3:
                st.write("**Recommendation:**")
                st.write(weather['recommendation'])
        else:
            st.info("Weather information not available for this destination.")
    
    with tab8:
        st.subheader("Packing List")
        if 'packing_list' in suggestions:
            col1, col2 = st.columns(2)
            for i, item in enumerate(suggestions['packing_list']):
                col = col1 if i % 2 == 0 else col2
                with col:
                    st.write(f"• {item}")
        else:
            st.info("Packing list not available for this destination.")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("�� Save Trip Plan", use_container_width=True):
            st.success("Trip plan saved to your trips!")
    with col2:
        if st.button("🔄 Generate New Plan", use_container_width=True):
            if 'current_trip' in st.session_state:
                del st.session_state.current_trip
            st.rerun()
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.nav_select = "Analytics"
            st.rerun()
    with col4:
        if st.button("📤 Export Plan", use_container_width=True):
            st.info("Export functionality coming soon!")

def show_my_trips():
    """Show user's saved trips with enhanced UI"""
    st.header("📚 My Saved Trips")
    
    user_id = st.session_state.user['id']
    trips = db.get_user_trips(user_id)
    
    if not trips:
        st.info("You haven't saved any trips yet. Plan your first trip!")
        return
    
    # Trip statistics
    total_trips = len(trips)
    total_budget = sum(trip[4] for trip in trips if trip[4])
    avg_budget = total_budget / total_trips if total_trips > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trips", total_trips)
    with col2:
        st.metric("Total Budget", f"${total_budget:,.0f}")
    with col3:
        st.metric("Average Budget", f"${avg_budget:,.0f}")
    
    st.markdown("---")
    
    # Display trips
    for trip in trips:
        with st.expander(f"🗺️ Trip to {trip[1]} - {trip[8]}"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**Destination:** {trip[1]}")
                st.write(f"**Dates:** {trip[2]} to {trip[3]}")
            with col2:
                st.write(f"**Budget:** ${trip[4]:,.0f}" if trip[4] else "**Budget:** Not specified")
                st.write(f"**Status:** {trip[7]}")
            with col3:
                st.write(f"**Preferences:** {trip[5]}" if trip[5] else "**Preferences:** None")
                st.write(f"**Created:** {trip[8]}")
            with col4:
                if st.button(f"View Details", key=f"view_{trip[0]}"):
                    try:
                        if isinstance(trip[6], str):
                            suggestions = json.loads(trip[6])
                        else:
                            suggestions = trip[6]
                        st.session_state.current_trip = suggestions
                        st.rerun()
                    except:
                        st.error("Could not load trip details")

def show_profile():
    """Show user profile with enhanced information"""
    st.header("👤 Profile Information")
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**User ID:** {user['id']}")
        if 'created_at' in user:
            st.write(f"**Member since:** {user['created_at']}")
        if 'last_login' in user:
            st.write(f"**Last login:** {user['last_login']}")
    
    with col2:
        st.subheader("Trip Statistics")
        trips = db.get_user_trips(user['id'])
        total_trips = len(trips)
        total_budget = sum(trip[4] for trip in trips if trip[4])
        avg_budget = total_budget / total_trips if total_trips > 0 else 0
        
        st.metric("Total Trips", total_trips)
        st.metric("Total Budget", f"${total_budget:,.0f}" if total_budget else "$0")
        st.metric("Average Budget", f"${avg_budget:,.0f}")
        
        # Most visited destinations
        destinations = [trip[1] for trip in trips]
        if destinations:
            from collections import Counter
            dest_count = Counter(destinations)
            most_visited = dest_count.most_common(1)[0]
            st.metric("Most Visited", f"{most_visited[0]} ({most_visited[1]} trips)")
    
    if st.button("Delete Account", type="secondary"):
        st.warning("Account deletion not implemented in this demo")

def show_analytics():
    """Show trip analytics and insights"""
    st.header("📊 Trip Analytics")
    
    user_id = st.session_state.user['id']
    trips = db.get_user_trips(user_id)
    
    if not trips:
        st.info("No trips to analyze yet. Plan your first trip!")
        return
    
    # Convert trips to DataFrame for analysis
    trip_data = []
    for trip in trips:
        trip_data.append({
            'destination': trip[1],
            'start_date': trip[2],
            'end_date': trip[3],
            'budget': trip[4] or 0,
            'preferences': trip[5] or '',
            'status': trip[7],
            'created_at': trip[8]
        })
    
    df = pd.DataFrame(trip_data)
    
    # Budget analysis
    st.subheader("�� Budget Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            df, 
            x='destination', 
            y='budget',
            title='Budget by Destination',
            color='budget',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(
            df, 
            values='budget', 
            names='destination',
            title='Budget Distribution by Destination'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Trip frequency
    st.subheader("📅 Trip Frequency")
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_trips = df.groupby('month').size().reset_index(name='trips')
    monthly_trips['month'] = monthly_trips['month'].astype(str)
    
    fig = px.line(
        monthly_trips, 
        x='month', 
        y='trips',
        title='Trips Planned Over Time',
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Destination preferences
    st.subheader("🗺️ Destination Preferences")
    dest_counts = df['destination'].value_counts()
    
    fig = px.bar(
        x=dest_counts.index, 
        y=dest_counts.values,
        title='Most Popular Destinations',
        labels={'x': 'Destination', 'y': 'Number of Trips'}
    )
    st.plotly_chart(fig, use_container_width=True)
