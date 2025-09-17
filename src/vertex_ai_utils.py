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
from weather_utils import weather_service

print("Current path:", os.getcwd())
log_file = "logs/app.log"

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

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_config_value(env_var, secret_key, default):
    
    try:
        return os.getenv(env_var, st.secrets.get(secret_key, default))
    except:
        return os.getenv(env_var, default)
    
class VertexAITripPlanner:
    def __init__(self):
        # Load configuration from environment or secrets with fallback

        self.project_id = get_config_value("VERTEX_AI_PROJECT_ID", "VERTEX_AI_PROJECT_ID", "your-project-id")
        self.location = get_config_value("VERTEX_AI_LOCATION", "VERTEX_AI_LOCATION", "us-central1")
        self.model_name = get_config_value("VERTEX_AI_MODEL", "VERTEX_AI_MODEL", "gemini-pro")
        
        # Check if we have valid configuration
        self.is_configured = self.project_id != "your-project-id"
        
        if not self.is_configured:
            st.warning("⚠️ Vertex AI not configured. Using demo mode with mock data.")
            self.model = None
        else:
            try:
                # Initialize Vertex AI
                self._initialize_vertex_ai()
                self.model = GenerativeModel(self.model_name,generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 1024
                })
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
                                budget: float, preferences: str, currency: str = "USD", currency_symbol: str = "$") -> Dict:
        """
        Generate AI-powered trip suggestions using Vertex AI with weather integration
        """
        weather_data = weather_service.get_weather_forecast(destination, start_date, end_date)

        if not self.is_configured or not self.model:
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences, currency, currency_symbol)
        
        try:
            # Create a comprehensive prompt for the AI
            prompt = self._create_trip_planning_prompt(destination, start_date, end_date, budget, preferences, currency, currency_symbol, weather_data)
            
            generation_config = GenerationConfig(
                max_output_tokens=20000,  # or higher if needed
                temperature=0.7,
                top_p=0.95,
            )
            # Generate response using Vertex AI
            response = self.model.generate_content(prompt, generation_config=generation_config)

            try:
                with open("logs/prompts/output.txt", "w", encoding="utf-8") as f:
                    f.write(prompt)
            except Exception as e:
                logger.warning(f"Could not write prompt to prompts/output.txt: {e}")
                    

            if response and response.text:
                try:
                    with open("logs/responses/output.txt", "w", encoding="utf-8") as f:
                        f.write(response.text)
                except Exception as e:
                    logger.warning(f"Could not write response to reponses/output.txt: {e}")
                        # Parse the AI response
                result= self._parse_ai_response(response.text, destination, start_date, end_date, budget, currency, currency_symbol)
                result['weather_data'] = weather_data

                return result
            
            else:
                logger.warning("Empty response from Vertex AI, falling back to mock data")
                return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences, currency, currency_symbol, weather_data)
                
        except Exception as e:
            logger.error(f"Error generating trip suggestions with Vertex AI: {str(e)}")
            st.warning(f"⚠️ AI generation failed: {str(e)}. Using enhanced mock data.")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences, currency, currency_symbol, weather_data)
    
    def _create_trip_planning_prompt(self, destination: str, start_date: str, end_date: str, 
                                   budget: float, preferences: str, currency: str = "USD", currency_symbol: str = "$", weather_data: Dict = None) -> str:
        """Create a comprehensive prompt for trip planning including weather data"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        duration_days = (end_dt - start_dt).days + 1
        weather_context = ""

        if weather_data and weather_data.get('daily_forecast'):
          weather_context = "\n\n**WEATHER FORECAST**\n"
          weather_context += f"Weather conditions for {destination} during your trip:\n"

          summary = weather_data.get('summary', {})

          weather_context += f"Overall: {summary.get('avg_temperature', 'N/A')} with {summary.get('conditions', 'varied')} conditions\n"

          weather_context += "Daily forecast:\n"

          for day in weather_data['daily_forecast'][:7]:  # Limit to 7 days to save prompt space
              date_str = day.get('date', '')

              day_name = day.get('day_name', '')

              temp_high = day.get('temperature', {}).get('high', 'N/A')

              temp_low = day.get('temperature', {}).get('low', 'N/A')

              description = day.get('description', 'N/A')

              precipitation = day.get('precipitation', 0)

              weather_context += f"- {day_name} ({date_str}): {description}, {temp_high}°C/{temp_low}°C"

              if precipitation > 20:
                weather_context += f", {precipitation}% chance of rain"
              weather_context += "\n"

# Weather recommendations

        if summary.get('recommendations'):
          weather_context += f"\nWeather recommendations: {', '.join(summary['recommendations'][:3])}\n" 
        
        prompt = f"""
You are a professional travel planner. Create a detailed, realistic, and budget-conscious travel plan in JSON format for the request below.
**IMPORTANT: Consider the weather forecast provided and adjust all recommendations accordingly.**
**TRIP DETAILS**
- Destination: {destination}
- Dates: {start_date} to {end_date} ({duration_days} days)
- Budget: {currency_symbol}{budget:,.2f} {currency}
- Preferences: {preferences}
{weather_context}

**RESPONSE INSTRUCTIONS**
Respond ONLY with a valid JSON object.
- Do NOT include markdown, code blocks, or explanations.
- JSON must be compact and properly formatted.
- Follow the exact structure and field names below.
- Ensure all fields are filled with realistic values.
- **WEATHER ADAPTATION**: Adjust all recommendations based on the weather forecast:

  * Suggest indoor activities for rainy/stormy days

  * Recommend appropriate clothing and gear

  * Adjust activity timing based on temperature

  * Include weather-specific tips and precautions

**REQUIRED JSON STRUCTURE**

{{
  "destination": "{destination}",
  "duration": "{duration_days} days",
  "budget": {budget},
  "budget_breakdown": {{
    "accommodation": "amount",
    "food": "amount",
    "activities": "amount",
    "transportation": "amount"
  }},
  "itinerary": [
    {{
      "day": 1,
      "date": "{start_date}",
      "day_name": "Day of week",
      "weather_conditions": "Brief weather note for this day",
      "activities": ["weather-appropriate activity 1", "weather-appropriate activity 2"],
      "weather_tips": ["tip for this specific day based on weather"],
      "meals": {{
        "breakfast": "meal suggestion",
        "lunch": "meal suggestion",
        "dinner": "meal suggestion"
      }}
    }}
    // Add more days accordingly, each with weather-specific adaptations
  ],
  "accommodations": [
    {{
      "name": "Hotel/B&B name",
      "type": "Hotel/B&B/Airbnb",
      "price_range": "price per night",
      "rating": 4.5,
      "amenities": ["amenity1", "amenity2"],
      "location": "area",
      "description": "short description",
      "weather_suitability": "How well-suited for expected weather"
    }}
    // Include 2-3 options
  ],
  "activities": [
    {{
      "name": "Activity name",
      "type": "Sightseeing/Cultural/Adventure",
      "duration": "time required",
      "cost": "cost range",
      "description": "brief overview",
      "rating": 4.5,
      "best_time": "best time of day or season",
      "weather_dependency": "high/medium/low - how weather affects this activity",
      "alternative_if_bad_weather": "backup plan if weather is poor"
    }}
    // Include 5-8 activities with weather considerations
  ],
  "restaurants": [
    {{
      "name": "Restaurant name",
      "cuisine": "type",
      "price_range": "per person",
      "rating": 4.3,
      "specialties": ["dish1", "dish2"],
      "location": "area",
      "reservation_required": true,
      "weather_notes": "outdoor seating, indoor dining, etc."
    }}
    // Include 3-5 options 
  ],
  "transportation": [
    {{
      "type": "Airport Transfer/Local/Intercity",
      "option": "e.g. taxi, train",
      "cost": "range",
      "duration": "time required",
      "description": "brief info",
      "booking_required": true,
      "weather_considerations": "How weather might affect this transport"
    }}
    // Include key transport modes
  ],
  "tips": [
    "weather-specific practical tip 1",
    "weather-specific practical tip 2", 
    "practical tip 3"
  ],
  "weather_adaptations": {{
  "rainy_day_activities": ["indoor activity 1", "indoor activity 2"],
  "hot_weather_tips": ["tip for hot days"],
  "cold_weather_tips": ["tip for cold days"],
  "packing_weather_essentials": ["weather-specific packing item 1", "item 2"]

   }},

   "packing_list": [

   "weather-appropriate essential item 1",
   "weather-appropriate essential item 2", 
  "weather-appropriate essential item 3"

  // Include weather-specific items based on forecast
   ]
}}

Only output the JSON. Nothing else.
"""
        

        
        return prompt
    
    def _parse_ai_response(self, response_text: str, destination: str, start_date: str, 
                          end_date: str, budget: float, currency: str = "USD", currency_symbol: str = "$") -> Dict:
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
            return self._validate_and_enhance_response(trip_data, destination, start_date, end_date, budget, currency, currency_symbol)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed", currency, currency_symbol)
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, "AI parsing failed", currency, currency_symbol)
    
    def _validate_and_enhance_response(self, trip_data: Dict, destination: str, start_date: str, 
                                     end_date: str, budget: float, currency: str = "USD", currency_symbol: str = "$") -> Dict:
        """Validate and enhance the AI response"""
        # Ensure required fields exist
        if 'destination' not in trip_data:
            trip_data['destination'] = destination
        
        if 'budget' not in trip_data:
            trip_data['budget'] = budget
        
        # Ensure currency information exists
        if 'currency' not in trip_data:
            trip_data['currency'] = currency
        if 'currency_symbol' not in trip_data:
            trip_data['currency_symbol'] = currency_symbol
        
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
        
        if 'weather_adaptations' not in trip_data:
            trip_data['weather_adaptations'] = {}
        
        if 'packing_list' not in trip_data:
            trip_data['packing_list'] = []
        
        return trip_data
    
    def _generate_enhanced_mock_suggestions(self, destination: str, start_date: str, end_date: str, 
                                          budget: float, preferences: str, currency: str = "USD", currency_symbol: str = "$", weather_data: Dict = None) -> Dict:
        """Generate enhanced mock suggestions with more realistic data"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        duration_days = (end_dt - start_dt).days + 1
        
        # Budget allocation
        accommodation_budget = budget * 0.4
        food_budget = budget * 0.3
        activities_budget = budget * 0.2
        transport_budget = budget * 0.1
        itinerary = self._generate_weather_adapted_itinerary(destination, start_date, end_date, preferences, weather_data)

        suggestions = {
            "destination": destination,
            "duration": f"{duration_days} days",
            "budget": budget,
            "currency": currency,
            "currency_symbol": currency_symbol,
            "budget_breakdown": {
                "accommodation": f"{currency_symbol}{accommodation_budget:,.2f}",
                "food": f"{currency_symbol}{food_budget:,.2f}",
                "activities": f"{currency_symbol}{activities_budget:,.2f}",
                "transportation": f"{currency_symbol}{transport_budget:,.2f}"
            },
            "itinerary": self._generate_enhanced_itinerary(destination, start_date, end_date, preferences),
            "accommodations": self._generate_enhanced_accommodations(destination, budget, duration_days, currency_symbol),
            "activities": self._generate_enhanced_activities(destination, preferences, activities_budget, currency_symbol),
            "restaurants": self._generate_enhanced_restaurants(destination, food_budget, duration_days, currency_symbol),
            "transportation": self._generate_enhanced_transportation(destination, transport_budget, currency_symbol),
            "tips": self._generate_enhanced_tips(destination, preferences),
            "weather_adaptations": self._generate_weather_adaptations(weather_data),
            "packing_list": self._generate_packing_list(destination, preferences, duration_days),
            "weather_data": weather_data
        }
        
        return suggestions

    def _generate_weather_adapted_itinerary(self, destination: str, start_date: str, end_date: str, preferences: str, weather_data: Dict) -> List[Dict]:
      """Generate daily itinerary adapted to weather conditions"""

      start_dt = datetime.strptime(start_date, "%Y-%m-%d")

      end_dt = datetime.strptime(end_date, "%Y-%m-%d")

      itinerary = []

      current_date = start_dt

      day_num = 1

# Get daily weather forecasts

      daily_weather_map = {}

      if weather_data and 'daily_forecast' in weather_data:
        for day_weather in weather_data['daily_forecast']:
          date_key = day_weather.get('date', '')

          daily_weather_map[date_key] = day_weather

      while current_date <= end_dt:
        date_str = current_date.strftime('%Y-%m-%d')

        day_weather = daily_weather_map.get(date_str, {})

# Get weather-appropriate activities

        activities = self._get_weather_appropriate_activities(destination, day_num, preferences, day_weather)

        weather_tips = self._get_daily_weather_tips(day_weather)

        weather_conditions = day_weather.get('description', 'Pleasant weather expected')

        if day_weather.get('temperature'):
          temp_high = day_weather['temperature'].get('high', 'N/A')

          temp_low = day_weather['temperature'].get('low', 'N/A')

          weather_conditions += f" (High: {temp_high}°C, Low: {temp_low}°C)"

        itinerary.append({

             "day": day_num,

             "date": date_str,

             "day_name": current_date.strftime("%A"),

            "weather_conditions": weather_conditions,

            "activities": activities,

            "weather_tips": weather_tips,

            "meals": self._get_meals_for_day(destination, day_num)

           })

        current_date += timedelta(days=1)

        day_num += 1

      return itinerary    
      
    def _get_weather_appropriate_activities(self, destination: str, day: int, preferences: str, day_weather: Dict) -> List[str]:
      """Get activities appropriate for the day's weather"""

      base_activities = []

      precipitation = day_weather.get('precipitation', 0)

      temp_high = day_weather.get('temperature', {}).get('high', 25)

# Weather-based activity selection

      if precipitation > 50:
        base_activities = [

f"Morning: Visit indoor attractions in {destination}",

f"Afternoon: Explore museums or shopping centers",

f"Evening: Indoor dining and entertainment"

]

      elif temp_high > 30:
        base_activities = [

f"Early morning: Outdoor sightseeing in {destination}",

f"Midday: Indoor activities during peak heat",

f"Evening: Outdoor activities as temperature cools"

]

      elif temp_high < 10:
        base_activities = [

f"Morning: Indoor cultural activities",

f"Afternoon: Brief outdoor sightseeing with warm clothing",

f"Evening: Cozy indoor experiences"

]

      else: 
        base_activities = [

f"Morning: Explore {destination} city center",

f"Afternoon: Visit local attractions",

f"Evening: Enjoy local cuisine and nightlife"

]

# Add preference-based activities

      if "adventure" in preferences.lower() and precipitation < 30 and temp_high > 10:
        base_activities.insert(1, f"Adventure activity in {destination}")

      if "culture" in preferences.lower():

        base_activities.insert(1, f"Visit museums and cultural sites")

      if "nature" in preferences.lower() and precipitation < 30:

        base_activities.insert(1, f"Explore natural attractions near {destination}")

      return base_activities  

    def _get_daily_weather_tips(self, day_weather: Dict) -> List[str]:
      """Get weather-specific tips for the day"""

      tips = []

      precipitation = day_weather.get('precipitation', 0)

      temp_high = day_weather.get('temperature', {}).get('high', 25)

      temp_low = day_weather.get('temperature', {}).get('low', 15)

      if precipitation > 50:
        tips.append("Carry waterproof clothing and umbrella")

        tips.append("Plan indoor backup activities")

      elif precipitation > 20:

        tips.append("Keep light rain gear handy")

      if temp_high > 30:

        tips.append("Stay hydrated and seek shade during midday")

        tips.append("Wear light, breathable clothing")

      elif temp_high < 10:

        tips.append("Dress in warm layers")

        tips.append("Plan shorter outdoor activities")

      if temp_high - temp_low > 15:

        tips.append("Layer clothing for temperature changes throughout the day")

      if not tips:

        tips.append("Perfect weather for outdoor activities!")

      return tips[:3]  

    def _generate_weather_aware_activities(self, destination: str, preferences: str, budget: float, currency_symbol: str = "$", weather_data: Dict = None) -> List[Dict]:
      """Generate activity suggestions with weather awareness"""

      activities = [

          {

          "name": f"Explore {destination} Historic Center",

          "type": "Sightseeing",

          "duration": "Half Day",

           "cost": f"Free - {currency_symbol}20",

           "description": "Walk through the historic district and visit key landmarks",

           "rating": 4.5,

           "best_time": "Morning (weather permitting)",

           "weather_dependency": "medium",

          "alternative_if_bad_weather": "Visit covered markets or indoor heritage sites"

          },

          {

         "name": f"{destination} Local Market Tour",

        "type": "Cultural",

        "duration": "2-3 hours",

         "cost": f"{currency_symbol}15-30",

         "description": "Experience local culture and taste traditional foods",

          "rating": 4.3,

         "best_time": "Morning to avoid crowds and heat",

         "weather_dependency": "low",

          "alternative_if_bad_weather": "Visit covered markets or food halls"

         }

          ]

       # Add weather-specific activities

      if weather_data and 'summary' in weather_data:
        conditions = weather_data['summary'].get('conditions', '').lower()

      if 'rainy' in conditions:

        activities.append({

        "name": f"{destination} Museum Complex",

        "type": "Cultural/Indoor",

          "duration": "Full Day",

         "cost": f"{currency_symbol}25-50",

         "description": "Perfect rainy day activity with extensive indoor exhibits",

        "rating": 4.6,

        "best_time": "All day",

         "weather_dependency": "low",

         "alternative_if_bad_weather": "Primary recommendation for rainy weather"

          })

      elif 'hot' in conditions:
        activities.append({

"name": f"Early Morning {destination} Walking Tour",

"type": "Sightseeing",

"duration": "3-4 hours",

"cost": f"{currency_symbol}20-40",

"description": "Beat the heat with early morning exploration",

"rating": 4.4,

"best_time": "Early morning (6-9 AM)",

"weather_dependency": "high",

"alternative_if_bad_weather": "Switch to air-conditioned venues"

})

# Add preference-based activities

      if "adventure" in preferences.lower():
        activities.append({
"name": f"{destination} Adventure Experience",

"type": "Adventure",

"duration": "Full Day",

"cost": f"{currency_symbol}50-100",

"description": "Exciting outdoor activities (weather dependent)",

"rating": 4.7,

"best_time": "Weather dependent",

"weather_dependency": "high",

"alternative_if_bad_weather": "Indoor climbing or adventure centers"

})

      if "culture" in preferences.lower():
        activities.append({

"name": f"{destination} Cultural Heritage Tour",

"type": "Cultural",

"duration": "Half Day",

"cost": f"{currency_symbol}25-40",

"description": "Deep dive into local culture and history",

"rating": 4.4,

"best_time": "All day",

"weather_dependency": "low",

"alternative_if_bad_weather": "Indoor cultural centers and galleries"

})

        return activities  

    def _generate_weather_enhanced_tips(self, destination: str, preferences: str, weather_data: Dict) -> List[str]:
      """Generate travel tips enhanced with weather information"""

      tips = [

f"Check weather updates daily for {destination}",

"Download offline maps before your trip",

"Keep copies of important documents"

]

      if weather_data and 'summary' in weather_data:
        summary = weather_data['summary']

        recommendations = summary.get('recommendations', [])

# Add weather-specific tips

        if recommendations:
          tips.extend(recommendations[:2]) # Add top 2 weather recommendations

        conditions = summary.get('conditions', '').lower()

        if 'rainy' in conditions:

          tips.append("Pack extra plastic bags for electronics and documents")

          tips.append("Research indoor activities as backup options")

        elif 'hot' in conditions:

          tips.append("Plan activities for early morning and evening")

          tips.append("Stay in shaded areas during midday heat")

        elif 'cold' in conditions:

          tips.append("Layer clothing for easy temperature adjustment")

          tips.append("Keep extremities warm with proper accessories")

      return tips[:6] # Limit to 6 tips

    def _generate_weather_adaptations(self, weather_data: Dict) -> Dict:
      """Generate weather-specific adaptations"""

      adaptations = {

         "rainy_day_activities": [

           "Museum visits",

          "Shopping centers",

            "Indoor cultural sites",

           "Cooking classes"

           ],

         "hot_weather_tips": [

         "Start activities early in the morning",

         "Take midday breaks in air conditioning",

          "Stay hydrated throughout the day"

          ],
          "cold_weather_tips": [

"Dress in layers",

"Keep extremities warm",

"Plan shorter outdoor activities"

],

"packing_weather_essentials": [

"Weather-appropriate clothing",

"Comfortable walking shoes",

"Weather protection gear"

]

}

      if weather_data and 'summary' in weather_data:
        conditions = weather_data['summary'].get('conditions', '').lower()
        if 'rainy' in conditions:
          adaptations["packing_weather_essentials"].extend([

"Waterproof jacket",

"Umbrella",

"Waterproof bag covers"

])

        elif 'hot' in conditions:
          adaptations["packing_weather_essentials"].extend([

"Sunscreen SPF 30+",

"Wide-brimmed hat",

"Light, breathable fabrics"

])

        elif 'cold' in conditions:
          adaptations["packing_weather_essentials"].extend([

"Warm layers",

"Insulated jacket",

"Gloves and warm accessories"

])

      return adaptations 

    def _generate_weather_packing_list(self, destination: str, preferences: str, duration_days: int, weather_data: Dict) -> List[str]:
      """Generate packing list with weather-specific items"""

      essentials = [
        "Passport and travel documents",

"Comfortable walking shoes",

"Camera or smartphone",

"Universal adapter",

"Basic first aid kit"

]


      if weather_data and 'summary' in weather_data:
        conditions = weather_data['summary'].get('conditions', '').lower()

        avg_temp = weather_data['summary'].get('avg_temperature', '')

        if 'rainy' in conditions or any('rain' in day.get('description', '').lower() for day in weather_data.get('daily_forecast', [])):
          essentials.extend([

"Waterproof jacket or raincoat",

"Umbrella",

"Waterproof bags for electronics",

"Extra socks and undergarments"

])

          if 'hot' in conditions or '30' in avg_temp:
            essentials.extend([

"Sunscreen SPF 30+",

"Sunglasses",

"Light, breathable clothing",

"Wide-brimmed hat",

"Insulated water bottle"

])

          if 'cold' in conditions or any(temp < 10 for temp in [day.get('temperature', {}).get('low', 20) for day in weather_data.get('daily_forecast', [])]):
            essentials.extend([

"Warm layers and jackets",

"Gloves and hat",

"Warm socks and thermal wear",

"Scarf or neck warmer"

])

# Add preference-based items

          if "adventure" in preferences.lower():
            essentials.extend(["Hiking boots", "Outdoor gear", "Quick-dry clothing"])

          if "culture" in preferences.lower():
            essentials.extend(["Modest clothing for religious sites", "Guidebook", "Notebook"])

      return essentials

   

    def _generate_enhanced_itinerary(self, destination: str, start_date: str, end_date: str, preferences: str, weather_data: Dict) -> List[Dict]:
        """Generate enhanced daily itinerary"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        itinerary = []
        current_date = start_dt
        day_num=1
        daily_weather_map = {}

        if weather_data and 'daily_forecast' in weather_data:
          for day_weather in weather_data['daily_forecast']:
            date_key = day_weather.get('date', '')
            daily_weather_map[date_key] = day_weather

        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            day_weather = daily_weather_map.get(date_str, {})
            # Generate activities based on preferences
            activities = self._get_weather_appropriate_activities(destination, day_num, preferences, day_weather)
            weather_tips = self._get_daily_weather_tips(day_weather)
            weather_conditions = day_weather.get('description', 'Pleasant weather expected')
            if day_weather.get('temperature'):
              temp_high = day_weather['temperature'].get('high', 'N/A')
              temp_low = day_weather['temperature'].get('low', 'N/A')
              weather_conditions += f" (High: {temp_high}°C, Low: {temp_low}°C)"

            itinerary.append({
                "day": day_num,
                "date": current_date.strftime("%Y-%m-%d"),
                "day_name": current_date.strftime("%A"),
                "weather_conditions": weather_conditions,
                "activities": activities,
                "weather_tips": weather_tips,
                "meals": self._get_meals_for_day(destination, day_num)
            })
            
            current_date += timedelta(days=1)
            day_num += 1
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
    
    def _generate_enhanced_accommodations(self, destination: str, budget: float, duration_days: int, currency_symbol: str = "$", weather_data: Dict = None) -> List[Dict]:
      """Generate accommodation suggestions with weather considerations"""

      budget_per_night = budget * 0.4 / duration_days if duration_days > 0 else budget * 0.4

      if budget_per_night < 50:
        budget_level = "budget"

        price_range = f"{currency_symbol}{budget_per_night * 0.8:.0f} - {currency_symbol}{budget_per_night * 1.2:.0f}"

      elif budget_per_night < 150:
        budget_level = "mid-range"

        price_range = f"{currency_symbol}{budget_per_night * 0.8:.0f} - {currency_symbol}{budget_per_night * 1.2:.0f}"

      else:

        budget_level = "luxury"

        price_range = f"{currency_symbol}{budget_per_night * 0.8:.0f} - {currency_symbol}{budget_per_night * 1.2:.0f}"

# Base amenities

      base_amenities = ["WiFi", "Breakfast"]

      weather_suitability = "Good for all weather conditions"

# Add weather-specific amenities and considerations

      if weather_data and 'summary' in weather_data:
        conditions = weather_data['summary'].get('conditions', '').lower()

        if 'rainy' in conditions:
          base_amenities.extend(["Covered parking", "Indoor facilities"])
          weather_suitability = "Excellent for rainy weather with indoor amenities"

        elif 'hot' in conditions:

          base_amenities.extend(["Air conditioning", "Pool", "Spa"])

          weather_suitability = "Perfect for hot weather with cooling amenities"

        elif 'cold' in conditions:

           base_amenities.extend(["Heating", "Fireplace", "Hot tub"])

           weather_suitability = "Ideal for cold weather with warming amenities"

        else:

           base_amenities.extend(["Pool", "Gym"])

      accommodations = [

{

"name": f"Best {budget_level.title()} Hotel in {destination}",

"type": "Hotel",

"price_range": f"{price_range} per night",

"rating": 4.5,

"amenities": base_amenities[:6], # Limit amenities

"location": f"Central {destination}",

"description": f"Comfortable {budget_level} accommodation with excellent amenities",

"weather_suitability": weather_suitability

},

{

"name": f"Cozy {budget_level.title()} B&B",

"type": "Bed & Breakfast",

"price_range": f"{price_range} per night", 

"rating": 4.2,

"amenities": ["WiFi", "Breakfast", "Garden", "Kitchen"],

"location": f"Quiet neighborhood in {destination}",

"description": f"Charming {budget_level} B&B with personal touch",

"weather_suitability": "Comfortable indoor spaces for any weather"

}

]

      return accommodations
    
    def _generate_enhanced_activities(self, destination: str, preferences: str, budget: float, currency_symbol: str = "$") -> List[Dict]:
        """Generate enhanced activity suggestions"""
        activities = [
            {
                "name": f"Explore {destination} Historic Center",
                "type": "Sightseeing",
                "duration": "Half Day",
                "cost": f"Free - {currency_symbol}20",
                "description": "Walk through the historic district and visit key landmarks",
                "rating": 4.5,
                "best_time": "Morning"
            },
            {
                "name": f"{destination} Local Market Tour",
                "type": "Cultural",
                "duration": "2-3 hours",
                "cost": f"{currency_symbol}15-30",
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
                "cost": f"{currency_symbol}50-100",
                "description": "Exciting outdoor activities and adventure sports",
                "rating": 4.7,
                "best_time": "All Day"
            })
        
        if "culture" in preferences.lower():
            activities.append({
                "name": f"{destination} Museum Pass",
                "type": "Cultural",
                "duration": "Full Day",
                "cost": f"{currency_symbol}25-40",
                "description": "Access to multiple museums and cultural sites",
                "rating": 4.4,
                "best_time": "All Day"
            })
        
        return activities
    
    def _generate_enhanced_restaurants(self, destination: str, budget: float, duration_days: int, currency_symbol: str = "$") -> List[Dict]:
        """Generate enhanced restaurant suggestions"""
        budget_per_meal = budget / (duration_days * 3) if duration_days > 0 else budget / 3
        
        restaurants = [
            {
                "name": f"Local Traditional Restaurant",
                "cuisine": "Local Traditional",
                "price_range": f"{currency_symbol}{budget_per_meal * 0.8:.0f}-{budget_per_meal * 1.2:.0f} per person",
                "rating": 4.3,
                "specialties": ["Traditional dishes", "Local ingredients", "Authentic flavors"],
                "location": f"Central {destination}",
                "reservation_required": True,
                "weather_notes": "Indoor seating available, cozy atmosphere"
            },
            {
                "name": f"{destination} Street Food Market",
                "cuisine": "Street Food",
                "price_range": f"{currency_symbol}{budget_per_meal * 0.3:.0f}-{budget_per_meal * 0.7:.0f} per person",
                "rating": 4.5,
                "specialties": ["Authentic local flavors", "Quick bites", "Local specialties"],
                "location": f"Historic {destination}",
                "reservation_required": False,
                "weather_notes": "Covered market areas available"
            }
        ]
        
        return restaurants
    
    def _generate_enhanced_transportation(self, destination: str, budget: float, currency_symbol: str = "$") -> List[Dict]:
        """Generate enhanced transportation suggestions"""
        return [
            {
                "type": "Airport Transfer",
                "option": "Taxi/Uber",
                "cost": f"{currency_symbol}20-40",
                "duration": "30-45 minutes",
                "description": "Convenient door-to-door service",
                "booking_required": False,
                "weather_considerations": "Covered transport, good for all weather"
            },
            {
                "type": "Local Transport",
                "option": "Public Transport Pass",
                "cost": f"{currency_symbol}10-20 per day",
                "duration": "Unlimited daily use",
                "description": "Cost-effective way to explore the city",
                "booking_required": False,
                "weather_considerations": "Indoor stations and covered waiting areas"
            },
            {
                "type": "Intercity Travel",
                "option": "Train/Bus",
                "cost": f"{currency_symbol}15-50",
                "duration": "1-3 hours",
                "description": "Comfortable travel between cities",
                "booking_required": True,
                "weather_considerations": "Climate-controlled vehicles"
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
    
    def generate_chat_response(self, user_message: str, trip_context: Dict, user_id: int = None, trip_id: int = None) -> str:
        """Generate AI response for trip refinement chat"""
        if not self.is_configured or not self.model:
            return self._generate_fallback_chat_response(user_message, trip_context)
        
        try:
            # Create a context-aware prompt for chat
            prompt = self._create_chat_prompt(user_message, trip_context)
            
            generation_config = GenerationConfig(
                max_output_tokens=2048,  # Increased from 1024
                temperature=0.7,
                top_p=0.95,
            )
            
            # Generate response using Vertex AI
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            if response and response.text:
                return response.text.strip()
            else:
                return self._generate_fallback_chat_response(user_message, trip_context)
                
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            return self._generate_fallback_chat_response(user_message, trip_context)
    
    def _create_chat_prompt(self, user_message: str, trip_context: Dict) -> str:
        """Create a context-aware prompt for chat interactions"""
        destination = trip_context.get('destination', 'Unknown')
        budget = trip_context.get('budget', 0)
        currency_symbol = trip_context.get('currency_symbol', '$')
        duration = trip_context.get('duration', 'Unknown')
        preferences = trip_context.get('preferences', 'General travel')
        
        # Get current itinerary summary
        itinerary_summary = ""
        if 'itinerary' in trip_context and trip_context['itinerary']:
            itinerary_summary = "Current itinerary includes: "
            for day in trip_context['itinerary'][:3]:  # Show first 3 days
                if isinstance(day, dict) and 'activities' in day:
                    itinerary_summary += f"Day {day.get('day', 'N/A')}: {', '.join(day['activities'][:2])}; "
        
        # Get current activities summary
        activities_summary = ""
        if 'activities' in trip_context and trip_context['activities']:
            activities_summary = "Current activities: "
            for activity in trip_context['activities'][:3]:  # Show first 3 activities
                if isinstance(activity, dict):
                    activities_summary += f"{activity.get('name', 'Activity')}, "
                    weather_context = ""

                    if 'weather_data' in trip_context and trip_context['weather_data']:
                      weather_data = trip_context['weather_data']

                      if 'summary' in weather_data:
                        summary = weather_data['summary']

                        weather_context = f"\nWeather forecast: {summary.get('avg_temperature', 'N/A')} with {summary.get('conditions', 'varied')} conditions" 
        prompt = f"""
You are an expert travel planner helping to refine a trip plan. Be conversational, helpful, and specific.
Consider the weather forecast when making recommendations.
CURRENT TRIP CONTEXT:
- Destination: {destination}
- Budget: {currency_symbol}{budget:,.2f}
- Duration: {duration}
- Preferences: {preferences}
- {itinerary_summary}
- {activities_summary}
- {weather_context}

USER REQUEST: "{user_message}"

INSTRUCTIONS:
1. Respond in a conversational, helpful tone
2. Be specific about what changes you can make
3. If the request is about budget, provide specific cost adjustments and alternatives
4. If about activities, suggest specific alternatives with details and weather considerations
5. If about accommodations, recommend specific types or areas with reasons including weather suitability
6. If about food, suggest specific restaurants or experiences
7. Provide detailed, actionable suggestions (3-4 sentences minimum)
8. Always end with a question to encourage further refinement
9. If the user wants to finalize changes, explain what will be updated
10. Be encouraging and show enthusiasm for their travel plans
11.Consider weather conditions in all recommendations
12. Include weather-appropriate recommendations when relevant

RESPONSE FORMAT:
Provide a helpful, detailed response that addresses the user's request and offers specific suggestions for improvement. Make sure to give complete information and be thorough in your recommendations.
"""
        
        return prompt
    
    def _generate_fallback_chat_response(self, user_message: str, trip_context: Dict) -> str:
        """Generate fallback response when AI is not available"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['budget', 'cheaper', 'expensive', 'cost', 'money']):
            return "I can help you adjust the budget! I can suggest more budget-friendly accommodations, free activities, or local dining options. What specific budget changes would you like to make?"
        elif any(word in message_lower for word in ['budget', 'cheaper', 'expensive', 'cost', 'money']):

           return f"I can help you adjust the budget! I can suggest more budget-friendly accommodations, free activities, or local dining options.{weather_note} What specific budget changes would you like to make?"

        elif any(word in message_lower for word in ['adventure', 'adventurous', 'exciting', 'thrilling']):

           return f"Great! I can add more adventurous activities like hiking, water sports, or extreme experiences.{weather_note} What type of adventure activities interest you most?"

        elif any(word in message_lower for word in ['culture', 'cultural', 'museum', 'historical']):

           return f"I'd love to add more cultural experiences! I can include museum visits, historical sites, local festivals, or cultural workshops.{weather_note} What cultural aspects interest you?"

        elif any(word in message_lower for word in ['relax', 'relaxing', 'spa', 'peaceful']):

           return f"I can make your trip more relaxing by adding spa visits, beach time, or quiet retreats.{weather_note} Would you like me to focus on wellness activities?"

        elif any(word in message_lower for word in ['food', 'restaurant', 'dining', 'cuisine']):

           return f"I can enhance your food experience with local restaurants, food tours, cooking classes, or street food adventures.{weather_note} What type of culinary experience interests you?"

        elif any(word in message_lower for word in ['weather', 'rain', 'hot', 'cold', 'climate']):

          return f"I can definitely adjust your itinerary based on the weather forecast! I can suggest indoor alternatives for rainy days, early morning activities for hot weather, or cozy indoor experiences for cold weather. What weather concerns do you have?"

        elif any(word in message_lower for word in ['finalize', 'final', 'done', 'complete', 'update']):

          return f"Perfect! I can help you finalize these changes.{weather_note} What specific modifications would you like me to apply to your trip plan?"    
        
        elif any(word in message_lower for word in ['adventure', 'adventurous', 'exciting', 'thrilling']):
            return "Great! I can add more adventurous activities like hiking, water sports, or extreme experiences. What type of adventure activities interest you most?"
        
        elif any(word in message_lower for word in ['culture', 'cultural', 'museum', 'historical']):
            return "I'd love to add more cultural experiences! I can include museum visits, historical sites, local festivals, or cultural workshops. What cultural aspects interest you?"
        
        elif any(word in message_lower for word in ['relax', 'relaxing', 'spa', 'peaceful']):
            return "I can make your trip more relaxing by adding spa visits, beach time, or quiet retreats. Would you like me to focus on wellness activities?"
        
        elif any(word in message_lower for word in ['food', 'restaurant', 'dining', 'cuisine']):
            return "I can enhance your food experience with local restaurants, food tours, cooking classes, or street food adventures. What type of culinary experience interests you?"
        
        elif any(word in message_lower for word in ['finalize', 'final', 'done', 'complete', 'update']):
            return "Perfect! I can help you finalize these changes. What specific modifications would you like me to apply to your trip plan?"
        
        else:
            return "I understand you'd like to refine your trip! I can help adjust the budget, activities, accommodations, or dining options. What specific changes would you like to make?"
    
    def calculate_chat_credits(self, user_message: str, response_length: int = 0) -> int:
        """Calculate credits used for chat interaction"""
        # Base credits for chat interaction
        base_credits = 1
        
        # Additional credits based on message complexity
        additional_credits = 0
        
        # Check for complex requests
        if any(word in user_message.lower() for word in ['budget', 'cost', 'money', 'expensive', 'cheaper']):
            additional_credits += 1
        
        if any(word in user_message.lower() for word in ['itinerary', 'schedule', 'activities', 'plan']):
            additional_credits += 1
        
        if any(word in user_message.lower() for word in ['accommodation', 'hotel', 'stay', 'lodging']):
            additional_credits += 1
        
        if any(word in user_message.lower() for word in ['restaurant', 'food', 'dining', 'cuisine']):
            additional_credits += 1
        
        # Credits based on response length
        if response_length > 200:
            additional_credits += 1
        
        return base_credits + additional_credits

# Initialize the trip planner
trip_planner = VertexAITripPlanner()
