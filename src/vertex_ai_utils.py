# vertex_ai_utils.py
import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.preview.generative_models import GenerationConfig
from google.cloud import aiplatform
from google.oauth2 import service_account
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))



class VertexAITripPlanner:
    def __init__(self):
        # Load configuration from environment variables ONLY (no st.secrets)
        self.project_id = os.getenv("VERTEX_AI_PROJECT_ID", "your-project-id")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = os.getenv("VERTEX_AI_MODEL", "gemini-pro")
        
        # Check if we have valid configuration
        self.is_configured = self.project_id != "your-project-id"
        
        if not self.is_configured:
            print("⚠️ Vertex AI not configured. Using demo mode with mock data.")
            self.model = None
        else:
            try:
                # Initialize Vertex AI
                self._initialize_vertex_ai()
                self.model = GenerativeModel(
                    self.model_name,
                    generation_config={
                        "temperature": 0.7,
                        "max_output_tokens": 8192
                    }
                )
                logger.info(f"Vertex AI initialized successfully with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {str(e)}")
                print(f"❌ Failed to initialize Vertex AI: {str(e)}")
                self.is_configured = False
                self.model = None


    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with proper authentication"""
        try:
            # Try to get credentials from service account file
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            logger.info(f"Using credential path: {credentials_path if credentials_path else 'Default credentials'}")
            
            if credentials_path and os.path.exists(credentials_path):
                logger.info("Path to credentials exists!")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            else:
                logger.error("Path to credentials NOT found!")
                # Try to use default credentials
                vertexai.init(project=self.project_id, location=self.location)
            
            # Initialize AI Platform
            aiplatform.init(project=self.project_id, location=self.location)
            
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {str(e)}")
            raise e

    def generate_trip_suggestions(self, destination: str, start_date: str, end_date: str,
                                 budget: float, preferences: str, optimize_for: str = "Cost-Efficient",
                                 origin_city: str = "", travelers: int = 1) -> Dict:
        """Generate AI-powered trip suggestions with EaseMyTrip integration"""
        
        if not self.is_configured or not self.model:
            return self._generate_enhanced_mock_suggestions(
                destination, start_date, end_date, budget, preferences, optimize_for, origin_city, travelers
            )
        
        try:
            # Create a comprehensive prompt for the AI
            prompt = self._create_emt_integrated_prompt(
                destination, start_date, end_date, budget, preferences, optimize_for, origin_city, travelers
            )
            
            generation_config = GenerationConfig(
                max_output_tokens=8192,
                temperature=0.7,
                top_p=0.95,
            )
            
            # Generate response using Vertex AI
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            if response and response.text:
                # Parse the AI response
                return self._parse_ai_response(response.text, destination, start_date, end_date, budget)
            else:
                logger.warning("Empty response from Vertex AI, falling back to mock data")
                return self._generate_enhanced_mock_suggestions(
                    destination, start_date, end_date, budget, preferences, optimize_for, origin_city, travelers
                )
                
        except Exception as e:
            logger.error(f"Error generating trip suggestions with Vertex AI: {str(e)}")
            st.warning(f"⚠️ AI generation failed: {str(e)}. Using enhanced mock data.")
            return self._generate_enhanced_mock_suggestions(
                destination, start_date, end_date, budget, preferences, optimize_for, origin_city, travelers
            )

    def _create_emt_integrated_prompt(self, destination: str, start_date: str, end_date: str,
                                 budget: float, preferences: str, optimize_for: str,
                                 origin_city: str, travelers: int) -> str:
                                 """Create a comprehensive prompt for trip planning with EaseMyTrip integration"""
    
                                 start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                                 end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                                 duration_days = (end_dt - start_dt).days + 1
    
                                 prompt = f"""
You are a professional travel planner specializing in comprehensive trip planning with direct access to EaseMyTrip booking platform. Create a comprehensive, sustainable, and {optimize_for.lower()} travel plan.

**MANDATORY REQUIREMENTS:**
Generate EXACTLY TWO complete itineraries:

1. **SUSTAINABLE ITINERARY**: Prioritize eco-friendly options
   - Trains and buses over flights
   - Walking and cycling when possible
   - Eco-certified accommodations
   - Local, sustainable activities

2. **CHEAPEST ITINERARY**: Minimize costs while meeting preferences
   - Budget airlines and transport
   - Affordable accommodations
   - Free or low-cost activities
   - Budget dining options


**EACH ITINERARY MUST INCLUDE:**

✅ **2-3 accommodation options** with prices and amenities
✅ **5-8 activities** with costs, duration, and descriptions  
✅ **3-5 restaurant suggestions** with cuisine types and price ranges
✅ **Complete transport options** with valid EaseMyTrip booking URLs:
   - Flights: https://www.easemytrip.com/flights  https://www.easemytrip.com/low-cost-airlines.html
   - Hotels: https://www.easemytrip.com/hotels
   - Trains: https://www.easemytrip.com/railways
   - Buses: https://www.easemytrip.com/bus
   - Cabs: https://www.easemytrip.com/cabs
   - Activities https://www.easemytrip.com/activities
  
✅ **Day-wise detailed plan** for all {duration_days} days


Please provide a detailed trip plan in the following JSON format. Respond ONLY in compact JSON. Do not include explanations, markdown, or code blocks.

**REQUIRED JSON RESPONSE FORMAT:**
{{
    "destination": "{destination}",
    "duration": "{duration_days} days",
    "budget": {budget},
    "budget_breakdown": {{
        "accommodation": "suggested amount",
        "food": "suggested amount", 
        "activities": "suggested amount",
        "transportation": "suggested amount"
    }},
    "itinerary": [
        {{
            "day": 1,
            "date": "{start_date}",
            "day_name": "day of week",
            "activities": ["activity 1", "activity 2", "activity 3"],
            "meals": {{
                "breakfast": "suggestion",
                "lunch": "suggestion", 
                "dinner": "suggestion"
            }}
        }}
    ],
    "accommodations": [
        {{
            "name": "Hotel/B&B name",
            "type": "Hotel/B&B/Airbnb",
            "price_range": "price per night",
            "rating": 4.5,
            "amenities": ["amenity1", "amenity2"],
            "location": "area description",
            "description": "brief description"
        }}
    ],
    "activities": [
        {{
            "name": "Activity name",
            "type": "Sightseeing/Cultural/Adventure",
            "duration": "time needed",
            "cost": "cost range",
            "description": "what to expect",
            "rating": 4.5,
            "best_time": "when to do it"
        }}
    ],
    "restaurants": [
        {{
            "name": "Restaurant name",
            "cuisine": "cuisine type",
            "price_range": "price per person",
            "rating": 4.3,
            "specialties": ["dish1", "dish2"],
            "location": "area",
            "reservation_required": true
        }}
    ],
    "transportation": [
        {{
            "type": "Airport Transfer/Local/Intercity",
            "option": "specific option",
            "cost": "cost range",
            "duration": "time needed",
            "description": "what to expect",
            "booking_required": true
        }}
    ],
    "tips": [
        "practical tip 1",
        "practical tip 2",
        "practical tip 3"
    ],
    "weather": {{
        "temperature": "expected temperature range",
        "conditions": "weather conditions",
        "recommendation": "packing advice"
    }},
    "packing_list": [
        "essential item 1",
        "essential item 2",
        "essential item 3"
    ]
}}

IMPORTANT:
- Generate BOTH itineraries completely
- Include ALL required elements (accommodations, activities, restaurants, transport, daily plans)
- Use proper EaseMyTrip URL formats with real city codes
- Make sustainable itinerary focus on eco-friendly options
- Make cheapest itinerary focus on budget options
- Ensure JSON is valid and complete
- No markdown, explanations, or extra text
- Make the plan realistic and practical
- Consider the budget constraints carefully
- Include specific, actionable recommendations
- Base recommendations on the preferences provided
- Ensure all JSON is properly formatted
- Include 2-3 accommodation options
- Include 5-8 activities
- Include 3-5 restaurant suggestions
- Make the itinerary detailed for each day
- Include practical travel tips
- Consider local customs and best practices

Please respond with ONLY the JSON object, no additional text.

CRITICAL: 
- INCLUDE easy my trip valid clicakble link for every option.
- Use REAL city codes (DEL, BOM, BLR, etc.)
- Make URLs clickable and valid
- Prioritize sustainability in every recommendation
- Include {travelers} travelers in pricing
- Optimize for {optimize_for.lower()} while maintaining sustainability
"""
    
                                 return prompt


    def _parse_ai_response(self, response_text: str, destination: str, start_date: str,
                          end_date: str, budget: float) -> Dict:
        """Parse the AI response and return structured data"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Try to extract JSON from the response
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
                
            # Parse JSON
            trip_data = json.loads(cleaned_text)
            
            # Validate and enhance the response
            return self._validate_and_enhance_response(trip_data, destination, start_date, end_date, budget)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed", "Cost-Efficient", "", 1)
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed", "Cost-Efficient", "", 1)

    def _validate_and_enhance_response(self, trip_data: Dict, destination: str, start_date: str,
                                     end_date: str, budget: float) -> Dict:
        """Validate and enhance the AI response"""
        # Ensure required fields exist
        if 'destination' not in trip_data:
            trip_data['destination'] = destination
        if 'budget' not in trip_data:
            trip_data['budget'] = budget
            
        # Ensure EaseMyTrip bookings exist
        if 'easemytrip_bookings' not in trip_data:
            trip_data['easemytrip_bookings'] = {}
            
        # Ensure itinerary exists
        if 'itinerary' not in trip_data or not isinstance(trip_data['itinerary'], list):
            trip_data['itinerary'] = self._generate_basic_itinerary(destination, start_date, end_date)
            
        return trip_data

    def _generate_enhanced_mock_suggestions(self, destination: str, start_date: str, end_date: str,
                                          budget: float, preferences: str, optimize_for: str,
                                          origin_city: str, travelers: int) -> Dict:
        """Generate enhanced mock suggestions with EaseMyTrip integration"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        duration_days = (end_dt - start_dt).days + 1
        
        # Mock EaseMyTrip URLs (these would be real in production)
        origin_code = self._get_city_code(origin_city)
        dest_code = self._get_city_code(destination)
        
        suggestions = {
            "destination": destination,
            "duration": f"{duration_days} days",
            "budget": budget,
            "travelers": travelers,
            "optimization": optimize_for,
            "easemytrip_bookings": {
                "trains": [
                    {
                        "route": f"{origin_city} to {destination}",
                        "train": "Express Train Service",
                        "duration": "8-12 hours",
                        "price_range": f"₹{800*travelers:,} - ₹{1500*travelers:,}",
                        "booking_url": f"https://www.easemytrip.com/railways/?from={origin_code}&to={dest_code}&date={start_date}",
                        "sustainable": True,
                        "priority": 1
                    }
                ],
                "buses": [
                    {
                        "route": f"{origin_city} to {destination}",
                        "operator": "Premium Bus Service",
                        "duration": "10-14 hours",
                        "price_range": f"₹{600*travelers:,} - ₹{1200*travelers:,}",
                        "booking_url": f"https://www.easemytrip.com/bus/?from={origin_code}&to={dest_code}&date={start_date}",
                        "sustainable": True,
                        "priority": 2
                    }
                ],
                "flights": [
                    {
                        "route": f"{origin_code} to {dest_code}",
                        "airline": "IndiGo/Air India",
                        "duration": "2-3 hours",
                        "price_range": f"₹{4000*travelers:,} - ₹{8000*travelers:,}",
                        "date": start_date,
                        "booking_url": f"https://www.easemytrip.com/flights/book-online/{origin_code}-{dest_code}-{start_date}.html",
                        "sustainable": False,
                        "priority": 3
                    }
                ],
                "hotels": [
                    {
                        "name": f"Best Hotel in {destination}",
                        "location": f"Central {destination}",
                        "type": "Hotel",
                        "price_range": f"₹{2000:,} - ₹{4000:,} per night",
                        "rating": 4.2,
                        "booking_url": f"https://www.easemytrip.com/hotels/{destination.lower().replace(' ', '')}/{start_date}/{end_date}/",
                        "sustainable": False,
                        "amenities": ["WiFi", "Breakfast", "AC", "Room Service"]
                    }
                ]
            },
            "itinerary": self._generate_basic_itinerary(destination, start_date, end_date),
            "sustainability_highlights": {
                "transport": "🌱 Train options reduce CO2 emissions by 75% compared to flights",
                "accommodation": "Eco-friendly hotels prioritized",
                "activities": "Walking tours and local transport emphasized"
            },
            "budget_breakdown": {
                "transport": f"${budget * 0.4:.0f} (40%)",
                "accommodation": f"${budget * 0.35:.0f} (35%)",
                "food": f"${budget * 0.15:.0f} (15%)",
                "activities": f"${budget * 0.10:.0f} (10%)"
            }
        }
        
        return suggestions

    def _get_city_code(self, city: str) -> str:
        """Get airport/city code for common Indian cities"""
        city_codes = {
            "mumbai": "BOM", "delhi": "DEL", "bangalore": "BLR",
            "chennai": "MAA", "hyderabad": "HYD", "kolkata": "CCU",
            "pune": "PNQ", "ahmedabad": "AMD", "goa": "GOI",
            "jaipur": "JAI", "kochi": "COK", "lucknow": "LKO"
        }
        return city_codes.get(city.lower(), city.upper()[:3])

    def _generate_basic_itinerary(self, destination: str, start_date: str, end_date: str) -> List[Dict]:
        """Generate a basic itinerary structure"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        itinerary = []
        current_date = start_dt
        
        while current_date <= end_dt:
            day_num = (current_date - start_dt).days + 1
            
            itinerary.append({
                "day": day_num,
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "activities": [
                    f"Morning: Explore {destination} city center (walking tour)",
                    f"Afternoon: Visit local attractions via public transport",
                    f"Evening: Traditional dinner in walkable area"
                ],
                "meals": {
                    "breakfast": f"Local breakfast café in {destination}",
                    "lunch": "Traditional local restaurant",
                    "dinner": "Recommended local cuisine"
                },
                "transport_tips": "Use metro/local buses, walk when possible for sustainability"
            })
            
            current_date += timedelta(days=1)
        
        return itinerary

# Initialize the trip planner
trip_planner = VertexAITripPlanner()