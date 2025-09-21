"""
Credit Calculator for AI Trip Planner
Calculates credit usage based on AI requests and responses
"""

import json
from typing import Dict, Any

class CreditCalculator:
    """Calculate credit usage for different AI operations"""
    
    # Credit rates (in credits per operation)
    CREDIT_RATES = {
        'trip_generation': 10.0,      # Full trip plan generation
        'trip_refinement': 2.0,       # Chat-based refinement
        'chat_response': 1.0,         # Simple chat response
        'detailed_analysis': 5.0,     # Detailed trip analysis
        'recommendation': 1.5,        # Activity/restaurant recommendations
    }
    
    # Base rates for different content types
    CONTENT_RATES = {
        'text_per_100_chars': 0.1,    # 0.1 credits per 100 characters
        'json_per_100_chars': 0.15,   # 0.15 credits per 100 characters (more complex)
        'structured_data': 2.0,       # Base rate for structured data
    }
    
    @classmethod
    def calculate_trip_generation_credits(cls, trip_data: Dict[str, Any]) -> float:
        """Calculate credits for trip generation based on content complexity"""
        base_credits = cls.CREDIT_RATES['trip_generation']
        
        # Calculate additional credits based on content size and complexity
        content_credits = 0
        
        # Count total characters in the response
        total_chars = 0
        if isinstance(trip_data, dict):
            total_chars = len(json.dumps(trip_data, ensure_ascii=False))
        
        # Add credits based on content size
        content_credits += (total_chars / 100) * cls.CONTENT_RATES['json_per_100_chars']
        
        # Add credits for structured data complexity
        if 'itinerary' in trip_data and trip_data['itinerary']:
            content_credits += cls.CONTENT_RATES['structured_data']
        
        if 'accommodations' in trip_data and trip_data['accommodations']:
            content_credits += cls.CONTENT_RATES['structured_data'] * 0.5
        
        if 'activities' in trip_data and trip_data['activities']:
            content_credits += cls.CONTENT_RATES['structured_data'] * 0.5
        
        if 'restaurants' in trip_data and trip_data['restaurants']:
            content_credits += cls.CONTENT_RATES['structured_data'] * 0.3
        
        return round(base_credits + content_credits, 2)
    
    @classmethod
    def calculate_chat_response_credits(cls, user_message: str, ai_response: str) -> float:
        """Calculate credits for chat responses"""
        base_credits = cls.CREDIT_RATES['chat_response']
        
        # Calculate based on response length
        response_chars = len(ai_response) if ai_response else 0
        content_credits = (response_chars / 100) * cls.CONTENT_RATES['text_per_100_chars']
        
        # Add complexity bonus for longer responses
        if response_chars > 500:
            content_credits += 0.5
        
        return round(base_credits + content_credits, 2)
    
    @classmethod
    def calculate_refinement_credits(cls, user_message: str, ai_response: str, 
                                   trip_context: Dict[str, Any] = None) -> float:
        """Calculate credits for trip refinement requests"""
        base_credits = cls.CREDIT_RATES['trip_refinement']
        
        # Calculate based on response length and complexity
        response_chars = len(ai_response) if ai_response else 0
        content_credits = (response_chars / 100) * cls.CONTENT_RATES['text_per_100_chars']
        
        # Add complexity bonus based on user request
        message_lower = user_message.lower()
        
        # Complex requests get more credits
        if any(word in message_lower for word in ['budget', 'accommodation', 'itinerary']):
            content_credits += 1.0
        
        if any(word in message_lower for word in ['detailed', 'specific', 'comprehensive']):
            content_credits += 0.5
        
        # If response includes structured data, add more credits
        if trip_context and any(key in trip_context for key in ['itinerary', 'accommodations', 'activities']):
            content_credits += 1.0
        
        return round(base_credits + content_credits, 2)
    
    @classmethod
    def calculate_usage_credits(cls, usage_type: str, content: str = None, 
                              metadata: Dict[str, Any] = None) -> float:
        """Calculate credits for general usage types"""
        
        if usage_type not in cls.CREDIT_RATES:
            # Default rate for unknown types
            base_credits = 1.0
        else:
            base_credits = cls.CREDIT_RATES[usage_type]
        
        content_credits = 0
        
        # Calculate based on content length if provided
        if content:
            content_chars = len(content)
            content_credits = (content_chars / 100) * cls.CONTENT_RATES['text_per_100_chars']
        
        # Add metadata-based credits
        if metadata:
            if metadata.get('complexity', 'simple') == 'complex':
                content_credits += 1.0
            elif metadata.get('complexity', 'simple') == 'medium':
                content_credits += 0.5
        
        return round(base_credits + content_credits, 2)
    
    @classmethod
    def estimate_credits_for_request(cls, request_type: str, estimated_response_size: int = 0) -> float:
        """Estimate credits before making a request"""
        
        if request_type == 'trip_generation':
            return cls.CREDIT_RATES['trip_generation'] + (estimated_response_size / 100) * 0.15
        
        elif request_type == 'chat_response':
            return cls.CREDIT_RATES['chat_response'] + (estimated_response_size / 100) * 0.1
        
        elif request_type == 'refinement':
            return cls.CREDIT_RATES['trip_refinement'] + (estimated_response_size / 100) * 0.1
        
        else:
            return cls.CREDIT_RATES.get(request_type, 1.0)
    
    @classmethod
    def get_credit_breakdown(cls, operation: str, credits_used: float) -> Dict[str, Any]:
        """Get detailed breakdown of credit usage"""
        
        breakdown = {
            'operation': operation,
            'total_credits': credits_used,
            'base_credits': cls.CREDIT_RATES.get(operation, 1.0),
            'content_credits': round(credits_used - cls.CREDIT_RATES.get(operation, 1.0), 2),
            'rate_info': {
                'trip_generation': cls.CREDIT_RATES['trip_generation'],
                'chat_response': cls.CREDIT_RATES['chat_response'],
                'refinement': cls.CREDIT_RATES['trip_refinement'],
            }
        }
        
        return breakdown

# Usage examples and testing
if __name__ == "__main__":
    calculator = CreditCalculator()
    
    # Example trip data
    sample_trip = {
        "destination": "Paris",
        "duration": "5 days",
        "itinerary": [
            {"day": 1, "activities": ["Visit Eiffel Tower", "Louvre Museum"]},
            {"day": 2, "activities": ["Notre Dame", "Seine River Cruise"]}
        ],
        "accommodations": [{"name": "Hotel Paris", "price": "$200/night"}],
        "activities": [{"name": "Eiffel Tower", "cost": "$25"}]
    }
    
    # Calculate credits for different operations
    trip_credits = calculator.calculate_trip_generation_credits(sample_trip)
    chat_credits = calculator.calculate_chat_response_credits(
        "Make it more adventurous", 
        "I can add more adventurous activities like hiking, water sports, or extreme experiences."
    )
    
    print(f"Trip generation credits: {trip_credits}")
    print(f"Chat response credits: {chat_credits}")
    print(f"Credit breakdown: {calculator.get_credit_breakdown('trip_generation', trip_credits)}")
