#!/usr/bin/env python3
"""
Test script for the Trip Modification Feature fixes

This script tests the fixes for:
1. AI response truncation
2. Trip update functionality
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from trip_modification_chat import TripModificationChat
from vertex_ai_utils import VertexAITripPlanner

def test_ai_response_length():
    """Test that AI responses are not truncated"""
    print("🧪 Testing AI Response Length...")
    
    # Create a test trip context
    trip_context = {
        'destination': 'Ujjain, India',
        'budget': 1500,
        'currency_symbol': '$',
        'duration': '3 days',
        'preferences': 'Spiritual, Cultural, Adventure',
        'itinerary': [
            {
                'day': 1,
                'activities': ['Visit Mahakaleshwar Temple', 'Explore Bade Ganesh Temple']
            },
            {
                'day': 2,
                'activities': ['Boat ride on Shipra River', 'Visit Kal Bhairav Temple']
            }
        ],
        'activities': [
            {
                'name': 'Temple Tour',
                'type': 'Spiritual',
                'description': 'Visit sacred temples'
            }
        ]
    }
    
    # Initialize AI
    vertex_ai = VertexAITripPlanner()
    
    # Test message
    test_message = "Include more adventurous activities"
    
    print(f"📝 Test message: {test_message}")
    
    try:
        # Generate response
        response = vertex_ai.generate_chat_response(
            user_message=test_message,
            trip_context=trip_context,
            user_id=1,
            trip_id=1
        )
        
        print(f"🤖 AI Response Length: {len(response)} characters")
        print(f"📄 AI Response: {response}")
        
        # Check if response is complete (not truncated)
        if len(response) > 100:  # Should be a substantial response
            print("✅ AI response appears complete (not truncated)")
        else:
            print("⚠️ AI response might be truncated")
            
        # Check for common truncation indicators
        if response.endswith('...') or response.endswith('I') or len(response.split('.')) < 2:
            print("⚠️ Response might be incomplete")
        else:
            print("✅ Response appears complete")
            
    except Exception as e:
        print(f"❌ Error testing AI response: {str(e)}")

def test_trip_update():
    """Test that trip updates work correctly"""
    print("\n🧪 Testing Trip Update Functionality...")
    
    # Create demo trip
    db = DatabaseManager()
    
    # Create demo user if not exists
    success, message = db.create_user("test_user", "test@example.com", "password123", "Test User")
    if success:
        print(f"✅ Test user created: {message}")
    else:
        print(f"ℹ️ Test user already exists: {message}")
    
    # Get user ID
    user = db.get_user_by_email("test@example.com")
    if not user:
        print("❌ Failed to get test user")
        return
    
    user_id = user['id']
    
    # Create a test trip
    test_trip_data = {
        "destination": "Ujjain, India",
        "duration": "3 days",
        "budget": 1500,
        "currency": "USD",
        "currency_symbol": "$",
        "itinerary": [
            {
                "day": 1,
                "date": "2024-06-01",
                "day_name": "Saturday",
                "activities": ["Visit Mahakaleshwar Temple", "Explore Bade Ganesh Temple"],
                "meals": {
                    "breakfast": "Hotel breakfast",
                    "lunch": "Local restaurant",
                    "dinner": "Traditional Indian cuisine"
                }
            }
        ],
        "activities": [
            {
                "name": "Temple Tour",
                "type": "Spiritual",
                "duration": "Half Day",
                "cost": "$20-30",
                "description": "Visit sacred temples",
                "rating": 4.5,
                "best_time": "Morning"
            }
        ],
        "accommodations": [
            {
                "name": "Hotel Ujjain",
                "type": "Hotel",
                "price_range": "$50-80 per night",
                "rating": 4.2,
                "amenities": ["WiFi", "Breakfast"],
                "location": "City center",
                "description": "Comfortable hotel near temples"
            }
        ]
    }
    
    # Create the trip
    success, message = db.create_trip(
        user_id=user_id,
        destination="Ujjain, India",
        start_date="2024-06-01",
        end_date="2024-06-03",
        budget=1500,
        preferences="Spiritual, Cultural",
        ai_suggestions=json.dumps(test_trip_data),
        currency="USD",
        currency_symbol="$"
    )
    
    if success:
        trip_id = int(message.split("ID: ")[1])
        print(f"✅ Test trip created with ID: {trip_id}")
        
        # Test trip modification
        modification_chat = TripModificationChat()
        
        # Simulate chat interactions
        test_requests = [
            "Include more adventurous activities",
            "Add budget-friendly options",
            "Make it more cultural"
        ]
        
        print(f"\n💬 Simulating chat interactions...")
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n--- Chat {i}: {request} ---")
            
            # Generate AI response
            try:
                ai_response = modification_chat.vertex_ai.generate_chat_response(
                    user_message=request,
                    trip_context=test_trip_data,
                    user_id=user_id,
                    trip_id=trip_id
                )
                print(f"🤖 AI: {ai_response[:100]}...")
                
                # Save to database
                credits_used = modification_chat.vertex_ai.calculate_chat_credits(request, len(ai_response))
                db.save_chat_interaction(trip_id, user_id, 'user', request)
                db.save_chat_interaction(trip_id, user_id, 'ai', request, ai_response, credits_used)
                
                print(f"💳 Credits used: {credits_used}")
                
            except Exception as e:
                print(f"❌ Error in chat {i}: {str(e)}")
        
        # Test trip update
        print(f"\n🔄 Testing trip update...")
        
        try:
            # Generate updated trip
            updated_trip_data = modification_chat._generate_updated_trip_from_chat(trip_id, user_id, test_trip_data)
            
            if updated_trip_data:
                print(f"✅ Updated trip data generated")
                print(f"📊 Original activities: {len(test_trip_data.get('activities', []))}")
                print(f"📊 Updated activities: {len(updated_trip_data.get('activities', []))}")
                
                # Save the modification
                db.save_trip_modification(
                    trip_id, user_id, "test_update", 
                    test_trip_data, updated_trip_data, 
                    "Test modification", 0
                )
                
                # Update the trip in database
                success, message = db.update_trip(
                    trip_id, user_id, 
                    ai_suggestions=json.dumps(updated_trip_data)
                )
                
                if success:
                    print(f"✅ Trip updated successfully in database!")
                    
                    # Verify the update
                    updated_trip = db.get_trip_by_id(trip_id, user_id)
                    if updated_trip:
                        parsed_data = json.loads(updated_trip['ai_suggestions'])
                        print(f"✅ Verified: Updated trip has {len(parsed_data.get('activities', []))} activities")
                    else:
                        print(f"❌ Failed to verify trip update")
                else:
                    print(f"❌ Failed to update trip: {message}")
            else:
                print(f"❌ Failed to generate updated trip data")
                
        except Exception as e:
            print(f"❌ Error in trip update: {str(e)}")
            import traceback
            traceback.print_exc()
        
    else:
        print(f"❌ Failed to create test trip: {message}")

def main():
    """Main test function"""
    print("🚀 Testing Trip Modification Fixes")
    print("="*60)
    
    try:
        # Test AI response length
        test_ai_response_length()
        
        # Test trip update functionality
        test_trip_update()
        
        print(f"\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

