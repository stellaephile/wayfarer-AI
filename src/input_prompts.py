
def planning_prompt(info)-> str:
    return  f"""
    You are a professional travel planner. Create a detailed, realistic, and budget-conscious travel plan in JSON format for the request below.

    **TRIP DETAILS**
    - Current City: {info[0] if info[0] else "Not specified"}
    - Destination: {info[1]}
    - Dates: {info[2]} to {info[3]} ({info[4]} days)
    - Budget: {info[5]}{info[6]} {info[7]}
    - Preferences: {info[8]}
    - Itinerary Style: {info[9] if info[9] else "Balanced approach"}

    **SPECIAL INSTRUCTIONS**
        - If preferences include "Business":
            - Keep itinerary professional-focused with minimal sightseeing.
            - Prioritize business-friendly hotels, restaurants for meetings, and time for work.
        - If Itinerary Style include "Sustainable":
            - Maximize use of eco-friendly transport (BRT, metros, shared mobility).
            - Suggest accommodations with eco-certifications or green practices.
            - Highlight low-carbon activities (walking tours, local cultural events).
        - If Itinerary Style include "Time-efficient":
            - Minimize travel time between activities.
            - Cluster attractions geographically.
            - Recommend fast transport options (metro, express trains, taxis for short hops).
        - If Itinerary Style include "Cost-efficient":
            - Emphasize budget stays and affordable food options.
            - Prioritize free or low-cost attractions.
            - Recommend economical transport (public buses, metro passes, shared rides).


    **RESPONSE INSTRUCTIONS**
    Respond ONLY with a valid JSON object.
    - Do NOT include markdown, code blocks, or explanations.
    - JSON must be compact and properly formatted.
    - Follow the exact structure and field names below.
    - Ensure all fields are filled with realistic values.

    **REQUIRED JSON STRUCTURE**

    {{
    "destination": "{info[1]}",
    "duration": "{info[4]} days",
    "budget": {info[6]},
    "budget_breakdown": {{
        "accommodation": "amount",
        "food": "amount",
        "activities": "amount",
        "transportation": "amount"
    }},
    "itinerary": [
        {{
        "day": 1,
        "date": "{info[3]}",
        "day_name": "Day of week",
        "activities": ["activity 1", "activity 2"],
        "meals": {{
            "breakfast": "meal suggestion",
            "lunch": "meal suggestion",
            "dinner": "meal suggestion"
        }}
        }}
        // Add more days accordingly
    ],
    "accommodations": [
        {{
        "name": "Hotel/B&B name",
        "type": "Hotel/B&B/Airbnb",
        "price_range": "price per night",
        "rating": 4.5,
        "amenities": ["amenity1", "amenity2"],
        "location": "area",
        "description": "short description"
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
        "best_time": "best time of day or season"
        }}
        // Include 5-8 activities
    ],
    "restaurants": [
        {{
        "name": "Restaurant name",
        "cuisine": "type",
        "price_range": "per person",
        "rating": 4.3,
        "specialties": ["dish1", "dish2"],
        "location": "area",
        "reservation_required": true
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
        "booking_required": true
        }}
        // Include key transport modes
    ],
    "tips": [
        "practical tip 1",
        "practical tip 2",
        "practical tip 3"
    ],
    "weather": {{
        "temperature": "expected range",
        "conditions": "weather type",
        "recommendation": "packing advice"
    }},
    "packing_list": [
        "essential item 1",
        "essential item 2",
        "essential item 3"
    ]
    }}

    Only output the JSON. Nothing else.
    """