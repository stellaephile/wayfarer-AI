# emt_utils.py
import os
from typing import Dict, List
from urllib.parse import quote

class EMTSearchGenerator:
    """Generate EaseMyTrip search URLs for flights, hotels, trains, and buses"""
    
    def __init__(self):
        self.base_urls = {
            "flights": "https://www.easemytrip.com/flights/book-online/",
            "hotels": "https://www.easemytrip.com/hotels/",
            "trains": "https://www.easemytrip.com/railways/",
            "buses": "https://www.easemytrip.com/bus/"
        }
    
    def generate_flight_search_url(self, origin: str, destination: str, date: str, return_date: str = None) -> str:
        """Generate EaseMyTrip flight search URL"""
        origin_code = self._get_airport_code(origin)
        dest_code = self._get_airport_code(destination)
        
        if return_date:
            # Round trip
            return f"{self.base_urls['flights']}{origin_code}-{dest_code}-{date}-{return_date}.html"
        else:
            # One way
            return f"{self.base_urls['flights']}{origin_code}-{dest_code}-{date}.html"
    
    def generate_hotel_search_url(self, city: str, checkin: str, checkout: str) -> str:
        """Generate EaseMyTrip hotel search URL"""
        city_formatted = city.lower().replace(' ', '').replace(',', '')
        return f"{self.base_urls['hotels']}{city_formatted}/{checkin}/{checkout}/"
    
    def generate_train_search_url(self, origin: str, destination: str, date: str) -> str:
        """Generate EaseMyTrip train search URL"""
        origin_formatted = self._format_city_for_url(origin)
        dest_formatted = self._format_city_for_url(destination)
        return f"{self.base_urls['trains']}?from={origin_formatted}&to={dest_formatted}&date={date}"
    
    def generate_bus_search_url(self, origin: str, destination: str, date: str) -> str:
        """Generate EaseMyTrip bus search URL"""
        origin_formatted = self._format_city_for_url(origin)
        dest_formatted = self._format_city_for_url(destination)
        return f"{self.base_urls['buses']}?from={origin_formatted}&to={dest_formatted}&date={date}"
    
    def _get_airport_code(self, city: str) -> str:
        """Get IATA airport code for common cities"""
        city_codes = {
            # Indian cities
            "mumbai": "BOM", "delhi": "DEL", "new delhi": "DEL",
            "bangalore": "BLR", "bengaluru": "BLR", "chennai": "MAA",
            "hyderabad": "HYD", "kolkata": "CCU", "pune": "PNQ",
            "ahmedabad": "AMD", "goa": "GOI", "jaipur": "JAI",
            "kochi": "COK", "lucknow": "LKO", "bhubaneswar": "BBI",
            "coimbatore": "CJB", "nagpur": "NAG", "indore": "IDR",
            "vadodara": "BDQ", "thiruvananthapuram": "TRV",
            
            # International cities
            "london": "LHR", "paris": "CDG", "new york": "JFK",
            "dubai": "DXB", "singapore": "SIN", "bangkok": "BKK",
            "kuala lumpur": "KUL", "hong kong": "HKG", "tokyo": "NRT",
            "sydney": "SYD", "melbourne": "MEL", "amsterdam": "AMS",
            "frankfurt": "FRA", "zurich": "ZUR", "istanbul": "IST",
            "doha": "DOH", "abu dhabi": "AUH", "muscat": "MCT"
        }
        
        city_clean = city.lower().strip()
        return city_codes.get(city_clean, city.upper()[:3])
    
    def _format_city_for_url(self, city: str) -> str:
        """Format city name for URL parameters"""
        return quote(city.strip())
    
    def generate_all_transport_options(self, origin: str, destination: str, date: str, 
                                     return_date: str = None) -> Dict[str, str]:
        """Generate all transport booking URLs for a route"""
        return {
            "flight_url": self.generate_flight_search_url(origin, destination, date, return_date),
            "train_url": self.generate_train_search_url(origin, destination, date),
            "bus_url": self.generate_bus_search_url(origin, destination, date)
        }
    
    def get_city_travel_options(self, origin: str, destination: str) -> Dict[str, bool]:
        """Determine which transport options are available between cities"""
        origin_lower = origin.lower()
        dest_lower = destination.lower()
        
        # Define domestic vs international routes
        indian_cities = {
            "mumbai", "delhi", "new delhi", "bangalore", "bengaluru", 
            "chennai", "hyderabad", "kolkata", "pune", "ahmedabad", 
            "goa", "jaipur", "kochi", "lucknow", "bhubaneswar"
        }
        
        origin_indian = origin_lower in indian_cities
        dest_indian = dest_lower in indian_cities
        
        # Determine available options
        options = {
            "flights": True,  # Always available
            "trains": origin_indian and dest_indian,  # Only for domestic routes
            "buses": origin_indian and dest_indian,   # Only for domestic routes
            "international": not (origin_indian and dest_indian)
        }
        
        return options

# Create global instance
emt_generator = EMTSearchGenerator()