# calendar_utils.py
import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
import io

logger = logging.getLogger(__name__)

class CalendarService:
    """Service for creating calendar events from trip itineraries"""
    
    def __init__(self):
        pass

    def create_calendar_from_itinerary(self, trip_data: Dict, ai_suggestions: Dict) -> str:
        """
        Create an .ics calendar file from trip itinerary
        
        Args:
            trip_data: Trip data including dates and destination
            ai_suggestions: AI-generated suggestions including itinerary
            
        Returns:
            str: Calendar content in .ics format
        """
        try:
            # Create calendar
            calendar = Calendar()
            calendar.creator = "AI Trip Planner"
            calendar.prodid = "-//AI Trip Planner//Trip Calendar//EN"
            
            # Extract trip information
            destination = trip_data.get('destination', 'Unknown Destination')
            start_date = trip_data.get('start_date', '')
            end_date = trip_data.get('end_date', '')
            preferences = trip_data.get('preferences', '')
            
            # Add main trip event
            self._add_main_trip_event(calendar, destination, start_date, end_date, preferences)
            
            # Add daily itinerary events
            if 'itinerary' in ai_suggestions and ai_suggestions['itinerary']:
                self._add_itinerary_events(calendar, ai_suggestions['itinerary'], destination)
            
            # Add accommodation events
            if 'accommodations' in ai_suggestions and ai_suggestions['accommodations']:
                self._add_accommodation_events(calendar, ai_suggestions['accommodations'], start_date, end_date, destination)
            
            # Add activity reminders
            if 'activities' in ai_suggestions and ai_suggestions['activities']:
                self._add_activity_reminders(calendar, ai_suggestions['activities'], start_date, destination)
            
            # Add restaurant reservations
            if 'restaurants' in ai_suggestions and ai_suggestions['restaurants']:
                self._add_restaurant_events(calendar, ai_suggestions['restaurants'], start_date, destination)
            
            # Add transportation events
            if 'transportation' in ai_suggestions and ai_suggestions['transportation']:
                self._add_transportation_events(calendar, ai_suggestions['transportation'], start_date, end_date, destination)
            
            return str(calendar)
            
        except Exception as e:
            logger.error(f"Error creating calendar: {str(e)}")
            return self._create_basic_calendar(trip_data)

    def _add_main_trip_event(self, calendar: Calendar, destination: str, start_date: str, end_date: str, preferences: str):
        """Add the main trip event to calendar"""
        try:
            event = Event()
            event.name = f"Trip to {destination}"
            event.begin = datetime.strptime(start_date, '%Y-%m-%d')
            
            # Calculate end date (add one day since it's all-day event)
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            event.end = end_dt
            
            event.all_day = True
            event.description = f"Trip to {destination}"
            if preferences:
                event.description += f"\n\nPreferences: {preferences}"
            
            event.location = destination
            event.uid = str(uuid.uuid4())
            
            # Add reminder 1 week before
            alarm = DisplayAlarm(trigger=timedelta(weeks=-1))
            event.alarms.append(alarm)
            
            calendar.events.add(event)
            
        except Exception as e:
            logger.error(f"Error adding main trip event: {str(e)}")

    def _add_itinerary_events(self, calendar: Calendar, itinerary: List[Dict], destination: str):
        """Add daily itinerary events to calendar"""
        try:
            for day_plan in itinerary:
                if not isinstance(day_plan, dict):
                    continue
                
                date_str = day_plan.get('date', '')
                day_num = day_plan.get('day', '')
                activities = day_plan.get('activities', [])
                meals = day_plan.get('meals', {})
                
                if not date_str:
                    continue
                
                # Add daily overview event
                event = Event()
                event.name = f"Day {day_num} - {destination}"
                event.begin = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=9)
                event.end = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=18)
                
                # Create description
                description = f"Daily itinerary for {destination}\n\n"
                
                if activities:
                    description += "Activities:\n"
                    for activity in activities:
                        if isinstance(activity, str):
                            description += f"• {activity}\n"
                    description += "\n"
                
                if meals:
                    description += "Meals:\n"
                    for meal_type, meal_desc in meals.items():
                        if meal_desc:
                            description += f"• {meal_type.title()}: {meal_desc}\n"
                
                event.description = description.strip()
                event.location = destination
                event.uid = str(uuid.uuid4())
                
                # Add reminder 2 hours before
                alarm = DisplayAlarm(trigger=timedelta(hours=-2))
                event.alarms.append(alarm)
                
                calendar.events.add(event)
                
                # Add specific meal events
                self._add_meal_events(calendar, meals, date_str, destination)
                
        except Exception as e:
            logger.error(f"Error adding itinerary events: {str(e)}")

    def _add_meal_events(self, calendar: Calendar, meals: Dict, date_str: str, destination: str):
        """Add individual meal events"""
        try:
            meal_times = {
                'breakfast': (8, 0),
                'lunch': (13, 0),
                'dinner': (19, 0)
            }
            
            for meal_type, meal_desc in meals.items():
                if not meal_desc or meal_type not in meal_times:
                    continue
                
                hour, minute = meal_times[meal_type]
                
                event = Event()
                event.name = f"{meal_type.title()} - {destination}"
                event.begin = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=hour, minute=minute)
                event.end = event.begin + timedelta(hours=1.5)
                
                event.description = f"{meal_type.title()}: {meal_desc}"
                event.location = destination
                event.uid = str(uuid.uuid4())
                
                # Add reminder 30 minutes before
                alarm = DisplayAlarm(trigger=timedelta(minutes=-30))
                event.alarms.append(alarm)
                
                calendar.events.add(event)
                
        except Exception as e:
            logger.error(f"Error adding meal events: {str(e)}")

    def _add_accommodation_events(self, calendar: Calendar, accommodations: List[Dict], start_date: str, end_date: str, destination: str):
        """Add accommodation check-in/check-out events"""
        try:
            if not accommodations:
                return
            
            # Use first accommodation for check-in/out events
            hotel = accommodations[0] if isinstance(accommodations[0], dict) else {}
            hotel_name = hotel.get('name', 'Hotel')
            
            # Check-in event
            checkin_event = Event()
            checkin_event.name = f"Check-in: {hotel_name}"
            checkin_event.begin = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=15)
            checkin_event.end = checkin_event.begin + timedelta(hours=1)
            checkin_event.description = f"Check-in at {hotel_name}\n\n{hotel.get('description', '')}"
            checkin_event.location = f"{hotel_name}, {destination}"
            checkin_event.uid = str(uuid.uuid4())
            
            # Add reminder 2 hours before
            alarm = DisplayAlarm(trigger=timedelta(hours=-2))
            checkin_event.alarms.append(alarm)
            
            calendar.events.add(checkin_event)
            
            # Check-out event
            checkout_event = Event()
            checkout_event.name = f"Check-out: {hotel_name}"
            checkout_event.begin = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=11)
            checkout_event.end = checkout_event.begin + timedelta(hours=1)
            checkout_event.description = f"Check-out from {hotel_name}"
            checkout_event.location = f"{hotel_name}, {destination}"
            checkout_event.uid = str(uuid.uuid4())
            
            # Add reminder 1 hour before
            alarm = DisplayAlarm(trigger=timedelta(hours=-1))
            checkout_event.alarms.append(alarm)
            
            calendar.events.add(checkout_event)
            
        except Exception as e:
            logger.error(f"Error adding accommodation events: {str(e)}")

    def _add_activity_reminders(self, calendar: Calendar, activities: List[Dict], start_date: str, destination: str):
        """Add activity reminder events"""
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            
            for i, activity in enumerate(activities):
                if not isinstance(activity, dict):
                    continue
                
                name = activity.get('name', f'Activity {i+1}')
                description = activity.get('description', '')
                duration = activity.get('duration', '2 hours')
                cost = activity.get('cost', '')
                best_time = activity.get('best_time', '')
                
                # Schedule activity reminder on second day (adjust as needed)
                activity_date = start_dt + timedelta(days=min(i+1, 3))
                
                event = Event()
                event.name = f"Activity: {name}"
                event.begin = activity_date.replace(hour=10 + (i % 6))  # Spread activities throughout day
                event.end = event.begin + timedelta(hours=2)  # Default 2 hour duration
                
                event_description = f"Activity: {name}\n\n{description}"
                if duration:
                    event_description += f"\nDuration: {duration}"
                if cost:
                    event_description += f"\nCost: {cost}"
                if best_time:
                    event_description += f"\nBest time: {best_time}"
                
                event.description = event_description
                event.location = destination
                event.uid = str(uuid.uuid4())
                
                # Add reminder 1 hour before
                alarm = DisplayAlarm(trigger=timedelta(hours=-1))
                event.alarms.append(alarm)
                
                calendar.events.add(event)
                
        except Exception as e:
            logger.error(f"Error adding activity reminders: {str(e)}")

    def _add_restaurant_events(self, calendar: Calendar, restaurants: List[Dict], start_date: str, destination: str):
        """Add restaurant reservation reminders"""
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            
            for i, restaurant in enumerate(restaurants):
                if not isinstance(restaurant, dict):
                    continue
                
                name = restaurant.get('name', f'Restaurant {i+1}')
                cuisine = restaurant.get('cuisine', '')
                reservation_required = restaurant.get('reservation_required', False)
                
                if not reservation_required:
                    continue
                
                # Schedule reservation reminder for the day before trip
                reminder_date = start_dt - timedelta(days=1)
                
                event = Event()
                event.name = f"Make Reservation: {name}"
                event.begin = reminder_date.replace(hour=10)
                event.end = event.begin + timedelta(minutes=30)
                
                event_description = f"Remember to make reservation at {name}"
                if cuisine:
                    event_description += f"\nCuisine: {cuisine}"
                
                event.description = event_description
                event.location = destination
                event.uid = str(uuid.uuid4())
                
                calendar.events.add(event)
                
        except Exception as e:
            logger.error(f"Error adding restaurant events: {str(e)}")

    def _add_transportation_events(self, calendar: Calendar, transportation: List[Dict], start_date: str, end_date: str, destination: str):
        """Add transportation booking reminders"""
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            for transport in transportation:
                if not isinstance(transport, dict):
                    continue
                
                transport_type = transport.get('type', 'Transportation')
                option = transport.get('option', '')
                booking_required = transport.get('booking_required', False)
                
                if not booking_required:
                    continue
                
                # Add booking reminder 1 week before trip
                reminder_date = start_dt - timedelta(days=7)
                
                event = Event()
                event.name = f"Book {transport_type}: {option}"
                event.begin = reminder_date.replace(hour=10)
                event.end = event.begin + timedelta(minutes=30)
                
                event.description = f"Book {transport_type} ({option}) for trip to {destination}"
                event.location = "Online/Phone booking"
                event.uid = str(uuid.uuid4())
                
                calendar.events.add(event)
                
        except Exception as e:
            logger.error(f"Error adding transportation events: {str(e)}")

    def _create_basic_calendar(self, trip_data: Dict) -> str:
        """Create basic calendar with minimal trip information"""
        try:
            calendar = Calendar()
            calendar.creator = "AI Trip Planner"
            
            destination = trip_data.get('destination', 'Trip')
            start_date = trip_data.get('start_date', '')
            end_date = trip_data.get('end_date', '')
            
            if start_date and end_date:
                event = Event()
                event.name = f"Trip to {destination}"
                event.begin = datetime.strptime(start_date, '%Y-%m-%d')
                event.end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                event.all_day = True
                event.description = f"Trip to {destination}"
                event.location = destination
                event.uid = str(uuid.uuid4())
                
                calendar.events.add(event)
            
            return str(calendar)
            
        except Exception as e:
            logger.error(f"Error creating basic calendar: {str(e)}")
            return "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//AI Trip Planner//Basic Calendar//EN\nEND:VCALENDAR"

    def create_google_calendar_url(self, trip_data: Dict, ai_suggestions: Dict) -> str:
        """
        Create a Google Calendar quick add URL for the main trip event
        
        Args:
            trip_data: Trip data including dates and destination
            ai_suggestions: AI-generated suggestions
            
        Returns:
            str: Google Calendar URL for quick adding
        """
        try:
            destination = trip_data.get('destination', 'Trip')
            start_date = trip_data.get('start_date', '')
            end_date = trip_data.get('end_date', '')
            preferences = trip_data.get('preferences', '')
            
            # Format for Google Calendar
            title = f"Trip to {destination}"
            
            # Create description
            description = f"Trip to {destination}"
            if preferences:
                description += f"\\n\\nPreferences: {preferences}"
            
            if 'itinerary' in ai_suggestions and ai_suggestions['itinerary']:
                description += "\\n\\nItinerary highlights:"
                for i, day in enumerate(ai_suggestions['itinerary'][:3]):  # First 3 days
                    if isinstance(day, dict) and 'activities' in day:
                        description += f"\\nDay {day.get('day', i+1)}: {', '.join(day['activities'][:2])}"
            
            # Create dates (Google Calendar format: YYYYMMDD)
            start_date_formatted = start_date.replace('-', '')
            end_date_formatted = end_date.replace('-', '')
            
            # Build Google Calendar URL
            base_url = "https://calendar.google.com/calendar/render"
            params = {
                'action': 'TEMPLATE',
                'text': title,
                'dates': f"{start_date_formatted}/{end_date_formatted}",
                'details': description,
                'location': destination
            }
            
            # Build URL
            url = base_url + "?" + "&".join([f"{k}={v.replace(' ', '%20').replace('\n', '%0A')}" for k, v in params.items()])
            return url
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar URL: {str(e)}")
            return "https://calendar.google.com"

# Global calendar service instance
calendar_service = CalendarService()