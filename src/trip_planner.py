import streamlit as st
import json,logging,os
from datetime import datetime, timedelta
from cloudsql_database_config import get_database
db = get_database()
from vertex_ai_utils import VertexAITripPlanner
from css_styles import inject_css, inject_compact_css, inject_app_header
from credit_widget import credit_widget
from widgets import with_dynamic_spinner, get_fun_spinner_messages,format_date_pretty,generate_and_display_pdf_options, generate_and_display_ics_options
from currency import currency_mapping,get_currency_options

log_file = os.getenv("TRIP_PLANNER_LOG")

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Or DEBUG
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),           # Log to file
        logging.StreamHandler()                  # Also print to terminal
    ]
)

# Optional: Get named logger for your module
logger = logging.getLogger(__name__)

@with_dynamic_spinner(get_fun_spinner_messages())
def get_suggestions(vertex_ai,destination,start_date,end_date,budget,preferences_str,selected_currency,currency_symbol):
    return vertex_ai.generate_trip_suggestions(
        destination=destination.strip(),
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        budget=float(budget),
        preferences=preferences_str,
        currency=selected_currency,
        currency_symbol=currency_symbol
    )

def validate_trip_dates(start_date, end_date):
    """Validate trip dates to ensure they are not in the past and end date is after start date"""
    today = datetime.now().date()
    
    if start_date < today:
        st.error("❌ Start date cannot be in the past!")
        return False
    
    if end_date < today:
        st.error("❌ End date cannot be in the past!")
        return False
        
    if start_date >= end_date:
        st.error("❌ End date must be after start date!")
        return False
    
    return True

def calculate_credits_used(suggestions):
    """Calculate credits used based on AI suggestions complexity"""
    try:
        base_credits = 5  # Base credits for trip generation
        
        # Additional credits based on content complexity
        additional_credits = 0
        
        # Check itinerary complexity
        if 'itinerary' in suggestions and suggestions['itinerary']:
            if isinstance(suggestions['itinerary'], list):
                additional_credits += len(suggestions['itinerary']) * 0.5
            else:
                additional_credits += 2
        
        # Check accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
            additional_credits += len(suggestions['accommodations']) * 0.3
        
        # Check activities
        if 'activities' in suggestions and suggestions['activities']:
            additional_credits += len(suggestions['activities']) * 0.4
        
        # Check restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
            additional_credits += len(suggestions['restaurants']) * 0.3
        
        # Check transportation
        if 'transportation' in suggestions and suggestions['transportation']:
            additional_credits += len(suggestions['transportation']) * 0.2
        
        total_credits = base_credits + additional_credits
        
        # Cap at maximum 20 credits per trip
        return min(int(total_credits), 20)
        
    except Exception as e:
        # Default to 5 credits if calculation fails
        return 5


# # Configure page FIRST - before any other Streamlit commands
# st.set_page_config(
#     page_title="AI Trip Planner",
#     page_icon="🗺️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Now import other modules
from auth import  check_auth
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



def show_dashboard():
    """Show modern user dashboard overview (sidebar handled by parent)"""
    # Inject compact CSS only
    inject_compact_css()
    
    if 'user' not in st.session_state:
        st.error("❌ Please log in to view dashboard!")
        return
    
    user = st.session_state.user
    user_trips = db.get_user_trips(user['id'])
    
    # Note: Sidebar is handled by the parent show_trip_planner() function
    
    # Main content area
    # Welcome banner
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #3B82F6, #06B6D4, #F59E0B);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    ">
        <h1 style="margin: 0 0 0.5rem 0; font-size: 2.5rem; font-weight: bold;">
            Welcome back, {user['name'] or user['username']}! ✈️
        </h1>
        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">
            Ready to plan your next adventure?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            position: relative;
        ">
            <div style="position: absolute; top: 1rem; right: 1rem; font-size: 1.5rem;">✈️</div>
            <h3 style="margin: 0 0 0.5rem 0; color: #1f2937; font-size: 2rem; font-weight: bold;">
                {len(user_trips)}
            </h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Total Trips</p>
            <p style="margin: 0.5rem 0 0 0; color: #10b981; font-size: 0.8rem;">+2 from last month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active_trips = len([trip for trip in user_trips if trip['status'] == 'active'])
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            position: relative;
        ">
            <div style="position: absolute; top: 1rem; right: 1rem; font-size: 1.5rem;">📍</div>
            <h3 style="margin: 0 0 0.5rem 0; color: #1f2937; font-size: 2rem; font-weight: bold;">
                {active_trips}
            </h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Active Trips</p>
            <p style="margin: 0.5rem 0 0 0; color: #f59e0b; font-size: 0.8rem;">Currently planning</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        completed_trips = len([trip for trip in user_trips if trip['status'] == 'completed'])
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            position: relative;
        ">
            <div style="position: absolute; top: 1rem; right: 1rem; font-size: 1.5rem;">✅</div>
            <h3 style="margin: 0 0 0.5rem 0; color: #1f2937; font-size: 2rem; font-weight: bold;">
                {completed_trips}
            </h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Completed Trips</p>
            <p style="margin: 0.5rem 0 0 0; color: #10b981; font-size: 0.8rem;">Amazing memories!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_budget = sum(trip['budget'] for trip in user_trips)
        currency_symbol = user_trips[0].get('currency_symbol', '$') if user_trips else '$'
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            position: relative;
        ">
            <div style="position: absolute; top: 1rem; right: 1rem; font-size: 1.5rem;">💰</div>
            <h3 style="margin: 0 0 0.5rem 0; color: #1f2937; font-size: 2rem; font-weight: bold;">
                {currency_symbol}{total_budget:,.0f}
            </h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">Total Budget</p>
            <p style="margin: 0.5rem 0 0 0; color: #3b82f6; font-size: 0.8rem;">This year</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Plan New Trip", use_container_width=True, type="primary"):
            st.session_state.navigation_target = "🗺️ Plan Trip"
            st.rerun()
    
    with col2:
        if st.button("👁️ View My Trips", use_container_width=True, type="secondary"):
            st.session_state.navigation_target = "📚 My Trips"
            st.rerun()
    
    with col3:
        if st.button("👤 Edit Profile", use_container_width=True, type="secondary"):
            st.session_state.navigation_target = "👤 Profile"
            st.rerun()
    
    # Recent Trips
    st.markdown("### Recent Trips")
    recent_trips = user_trips[:3]  # Show last 3 trips
    
    if recent_trips:
        cols = st.columns(3)
        for i, trip in enumerate(recent_trips):
            with cols[i]:
                # Determine status colors
                if trip['status'] == 'planned':
                    card_bg = "linear-gradient(135deg, #3B82F6, #06B6D4)"
                    status_text = "Upcoming"
                elif trip['status'] == 'active':
                    card_bg = "linear-gradient(135deg, #F59E0B, #84CC16)"
                    status_text = "Active"
                elif trip['status'] == 'completed':
                    card_bg = "linear-gradient(135deg, #6B7280, #8B5CF6)"
                    status_text = "Completed"
                else:
                    card_bg = "linear-gradient(135deg, #3B82F6, #06B6D4)"
                    status_text = "Planned"
                
                st.markdown(f"""
                <div style="
                    background: {card_bg};
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin-bottom: 1rem;
                    position: relative;
                ">
                    <div style="position: absolute; top: 1rem; right: 1rem; 
                                background: rgba(255,255,255,0.2); padding: 0.25rem 0.75rem; 
                                border-radius: 20px; font-size: 0.8rem;">
                        {status_text}
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="font-size: 1.2rem; margin-right: 0.5rem;">📍</span>
                        <h4 style="margin: 0; font-size: 1.1rem;">{trip['destination']}</h4>
                    </div>
                    <p style="margin: 0; opacity: 0.9; font-size: 0.9rem;">
                        {trip['start_date']} - {trip['end_date']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No trips found. Start planning your first trip!")
    
    # Tips and suggestions
    st.subheader("💡 Tips & Suggestions")
    
    tips = [
        "🗺️ Use the Wayfarer AI trip planner to get personalized recommendations",
        "📚 Save your favorite trips for future reference",
        "📊 Check your analytics to see your travel patterns",
        "👤 Keep your profile updated for better recommendations"
    ]
    
    for tip in tips:
        st.write(tip)

def show_trip_planner():
    """Main trip planner interface with optimized sidebar"""
    
    # Inject compact CSS only (header will be injected by individual pages)
    inject_compact_css()
    
    # Check for navigation target from dashboard
    if 'navigation_target' in st.session_state:
        target = st.session_state.navigation_target
        del st.session_state.navigation_target
        st.session_state.trip_planner_page = target
    
    # Check if we're in modification mode
    if 'modification_mode' in st.session_state and st.session_state.modification_mode:
        show_trip_modification_interface()
        return
    
    # Check if we're in booking mode
    if 'show_booking_interface' in st.session_state and st.session_state.show_booking_interface:
        from booking_interface import booking_interface
        booking_interface.show_booking_interface()
        return
    
    # Optimized sidebar
    with st.sidebar:
        # Compact header with app name and icon
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem; margin-right: 0.5rem;">ᨒ</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #1e293b;">Wayfarer AI</h1>
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
            credit_widget.show_credit_sidebar(st.session_state.user['id'])
       
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
                "💳 Credits",
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
    elif page == "💳 Credits":
        show_credits_page()
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
            currency_symbol = suggestions.get('currency_symbol', '$')
            st.write(f"**Budget:** {currency_symbol}{suggestions.get('budget', 'N/A')}")
            st.write(f"**Trip ID:** {trip_id}")
        
        # Show itinerary
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("🧳 Daily Itinerary")
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
            currency_symbol = suggestions.get('currency_symbol', '$')
            for hotel in suggestions['accommodations']:
                price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                if isinstance(price_info, str) and price_info != 'Price not available':
                    # If price contains dollar sign, replace with correct currency
                    if '$' in price_info:
                        price_info = price_info.replace('$', currency_symbol)
                st.write(f"**{hotel['name']}** - {price_info}")
                if 'description' in hotel:
                    st.write(f"*{hotel['description']}*")
        
        # Show additional info
        if 'additional_info' in suggestions and suggestions['additional_info']:
            st.subheader("ℹ️ Additional Information")
            st.write(suggestions['additional_info'])
        
        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("🔄 Generate New Trip", type="secondary"):
                # Clear current trip and show form again
                if 'current_trip' in st.session_state:
                    del st.session_state.current_trip
                if 'trip_id' in st.session_state:
                    del st.session_state.trip_id
                st.rerun()
        
        with col2:
            if st.button("💬 Modify Trip", type="primary"):
                st.session_state.modification_mode = True
                st.session_state.modification_trip_id = trip_id
                st.rerun()
        
        with col3:
            if st.button("👁️ View in My Trips", type="secondary"):
                st.session_state.page = "my_trips"
                st.rerun()
        
        with col4:
            if st.button("💾 Save & Continue", type="secondary"):
                st.success("✅ Trip saved! You can view it in 'My Trips' anytime.")
        
        with col5:
            # Import booking interface
            from booking_interface import booking_interface
            
            # Show booking button
            if booking_interface.show_booking_button(suggestions, st.session_state.user):
                st.rerun()
        
        return
    
    # Create form for new trip planning
    with st.form("trip_planning_form", clear_on_submit=False):
        st.subheader("Trip Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "Destination *", 
                placeholder="e.g., Goa, Amsterdam",
                help="Enter your travel destination"
            )
            if destination:
                destination = destination.strip().title()

            
            current_city = st.text_input(
                "Current City *", 
                placeholder="e.g., New York, USA",
                help="Enter your current city or departure location"
            )
            
            today = datetime.now().date()
            start_date = st.date_input(
                "Start Date *", 
                value=today,
                min_value=today,
                help=f"When does your trip start? (Earliest: {today.strftime('%B %d, %Y')})"
            )
            default_end_date=today + timedelta(days=7)
            end_date = st.date_input(
                "End Date *", 
                value=default_end_date,
                min_value=today,
                help=f"When does your trip end? (Earliest: {today.strftime('%B %d, %Y')})"
            )
            # Currency and Budget selection - Original layout with flags
            col_budget, col_currency = st.columns([2, 1])
            
            with col_currency:
                currency_options = get_currency_options()
                popular_currencies_display = currency_mapping                
                # Create currency options for selectbox
                currency_choices = [display for code, display in popular_currencies_display]
                currency_codes = [code for code, display in popular_currencies_display]
                
                selected_currency_display = st.selectbox(
                    "Currency",
                    currency_choices,
                    index=0,  # Default to INR
                    help="Select your preferred currency",
                    key="currency_selectbox"
                )
                
                # Extract currency code from selection
                selected_index = currency_choices.index(selected_currency_display)
                selected_currency = currency_codes[selected_index]
                currency_symbol = currency_options[selected_currency]["symbol"]
                
                # Show selected currency with flag
                #st.caption(f"Selected: {selected_currency_display}")
            
            with col_budget:
                budget = st.number_input(
                    f"Budget ({selected_currency}) *", 
                    min_value=0, 
                    step=100, 
                    help=f"Your total trip budget in {selected_currency}"
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
        
        # Itinerary preference selection
        st.markdown("#### Itinerary Preference")

        itinerary_preference = st.radio(
            "Choose your preferred itinerary style:",
            [
                "🌱 Sustainable",
                "⚡ Time-Efficient",
                "💰 Cost-Efficient"
                
            ],
            help=(
                "🌱 Sustainable: Eco-friendly transport & stays • "
                "⚡ Time-Efficient: Fastest travel, premium stays, skip-the-line options • "
                "💰 Cost-Efficient: Budget airlines, hostels, street food"
                
            )
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
            
            if not current_city or not current_city.strip():
                st.error("❌ Please enter your current city")
                return
            
            # Validate dates
            if not validate_trip_dates(start_date, end_date):
                return
            
            # Calculate trip duration
            total_days = (end_date - start_date).days + 1
            nights = total_days - 1
            st.info(f"⏱ Trip Duration: {total_days} day{'s' if total_days > 1 else ''}, "
                    f"{nights} night{'s' if nights != 1 else ''}")

            if budget <= 0:
                st.error("❌ Please enter a valid budget")
                return
            
            logger.info("✅ Form validation passed!")
            
            # Prepare preferences string
            preferences_str = ", ".join(preferences) if preferences else "General travel"
            if additional_preferences and additional_preferences.strip():
                preferences_str += f" | Additional: {additional_preferences.strip()}"
            
            # Store form data in session state
            st.session_state.form_data = {
                'destination': destination.strip(),
                'current_city': current_city.strip(),
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'budget': float(budget),
                'currency': selected_currency,
                'currency_symbol': currency_symbol,
                'preferences': preferences_str,
                'travel_type': travel_type,
                'accommodation_type': accommodation_type,
                'itinerary_preference': itinerary_preference
            }
            
            # Generate suggestions
            try:
                suggestions = get_suggestions(vertex_ai,destination,start_date,
                                              end_date,budget,preferences_str,selected_currency,currency_symbol)
                
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
                    json.dumps(suggestions),
                    selected_currency,
                    currency_symbol,
                    current_city.strip(),
                    itinerary_preference
                )
                
                if success:
                    # Extract trip_id from message
                    trip_id = message
                    
                    # Calculate and track credits used
                    credits_used = calculate_credits_used(suggestions)
                    db.update_trip_credits(trip_id, credits_used)
                    db.add_credit_transaction(
                        st.session_state.user['id'],
                        trip_id,
                        'usage',
                        credits_used,
                        f"AI trip generation for {destination}"
                    )
                    
                    st.session_state.current_trip = suggestions
                    st.session_state.trip_id = trip_id
                    st.success(f"🎉 Trip plan generated and saved successfully! (Used {credits_used} credits)")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save trip: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error saving trip: {str(e)}")
                st.write(f"Debug info: {str(e)}")

def show_my_trips():
    """Display user's saved trips with modern card-based layout"""
    # Inject compact CSS only
    inject_compact_css()
    
    # Header section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📚 My Trips")
    with col2:
        if st.button("➕ Plan New Trip", type="primary", use_container_width=True):
            st.session_state.navigation_target = "🗺️ Plan Trip"
            st.rerun()
    
    if 'user' not in st.session_state:
        st.error("Please log in to view your trips")
        return
    
    user_id = st.session_state.user['id']
    trips = db.get_user_trips(user_id)
    
    if not trips:
        st.info("No trips found. Start planning your first trip!")
        return
    
    # Search and filter section
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("", placeholder="Search destinations...", key="trip_search")
    with col2:
        filter_option = st.selectbox("", ["All Trips", "Upcoming", "Active", "Completed", "Booked"], key="trip_filter")
    
    # Filter trips based on search and filter
    filtered_trips = trips
    if search_query:
        filtered_trips = [trip for trip in filtered_trips if search_query.lower() in trip['destination'].lower()]
    
    if filter_option != "All Trips":
        if filter_option == "Booked":
            # Filter for trips that are booked (booking_status = 'confirmed')
            filtered_trips = [trip for trip in filtered_trips if trip.get('booking_status') == 'confirmed']
        else:
            # Filter by trip status
            status_map = {"Upcoming": "planned", "Active": "active", "Completed": "completed"}
            filtered_trips = [trip for trip in filtered_trips if trip['status'] == status_map[filter_option]]
    
    # Display trips in card layout
    if filtered_trips:
        # Create columns for card grid (3 cards per row)
        cols = st.columns(3)
        
        for i, trip in enumerate(filtered_trips):
            col_index = i % 3
            with cols[col_index]:
                # Determine status and colors
                status = trip['status'].title()
                booking_status = trip.get('booking_status', 'not_booked')
                
                # Create card using Streamlit containers with proper styling
                with st.container():
                    # Card header with gradient background
                    if status == "Planned":
                        header_bg = "linear-gradient(90deg, #3B82F6, #06B6D4)"
                        status_bg = "#1E40AF"
                    elif status == "Active":
                        header_bg = "linear-gradient(90deg, #F59E0B, #84CC16)"
                        status_bg = "#D97706"
                    elif status == "Completed":
                        header_bg = "linear-gradient(90deg, #6B7280, #8B5CF6)"
                        status_bg = "#4B5563"
                    else:
                        header_bg = "linear-gradient(90deg, #3B82F6, #06B6D4)"
                        status_bg = "#1E40AF"
                    
                    # Card container
                    st.markdown(f"""
                    <div style="
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        margin-bottom: 1rem;
                        border: 1px solid #E5E7EB;
                        overflow: hidden;
                    ">
                    """, unsafe_allow_html=True)
                    
                    # Header section
                    st.markdown(f"""
                    <div style="
                        background: {header_bg};
                        color: white;
                        padding: 1rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <div style="display: flex; align-items: center;">
                            <span style="font-size: 1.2rem; margin-right: 0.5rem;">📍</span>
                            <span style="font-weight: 600; font-size: 1.1rem;">{trip['destination']}</span>
                        </div>
                        <div style="
                            background: {status_bg};
                            color: white;
                            padding: 0.25rem 0.75rem;
                            border-radius: 20px;
                            font-size: 0.8rem;
                            font-weight: 500;
                        ">
                            {status}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Content section
                    st.markdown(f"""
                    <div style="padding: 1rem;">
                        <h3 style="margin: 0 0 0.75rem 0; color: #1F2937; font-size: 1.25rem; font-weight: 700;">
                            {trip['destination']}
                        </h3>
                        <div style="margin-bottom: 0.5rem; color: #6B7280; font-size: 0.9rem;">
                            📅 {format_date_pretty(trip['start_date'])} - {format_date_pretty(trip['end_date'])}
                        </div>
                        <div style="margin-bottom: 1rem; color: #6B7280; font-size: 0.9rem;">
                            💰 {trip.get('currency_symbol', '$')}{trip['budget']:,.0f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Close card container
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Action buttons outside the card but within the column
                col_view, col_book, col_complete, col_delete = st.columns(4)
                
                with col_view:
                    if st.button("👁️ View", key=f"view_{trip['id']}", use_container_width=True, type="primary"):
                        st.session_state.selected_trip = trip
                        st.rerun()
                
                with col_book:
                    # Import booking interface
                    from booking_interface import booking_interface
                    
                    # Check booking status
                    booking_status = trip.get('booking_status', 'not_booked')
                    ai_suggestions = trip.get('ai_suggestions', {})
                    
                    # Parse AI suggestions if it's a string
                    try:
                        if isinstance(ai_suggestions, str):
                            ai_suggestions = json.loads(ai_suggestions)
                    except:
                        ai_suggestions = {}
                    
                    # Determine button state and styling
                    if booking_status == 'confirmed':
                        # Trip is already booked - show disabled button
                        st.button("✅ Booked", key=f"book_{trip['id']}", use_container_width=True, disabled=True, 
                                help="This trip has already been booked", type="secondary")
                        
                    elif booking_status == 'pending':
                        # Booking is pending - show disabled button
                        st.button("⏳ Pending", key=f"book_{trip['id']}", use_container_width=True, disabled=True,
                                help="Booking is pending confirmation", type="secondary")
                        
                    elif ai_suggestions and trip['status'] != 'booked':
                        # Trip can be booked - show active book button
                        if st.button("🧳 Book", key=f"book_{trip['id']}", use_container_width=True, type="primary"):
                            # Prepare trip data for booking
                            trip_data = {
                                'trip_id': trip['id'],
                                'destination': trip['destination'],
                                'start_date': trip['start_date'],
                                'end_date': trip['end_date'],
                                'budget': trip['budget'],
                                'currency': trip.get('currency', 'INR'),
                                'currency_symbol': trip.get('currency_symbol', '₹'),
                                'preferences': trip['preferences'],
                                'ai_suggestions': ai_suggestions
                            }
                            
                            # Store booking data in session state
                            st.session_state.booking_trip_data = trip_data
                            st.session_state.booking_user_data = st.session_state.user
                            st.session_state.show_booking_interface = True
                            st.rerun()
                    else:
                        # No AI suggestions or other conditions - show disabled button
                        st.button("🧳 Book", key=f"book_{trip['id']}", use_container_width=True, disabled=True,
                                help="No booking options available for this trip", type="secondary")
                
                with col_complete:
                    # Complete trip functionality
                    if trip['status'] == 'completed':
                        # Trip is already completed - show disabled button
                        st.button("✅ Completed", key=f"complete_{trip['id']}", use_container_width=True, disabled=True,
                                help="This trip has already been completed", type="secondary")
                    elif trip['status'] in ['planned', 'active']:
                        # Trip can be completed - show active button
                        if st.button("🏁 Complete", key=f"complete_{trip['id']}", use_container_width=True, type="secondary"):
                            # Update trip status directly
                            success, message = db.update_trip(trip['id'], user_id, status='completed')
                            if success:
                                st.success(f"🎉 Trip to {trip['destination']} marked as completed!")
                                st.rerun()
                            else:
                                st.error(f"Error completing trip: {message}")
                    else:
                        # Other status - show disabled button
                        st.button("🏁 Complete", key=f"complete_{trip['id']}", use_container_width=True, disabled=True,
                                help="Cannot complete this trip", type="secondary")
                
                with col_delete:
                    if st.button("🗑️ Delete", key=f"delete_{trip['id']}", use_container_width=True, type="secondary"):
                        success, message = db.delete_trip(trip['id'], user_id)
                        if success:
                            st.success("Trip deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error deleting trip: {message}")
    else:
        st.info("No trips match your search criteria.")
    
    # Show selected trip details in a separate section
    if 'selected_trip' in st.session_state:
        st.markdown("---")
        st.markdown(
        """<h1 style='font-size:40px; color:#333; margin-bottom:0.5rem;'>
            Trip Details</h1>
        """,
        unsafe_allow_html=True
        )
        trip = st.session_state.selected_trip
        exp1,exp2,exp3 = st.columns([1,2,1])
        with exp1:
            generate_and_display_pdf_options(trip, trip['ai_suggestions'], weather_data=None) ##Generate pdf itinerary
        with exp2:
            generate_and_display_ics_options(trip, trip['ai_suggestions'], weather_data=None)
        #print(trip)
        show_trip_details(trip)

        
        
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
        try:
            start_dt = trip_data['start_date']
            end_dt = trip_data['end_date']
            num_days = (end_dt - start_dt).days + 1
            num_nights = num_days - 1
            duration_str = f"{num_days} Days, {num_nights} Nights"
        except Exception as e:
            logger.error(f" Duration Not Found: {str(e)}")
            duration_str="Unknown"
        st.metric("Duration", f"{duration_str}")
    with col2:
        currency_symbol = trip_data.get('currency_symbol', '$')
        st.metric("Budget", f"{currency_symbol}{trip_data['budget']:,.2f}")
    with col3:
        status = trip_data['status'].title()
        booking_status = trip_data.get('booking_status', 'not_booked')
        
        if booking_status == 'confirmed':
            st.metric("Status", f"{status} ✅ Booked")
        elif booking_status == 'pending':
            st.metric("Status", f"{status} ⏳ Booking Pending")
        else:
            st.metric("Status", status)
    
    # AI suggestions
    if suggestions:
        st.markdown(
        """<h2 style='font-size:32px; color:#333; margin-bottom:0.5rem;'>
            📋 Wayfarer AI Recommendations</h2>
        """,
        unsafe_allow_html=True
        )
        
        # Itinerary
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("🧳 Daily Itinerary")
            # Handle itinerary as list of dictionaries
            if isinstance(suggestions['itinerary'], list):
                for day_info in suggestions['itinerary']:
                    with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')} ({format_date_pretty(day_info.get('date', ''))})"):
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
            currency_symbol = suggestions.get('currency_symbol', '$')
            for hotel in suggestions['accommodations']:
                with st.container():
                    st.write(f"**{hotel['name']}**")
                    st.write(f"📍 {hotel.get('location', 'Location not specified')}")
                    # Use price_range instead of price and fix currency
                    price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                    if isinstance(price_info, str) and price_info != 'Price not available':
                        # If price contains dollar sign, replace with correct currency
                        if '$' in price_info:
                            price_info = price_info.replace('$', currency_symbol)
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
            currency_symbol = suggestions.get('currency_symbol', '$')
            for activity in suggestions['activities']:
                with st.container():
                    st.write(f"**{activity['name']}**")
                    st.write(f"📍 {activity.get('location', 'Location not specified')}")
                    # Display cost with correct currency symbol
                    cost = activity.get('cost', 'Cost not specified')
                    if isinstance(cost, str) and cost != 'Cost not specified':
                        # If cost contains dollar sign, replace with correct currency
                        if '$' in cost:
                            cost = cost.replace('$', currency_symbol)
                    st.write(f"💰 {cost}")
                    st.write(f"⏰ {activity.get('duration', 'Duration not specified')}")
                    if 'description' in activity:
                        st.write(f"📝 {activity['description']}")
                    st.write("---")
        
        # Restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
            st.subheader("🍽️ Restaurants")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for restaurant in suggestions['restaurants']:
                with st.container():
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"📍 {restaurant.get('location', 'Location not specified')}")
                    # Display price range with correct currency symbol
                    price_range = restaurant.get('price_range', 'Price not available')
                    if isinstance(price_range, str) and price_range != 'Price not available':
                        # If price contains dollar sign, replace with correct currency
                        if '$' in price_range:
                            price_range = price_range.replace('$', currency_symbol)
                    st.write(f"💰 {price_range}")
                    if 'cuisine' in restaurant:
                        st.write(f"🍴 {restaurant['cuisine']}")
                    st.write("---")
        
        # Transportation
        if 'transportation' in suggestions and suggestions['transportation']:
            st.subheader("🚗 Transportation")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for transport in suggestions['transportation']:
                with st.container():
                    st.write(f"**{transport['type']}**")
                    st.write(f"📍 {transport.get('route', 'Route not specified')}")
                    # Display cost with correct currency symbol
                    cost = transport.get('cost', 'Cost not specified')
                    if isinstance(cost, str) and cost != 'Cost not specified':
                        # If cost contains dollar sign, replace with correct currency
                        if '$' in cost:
                            cost = cost.replace('$', currency_symbol)
                    st.write(f"💰 {cost}")
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
    
    # Booking information
    if trip_data.get('booking_status') == 'confirmed' and trip_data.get('booking_confirmation'):
        st.subheader("🎫 Booking Information")
        
        try:
            booking_confirmation = json.loads(trip_data['booking_confirmation']) if isinstance(trip_data['booking_confirmation'], str) else trip_data['booking_confirmation']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Booking ID:** {booking_confirmation.get('booking_id', 'N/A')}")
                st.write(f"**Confirmation Number:** {booking_confirmation.get('confirmation_number', 'N/A')}")
                st.write(f"**Booking Date:** {booking_confirmation.get('booking_date', 'N/A')[:10]}")
            
            with col2:
                st.write(f"**Total Amount:** ₹{booking_confirmation.get('total_amount', 0):,}")
                st.write(f"**Payment Status:** {booking_confirmation.get('payment_status', 'N/A').title()}")
                st.write(f"**Status:** {booking_confirmation.get('status', 'N/A').title()}")
            
            # Show booking details
            if 'booking_details' in booking_confirmation:
                st.subheader("📋 Booking Details")
                details = booking_confirmation['booking_details']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer Name:** {details.get('customer_name', 'N/A')}")
                    st.write(f"**Email:** {details.get('customer_email', 'N/A')}")
                
                with col2:
                    st.write(f"**Phone:** {details.get('customer_phone', 'N/A')}")
                    st.write(f"**Travel Dates:** {details.get('travel_dates', {}).get('start', 'N/A')} to {details.get('travel_dates', {}).get('end', 'N/A')}")
            
            # Show support contact
            if 'support_contact' in booking_confirmation:
                st.subheader("📞 Support Contact")
                support = booking_confirmation['support_contact']
                st.write(f"**Phone:** {support.get('phone', 'N/A')}")
                st.write(f"**Email:** {support.get('email', 'N/A')}")
            
            # Show next steps
            if 'next_steps' in booking_confirmation:
                st.subheader("📝 Next Steps")
                for step in booking_confirmation['next_steps']:
                    st.write(f"• {step}")
                    
        except Exception as e:
            st.error(f"Error loading booking information: {str(e)}")

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
        # For stats, we'll show USD as default since it's a summary
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

def show_trip_modification_interface():
    """Show the trip modification interface with chat"""
    from trip_modification_chat import TripModificationChat
    
    st.title("🗺️ Trip Modification Center")
    
    if 'user' not in st.session_state:
        st.error("❌ Please log in to modify trips!")
        return
    
    if 'modification_trip_id' not in st.session_state:
        st.error("❌ No trip selected for modification!")
        return
    
    trip_id = st.session_state.modification_trip_id
    user_id = st.session_state.user['id']
    
    # Get trip data
    trip_data = db.get_trip_by_id(trip_id, user_id)
    if not trip_data:
        st.error("❌ Trip not found!")
        return
    
    # Parse AI suggestions
    try:
        current_trip_data = json.loads(trip_data['ai_suggestions']) if isinstance(trip_data['ai_suggestions'], str) else trip_data['ai_suggestions']
    except Exception as e:
        st.error(f"❌ Error loading trip data: {str(e)}")
        return
    
    # Add trip metadata to current_trip_data
    current_trip_data.update({
        'trip_id': trip_id,
        'user_id': user_id,
        'destination': trip_data['destination'],
        'start_date': trip_data['start_date'],
        'end_date': trip_data['end_date'],
        'budget': trip_data['budget'],
        'currency': trip_data['currency'],
        'currency_symbol': trip_data['currency_symbol'],
        'preferences': trip_data['preferences']
    })
    
    # Initialize and show modification interface
    modification_chat = TripModificationChat()
    modification_chat.show_modification_interface(trip_id, user_id, current_trip_data)
    
    # Back button
    if st.button("← Back to Trip Planner", type="secondary"):
        del st.session_state.modification_mode
        if 'modification_trip_id' in st.session_state:
            del st.session_state.modification_trip_id
        st.rerun()

def show_credits_page():
    """Show credits management page"""
    if 'user' not in st.session_state:
        st.error("Please log in first!")
        return
    
    st.title("💳 AI Credits")
    
    # Import credit widget
    from credit_widget import credit_widget
    
    # Show credit card
    credit_widget.show_credit_card(st.session_state.user['id'])
    
    # Show upgrade prompt if credits are low
    credit_widget.show_upgrade_prompt(st.session_state.user['id'])
    
    # Tabs for different credit views
    tab1, tab2, tab3 = st.tabs(["📊 Usage Breakdown", "📋 Transaction History", "ℹ️ About Credits"])
    
    with tab1:
        credit_widget.show_credit_usage_breakdown(st.session_state.user['id'])
    
    with tab2:
        credit_widget.show_credit_history(st.session_state.user['id'])
    
    with tab3:
        st.subheader("ℹ️ About AI Credits")
        
        st.markdown("""
        ### How Credits Work
        
        **AI Credits** are used to generate personalized trip recommendations using our advanced AI system.
        
        #### Credit Usage:
        - **Base Trip Generation**: 5 credits
        - **Additional Credits**: Based on content complexity
          - Itinerary items: +0.5 credits each
          - Accommodations: +0.3 credits each  
          - Activities: +0.4 credits each
          - Restaurants: +0.3 credits each
          - Transportation: +0.2 credits each
        
        #### Credit Limits:
        - **Maximum per trip**: 20 credits
        - **Starting credits**: 1000 credits
        - **Refill options**: Coming soon!
        
        #### Tips to Save Credits:
        - Be specific in your preferences
        - Choose shorter trip durations
        - Focus on fewer destinations
        - Use the budget calculator wisely
        
        ### Need More Credits?
        
        Contact our support team to discuss credit packages and upgrade options!
        """)

# Initialize the trip planner
if __name__ == "__main__":
    show_trip_planner()
