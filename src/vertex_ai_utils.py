import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import aiplatform
from google.oauth2 import service_account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VertexAITripPlanner:
    def __init__(self):
        # Load configuration from environment or secrets with fallback
        try:
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID", st.secrets.get("VERTEX_AI_PROJECT_ID", "your-project-id"))
        except:
            self.project_id = os.getenv("VERTEX_AI_PROJECT_ID", "your-project-id")
        
        try:
            self.location = os.getenv("VERTEX_AI_LOCATION", st.secrets.get("VERTEX_AI_LOCATION", "us-central1"))
        except:
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        try:
            self.model_name = os.getenv("VERTEX_AI_MODEL", st.secrets.get("VERTEX_AI_MODEL", "gemini-pro"))
        except:
            self.model_name = os.getenv("VERTEX_AI_MODEL", "gemini-pro")
        
        # Check if we have valid configuration
        self.is_configured = self.project_id != "your-project-id"
        
        if not self.is_configured:
            st.warning("⚠️ Vertex AI not configured. Using demo mode with mock data.")
            self.model = None
        else:
            try:
                # Initialize Vertex AI
                self._initialize_vertex_ai()
                self.model = GenerativeModel(self.model_name)
                logger.info(f"Vertex AI initialized successfully with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {str(e)}")
                st.error(f"❌ Failed to initialize Vertex AI: {str(e)}")
                self.is_configured = False
                self.model = None
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with proper authentication"""
        try:
            # Try to get credentials from service account file
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                vertexai.init(project=self.project_id, location=self.location, credentials=credentials)
            else:
                # Try to use default credentials
                vertexai.init(project=self.project_id, location=self.location)
            
            # Initialize AI Platform
            aiplatform.init(project=self.project_id, location=self.location)
            
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {str(e)}")
            raise e
    
    def generate_trip_suggestions(self, destination: str, start_date: str, end_date: str, 
                                budget: float, preferences: str) -> Dict:
        """
        Generate AI-powered trip suggestions using Vertex AI
        """
        if not self.is_configured or not self.model:
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences)
        
        try:
            # Create a comprehensive prompt for the AI
            prompt = self._create_trip_planning_prompt(destination, start_date, end_date, budget, preferences)
            
            # Generate response using Vertex AI
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse the AI response
                return self._parse_ai_response(response.text, destination, start_date, end_date, budget)
            else:
                logger.warning("Empty response from Vertex AI, falling back to mock data")
                return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences)
                
        except Exception as e:
            logger.error(f"Error generating trip suggestions with Vertex AI: {str(e)}")
            st.warning(f"⚠️ AI generation failed: {str(e)}. Using enhanced mock data.")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences)
    
    def _create_trip_planning_prompt(self, destination: str, start_date: str, end_date: str, 
                                   budget: float, preferences: str) -> str:
        """Create a comprehensive prompt for trip planning"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        duration_days = (end_dt - start_dt).days + 1
        
        prompt = f"""
You are an expert travel planner. Create a comprehensive trip plan for the following request:

DESTINATION: {destination}
DATES: {start_date} to {end_date} ({duration_days} days)
BUDGET: ${budget:,.2f} USD
PREFERENCES: {preferences}

Please provide a detailed trip plan in the following JSON format:

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
            "reservation_required": true/false
        }}
    ],
    "transportation": [
        {{
            "type": "Airport Transfer/Local/Intercity",
            "option": "specific option",
            "cost": "cost range",
            "duration": "time needed",
            "description": "what to expect",
            "booking_required": true/false
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
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed")
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed")
    
    def _validate_and_enhance_response(self, trip_data: Dict, destination: str, start_date: str, 
                                     end_date: str, budget: float) -> Dict:
        """Validate and enhance the AI response"""
        # Ensure required fields exist
        if 'destination' not in trip_data:
            trip_data['destination'] = destination
        
        if 'budget' not in trip_data:
            trip_data['budget'] = budget
        
        # Ensure itinerary is properly formatted
        if 'itinerary' not in trip_data or not isinstance(trip_data['itinerary'], list):
            trip_data['itinerary'] = self._generate_enhanced_itinerary(destination, start_date, end_date, "general")
        
        # Ensure other sections exist
        if 'accommodations' not in trip_data:
            trip_data['accommodations'] = []
        
        if 'activities' not in trip_data:
            trip_data['activities'] = []
        
        if 'restaurants' not in trip_data:
            trip_data['restaurants'] = []
        
        if 'transportation' not in trip_data:
            trip_data['transportation'] = []
        
        if 'tips' not in trip_data:
            trip_data['tips'] = []
        
        if 'weather' not in trip_data:
            trip_data['weather'] = {}
        
        if 'packing_list' not in trip_data:
            trip_data['packing_list'] = []
        
        return trip_data
    
    def _generate_enhanced_mock_suggestions(self, destination: str, start_date: str, end_date: str, 
                                          budget: float, preferences: str) -> Dict:
        """Generate enhanced mock suggestions with more realistic data"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        duration_days = (end_dt - start_dt).days + 1
        
        # Budget allocation
        accommodation_budget = budget * 0.4
        food_budget = budget * 0.3
        activities_budget = budget * 0.2
        transport_budget = budget * 0.1
        
        suggestions = {
            "destination": destination,
            "duration": f"{duration_days} days",
            "budget": budget,
            "budget_breakdown": {
                "accommodation": accommodation_budget,
                "food": food_budget,
                "activities": activities_budget,
                "transportation": transport_budget
            },
            "itinerary": self._generate_enhanced_itinerary(destination, start_date, end_date, preferences),
            "accommodations": self._generate_enhanced_accommodations(destination, budget, duration_days),
            "activities": self._generate_enhanced_activities(destination, preferences, activities_budget),
            "restaurants": self._generate_enhanced_restaurants(destination, food_budget, duration_days),
            "transportation": self._generate_enhanced_transportation(destination, transport_budget),
            "tips": self._generate_enhanced_tips(destination, preferences),
            "weather": self._generate_weather_info(destination, start_date),
            "packing_list": self._generate_packing_list(destination, preferences, duration_days)
        }
        
        return suggestions
    
    def _generate_enhanced_itinerary(self, destination: str, start_date: str, end_date: str, preferences: str) -> List[Dict]:
        """Generate enhanced daily itinerary"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        itinerary = []
        current_date = start_dt
        
        while current_date <= end_dt:
            day_num = (current_date - start_dt).days + 1
            
            # Generate activities based on preferences
            activities = self._get_activities_for_day(destination, day_num, preferences)
            
            itinerary.append({
                "day": day_num,
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "activities": activities,
                "meals": self._get_meals_for_day(destination, day_num)
            })
            
            current_date += timedelta(days=1)
        
        return itinerary
    
    def _get_activities_for_day(self, destination: str, day: int, preferences: str) -> List[str]:
        """Get activities for a specific day based on preferences"""
        base_activities = [
            f"Morning: Explore {destination} city center",
            f"Afternoon: Visit local attractions",
            f"Evening: Enjoy local cuisine"
        ]
        
        if "adventure" in preferences.lower():
            base_activities.insert(1, f"Adventure activity in {destination}")
        if "culture" in preferences.lower():
            base_activities.insert(1, f"Visit museums and cultural sites")
        if "nature" in preferences.lower():
            base_activities.insert(1, f"Explore natural attractions near {destination}")
        if "food" in preferences.lower():
            base_activities.append(f"Food tour in {destination}")
        
        return base_activities
    
    def _get_meals_for_day(self, destination: str, day: int) -> Dict:
        """Get meal suggestions for a day"""
        return {
            "breakfast": f"Local breakfast spot in {destination}",
            "lunch": f"Traditional lunch restaurant",
            "dinner": f"Recommended dinner venue"
        }
    
    def _generate_enhanced_accommodations(self, destination: str, budget: float, duration_days: int) -> List[Dict]:
        """Generate enhanced accommodation suggestions"""
        budget_per_night = budget * 0.4 / duration_days if duration_days > 0 else budget * 0.4
        
        if budget_per_night < 50:
            budget_level = "budget"
            price_range = f"${budget_per_night * 0.8:.0f} - ${budget_per_night * 1.2:.0f}"
        elif budget_per_night < 150:
            budget_level = "mid-range"
            price_range = f"${budget_per_night * 0.8:.0f} - ${budget_per_night * 1.2:.0f}"
        else:
            budget_level = "luxury"
            price_range = f"${budget_per_night * 0.8:.0f} - ${budget_per_night * 1.2:.0f}"
        
        accommodations = [
            {
                "name": f"Best {budget_level.title()} Hotel in {destination}",
                "type": "Hotel",
                "price_range": f"{price_range} per night",
                "rating": 4.5,
                "amenities": ["WiFi", "Breakfast", "Pool", "Gym", "Spa"],
                "location": f"Central {destination}",
                "description": f"Comfortable {budget_level} accommodation with excellent amenities"
            },
            {
                "name": f"Cozy {budget_level.title()} B&B",
                "type": "Bed & Breakfast",
                "price_range": f"{price_range} per night",
                "rating": 4.2,
                "amenities": ["WiFi", "Breakfast", "Garden", "Kitchen"],
                "location": f"Quiet neighborhood in {destination}",
                "description": f"Charming {budget_level} B&B with personal touch"
            }
        ]
        
        return accommodations
    
    def _generate_enhanced_activities(self, destination: str, preferences: str, budget: float) -> List[Dict]:
        """Generate enhanced activity suggestions"""
        activities = [
            {
                "name": f"Explore {destination} Historic Center",
                "type": "Sightseeing",
                "duration": "Half Day",
                "cost": "Free - $20",
                "description": "Walk through the historic district and visit key landmarks",
                "rating": 4.5,
                "best_time": "Morning"
            },
            {
                "name": f"{destination} Local Market Tour",
                "type": "Cultural",
                "duration": "2-3 hours",
                "cost": "$15-30",
                "description": "Experience local culture and taste traditional foods",
                "rating": 4.3,
                "best_time": "Afternoon"
            }
        ]
        
        # Add preferences-based activities
        if "adventure" in preferences.lower():
            activities.append({
                "name": f"{destination} Adventure Tour",
                "type": "Adventure",
                "duration": "Full Day",
                "cost": "$50-100",
                "description": "Exciting outdoor activities and adventure sports",
                "rating": 4.7,
                "best_time": "All Day"
            })
        
        if "culture" in preferences.lower():
            activities.append({
                "name": f"{destination} Museum Pass",
                "type": "Cultural",
                "duration": "Full Day",
                "cost": "$25-40",
                "description": "Access to multiple museums and cultural sites",
                "rating": 4.4,
                "best_time": "All Day"
            })
        
        return activities
    
    def _generate_enhanced_restaurants(self, destination: str, budget: float, duration_days: int) -> List[Dict]:
        """Generate enhanced restaurant suggestions"""
        budget_per_meal = budget / (duration_days * 3) if duration_days > 0 else budget / 3
        
        restaurants = [
            {
                "name": f"Local Traditional Restaurant",
                "cuisine": "Local Traditional",
                "price_range": f"${budget_per_meal * 0.8:.0f}-{budget_per_meal * 1.2:.0f} per person",
                "rating": 4.3,
                "specialties": ["Traditional dishes", "Local ingredients", "Authentic flavors"],
                "location": f"Central {destination}",
                "reservation_required": True
            },
            {
                "name": f"{destination} Street Food Market",
                "cuisine": "Street Food",
                "price_range": f"${budget_per_meal * 0.3:.0f}-{budget_per_meal * 0.7:.0f} per person",
                "rating": 4.5,
                "specialties": ["Authentic local flavors", "Quick bites", "Local specialties"],
                "location": f"Historic {destination}",
                "reservation_required": False
            }
        ]
        
        return restaurants
    
    def _generate_enhanced_transportation(self, destination: str, budget: float) -> List[Dict]:
        """Generate enhanced transportation suggestions"""
        return [
            {
                "type": "Airport Transfer",
                "option": "Taxi/Uber",
                "cost": "$20-40",
                "duration": "30-45 minutes",
                "description": "Convenient door-to-door service",
                "booking_required": False
            },
            {
                "type": "Local Transport",
                "option": "Public Transport Pass",
                "cost": "$10-20 per day",
                "duration": "Unlimited daily use",
                "description": "Cost-effective way to explore the city",
                "booking_required": False
            },
            {
                "type": "Intercity Travel",
                "option": "Train/Bus",
                "cost": "$15-50",
                "duration": "1-3 hours",
                "description": "Comfortable travel between cities",
                "booking_required": True
            }
        ]
    
    def _generate_enhanced_tips(self, destination: str, preferences: str) -> List[str]:
        """Generate enhanced travel tips"""
        tips = [
            f"Best time to visit {destination} is during spring or fall for pleasant weather",
            "Learn a few basic phrases in the local language",
            "Carry cash as some local places don't accept cards",
            "Download offline maps before your trip",
            "Check local customs and dress codes",
            "Keep copies of important documents"
        ]
        
        if "adventure" in preferences.lower():
            tips.append("Pack appropriate gear for outdoor activities")
        
        if "culture" in preferences.lower():
            tips.append("Research cultural sites and their visiting hours")
        
        return tips
    
    def _generate_weather_info(self, destination: str, start_date: str) -> Dict:
        """Generate weather information"""
        return {
            "temperature": "22°C - 28°C",
            "conditions": "Partly cloudy",
            "recommendation": "Pack light layers and an umbrella"
        }
    
    def _generate_packing_list(self, destination: str, preferences: str, duration_days: int) -> List[str]:
        """Generate packing list based on destination and preferences"""
        essentials = [
            "Passport and travel documents",
            "Comfortable walking shoes",
            "Weather-appropriate clothing",
            "Camera or smartphone",
            "Universal adapter",
            "Basic first aid kit"
        ]
        
        if "adventure" in preferences.lower():
            essentials.extend(["Hiking boots", "Outdoor gear", "Water bottle"])
        
        if "culture" in preferences.lower():
            essentials.extend(["Modest clothing", "Guidebook", "Notebook"])
        
        return essentials

# Initialize the trip planner
trip_planner = VertexAITripPlanner()
