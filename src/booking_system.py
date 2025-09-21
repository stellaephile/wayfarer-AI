import streamlit as st
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EaseMyTripBookingSystem:
    """Handles booking integration with EaseMyTrip API"""
    
    def __init__(self):
        self.base_url = "https://api.easemytrip.com/v1"  # Replace with actual EaseMyTrip API URL
        self.api_key = st.secrets.get("EASEMYTRIP_API_KEY", "demo_key")  # Store in Streamlit secrets
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Version": "1.0"
        }
    
    def search_flights(self, origin: str, destination: str, departure_date: str, 
                      return_date: str = None, passengers: int = 1, 
                      class_type: str = "Economy") -> Dict:
        """
        Search for flights using EaseMyTrip API
        
        Args:
            origin: Origin city code (e.g., "DEL" for Delhi)
            destination: Destination city code (e.g., "BOM" for Mumbai)
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date for round trip (optional)
            passengers: Number of passengers
            class_type: Flight class (Economy, Business, First)
        
        Returns:
            Dict containing flight search results
        """
        try:
            payload = {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": passengers,
                "class_type": class_type,
                "search_id": f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # For demo purposes, return mock data
            if self.api_key == "demo_key":
                return self._get_mock_flight_data(origin, destination, departure_date, return_date)
            
            response = requests.post(
                f"{self.base_url}/flights/search",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Flight search failed: {response.status_code} - {response.text}")
                return {"error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            return {"error": f"Search failed: {str(e)}"}
    
    def search_hotels(self, city: str, check_in: str, check_out: str, 
                     rooms: int = 1, guests: int = 2) -> Dict:
        """
        Search for hotels using EaseMyTrip API
        
        Args:
            city: City name or code
            check_in: Check-in date in YYYY-MM-DD format
            check_out: Check-out date in YYYY-MM-DD format
            rooms: Number of rooms
            guests: Number of guests
        
        Returns:
            Dict containing hotel search results
        """
        try:
            payload = {
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "rooms": rooms,
                "guests": guests,
                "search_id": f"hotel_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # For demo purposes, return mock data
            if self.api_key == "demo_key":
                return self._get_mock_hotel_data(city, check_in, check_out)
            
            response = requests.post(
                f"{self.base_url}/hotels/search",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Hotel search failed: {response.status_code} - {response.text}")
                return {"error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error searching hotels: {str(e)}")
            return {"error": f"Search failed: {str(e)}"}
    
    def create_booking(self, booking_data: Dict) -> Dict:
        """
        Create a booking with EaseMyTrip API
        
        Args:
            booking_data: Complete booking information
        
        Returns:
            Dict containing booking confirmation
        """
        try:
            # For demo purposes, return mock booking confirmation
            if self.api_key == "demo_key":
                return self._get_mock_booking_confirmation(booking_data)
            
            response = requests.post(
                f"{self.base_url}/bookings/create",
                headers=self.headers,
                json=booking_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Booking creation failed: {response.status_code} - {response.text}")
                return {"error": f"Booking failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {"error": f"Booking failed: {str(e)}"}
    
    def get_booking_status(self, booking_id: str) -> Dict:
        """
        Get booking status from EaseMyTrip API
        
        Args:
            booking_id: Unique booking identifier
        
        Returns:
            Dict containing booking status
        """
        try:
            # For demo purposes, return mock status
            if self.api_key == "demo_key":
                return self._get_mock_booking_status(booking_id)
            
            response = requests.get(
                f"{self.base_url}/bookings/{booking_id}/status",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Status check failed: {response.status_code} - {response.text}")
                return {"error": f"Status check failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error checking booking status: {str(e)}")
            return {"error": f"Status check failed: {str(e)}"}
    
    def _get_mock_flight_data(self, origin: str, destination: str, 
                             departure_date: str, return_date: str = None) -> Dict:
        """Generate mock flight data for demo purposes"""
        flights = []
        
        # Generate 3-5 mock flights
        airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "GoAir"]
        flight_codes = ["AI", "6E", "SG", "UK", "G8"]
        
        for i in range(3):
            airline = airlines[i % len(airlines)]
            flight_code = flight_codes[i % len(flight_codes)]
            
            flight = {
                "flight_id": f"{flight_code}{1000 + i}",
                "airline": airline,
                "flight_number": f"{flight_code}{1000 + i}",
                "origin": origin,
                "destination": destination,
                "departure_time": f"{8 + i*2:02d}:30",
                "arrival_time": f"{10 + i*2:02d}:45",
                "duration": f"{2 + i}h {15 + i*10}m",
                "price": 5000 + (i * 2000),
                "currency": "INR",
                "class_type": "Economy",
                "available_seats": 20 - i*3,
                "stops": "Non-stop" if i == 0 else f"{i} stop",
                "aircraft": "Boeing 737" if i % 2 == 0 else "Airbus A320"
            }
            flights.append(flight)
        
        return {
            "search_id": f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "flights": flights,
            "total_results": len(flights),
            "search_timestamp": datetime.now().isoformat()
        }
    
    def _get_mock_hotel_data(self, city: str, check_in: str, check_out: str) -> Dict:
        """Generate mock hotel data for demo purposes"""
        hotels = []
        
        # Generate 4-6 mock hotels
        hotel_names = [
            "Taj Palace", "Oberoi Hotel", "ITC Maratha", "Le Meridien", 
            "Holiday Inn", "Radisson Blu", "Hyatt Regency", "JW Marriott"
        ]
        
        for i in range(4):
            hotel = {
                "hotel_id": f"hotel_{1000 + i}",
                "name": hotel_names[i],
                "city": city,
                "address": f"123 Main Street, {city}",
                "star_rating": 4 + (i % 2),
                "price_per_night": 3000 + (i * 1500),
                "currency": "INR",
                "check_in": check_in,
                "check_out": check_out,
                "total_price": (3000 + (i * 1500)) * 2,  # Assuming 2 nights
                "amenities": ["WiFi", "Pool", "Gym", "Restaurant", "Spa"],
                "room_type": "Deluxe Room",
                "available_rooms": 5 - i,
                "cancellation_policy": "Free cancellation until 24 hours before check-in",
                "rating": 4.2 + (i * 0.1),
                "reviews_count": 150 + (i * 50)
            }
            hotels.append(hotel)
        
        return {
            "search_id": f"hotel_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "hotels": hotels,
            "total_results": len(hotels),
            "search_timestamp": datetime.now().isoformat()
        }
    
    def _get_mock_booking_confirmation(self, booking_data: Dict) -> Dict:
        """Generate mock booking confirmation for demo purposes"""
        booking_id = f"EMT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "booking_id": booking_id,
            "status": "confirmed",
            "confirmation_number": f"EMT-{booking_id}",
            "booking_date": datetime.now().isoformat(),
            "total_amount": booking_data.get("total_amount", 0),
            "currency": booking_data.get("currency", "INR"),
            "payment_status": "completed",
            "booking_details": {
                "customer_name": booking_data.get("customer_name", "Demo User"),
                "customer_email": booking_data.get("customer_email", "demo@example.com"),
                "customer_phone": booking_data.get("customer_phone", "+91-9876543210"),
                "travel_dates": booking_data.get("travel_dates", {}),
                "services": booking_data.get("services", [])
            },
            "cancellation_policy": "Free cancellation available until 24 hours before travel",
            "support_contact": {
                "phone": "+91-1800-123-4567",
                "email": "support@easemytrip.com"
            }
        }
    
    def _get_mock_booking_status(self, booking_id: str) -> Dict:
        """Generate mock booking status for demo purposes"""
        return {
            "booking_id": booking_id,
            "status": "confirmed",
            "last_updated": datetime.now().isoformat(),
            "services_status": {
                "flight": "confirmed",
                "hotel": "confirmed",
                "transportation": "pending"
            },
            "next_steps": [
                "Check-in online 24 hours before departure",
                "Arrive at airport 2 hours before domestic flights",
                "Contact hotel for early check-in options"
            ]
        }

class TripBookingManager:
    """Manages the booking process for trip itineraries"""
    
    def __init__(self):
        self.booking_system = EaseMyTripBookingSystem()
    
    def prepare_booking_data(self, trip_data: Dict, user_data: Dict) -> Dict:
        """
        Prepare booking data from trip itinerary and user information
        
        Args:
            trip_data: Complete trip data including AI suggestions
            user_data: User profile information
        
        Returns:
            Dict containing formatted booking data
        """
        try:
            # Extract trip information
            destination = trip_data.get('destination', '')
            start_date = trip_data.get('start_date', '')
            end_date = trip_data.get('end_date', '')
            budget = trip_data.get('budget', 0)
            currency = trip_data.get('currency', 'INR')
            currency_symbol = trip_data.get('currency_symbol', '₹')
            
            # Parse AI suggestions
            ai_suggestions = trip_data.get('ai_suggestions', {})
            if isinstance(ai_suggestions, str):
                ai_suggestions = json.loads(ai_suggestions)
            
            # Prepare services to book
            services = []
            
            # Add flight booking if itinerary includes flights
            if 'transportation' in ai_suggestions:
                for transport in ai_suggestions['transportation']:
                    if 'flight' in transport.get('type', '').lower():
                        services.append({
                            "type": "flight",
                            "description": f"Flight to {destination}",
                            "estimated_cost": 5000,
                            "currency": currency
                        })
            
            # Add hotel booking if accommodations are suggested
            if 'accommodations' in ai_suggestions:
                for hotel in ai_suggestions['accommodations']:
                    services.append({
                        "type": "hotel",
                        "description": f"Hotel: {hotel.get('name', 'Accommodation')}",
                        "estimated_cost": 3000,
                        "currency": currency
                    })
            
            # Calculate total estimated cost
            total_estimated_cost = sum(service.get('estimated_cost', 0) for service in services)
            
            booking_data = {
                "trip_id": trip_data.get('trip_id'),
                "user_id": user_data.get('id'),
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "total_amount": total_estimated_cost,
                "currency": currency,
                "currency_symbol": currency_symbol,
                "customer_name": user_data.get('name', user_data.get('username', '')),
                "customer_email": user_data.get('email', ''),
                "customer_phone": user_data.get('personal_number', ''),
                "travel_dates": {
                    "start": start_date,
                    "end": end_date
                },
                "services": services,
                "booking_notes": f"AI-generated trip to {destination}",
                "preferences": trip_data.get('preferences', ''),
                "created_at": datetime.now().isoformat()
            }
            
            return booking_data
            
        except Exception as e:
            logger.error(f"Error preparing booking data: {str(e)}")
            return {"error": f"Failed to prepare booking data: {str(e)}"}
    
    def search_and_display_options(self, booking_data: Dict) -> Tuple[Dict, Dict]:
        """
        Search for available booking options and return formatted results
        
        Args:
            booking_data: Prepared booking data
        
        Returns:
            Tuple of (flight_options, hotel_options)
        """
        try:
            destination = booking_data.get('destination', '')
            start_date = booking_data.get('start_date', '')
            end_date = booking_data.get('end_date', '')
            
            # Mock city codes for demo (in real implementation, use city mapping)
            city_codes = {
                'delhi': 'DEL', 'mumbai': 'BOM', 'bangalore': 'BLR', 
                'chennai': 'MAA', 'kolkata': 'CCU', 'hyderabad': 'HYD',
                'pune': 'PNQ', 'ahmedabad': 'AMD', 'jaipur': 'JAI',
                'goa': 'GOI', 'kerala': 'COK', 'rajasthan': 'JAI'
            }
            
            # Find matching city code
            origin_city = 'DEL'  # Default to Delhi
            dest_city = 'BOM'    # Default to Mumbai
            
            for city_name, code in city_codes.items():
                if city_name.lower() in destination.lower():
                    dest_city = code
                    break
            
            # Search flights
            flight_results = self.booking_system.search_flights(
                origin=origin_city,
                destination=dest_city,
                departure_date=start_date,
                return_date=end_date,
                passengers=1
            )
            
            # Search hotels
            hotel_results = self.booking_system.search_hotels(
                city=destination,
                check_in=start_date,
                check_out=end_date,
                rooms=1,
                guests=2
            )
            
            return flight_results, hotel_results
            
        except Exception as e:
            logger.error(f"Error searching booking options: {str(e)}")
            return {"error": str(e)}, {"error": str(e)}
    
    def create_booking_from_options(self, booking_data: Dict, selected_flights: List, 
                                  selected_hotels: List) -> Dict:
        """
        Create final booking with selected options
        
        Args:
            booking_data: Base booking data
            selected_flights: List of selected flight options
            selected_hotels: List of selected hotel options
        
        Returns:
            Dict containing booking confirmation
        """
        try:
            # Update booking data with selected options
            booking_data['selected_flights'] = selected_flights
            booking_data['selected_hotels'] = selected_hotels
            
            # Calculate final total
            flight_total = sum(flight.get('price', 0) for flight in selected_flights)
            hotel_total = sum(hotel.get('total_price', 0) for hotel in selected_hotels)
            booking_data['total_amount'] = flight_total + hotel_total
            
            # Create booking
            confirmation = self.booking_system.create_booking(booking_data)
            
            return confirmation
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {"error": f"Booking creation failed: {str(e)}"}

# Global booking manager instance
booking_manager = TripBookingManager()
