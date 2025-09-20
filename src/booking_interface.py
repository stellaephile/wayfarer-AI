import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional
from booking_system import booking_manager
from database_config import get_database

class BookingInterface:
    """Handles the UI for the booking process"""
    
    def __init__(self):
        self.booking_manager = booking_manager
    
    def show_booking_button(self, trip_data: Dict, user_data: Dict) -> bool:
        """
        Show booking button and handle booking process
        
        Args:
            trip_data: Complete trip data including AI suggestions
            user_data: User profile information
        
        Returns:
            bool: True if booking was initiated, False otherwise
        """
        try:
            # Check if trip is finalized (has AI suggestions)
            ai_suggestions = trip_data.get('ai_suggestions', {})
            if isinstance(ai_suggestions, str):
                ai_suggestions = json.loads(ai_suggestions)
            
            if not ai_suggestions:
                st.warning("⚠️ Please finalize your itinerary before booking")
                return False
            
            # Show booking button
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🎫 Book This Trip", type="primary", use_container_width=True):
                    # Store booking data in session state
                    st.session_state.booking_trip_data = trip_data
                    st.session_state.booking_user_data = user_data
                    st.session_state.show_booking_interface = True
                    st.rerun()
            
            return False
            
        except Exception as e:
            st.error(f"Error showing booking button: {str(e)}")
            return False
    
    def show_booking_interface(self):
        """Show the complete booking interface"""
        try:
            if 'booking_trip_data' not in st.session_state or 'booking_user_data' not in st.session_state:
                st.error("❌ No trip data available for booking")
                return
            
            trip_data = st.session_state.booking_trip_data
            user_data = st.session_state.booking_user_data
            
            st.title("🎫 Book Your Trip")
            st.markdown("---")
            
            # Show trip summary
            self._show_trip_summary(trip_data)
            
            # Prepare booking data
            booking_data = self.booking_manager.prepare_booking_data(trip_data, user_data)
            
            if "error" in booking_data:
                st.error(f"❌ {booking_data['error']}")
                return
            
            # Search for available options
            with st.spinner("🔍 Searching for available flights and hotels..."):
                flight_results, hotel_results = self.booking_manager.search_and_display_options(booking_data)
            
            if "error" in flight_results or "error" in hotel_results:
                st.error("❌ Failed to search for booking options. Please try again.")
                return
            
            # Show booking options
            selected_flights, selected_hotels = self._show_booking_options(flight_results, hotel_results)
            
            # Show booking summary and confirmation
            if selected_flights or selected_hotels:
                self._show_booking_summary(booking_data, selected_flights, selected_hotels)
            
            # Back button
            if st.button("← Back to Trip Details", type="secondary"):
                self._clear_booking_session()
                st.rerun()
                
        except Exception as e:
            st.error(f"Error in booking interface: {str(e)}")
    
    def _show_trip_summary(self, trip_data: Dict):
        """Show trip summary before booking"""
        st.subheader("📋 Trip Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Destination", trip_data.get('destination', 'N/A'))
        
        with col2:
            st.metric("Duration", f"{trip_data.get('start_date', '')} to {trip_data.get('end_date', '')}")
        
        with col3:
            currency_symbol = trip_data.get('currency_symbol', '₹')
            st.metric("Budget", f"{currency_symbol}{trip_data.get('budget', 0):,.0f}")
        
        st.markdown("---")
    
    def _show_booking_options(self, flight_results: Dict, hotel_results: Dict) -> tuple:
        """Show available booking options and return selected items"""
        # Initialize session state for selected items if not exists
        if 'selected_flights' not in st.session_state:
            st.session_state.selected_flights = []
        if 'selected_hotels' not in st.session_state:
            st.session_state.selected_hotels = []
        
        selected_flights = st.session_state.selected_flights
        selected_hotels = st.session_state.selected_hotels
        
        # Show current selections
        if selected_flights or selected_hotels:
            st.subheader("🛒 Current Selections")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if selected_flights:
                    st.write("**Selected Flights:**")
                    for flight in selected_flights:
                        st.write(f"• {flight['airline']} {flight['flight_number']} - ₹{flight['price']:,}")
                else:
                    st.write("**Selected Flights:** None")
            
            with col2:
                if selected_hotels:
                    st.write("**Selected Hotels:**")
                    for hotel in selected_hotels:
                        st.write(f"• {hotel['name']} - ₹{hotel['total_price']:,}")
                else:
                    st.write("**Selected Hotels:** None")
            
            # Add clear all button
            if st.button("🗑️ Clear All Selections", type="secondary"):
                st.session_state.selected_flights = []
                st.session_state.selected_hotels = []
                st.rerun()
            
            st.markdown("---")
        
        # Flight options
        if 'flights' in flight_results and flight_results['flights']:
            st.subheader("✈️ Available Flights")
            
            flights = flight_results['flights']
            for i, flight in enumerate(flights):
                # Check if this flight is already selected
                is_selected = any(f.get('flight_id') == flight['flight_id'] for f in selected_flights)
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        # Add selection indicator
                        selection_indicator = "✅ " if is_selected else ""
                        st.write(f"{selection_indicator}**{flight['airline']}** {flight['flight_number']}")
                        st.write(f"🛫 {flight['departure_time']} → 🛬 {flight['arrival_time']}")
                        st.write(f"⏱️ {flight['duration']} • {flight['stops']}")
                    
                    with col2:
                        st.write(f"**Aircraft:** {flight['aircraft']}")
                        st.write(f"**Seats:** {flight['available_seats']} available")
                    
                    with col3:
                        st.write(f"**Price:** ₹{flight['price']:,}")
                        st.write(f"**Class:** {flight['class_type']}")
                    
                    with col4:
                        
                        if is_selected:
                            if st.button("Remove", key=f"remove_flight_{i}", type="secondary"):
                                # Remove from selected flights
                                st.session_state.selected_flights = [f for f in selected_flights if f.get('flight_id') != flight['flight_id']]
                                st.rerun()
                        else:
                            if st.button("Select", key=f"select_flight_{i}"):
                                # Add to selected flights
                                st.session_state.selected_flights.append(flight)
                                st.rerun()
                    
                    st.divider()
        
        # Hotel options
        if 'hotels' in hotel_results and hotel_results['hotels']:
            st.subheader("🏨 Available Hotels")
            
            hotels = hotel_results['hotels']
            for i, hotel in enumerate(hotels):
                # Check if this hotel is already selected
                is_selected = any(h.get('hotel_id') == hotel['hotel_id'] for h in selected_hotels)
                
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        # Add selection indicator
                        selection_indicator = "✅ " if is_selected else ""
                        st.write(f"{selection_indicator}**{hotel['name']}** ⭐{hotel['star_rating']}")
                        st.write(f"📍 {hotel['address']}")
                        st.write(f"🏷️ {hotel['room_type']}")
                    
                    with col2:
                        amenities = ", ".join(hotel['amenities'][:3])
                        st.write(f"**Amenities:** {amenities}")
                        st.write(f"**Rating:** {hotel['rating']}/5 ({hotel['reviews_count']} reviews)")
                    
                    with col3:
                        st.write(f"**Price:** ₹{hotel['total_price']:,} total")
                        st.write(f"**Per night:** ₹{hotel['price_per_night']:,}")
                        st.write(f"**Rooms:** {hotel['available_rooms']} available")
                    
                    with col4:
                        
                        if is_selected:
                            if st.button("Remove", key=f"remove_hotel_{i}", type="secondary"):
                                # Remove from selected hotels
                                st.session_state.selected_hotels = [h for h in selected_hotels if h.get('hotel_id') != hotel['hotel_id']]
                                st.rerun()
                        else:
                            if st.button("Select", key=f"select_hotel_{i}"):
                                # Add to selected hotels
                                st.session_state.selected_hotels.append(hotel)
                                st.rerun()
                    
                    st.divider()
        
        return selected_flights, selected_hotels
    
    def _show_booking_summary(self, booking_data: Dict, selected_flights: List, selected_hotels: List):
        """Show booking summary and handle confirmation"""
        st.subheader("📊 Booking Summary")
        
        # Use session state values for consistency
        session_flights = st.session_state.get('selected_flights', [])
        session_hotels = st.session_state.get('selected_hotels', [])
        
        # Calculate totals
        flight_total = sum(flight.get('price', 0) for flight in session_flights)
        hotel_total = sum(hotel.get('total_price', 0) for hotel in session_hotels)
        total_amount = flight_total + hotel_total
        
        # Show selected items
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Selected Flights:**")
            if session_flights:
                for flight in session_flights:
                    st.write(f"• {flight['airline']} {flight['flight_number']} - ₹{flight['price']:,}")
            else:
                st.write("No flights selected")
        
        with col2:
            st.write("**Selected Hotels:**")
            if session_hotels:
                for hotel in session_hotels:
                    st.write(f"• {hotel['name']} - ₹{hotel['total_price']:,}")
            else:
                st.write("No hotels selected")
        
        # Show total
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.metric("Flight Total", f"₹{flight_total:,}")
        
        with col2:
            st.metric("Hotel Total", f"₹{hotel_total:,}")
        
        with col3:
            st.metric("**Grand Total**", f"₹{total_amount:,}", delta=None)
        
        # Customer information
        st.subheader("👤 Customer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {booking_data.get('customer_name', 'N/A')}")
            st.write(f"**Email:** {booking_data.get('customer_email', 'N/A')}")
        
        with col2:
            st.write(f"**Phone:** {booking_data.get('customer_phone', 'N/A')}")
            st.write(f"**Trip ID:** {booking_data.get('trip_id', 'N/A')}")
        
        # Booking confirmation
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎫 Confirm Booking", type="primary", use_container_width=True):
                self._process_booking_confirmation(booking_data, session_flights, session_hotels)
    
    def _process_booking_confirmation(self, booking_data: Dict, selected_flights: List, selected_hotels: List):
        """Process the final booking confirmation"""
        try:
            with st.spinner("🔄 Processing your booking..."):
                # Create booking
                confirmation = self.booking_manager.create_booking_from_options(
                    booking_data, selected_flights, selected_hotels
                )
            
            if "error" in confirmation:
                st.error(f"❌ Booking failed: {confirmation['error']}")
                return
            
            # Show success message
            st.success("🎉 Booking confirmed successfully!")
            
            # Display booking details
            st.subheader("📋 Booking Confirmation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Booking ID:** {confirmation['booking_id']}")
                st.write(f"**Confirmation Number:** {confirmation['confirmation_number']}")
                st.write(f"**Status:** {confirmation['status'].title()}")
            
            with col2:
                st.write(f"**Total Amount:** ₹{confirmation['total_amount']:,}")
                st.write(f"**Payment Status:** {confirmation['payment_status'].title()}")
                st.write(f"**Booking Date:** {confirmation['booking_date'][:10]}")
            
            # Show next steps
            st.subheader("📝 Next Steps")
            
            if 'next_steps' in confirmation:
                for step in confirmation['next_steps']:
                    st.write(f"• {step}")
            
            # Show support contact
            if 'support_contact' in confirmation:
                st.subheader("📞 Support Contact")
                support = confirmation['support_contact']
                st.write(f"**Phone:** {support.get('phone', 'N/A')}")
                st.write(f"**Email:** {support.get('email', 'N/A')}")
            
            # Update trip status in database
            trip_id = booking_data.get('trip_id')
            if trip_id:
                # Convert datetime objects to strings for JSON serialization
                confirmation_serializable = self._make_json_serializable(confirmation)
                
                db = get_database()
                db.update_trip(
                    trip_id, 
                    booking_data.get('user_id'), 
                    status='booked',
                    booking_status='confirmed',
                    booking_id=confirmation.get('booking_id'),
                    booking_confirmation=json.dumps(confirmation_serializable)
                )
            
            # Clear booking session
            self._clear_booking_session()
            
            # Show action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📚 View My Trips", type="secondary"):
                    st.session_state.trip_planner_page = "📚 My Trips"
                    st.rerun()
            
            with col2:
                if st.button("🗺️ Plan New Trip", type="secondary"):
                    st.session_state.trip_planner_page = "🗺️ Plan Trip"
                    st.rerun()
            
            with col3:
                if st.button("🏠 Dashboard", type="secondary"):
                    st.session_state.trip_planner_page = "🏠 Dashboard"
                    st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing booking: {str(e)}")
    
    def _make_json_serializable(self, obj):
        """Convert datetime objects to strings for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    def _clear_booking_session(self):
        """Clear booking-related session state"""
        keys_to_clear = [
            'booking_trip_data', 'booking_user_data', 'show_booking_interface',
            'selected_flights', 'selected_hotels'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

# Global booking interface instance
booking_interface = BookingInterface()
