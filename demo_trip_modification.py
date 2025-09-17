#!/usr/bin/env python3
"""
Demo script for the Trip Modification Feature

This script demonstrates how to use the new trip modification functionality
without running the full Streamlit application.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from trip_modification_chat import TripModificationChat
from vertex_ai_utils import VertexAITripPlanner

def create_demo_trip():
    """Create a demo trip for testing"""
    db = DatabaseManager()
    
    # Create a demo user if not exists
    success, message = db.create_user("demo_user", "demo@example.com", "password123", "Demo User")
    if success:
        print(f"✅ Demo user created: {message}")
    else:
        print(f"ℹ️ Demo user already exists or error: {message}")
    
    # Get user ID
    user = db.get_user_by_email("demo@example.com")
    if not user:
        print("❌ Failed to get demo user")
        return None
    
    user_id = user['id']
    
    # Create a demo trip
    demo_trip_data = {
        "destination": "Paris, France",
        "duration": "5 days",
        "budget": 2000,
        "currency": "USD",
        "currency_symbol": "$",
        "budget_breakdown": {
            "accommodation": "$800",
            "food": "$600",
            "activities": "$400",
            "transportation": "$200"
        },
        "itinerary": [
            {
                "day": 1,
                "date": "2024-06-01",
                "day_name": "Saturday",
                "activities": ["Arrive in Paris", "Check into hotel", "Evening walk along Seine"],
                "meals": {
                    "breakfast": "Hotel breakfast",
                    "lunch": "Local bistro",
                    "dinner": "Traditional French restaurant"
                }
            },
            {
                "day": 2,
                "date": "2024-06-02",
                "day_name": "Sunday",
                "activities": ["Visit Eiffel Tower", "Louvre Museum", "Champs-Élysées"],
                "meals": {
                    "breakfast": "Café near hotel",
                    "lunch": "Museum café",
                    "dinner": "Fine dining experience"
                }
            }
        ],
        "accommodations": [
            {
                "name": "Hotel des Invalides",
                "type": "Hotel",
                "price_range": "$150-200 per night",
                "rating": 4.5,
                "amenities": ["WiFi", "Breakfast", "Concierge"],
                "location": "7th arrondissement",
                "description": "Elegant hotel near major attractions"
            }
        ],
        "activities": [
            {
                "name": "Eiffel Tower Visit",
                "type": "Sightseeing",
                "duration": "2-3 hours",
                "cost": "$25-40",
                "description": "Iconic Paris landmark with city views",
                "rating": 4.8,
                "best_time": "Morning"
            },
            {
                "name": "Louvre Museum Tour",
                "type": "Cultural",
                "duration": "Half Day",
                "cost": "$20-30",
                "description": "World's largest art museum",
                "rating": 4.7,
                "best_time": "Afternoon"
            }
        ],
        "restaurants": [
            {
                "name": "Le Comptoir du Relais",
                "cuisine": "French Bistro",
                "price_range": "$40-60 per person",
                "rating": 4.4,
                "specialties": ["Traditional French dishes", "Wine selection"],
                "location": "Saint-Germain",
                "reservation_required": True
            }
        ],
        "transportation": [
            {
                "type": "Airport Transfer",
                "option": "Taxi/Uber",
                "cost": "$50-70",
                "duration": "45 minutes",
                "description": "Direct transfer from CDG airport",
                "booking_required": False
            }
        ],
        "tips": [
            "Learn basic French phrases",
            "Book museum tickets in advance",
            "Carry cash for small purchases",
            "Download offline maps"
        ],
        "weather": {
            "temperature": "18°C - 25°C",
            "conditions": "Pleasant spring weather",
            "recommendation": "Pack light layers and comfortable shoes"
        },
        "packing_list": [
            "Passport and travel documents",
            "Comfortable walking shoes",
            "Light jacket",
            "Camera",
            "Universal adapter"
        ]
    }
    
    # Create the trip
    success, message = db.create_trip(
        user_id=user_id,
        destination="Paris, France",
        start_date="2024-06-01",
        end_date="2024-06-05",
        budget=2000,
        preferences="Culture, Food, History",
        ai_suggestions=json.dumps(demo_trip_data),
        currency="USD",
        currency_symbol="$"
    )
    
    if success:
        trip_id = int(message.split("ID: ")[1])
        print(f"✅ Demo trip created with ID: {trip_id}")
        return trip_id, user_id, demo_trip_data
    else:
        print(f"❌ Failed to create demo trip: {message}")
        return None, None, None

def demo_chat_interaction():
    """Demonstrate chat interaction functionality"""
    print("\n" + "="*60)
    print("🗺️ TRIP MODIFICATION CHAT DEMO")
    print("="*60)
    
    # Create demo trip
    trip_id, user_id, trip_data = create_demo_trip()
    if not trip_id:
        return
    
    # Initialize chat interface
    chat_interface = TripModificationChat()
    
    # Add trip metadata
    trip_data.update({
        'trip_id': trip_id,
        'user_id': user_id,
        'destination': 'Paris, France',
        'start_date': '2024-06-01',
        'end_date': '2024-06-05',
        'budget': 2000,
        'currency': 'USD',
        'currency_symbol': '$',
        'preferences': 'Culture, Food, History'
    })
    
    print(f"\n📋 Demo Trip: {trip_data['destination']}")
    print(f"💰 Budget: {trip_data['currency_symbol']}{trip_data['budget']:,}")
    print(f"📅 Duration: {trip_data['duration']}")
    
    # Simulate chat interactions
    demo_messages = [
        "Make this trip more budget-friendly",
        "Add more adventure activities",
        "I want to focus more on food experiences",
        "Can you suggest luxury accommodations instead?"
    ]
    
    print(f"\n💬 Simulating chat interactions...")
    
    for i, message in enumerate(demo_messages, 1):
        print(f"\n--- Chat Interaction {i} ---")
        print(f"👤 User: {message}")
        
        # Generate AI response
        try:
            ai_response = chat_interface.vertex_ai.generate_chat_response(
                user_message=message,
                trip_context=trip_data,
                user_id=user_id,
                trip_id=trip_id
            )
            print(f"🤖 AI: {ai_response}")
            
            # Save to database
            db = DatabaseManager()
            credits_used = chat_interface.vertex_ai.calculate_chat_credits(message, len(ai_response))
            db.save_chat_interaction(trip_id, user_id, 'user', message)
            db.save_chat_interaction(trip_id, user_id, 'ai', message, ai_response, credits_used)
            
            print(f"💳 Credits used: {credits_used}")
            
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
    
    # Show chat history
    print(f"\n📚 Chat History Summary:")
    db = DatabaseManager()
    chat_history = db.get_chat_history(trip_id, user_id)
    print(f"Total interactions: {len(chat_history)}")
    
    for interaction in chat_history:
        print(f"- {interaction['message_type'].upper()}: {interaction['message_content'][:50]}...")
    
    # Show modification summary
    print(f"\n📊 Modification Summary:")
    summary = chat_interface.get_modification_summary(trip_id, user_id)
    print(summary)
    
    print(f"\n✅ Demo completed successfully!")
    print(f"Trip ID: {trip_id}")
    print(f"User ID: {user_id}")

def demo_database_schema():
    """Demonstrate the new database schema"""
    print("\n" + "="*60)
    print("🗄️ DATABASE SCHEMA DEMO")
    print("="*60)
    
    db = DatabaseManager()
    
    # Show new tables
    print("\n📋 New Tables Created:")
    print("1. chat_history - Stores chat interactions")
    print("2. trip_modifications - Tracks trip changes")
    
    # Show table structure
    print("\n🔍 Table Structure:")
    
    # Check if tables exist
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check chat_history table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
    if cursor.fetchone():
        print("✅ chat_history table exists")
        cursor.execute("PRAGMA table_info(chat_history)")
        columns = cursor.fetchall()
        print("   Columns:", [col[1] for col in columns])
    
    # Check trip_modifications table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trip_modifications'")
    if cursor.fetchone():
        print("✅ trip_modifications table exists")
        cursor.execute("PRAGMA table_info(trip_modifications)")
        columns = cursor.fetchall()
        print("   Columns:", [col[1] for col in columns])
    
    conn.close()
    
    print(f"\n✅ Database schema demo completed!")

def main():
    """Main demo function"""
    print("🚀 Trip Modification Feature Demo")
    print("="*60)
    
    try:
        # Demo database schema
        demo_database_schema()
        
        # Demo chat interaction
        demo_chat_interaction()
        
        print(f"\n🎉 All demos completed successfully!")
        print(f"\nTo use the full feature:")
        print(f"1. Run: streamlit run src/app.py")
        print(f"2. Create a trip")
        print(f"3. Click 'Modify Trip' button")
        print(f"4. Start chatting with AI!")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
