# weather_utils.py
import streamlit as st
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for fetching weather data using Google Weather API"""
    
    def __init__(self):
        # You'll need to get an API key from Google Cloud Console
        # Enable the Weather API and get credentials
        self.api_key = st.secrets.get("GOOGLE_WEATHER_API_KEY", os.getenv("GOOGLE_WEATHER_API_KEY", "demo_key"))
        self.base_url = "https://weather.googleapis.com/v1"
        self.is_configured = self.api_key != "demo_key"
        
        if not self.is_configured:
            logger.warning("Weather API not configured. Using mock data.")

    def get_weather_forecast(self, location: str, start_date: str, end_date: str) -> Dict:
        """
        Get weather forecast for a location and date range
        
        Args:
            location: City name or coordinates
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dict containing weather forecast data
        """
        try:
            if not self.is_configured:
                return self._get_mock_weather_data(location, start_date, end_date)
            
            # Prepare the request
            params = {
                'key': self.api_key,
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'units': 'metric',
                'fields': 'temperature,humidity,precipitation,wind,description,icon'
            }
            
            response = requests.get(f"{self.base_url}/forecast", params=params, timeout=10)
            
            if response.status_code == 200:
                weather_data = response.json()
                return self._format_weather_data(weather_data, location, start_date, end_date)
            else:
                logger.error(f"Weather API error: {response.status_code}")
                return self._get_mock_weather_data(location, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return self._get_mock_weather_data(location, start_date, end_date)

    def _format_weather_data(self, raw_data: Dict, location: str, start_date: str, end_date: str) -> Dict:
        """Format raw weather data into standardized format"""
        try:
            formatted_data = {
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'daily_forecast': [],
                'summary': {
                    'avg_temperature': 0,
                    'conditions': '',
                    'recommendations': []
                }
            }
            
            # Process daily forecasts
            if 'forecasts' in raw_data:
                for forecast in raw_data['forecasts']:
                    daily_data = {
                        'date': forecast.get('date'),
                        'day_name': datetime.strptime(forecast.get('date'), '%Y-%m-%d').strftime('%A'),
                        'temperature': {
                            'high': forecast.get('temperature', {}).get('high', 25),
                            'low': forecast.get('temperature', {}).get('low', 15)
                        },
                        'humidity': forecast.get('humidity', 60),
                        'precipitation': forecast.get('precipitation', 0),
                        'wind_speed': forecast.get('wind', {}).get('speed', 10),
                        'description': forecast.get('description', 'Partly cloudy'),
                        'icon': forecast.get('icon', '☀️'),
                        'recommendations': self._get_daily_recommendations(forecast)
                    }
                    formatted_data['daily_forecast'].append(daily_data)
            
            # Generate summary
            formatted_data['summary'] = self._generate_weather_summary(formatted_data['daily_forecast'])
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting weather data: {str(e)}")
            return self._get_mock_weather_data(location, start_date, end_date)

    def _get_daily_recommendations(self, forecast: Dict) -> List[str]:
        """Generate daily recommendations based on weather"""
        recommendations = []
        
        temp_high = forecast.get('temperature', {}).get('high', 25)
        temp_low = forecast.get('temperature', {}).get('low', 15)
        precipitation = forecast.get('precipitation', 0)
        
        # Temperature recommendations
        if temp_high > 30:
            recommendations.append("Pack light, breathable clothing")
            recommendations.append("Stay hydrated and seek shade during peak hours")
        elif temp_high < 10:
            recommendations.append("Pack warm layers and winter clothing")
            recommendations.append("Be prepared for cold weather activities")
        elif temp_low < 5:
            recommendations.append("Bring warm clothes for early morning/evening")
        
        # Precipitation recommendations
        if precipitation > 50:
            recommendations.append("Pack waterproof clothing and umbrella")
            recommendations.append("Consider indoor activities")
        elif precipitation > 20:
            recommendations.append("Keep light rain gear handy")
        
        # General recommendations
        if temp_high - temp_low > 15:
            recommendations.append("Layer clothing for temperature variations")
        
        return recommendations[:3]  # Limit to 3 recommendations

    def _generate_weather_summary(self, daily_forecasts: List[Dict]) -> Dict:
        """Generate overall weather summary for the trip"""
        if not daily_forecasts:
            return {
                'avg_temperature': 22,
                'conditions': 'Pleasant',
                'recommendations': ['Pack appropriate clothing for the season']
            }
        
        # Calculate averages
        total_high = sum(day['temperature']['high'] for day in daily_forecasts)
        total_low = sum(day['temperature']['low'] for day in daily_forecasts)
        avg_high = total_high / len(daily_forecasts)
        avg_low = total_low / len(daily_forecasts)
        
        # Determine overall conditions
        rainy_days = sum(1 for day in daily_forecasts if day['precipitation'] > 20)
        conditions = self._determine_overall_conditions(avg_high, avg_low, rainy_days, len(daily_forecasts))
        
        # Generate trip-level recommendations
        recommendations = self._generate_trip_recommendations(avg_high, avg_low, rainy_days, len(daily_forecasts))
        
        return {
            'avg_temperature': f"{avg_low:.0f}°C - {avg_high:.0f}°C",
            'conditions': conditions,
            'recommendations': recommendations
        }

    def _determine_overall_conditions(self, avg_high: float, avg_low: float, rainy_days: int, total_days: int) -> str:
        """Determine overall weather conditions"""
        if rainy_days >= total_days * 0.6:
            return "Rainy"
        elif rainy_days >= total_days * 0.3:
            return "Partly Rainy"
        elif avg_high > 30:
            return "Hot"
        elif avg_high > 25:
            return "Warm"
        elif avg_high > 15:
            return "Pleasant"
        else:
            return "Cool"

    def _generate_trip_recommendations(self, avg_high: float, avg_low: float, rainy_days: int, total_days: int) -> List[str]:
        """Generate overall trip recommendations"""
        recommendations = []
        
        # Temperature-based recommendations
        if avg_high > 30:
            recommendations.append("Pack lightweight, breathable fabrics")
            recommendations.append("Bring sun protection (hat, sunscreen)")
        elif avg_high < 15:
            recommendations.append("Pack warm layers and jackets")
            recommendations.append("Consider indoor activities on colder days")
        else:
            recommendations.append("Pack versatile clothing for varying temperatures")
        
        # Rain-based recommendations
        if rainy_days >= total_days * 0.4:
            recommendations.append("Essential rain gear required")
            recommendations.append("Plan indoor backup activities")
        elif rainy_days > 0:
            recommendations.append("Pack light rain protection")
        
        # General recommendations
        if avg_high - avg_low > 15:
            recommendations.append("Prepare for significant daily temperature changes")
        
        recommendations.append("Check weather updates before daily activities")
        
        return recommendations[:4]  # Limit to 4 recommendations

    def _get_mock_weather_data(self, location: str, start_date: str, end_date: str) -> Dict:
        """Generate mock weather data for demo purposes"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            daily_forecasts = []
            current_date = start_dt
            
            # Base weather patterns for different locations
            weather_patterns = {
                'default': {'base_high': 25, 'base_low': 15, 'rain_chance': 0.2},
                'tropical': {'base_high': 30, 'base_low': 22, 'rain_chance': 0.4},
                'temperate': {'base_high': 20, 'base_low': 10, 'rain_chance': 0.3},
                'desert': {'base_high': 35, 'base_low': 20, 'rain_chance': 0.1},
                'mountain': {'base_high': 15, 'base_low': 5, 'rain_chance': 0.3}
            }
            
            # Determine pattern based on location
            location_lower = location.lower()
            pattern = weather_patterns['default']
            
            if any(word in location_lower for word in ['goa', 'kerala', 'chennai', 'mumbai']):
                pattern = weather_patterns['tropical']
            elif any(word in location_lower for word in ['delhi', 'pune', 'bangalore']):
                pattern = weather_patterns['temperate']
            elif any(word in location_lower for word in ['rajasthan', 'jodhpur']):
                pattern = weather_patterns['desert']
            elif any(word in location_lower for word in ['manali', 'shimla', 'darjeeling']):
                pattern = weather_patterns['mountain']
            
            day_count = 0
            while current_date <= end_dt:
                # Add some variation
                temp_variation = (day_count % 3 - 1) * 3  # -3, 0, +3 pattern
                
                high_temp = pattern['base_high'] + temp_variation
                low_temp = pattern['base_low'] + temp_variation
                
                # Determine precipitation
                precipitation = 0
                if (day_count + hash(location)) % 5 == 0:  # Pseudo-random based on location
                    precipitation = 30 + (day_count % 3) * 20
                
                # Weather icons and descriptions
                if precipitation > 50:
                    icon = "🌧️"
                    description = "Heavy rain"
                elif precipitation > 20:
                    icon = "🌦️"
                    description = "Light rain"
                elif high_temp > 30:
                    icon = "☀️"
                    description = "Sunny and hot"
                elif high_temp < 15:
                    icon = "☁️"
                    description = "Cool and cloudy"
                else:
                    icon = "⛅"
                    description = "Partly cloudy"
                
                daily_data = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_name': current_date.strftime('%A'),
                    'temperature': {
                        'high': high_temp,
                        'low': low_temp
                    },
                    'humidity': 55 + (day_count % 4) * 10,  # 55-85%
                    'precipitation': precipitation,
                    'wind_speed': 8 + (day_count % 3) * 5,  # 8-18 km/h
                    'description': description,
                    'icon': icon,
                    'recommendations': self._get_daily_recommendations({
                        'temperature': {'high': high_temp, 'low': low_temp},
                        'precipitation': precipitation
                    })
                }
                
                daily_forecasts.append(daily_data)
                current_date += timedelta(days=1)
                day_count += 1
            
            # Generate summary
            summary = self._generate_weather_summary(daily_forecasts)
            
            return {
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'daily_forecast': daily_forecasts,
                'summary': summary,
                'data_source': 'mock'
            }
            
        except Exception as e:
            logger.error(f"Error generating mock weather data: {str(e)}")
            return {
                'location': location,
                'start_date': start_date,
                'end_date': end_date,
                'daily_forecast': [],
                'summary': {
                    'avg_temperature': '15°C - 25°C',
                    'conditions': 'Pleasant',
                    'recommendations': ['Pack appropriate clothing for the season']
                },
                'data_source': 'fallback'
            }

    def get_weather_recommendations_for_itinerary(self, weather_data: Dict) -> List[str]:
        """Get specific recommendations for itinerary planning"""
        if not weather_data or 'daily_forecast' not in weather_data:
            return ["Check local weather conditions before activities"]
        
        recommendations = []
        daily_forecasts = weather_data['daily_forecast']
        
        # Analyze patterns
        rainy_days = [day for day in daily_forecasts if day.get('precipitation', 0) > 20]
        hot_days = [day for day in daily_forecasts if day.get('temperature', {}).get('high', 25) > 30]
        cool_days = [day for day in daily_forecasts if day.get('temperature', {}).get('high', 25) < 15]
        
        # Activity recommendations
        if rainy_days:
            recommendations.append(f"Plan indoor activities for {len(rainy_days)} potentially rainy days")
        
        if hot_days:
            recommendations.append(f"Schedule outdoor activities early morning/evening on {len(hot_days)} hot days")
        
        if cool_days:
            recommendations.append(f"Plan indoor or warm activities for {len(cool_days)} cooler days")
        
        # General recommendations
        recommendations.extend([
            "Check weather updates daily for any changes",
            "Adjust activity timing based on weather conditions",
            "Pack weather-appropriate gear for all planned activities"
        ])
        
        return recommendations[:5]  # Limit to 5 recommendations

# Global weather service instance
weather_service = WeatherService()