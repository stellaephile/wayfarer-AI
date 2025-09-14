# maps_utils.py
import os
import googlemaps
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class GoogleMapsClient:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.client = None
        
        if self.api_key and self.api_key != "your-api-key":
            try:
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as e:
                st.warning(f"⚠️ Google Maps API initialization failed: {str(e)}")
        else:
            st.info("📍 Google Maps API not configured. Place details will be limited.")

    def fetch_place_details(self, place_name: str, location: str = ""):
        """Fetch place details from Google Places API"""
        if not self.client:
            return {
                "name": place_name,
                "rating": "N/A",
                "address": f"{place_name}, {location}" if location else place_name,
                "photos": [],
                "types": ["point_of_interest"]
            }
        
        try:
            # Search for places
            query = f"{place_name} {location}" if location else place_name
            places_result = self.client.places(query=query)
            
            if places_result.get("results"):
                place = places_result["results"][0]
                place_id = place.get("place_id")
                
                # Get detailed information
                details = self.client.place(place_id=place_id)
                place_details = details.get("result", {})
                
                return {
                    "name": place_details.get("name", place_name),
                    "rating": place_details.get("rating", "N/A"),
                    "address": place_details.get("formatted_address", "Address not available"),
                    "phone": place_details.get("formatted_phone_number", "N/A"),
                    "website": place_details.get("website", "N/A"),
                    "types": place_details.get("types", []),
                    "photos": [photo.get("photo_reference", "") for photo in place_details.get("photos", [])[:3]],
                    "price_level": place_details.get("price_level", "N/A"),
                    "opening_hours": place_details.get("opening_hours", {}).get("weekday_text", [])
                }
                
        except Exception as e:
            st.warning(f"⚠️ Error fetching place details for {place_name}: {str(e)}")
            
        return {
            "name": place_name,
            "rating": "N/A",
            "address": f"{place_name}, {location}" if location else place_name,
            "error": "Could not fetch details"
        }

    def get_directions(self, origin: str, destination: str, mode: str = "driving"):
        """Get directions between two locations"""
        if not self.client:
            return {
                "distance": "N/A",
                "duration": "N/A",
                "steps": []
            }
        
        try:
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,  # driving, walking, transit, bicycling
                alternatives=True
            )
            
            if directions_result:
                route = directions_result[0]
                leg = route["legs"][0]
                
                return {
                    "distance": leg["distance"]["text"],
                    "duration": leg["duration"]["text"],
                    "steps": [step["html_instructions"] for step in leg["steps"]],
                    "polyline": route["overview_polyline"]["points"]
                }
                
        except Exception as e:
            st.warning(f"⚠️ Error getting directions: {str(e)}")
            
        return {
            "distance": "N/A",
            "duration": "N/A",
            "steps": []
        }

    def find_nearby_places(self, location: str, place_type: str = "tourist_attraction", radius: int = 5000):
        """Find nearby places of interest"""
        if not self.client:
            return []
        
        try:
            # First geocode the location
            geocode_result = self.client.geocode(location)
            if not geocode_result:
                return []
                
            lat_lng = geocode_result[0]["geometry"]["location"]
            
            # Search for nearby places
            nearby_search = self.client.places_nearby(
                location=lat_lng,
                radius=radius,
                type=place_type
            )
            
            places = []
            for place in nearby_search.get("results", [])[:10]:  # Limit to 10 results
                places.append({
                    "name": place.get("name"),
                    "rating": place.get("rating", "N/A"),
                    "types": place.get("types", []),
                    "vicinity": place.get("vicinity"),
                    "price_level": place.get("price_level", "N/A"),
                    "photos": [photo.get("photo_reference", "") for photo in place.get("photos", [])[:1]]
                })
            
            return places
            
        except Exception as e:
            st.warning(f"⚠️ Error finding nearby places: {str(e)}")
            return []

# Create global maps client instance
maps_client = GoogleMapsClient()

# Convenience functions
def fetch_place_details(place_name: str, location: str = ""):
    """Convenience function to fetch place details"""
    return maps_client.fetch_place_details(place_name, location)

def get_directions(origin: str, destination: str, mode: str = "driving"):
    """Convenience function to get directions"""
    return maps_client.get_directions(origin, destination, mode)

def find_nearby_places(location: str, place_type: str = "tourist_attraction"):
    """Convenience function to find nearby places"""
    return maps_client.find_nearby_places(location, place_type)