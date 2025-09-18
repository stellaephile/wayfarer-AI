import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from vertex_ai_utils import VertexAITripPlanner
import random

# Configure logging
logger = logging.getLogger(__name__)

class AIBookingDataGenerator:
    """Generates dynamic hotel and flight booking data using AI"""
    
    def __init__(self):
        self.vertex_ai = VertexAITripPlanner()
    
    def generate_flight_data(self, origin: str, destination: str, departure_date: str, 
                           return_date: str = None, passengers: int = 1, 
                           class_type: str = "Economy") -> Dict:
        """
        Generate realistic flight data using AI based on destination
        
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
            # Generate AI-powered flight suggestions
            flight_suggestions = self._generate_ai_flight_suggestions(
                origin, destination, departure_date, return_date, passengers, class_type
            )
            
            return {
                "search_id": f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "flights": flight_suggestions,
                "total_results": len(flight_suggestions),
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating flight data: {str(e)}")
            return self._get_fallback_flight_data(origin, destination, departure_date, return_date)
    
    def generate_hotel_data(self, city: str, check_in: str, check_out: str, 
                           rooms: int = 1, guests: int = 2) -> Dict:
        """
        Generate realistic hotel data using AI based on destination city
        
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
            # Generate AI-powered hotel suggestions
            hotel_suggestions = self._generate_ai_hotel_suggestions(
                city, check_in, check_out, rooms, guests
            )
            
            return {
                "search_id": f"hotel_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "hotels": hotel_suggestions,
                "total_results": len(hotel_suggestions),
                "search_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating hotel data: {str(e)}")
            return self._get_fallback_hotel_data(city, check_in, check_out)
    
    def _generate_ai_flight_suggestions(self, origin: str, destination: str, 
                                       departure_date: str, return_date: str = None, 
                                       passengers: int = 1, class_type: str = "Economy") -> List[Dict]:
        """Generate AI-powered flight suggestions"""
        try:
            # Create prompt for flight generation
            prompt = self._create_flight_prompt(origin, destination, departure_date, return_date, passengers, class_type)
            
            # Log the prompt being sent to AI
            logger.info("=" * 80)
            logger.info("🤖 AI FLIGHT GENERATION REQUEST")
            logger.info("=" * 80)
            logger.info(f"Origin: {origin} → Destination: {destination}")
            logger.info(f"Departure: {departure_date}, Return: {return_date}")
            logger.info(f"Passengers: {passengers}, Class: {class_type}")
            logger.info("-" * 80)
            logger.info("PROMPT SENT TO AI:")
            logger.info(prompt)
            logger.info("-" * 80)
            
            # Use Vertex AI to generate flight suggestions
            if self.vertex_ai.is_configured and self.vertex_ai.model:
                logger.info("🔄 Calling Vertex AI for flight generation...")
                response = self.vertex_ai.model.generate_content(prompt)
                if response and response.text:
                    logger.info("✅ AI Response received!")
                    logger.info("=" * 80)
                    logger.info("🤖 AI FLIGHT RESPONSE")
                    logger.info("=" * 80)
                    logger.info("RAW AI RESPONSE:")
                    logger.info(f"Response length: {len(response.text)} characters")
                    logger.info("Full response:")
                    logger.info(response.text)
                    logger.info("=" * 80)
                    
                    parsed_flights = self._parse_flight_response(response.text, origin, destination, departure_date, return_date)
                    
                    logger.info("📋 PARSED FLIGHT DATA:")
                    for i, flight in enumerate(parsed_flights, 1):
                        logger.info(f"  Flight {i}: {flight.get('airline', 'N/A')} {flight.get('flight_number', 'N/A')} - ₹{flight.get('price', 0):,}")
                    
                    logger.info("=" * 80)
                    return parsed_flights
                else:
                    logger.warning("⚠️ Empty response from AI, falling back to mock data")
            else:
                logger.warning("⚠️ Vertex AI not configured, using enhanced mock data")
            
            # Fallback to enhanced mock data
            logger.info("🔄 Generating enhanced mock flight data...")
            mock_data = self._generate_enhanced_flight_mock_data(origin, destination, departure_date, return_date, passengers, class_type)
            
            logger.info("📋 MOCK FLIGHT DATA GENERATED:")
            for i, flight in enumerate(mock_data, 1):
                logger.info(f"  Flight {i}: {flight.get('airline', 'N/A')} {flight.get('flight_number', 'N/A')} - ₹{flight.get('price', 0):,}")
            
            return mock_data
            
        except Exception as e:
            logger.error(f"❌ Error generating AI flight suggestions: {str(e)}")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_flight_mock_data(origin, destination, departure_date, return_date, passengers, class_type)
    
    def _generate_ai_hotel_suggestions(self, city: str, check_in: str, check_out: str, 
                                      rooms: int = 1, guests: int = 2) -> List[Dict]:
        """Generate AI-powered hotel suggestions"""
        try:
            # Create prompt for hotel generation
            prompt = self._create_hotel_prompt(city, check_in, check_out, rooms, guests)
            
            # Log the prompt being sent to AI
            logger.info("=" * 80)
            logger.info("🏨 AI HOTEL GENERATION REQUEST")
            logger.info("=" * 80)
            logger.info(f"City: {city}")
            logger.info(f"Check-in: {check_in} → Check-out: {check_out}")
            logger.info(f"Rooms: {rooms}, Guests: {guests}")
            logger.info("-" * 80)
            logger.info("PROMPT SENT TO AI:")
            logger.info(prompt)
            logger.info("-" * 80)
            
            # Use Vertex AI to generate hotel suggestions
            if self.vertex_ai.is_configured and self.vertex_ai.model:
                logger.info("🔄 Calling Vertex AI for hotel generation...")
                response = self.vertex_ai.model.generate_content(prompt)
                if response and response.text:
                    logger.info("✅ AI Response received!")
                    logger.info("=" * 80)
                    logger.info("🏨 AI HOTEL RESPONSE")
                    logger.info("=" * 80)
                    logger.info("RAW AI RESPONSE:")
                    logger.info(f"Response length: {len(response.text)} characters")
                    logger.info("Full response:")
                    logger.info(response.text)
                    logger.info("=" * 80)
                    
                    parsed_hotels = self._parse_hotel_response(response.text, city, check_in, check_out)
                    
                    logger.info("📋 PARSED HOTEL DATA:")
                    for i, hotel in enumerate(parsed_hotels, 1):
                        logger.info(f"  Hotel {i}: {hotel.get('name', 'N/A')} - ₹{hotel.get('price_per_night', 0):,}/night")
                    
                    logger.info("=" * 80)
                    return parsed_hotels
                else:
                    logger.warning("⚠️ Empty response from AI, falling back to mock data")
            else:
                logger.warning("⚠️ Vertex AI not configured, using enhanced mock data")
            
            # Fallback to enhanced mock data
            logger.info("🔄 Generating enhanced mock hotel data...")
            mock_data = self._generate_enhanced_hotel_mock_data(city, check_in, check_out, rooms, guests)
            
            logger.info("📋 MOCK HOTEL DATA GENERATED:")
            for i, hotel in enumerate(mock_data, 1):
                logger.info(f"  Hotel {i}: {hotel.get('name', 'N/A')} - ₹{hotel.get('price_per_night', 0):,}/night")
            
            return mock_data
            
        except Exception as e:
            logger.error(f"❌ Error generating AI hotel suggestions: {str(e)}")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_hotel_mock_data(city, check_in, check_out, rooms, guests)
    
    def _create_flight_prompt(self, origin: str, destination: str, departure_date: str, 
                             return_date: str = None, passengers: int = 1, class_type: str = "Economy") -> str:
        """Create prompt for flight data generation"""
        return f"""
You are a travel booking expert. Generate realistic flight options for the following search criteria.

SEARCH CRITERIA:
- Origin: {origin}
- Destination: {destination}
- Departure Date: {departure_date}
- Return Date: {return_date if return_date else 'One-way trip'}
- Passengers: {passengers}
- Class: {class_type}

Generate exactly 3 realistic flight options with the following details for each flight:
- flight_id: unique identifier
- airline: realistic airline name
- flight_number: realistic flight number
- origin: {origin}
- destination: {destination}
- departure_time: realistic departure time (HH:MM format)
- arrival_time: realistic arrival time (HH:MM format)
- duration: realistic flight duration
- price: realistic price in INR (₹)
- currency: INR
- class_type: {class_type}
- available_seats: realistic number (5-25)
- stops: "Non-stop" or "1 stop" or "2 stops"
- aircraft: realistic aircraft type

IMPORTANT JSON FORMATTING RULES:
1. Return ONLY a valid JSON array starting with [ and ending with ]
2. Each flight object must be properly formatted with double quotes
3. All string values must be enclosed in double quotes
4. No trailing commas
5. No newlines within string values
6. No additional text before or after the JSON array

Example format:
[
  {{
    "flight_id": "AI1001",
    "airline": "Air India",
    "flight_number": "AI1001",
    "origin": "DEL",
    "destination": "BOM",
    "departure_time": "08:30",
    "arrival_time": "10:45",
    "duration": "2h 15m",
    "price": 5000,
    "currency": "INR",
    "class_type": "Economy",
    "available_seats": 15,
    "stops": "Non-stop",
    "aircraft": "Boeing 737"
  }}
]

Return ONLY the JSON array, no other text.
"""
    
    def _create_hotel_prompt(self, city: str, check_in: str, check_out: str, 
                            rooms: int = 1, guests: int = 2) -> str:
        """Create prompt for hotel data generation"""
        return f"""
You are a hotel booking expert. Generate realistic hotel options for the following search criteria.

SEARCH CRITERIA:
- City: {city}
- Check-in: {check_in}
- Check-out: {check_out}
- Rooms: {rooms}
- Guests: {guests}

Generate exactly 3 realistic hotel options with the following details for each hotel:
- hotel_id: unique identifier
- name: realistic hotel name in {city}
- city: {city}
- address: realistic address in {city}
- star_rating: 3-5 stars
- price_per_night: realistic price in INR (₹)
- currency: INR
- check_in: {check_in}
- check_out: {check_out}
- total_price: calculated total for stay
- amenities: array of realistic amenities
- room_type: realistic room type
- available_rooms: realistic number (1-8)
- cancellation_policy: realistic policy
- rating: realistic rating (3.5-4.8)
- reviews_count: realistic number (50-500)

IMPORTANT JSON FORMATTING RULES:
1. Return ONLY a valid JSON array starting with [ and ending with ]
2. Each hotel object must be properly formatted with double quotes
3. All string values must be enclosed in double quotes
4. No trailing commas
5. No newlines within string values
6. No additional text before or after the JSON array

Example format:
[
  {{
    "hotel_id": "hotel_1001",
    "name": "Taj Palace",
    "city": "{city}",
    "address": "123 Main Street, {city}",
    "star_rating": 4,
    "price_per_night": 3000,
    "currency": "INR",
    "check_in": "{check_in}",
    "check_out": "{check_out}",
    "total_price": 15000,
    "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
    "room_type": "Deluxe Room",
    "available_rooms": 5,
    "cancellation_policy": "Free cancellation until 24 hours before check-in",
    "rating": 4.2,
    "reviews_count": 150
  }}
]

Return ONLY the JSON array, no other text.
"""
    
    def _clean_json_response(self, text: str) -> str:
        """Clean AI response text to make it valid JSON"""
        try:
            # Remove any text before the first '[' or '{'
            start_idx = -1
            for i, char in enumerate(text):
                if char in '[{':
                    start_idx = i
                    break
            
            if start_idx != -1:
                text = text[start_idx:]
            
            # Remove any text after the last ']' or '}'
            end_idx = -1
            for i in range(len(text) - 1, -1, -1):
                if text[i] in ']}':
                    end_idx = i + 1
                    break
            
            if end_idx != -1:
                text = text[:end_idx]
            
            # Fix common JSON issues
            text = text.replace('\n', ' ')  # Remove newlines
            text = text.replace('\r', ' ')  # Remove carriage returns
            text = text.replace('\t', ' ')  # Remove tabs
            
            # Fix unterminated strings by adding quotes
            text = self._fix_unterminated_strings(text)
            
            # Fix trailing commas
            text = self._fix_trailing_commas(text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"Error cleaning JSON response: {str(e)}")
            return text
    
    def _fix_unterminated_strings(self, text: str) -> str:
        """Fix unterminated strings in JSON"""
        try:
            # Simple approach: find and fix common unterminated string patterns
            import re
            
            # Fix strings that end with newline or are not properly quoted
            # This is a basic fix - more sophisticated parsing could be added
            text = re.sub(r'"([^"]*?)\n', r'"\1"', text)
            text = re.sub(r'"([^"]*?)$', r'"\1"', text)
            
            return text
        except Exception:
            return text
    
    def _fix_trailing_commas(self, text: str) -> str:
        """Fix trailing commas in JSON"""
        try:
            import re
            # Remove trailing commas before closing brackets/braces
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            return text
        except Exception:
            return text
    
    def _safe_json_parse(self, text: str) -> List[Dict]:
        """Safely parse JSON with multiple fallback strategies"""
        logger.info("🔧 SAFE JSON PARSING")
        logger.info("-" * 30)
        
        try:
            # Try direct parsing first
            logger.info("Attempt 1: Direct JSON parsing...")
            result = json.loads(text)
            logger.info(f"✅ Direct parsing successful! Found {len(result)} items")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Direct parsing failed: {str(e)}")
            
        try:
            # Try to find and extract JSON array
            logger.info("Attempt 2: Extract JSON array pattern...")
            import re
            # Look for array pattern (including incomplete ones)
            array_match = re.search(r'\[.*', text, re.DOTALL)
            if array_match:
                array_text = array_match.group()
                logger.info(f"Found array pattern, length: {len(array_text)}")
                
                # Try to fix incomplete array
                if not array_text.endswith(']'):
                    # Count brackets to see if we need to close
                    open_brackets = array_text.count('[')
                    close_brackets = array_text.count(']')
                    if open_brackets > close_brackets:
                        array_text += ']' * (open_brackets - close_brackets)
                        logger.info(f"Added {open_brackets - close_brackets} closing brackets")
                
                result = json.loads(array_text)
                logger.info(f"✅ Array extraction successful! Found {len(result)} items")
                
                # If we got less than 3 items, try to expand to 3
                if len(result) < 3 and len(result) > 0:
                    logger.info(f"Expanding {len(result)} items to 3 options")
                    expanded_result = []
                    for i in range(3):
                        if i < len(result):
                            # Use existing item
                            expanded_result.append(result[i])
                        else:
                            # Create additional item based on first item
                            base_item = result[0].copy()
                            if 'hotel_id' in base_item:
                                # Hotel expansion
                                base_item['hotel_id'] = f"hotel_{1000 + i}"
                                base_item['name'] = f"{base_item.get('name', 'Hotel')} {i+1}"
                                base_item['price_per_night'] = base_item.get('price_per_night', 3000) + (i * 1500)
                                base_item['star_rating'] = base_item.get('star_rating', 4) + (i % 2)
                            elif 'flight_id' in base_item:
                                # Flight expansion
                                base_item['flight_id'] = f"flight_{1000 + i}"
                                base_item['airline'] = f"{base_item.get('airline', 'Airline')} {i+1}"
                                base_item['flight_number'] = f"FL{1000 + i}"
                                base_item['price'] = base_item.get('price', 5000) + (i * 2000)
                                base_item['departure_time'] = f"{8 + i * 2:02d}:30"
                                base_item['arrival_time'] = f"{10 + i * 2:02d}:45"
                            
                            expanded_result.append(base_item)
                    
                    logger.info(f"✅ Expanded to {len(expanded_result)} options")
                    return expanded_result
                
                return result
            else:
                logger.warning("No array pattern found")
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Array extraction failed: {str(e)}")
            
        try:
            # Try to fix common issues and parse again
            logger.info("Attempt 3: Fix JSON issues and parse...")
            fixed_text = self._fix_json_issues(text)
            logger.info(f"Fixed text length: {len(fixed_text)}")
            result = json.loads(fixed_text)
            logger.info(f"✅ Fixed JSON parsing successful! Found {len(result)} items")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"❌ Fixed JSON parsing failed: {str(e)}")
            
        try:
            # Last attempt: Create minimal valid JSON from partial data
            logger.info("Attempt 4: Create minimal valid JSON from partial data...")
            minimal_data = self._create_minimal_json_from_partial(text)
            if minimal_data:
                logger.info(f"✅ Minimal JSON creation successful! Found {len(minimal_data)} items")
                return minimal_data
        except Exception as e:
            logger.warning(f"❌ Minimal JSON creation failed: {str(e)}")
        
        # If all else fails, return empty list
        logger.warning("❌ All JSON parsing attempts failed, returning empty list")
        return []
    
    def _fix_json_issues(self, text: str) -> str:
        """Fix common JSON issues"""
        import re
        
        # Fix unescaped quotes in strings
        text = re.sub(r'"([^"]*)"([^"]*)"([^"]*)"', r'"\1\2\3"', text)
        
        # Fix missing quotes around keys
        text = re.sub(r'(\w+):', r'"\1":', text)
        
        # Fix single quotes to double quotes
        text = text.replace("'", '"')
        
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix unterminated strings by adding closing quotes
        text = self._fix_unterminated_strings(text)
        
        # Fix incomplete JSON by adding closing brackets
        text = self._fix_incomplete_json(text)
        
        return text
    
    def _fix_incomplete_json(self, text: str) -> str:
        """Fix incomplete JSON by adding missing closing brackets"""
        try:
            # Count opening and closing brackets
            open_brackets = text.count('[')
            close_brackets = text.count(']')
            open_braces = text.count('{')
            close_braces = text.count('}')
            
            # Add missing closing brackets
            if open_brackets > close_brackets:
                text += ']' * (open_brackets - close_brackets)
            
            if open_braces > close_braces:
                text += '}' * (open_braces - close_braces)
            
            return text
        except Exception:
            return text
    
    def _create_minimal_json_from_partial(self, text: str) -> List[Dict]:
        """Create minimal valid JSON from partial/truncated data"""
        try:
            import re
            
            # Look for any object-like patterns in the text
            # Find patterns that look like: "key": "value"
            key_value_patterns = re.findall(r'"([^"]+)":\s*"([^"]*)"', text)
            
            if key_value_patterns:
                # Create a minimal object with the found key-value pairs
                minimal_obj = {}
                for key, value in key_value_patterns:
                    minimal_obj[key] = value
                
                # Determine if this is hotel or flight data
                is_hotel = 'hotel_id' in minimal_obj
                is_flight = 'flight_id' in minimal_obj
                
                if is_hotel or is_flight:
                    # Generate exactly 3 options based on the partial data
                    options = []
                    
                    for i in range(3):
                        option = {}
                        
                        if is_hotel:
                            # Create 3 unique hotel options
                            hotel_names = ['Taj Palace', 'Oberoi Hotel', 'ITC Maratha']
                            room_types = ['Deluxe Room', 'Executive Suite', 'Presidential Suite']
                            amenity_sets = [
                                ['WiFi', 'Pool', 'Gym', 'Restaurant'],
                                ['WiFi', 'Spa', 'Business Center', 'Restaurant', 'Pool'],
                                ['WiFi', 'Pool', 'Gym', 'Restaurant', 'Spa', 'Concierge', 'Room Service']
                            ]
                            
                            option = {
                                'hotel_id': f"hotel_{1000 + i}",
                                'name': hotel_names[i] if i < len(hotel_names) else f'Hotel Option {i+1}',
                                'city': minimal_obj.get('city', 'Unknown City'),
                                'address': f"{100 + i*50} Main Street, {minimal_obj.get('city', 'Unknown City')}",
                                'star_rating': 3 + i,  # 3, 4, 5 stars
                                'price_per_night': 2000 + (i * 2000) + (i * 500),  # 2000, 4500, 7000
                                'currency': 'INR',
                                'check_in': minimal_obj.get('check_in', '2025-09-20'),
                                'check_out': minimal_obj.get('check_out', '2025-09-25'),
                                'total_price': (2000 + (i * 2000) + (i * 500)) * 5,  # Assuming 5 nights
                                'amenities': amenity_sets[i] if i < len(amenity_sets) else ['WiFi', 'Pool', 'Gym', 'Restaurant', 'Spa'],
                                'room_type': room_types[i] if i < len(room_types) else 'Deluxe Room',
                                'available_rooms': 8 - i*2,
                                'cancellation_policy': 'Free cancellation until 24 hours before check-in',
                                'rating': 4.0 + (i * 0.3),
                                'reviews_count': 100 + (i * 100)
                            }
                        else:
                            # Create 3 unique flight options
                            airlines = ['Air India', 'IndiGo', 'SpiceJet']
                            flight_codes = ['AI', '6E', 'SG']
                            aircraft_types = ['Boeing 737', 'Airbus A320', 'Boeing 777']
                            
                            option = {
                                'flight_id': f"flight_{1000 + i}",
                                'airline': airlines[i] if i < len(airlines) else f'Airline {i+1}',
                                'flight_number': f"{flight_codes[i] if i < len(flight_codes) else 'FL'}{1000 + i}",
                                'origin': minimal_obj.get('origin', 'DEL'),
                                'destination': minimal_obj.get('destination', 'BOM'),
                                'departure_time': f"{6 + i * 3:02d}:{30 + i*15:02d}",  # 6:30, 9:45, 12:00
                                'arrival_time': f"{8 + i * 3:02d}:{45 + i*10:02d}",  # 8:45, 11:55, 15:00
                                'duration': f"{2 + i}h {15 + i*15}m",
                                'price': 4000 + (i * 2500) + (i * 500),  # 4000, 7000, 10000
                                'currency': 'INR',
                                'class_type': 'Economy',
                                'available_seats': 25 - i*5,
                                'stops': 'Non-stop' if i == 0 else f"{i} stop",
                                'aircraft': aircraft_types[i] if i < len(aircraft_types) else 'Boeing 737'
                            }
                        
                        options.append(option)
                    
                    logger.info(f"Created {len(options)} minimal options from partial data")
                    return options
            
            return []
        except Exception as e:
            logger.warning(f"Error creating minimal JSON: {str(e)}")
            return []
    
    def _parse_flight_response(self, response_text: str, origin: str, destination: str, 
                              departure_date: str, return_date: str = None) -> List[Dict]:
        """Parse AI response for flight data"""
        try:
            logger.info("🔍 PARSING FLIGHT RESPONSE")
            logger.info("-" * 40)
            
            # Clean the response text
            cleaned_text = response_text.strip()
            logger.info(f"Original response length: {len(response_text)} characters")
            
            # Try to extract JSON from the response
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
                logger.info("Removed ```json prefix")
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
                logger.info("Removed ``` suffix")
            
            # Additional cleaning for common AI response issues
            cleaned_text = self._clean_json_response(cleaned_text)
            logger.info(f"Cleaned response length: {len(cleaned_text)} characters")
            logger.info(f"Cleaned response preview: {cleaned_text[:200]}...")
            
            # Parse JSON with safe parsing
            logger.info("Attempting JSON parsing...")
            flights = self._safe_json_parse(cleaned_text)
            logger.info(f"Successfully parsed {len(flights)} flights")
            
            # Validate and enhance the response
            validated_flights = self._validate_flight_data(flights, origin, destination, departure_date, return_date)
            logger.info(f"Validated {len(validated_flights)} flights")
            
            return validated_flights
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse flight response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_flight_mock_data(origin, destination, departure_date, return_date)
        except Exception as e:
            logger.error(f"❌ Error parsing flight response: {str(e)}")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_flight_mock_data(origin, destination, departure_date, return_date)
    
    def _parse_hotel_response(self, response_text: str, city: str, check_in: str, check_out: str) -> List[Dict]:
        """Parse AI response for hotel data"""
        try:
            logger.info("🔍 PARSING HOTEL RESPONSE")
            logger.info("-" * 40)
            
            # Clean the response text
            cleaned_text = response_text.strip()
            logger.info(f"Original response length: {len(response_text)} characters")
            
            # Try to extract JSON from the response
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
                logger.info("Removed ```json prefix")
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
                logger.info("Removed ``` suffix")
            
            # Additional cleaning for common AI response issues
            cleaned_text = self._clean_json_response(cleaned_text)
            logger.info(f"Cleaned response length: {len(cleaned_text)} characters")
            logger.info(f"Cleaned response preview: {cleaned_text[:200]}...")
            
            # Parse JSON with safe parsing
            logger.info("Attempting JSON parsing...")
            hotels = self._safe_json_parse(cleaned_text)
            logger.info(f"Successfully parsed {len(hotels)} hotels")
            
            # Validate and enhance the response
            validated_hotels = self._validate_hotel_data(hotels, city, check_in, check_out)
            logger.info(f"Validated {len(validated_hotels)} hotels")
            
            return validated_hotels
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse hotel response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_hotel_mock_data(city, check_in, check_out)
        except Exception as e:
            logger.error(f"❌ Error parsing hotel response: {str(e)}")
            logger.info("🔄 Falling back to enhanced mock data...")
            return self._generate_enhanced_hotel_mock_data(city, check_in, check_out)
    
    def _validate_flight_data(self, flights: List[Dict], origin: str, destination: str, 
                             departure_date: str, return_date: str = None) -> List[Dict]:
        """Validate and enhance flight data"""
        validated_flights = []
        
        for flight in flights:
            # Ensure required fields exist
            validated_flight = {
                "flight_id": flight.get("flight_id", f"FL{random.randint(1000, 9999)}"),
                "airline": flight.get("airline", "Unknown Airline"),
                "flight_number": flight.get("flight_number", f"FL{random.randint(100, 999)}"),
                "origin": origin,
                "destination": destination,
                "departure_time": flight.get("departure_time", "08:00"),
                "arrival_time": flight.get("arrival_time", "10:00"),
                "duration": flight.get("duration", "2h 00m"),
                "price": flight.get("price", 5000),
                "currency": "INR",
                "class_type": flight.get("class_type", "Economy"),
                "available_seats": flight.get("available_seats", 15),
                "stops": flight.get("stops", "Non-stop"),
                "aircraft": flight.get("aircraft", "Boeing 737")
            }
            validated_flights.append(validated_flight)
        
        return validated_flights
    
    def _validate_hotel_data(self, hotels: List[Dict], city: str, check_in: str, check_out: str) -> List[Dict]:
        """Validate and enhance hotel data"""
        validated_hotels = []
        
        for hotel in hotels:
            # Calculate total price
            price_per_night = hotel.get("price_per_night", 3000)
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (check_out_date - check_in_date).days
            total_price = price_per_night * nights
            
            # Ensure required fields exist
            validated_hotel = {
                "hotel_id": hotel.get("hotel_id", f"hotel_{random.randint(1000, 9999)}"),
                "name": hotel.get("name", f"Hotel in {city}"),
                "city": city,
                "address": hotel.get("address", f"123 Main Street, {city}"),
                "star_rating": hotel.get("star_rating", 4),
                "price_per_night": price_per_night,
                "currency": "INR",
                "check_in": check_in,
                "check_out": check_out,
                "total_price": total_price,
                "amenities": hotel.get("amenities", ["WiFi", "Pool", "Gym", "Restaurant"]),
                "room_type": hotel.get("room_type", "Deluxe Room"),
                "available_rooms": hotel.get("available_rooms", 5),
                "cancellation_policy": hotel.get("cancellation_policy", "Free cancellation until 24 hours before check-in"),
                "rating": hotel.get("rating", 4.2),
                "reviews_count": hotel.get("reviews_count", 150)
            }
            validated_hotels.append(validated_hotel)
        
        return validated_hotels
    
    def _generate_enhanced_flight_mock_data(self, origin: str, destination: str, 
                                           departure_date: str, return_date: str = None, 
                                           passengers: int = 1, class_type: str = "Economy") -> List[Dict]:
        """Generate enhanced mock flight data with destination-specific information"""
        flights = []
        
        # Destination-specific airline and flight data
        destination_airlines = {
            'BOM': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'DEL': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'BLR': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'MAA': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'CCU': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'HYD': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'PNQ': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'AMD': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'JAI': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'GOI': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'],
            'COK': ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir']
        }
        
        # Get airlines for destination or use default
        airlines = destination_airlines.get(destination, ['Air India', 'IndiGo', 'SpiceJet', 'Vistara', 'GoAir'])
        flight_codes = ['AI', '6E', 'SG', 'UK', 'G8']
        
        # Ensure we have at least 3 unique airlines
        unique_airlines = airlines[:3] if len(airlines) >= 3 else airlines + ['Jet Airways', 'Air Asia', 'TruJet'][:3-len(airlines)]
        unique_codes = flight_codes[:3] if len(flight_codes) >= 3 else flight_codes + ['9W', 'I5', '2T'][:3-len(flight_codes)]
        
        for i in range(3):
            airline = unique_airlines[i]
            flight_code = unique_codes[i]
            
            # Generate realistic times with more variation
            departure_hour = 6 + i * 3  # 6, 9, 12
            arrival_hour = departure_hour + 2 + (i * 0.5)
            
            # Add some randomness to make each flight unique
            import random
            random.seed(hash(f"{origin}{destination}{i}"))  # Deterministic but unique per route
            
            flight = {
                "flight_id": f"{flight_code}{1000 + i}",
                "airline": airline,
                "flight_number": f"{flight_code}{1000 + i}",
                "origin": origin,
                "destination": destination,
                "departure_time": f"{departure_hour:02d}:{30 + i*15:02d}",
                "arrival_time": f"{int(arrival_hour):02d}:{45 + i*10:02d}",
                "duration": f"{2 + i}h {15 + i*15}m",
                "price": 4000 + (i * 2500) + random.randint(0, 1000),
                "currency": "INR",
                "class_type": class_type,
                "available_seats": 25 - i*5,
                "stops": "Non-stop" if i == 0 else f"{i} stop",
                "aircraft": ["Boeing 737", "Airbus A320", "Boeing 777"][i]
            }
            flights.append(flight)
        
        return flights
    
    def _generate_enhanced_hotel_mock_data(self, city: str, check_in: str, check_out: str, 
                                          rooms: int = 1, guests: int = 2) -> List[Dict]:
        """Generate enhanced mock hotel data with city-specific information"""
        hotels = []
        
        # City-specific hotel names and characteristics
        city_hotels = {
            'Mumbai': ['Taj Palace', 'Oberoi Hotel', 'ITC Maratha', 'Le Meridien', 'Holiday Inn', 'Radisson Blu'],
            'Delhi': ['The Leela Palace', 'Taj Palace', 'The Oberoi', 'ITC Maurya', 'Holiday Inn', 'Radisson Blu'],
            'Bangalore': ['Taj West End', 'The Leela Palace', 'ITC Gardenia', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Chennai': ['Taj Coromandel', 'The Leela Palace', 'ITC Grand Chola', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Kolkata': ['Taj Bengal', 'The Oberoi', 'ITC Sonar', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Hyderabad': ['Taj Falaknuma Palace', 'The Leela Palace', 'ITC Kakatiya', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Pune': ['Taj Blue Diamond', 'The Leela Palace', 'ITC Maratha', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Ahmedabad': ['Taj Skyline', 'The Leela Palace', 'ITC Narmada', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Jaipur': ['Taj Rambagh Palace', 'The Leela Palace', 'ITC Rajputana', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Goa': ['Taj Exotica', 'The Leela Palace', 'ITC Maratha', 'JW Marriott', 'Holiday Inn', 'Radisson Blu'],
            'Kerala': ['Taj Malabar', 'The Leela Palace', 'ITC Grand Chola', 'JW Marriott', 'Holiday Inn', 'Radisson Blu']
        }
        
        # Get hotels for city or use default
        city_hotel_names = city_hotels.get(city, ['Taj Palace', 'Oberoi Hotel', 'ITC Maratha', 'Le Meridien', 'Holiday Inn', 'Radisson Blu'])
        
        # Ensure we have at least 3 unique hotels
        unique_hotels = city_hotel_names[:3] if len(city_hotel_names) >= 3 else city_hotel_names + ['Marriott', 'Hilton', 'Hyatt'][:3-len(city_hotel_names)]
        
        # Calculate total price
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (check_out_date - check_in_date).days
        
        # Add some randomness to make each hotel unique
        import random
        
        for i in range(3):
            random.seed(hash(f"{city}{check_in}{i}"))  # Deterministic but unique per city/date
            hotel_name = unique_hotels[i]
            base_price = 2000 + (i * 2000)  # 2000, 4000, 6000
            price_per_night = base_price + random.randint(0, 1000)
            total_price = price_per_night * nights
            
            # Different room types and amenities for variety
            room_types = ["Deluxe Room", "Executive Suite", "Presidential Suite"]
            amenity_sets = [
                ["WiFi", "Pool", "Gym", "Restaurant"],
                ["WiFi", "Spa", "Business Center", "Restaurant", "Pool"],
                ["WiFi", "Pool", "Gym", "Restaurant", "Spa", "Concierge", "Room Service"]
            ]
            
            hotel = {
                "hotel_id": f"hotel_{1000 + i}",
                "name": hotel_name,
                "city": city,
                "address": f"{100 + i*50} Main Street, {city}",
                "star_rating": 3 + i,  # 3, 4, 5 stars
                "price_per_night": price_per_night,
                "currency": "INR",
                "check_in": check_in,
                "check_out": check_out,
                "total_price": total_price,
                "amenities": amenity_sets[i],
                "room_type": room_types[i],
                "available_rooms": 8 - i*2,
                "cancellation_policy": "Free cancellation until 24 hours before check-in",
                "rating": 4.0 + (i * 0.3) + random.uniform(0, 0.2),
                "reviews_count": 100 + (i * 100) + random.randint(0, 50)
            }
            hotels.append(hotel)
        
        return hotels
    
    def _get_fallback_flight_data(self, origin: str, destination: str, 
                                 departure_date: str, return_date: str = None) -> Dict:
        """Fallback flight data when AI generation fails"""
        return {
            "search_id": f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "flights": self._generate_enhanced_flight_mock_data(origin, destination, departure_date, return_date),
            "total_results": 3,
            "search_timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_hotel_data(self, city: str, check_in: str, check_out: str) -> Dict:
        """Fallback hotel data when AI generation fails"""
        return {
            "search_id": f"hotel_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "hotels": self._generate_enhanced_hotel_mock_data(city, check_in, check_out),
            "total_results": 3,
            "search_timestamp": datetime.now().isoformat()
        }

# Global instance
ai_booking_generator = AIBookingDataGenerator()
