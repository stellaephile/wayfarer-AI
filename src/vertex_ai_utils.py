import streamlit as st
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
    
    def generate_trip_suggestions(self, destination: str, start_date: str, end_date: str, 
                                budget: float, preferences: str) -> Dict:
        """
        Generate AI-powered trip suggestions using Vertex AI
        """
        if not self.is_configured:
            return self._generate_mock_suggestions(destination, start_date, end_date, budget, preferences)
        
        try:
            # TODO: Implement actual Vertex AI call here
            # For now, return enhanced mock data
            return self._generate_enhanced_mock_suggestions(destination, start_date, end_date, budget, preferences)
        except Exception as e:
            st.error(f"Error generating trip suggestions: {str(e)}")
            return self._generate_mock_suggestions(destination, start_date, end_date, budget, preferences)
    
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
    
    def _generate_mock_suggestions(self, destination: str, start_date: str, end_date: str, 
                                 budget: float, preferences: str) -> Dict:
        """Fallback mock suggestions for demo purposes"""
        return {
            "destination": destination,
            "duration": f"{start_date} to {end_date}",
            "budget": budget,
            "itinerary": [
                {
                    "day": 1,
                    "date": start_date,
                    "activities": ["Arrive at destination", "Check into accommodation", "Explore local area"]
                }
            ],
            "accommodations": [
                {
                    "name": f"Demo Hotel in {destination}",
                    "type": "Hotel",
                    "price_range": f"${budget * 0.3:.0f} - ${budget * 0.5:.0f} per night",
                    "rating": 4.0,
                    "amenities": ["WiFi", "Breakfast"]
                }
            ],
            "activities": [
                {
                    "name": f"Explore {destination}",
                    "type": "Sightseeing",
                    "duration": "Half Day",
                    "cost": "Free - $20",
                    "description": "Walk through the city and visit landmarks"
                }
            ],
            "restaurants": [
                {
                    "name": f"Local Restaurant in {destination}",
                    "cuisine": "Local",
                    "price_range": "$10-25 per person",
                    "rating": 4.0,
                    "specialties": ["Traditional dishes"]
                }
            ],
            "transportation": [
                {
                    "type": "Local Transport",
                    "option": "Public Transport",
                    "cost": "$10-20 per day",
                    "duration": "Unlimited daily use"
                }
            ],
            "tips": [
                f"Enjoy your trip to {destination}!",
                "Check local customs and dress codes"
            ]
        }

# Initialize the trip planner
trip_planner = VertexAITripPlanner()
