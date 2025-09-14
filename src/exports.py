# exports.py - Fixed PDF Download
from io import BytesIO
import json
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

def generate_pdf(itinerary: dict, destination: str = "Trip") -> bytes:
    """Generate a PDF from the itinerary data and return as bytes"""
    
    if not FPDF_AVAILABLE:
        # Fallback: Create simple text content as bytes
        content = create_text_summary(itinerary, destination)
        return content.encode('utf-8')
    
    try:
        # Create PDF using FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, f"AI Trip Planner - {destination}", ln=True, align="C")
        pdf.ln(10)
        
        # Trip details
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Destination: {itinerary.get('destination', 'Unknown')}", ln=True)
        pdf.cell(0, 8, f"Duration: {itinerary.get('duration', 'Unknown')}", ln=True)
        pdf.cell(0, 8, f"Budget: ${itinerary.get('budget', 'Unknown'):,}", ln=True)
        pdf.ln(5)
        
        # Budget breakdown
        if "budget_breakdown" in itinerary:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Budget Breakdown", ln=True)
            pdf.set_font("Arial", "", 10)
            
            budget_breakdown = itinerary["budget_breakdown"]
            for category, amount in budget_breakdown.items():
                pdf.cell(0, 6, f"• {category.title()}: {amount}", ln=True)
            pdf.ln(3)
        
        # Daily itinerary
        if "itinerary" in itinerary and itinerary["itinerary"]:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Daily Itinerary", ln=True)
            
            for day in itinerary["itinerary"]:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"Day {day.get('day', '?')} - {day.get('date', 'Unknown')} ({day.get('day_name', 'Unknown')})", ln=True)
                
                # Activities
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, "Activities:", ln=True)
                pdf.set_font("Arial", "", 10)
                for activity in day.get("activities", []):
                    # Handle long text that might cause issues
                    activity_text = activity[:80] + "..." if len(activity) > 80 else activity
                    pdf.cell(0, 5, f"• {activity_text}", ln=True)
                
                # Meals
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, "Meals:", ln=True)
                pdf.set_font("Arial", "", 10)
                meals = day.get("meals", {})
                for meal_type, suggestion in meals.items():
                    meal_text = suggestion[:60] + "..." if len(suggestion) > 60 else suggestion
                    pdf.cell(0, 5, f"• {meal_type.title()}: {meal_text}", ln=True)
                
                pdf.ln(3)
        
        # Accommodations
        if "accommodations" in itinerary:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Recommended Accommodations", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for hotel in itinerary["accommodations"]:
                pdf.cell(0, 6, f"• {hotel.get('name', 'Hotel')}: {hotel.get('price_range', 'Price varies')}", ln=True)
                if hotel.get('description'):
                    desc_text = hotel['description'][:70] + "..." if len(hotel['description']) > 70 else hotel['description']
                    pdf.cell(0, 5, f"  {desc_text}", ln=True)
                pdf.ln(2)
        
        # Activities
        if "activities" in itinerary:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Recommended Activities", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for activity in itinerary["activities"]:
                activity_name = activity.get('name', 'Activity')[:50]
                cost = activity.get('cost', 'Price varies')
                pdf.cell(0, 6, f"• {activity_name}: {cost}", ln=True)
                if activity.get('description'):
                    desc_text = activity['description'][:70] + "..." if len(activity['description']) > 70 else activity['description']
                    pdf.cell(0, 5, f"  {desc_text}", ln=True)
                pdf.ln(2)
        
        # Tips
        if "tips" in itinerary:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Travel Tips", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for tip in itinerary["tips"]:
                tip_text = tip[:80] + "..." if len(tip) > 80 else tip
                pdf.cell(0, 5, f"• {tip_text}", ln=True)
        
        # Return PDF as bytes - THIS IS KEY!
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        # Fallback to text format if PDF generation fails
        print(f"PDF generation error: {e}")
        content = create_text_summary(itinerary, destination)
        return content.encode('utf-8')

def create_text_summary(itinerary: dict, destination: str) -> str:
    """Create a text summary as fallback"""
    content = f"AI Trip Planner Itinerary\n\n"
    content += f"Destination: {itinerary.get('destination', 'Unknown')}\n"
    content += f"Duration: {itinerary.get('duration', 'Unknown')}\n"
    content += f"Budget: ${itinerary.get('budget', 'Unknown')}\n\n"
    
    if "itinerary" in itinerary:
        content += "Daily Itinerary:\n"
        for day in itinerary["itinerary"]:
            content += f"\nDay {day.get('day', '?')} - {day.get('date', 'Unknown')}\n"
            for activity in day.get('activities', []):
                content += f"• {activity}\n"
    
    content += f"\n\nGenerated by AI Trip Planner"
    return content

def generate_ics(itinerary: dict) -> str:
    """Generate an ICS calendar file from the itinerary"""
    try:
        # Try using ics library
        from ics import Calendar, Event
        from datetime import datetime, date
        
        cal = Calendar()
        
        if "itinerary" in itinerary:
            for day in itinerary["itinerary"]:
                event = Event()
                event.name = f"{itinerary.get('destination', 'Trip')} - Day {day.get('day', 'X')}"
                
                # Parse date
                try:
                    event_date = datetime.strptime(day.get('date', ''), '%Y-%m-%d').date()
                    event.begin = event_date
                    event.make_all_day()
                except:
                    continue
                
                # Add description
                description = f"Activities: {', '.join(day.get('activities', []))}\n"
                meals = day.get('meals', {})
                description += f"Meals:\n"
                for meal_type, suggestion in meals.items():
                    description += f"• {meal_type.title()}: {suggestion}\n"
                
                event.description = description
                cal.events.add(event)
        
        return str(cal)
        
    except ImportError:
        # Fallback to simple ICS format
        content = "BEGIN:VCALENDAR\n"
        content += "VERSION:2.0\n"
        content += "PRODID:-//AI Trip Planner//EN\n"
        content += "CALSCALE:GREGORIAN\n"
        
        if "itinerary" in itinerary:
            for day in itinerary["itinerary"]:
                date_str = day.get('date', '').replace('-', '')
                content += "BEGIN:VEVENT\n"
                content += f"DTSTART:{date_str}T090000Z\n"
                content += f"DTEND:{date_str}T180000Z\n"
                content += f"SUMMARY:{itinerary.get('destination', 'Trip')} - Day {day.get('day', 'X')}\n"
                content += f"DESCRIPTION:Activities: {', '.join(day.get('activities', []))}\n"
                content += f"UID:{date_str}-trip-{day.get('day', 'x')}@aitripplanner.com\n"
                content += "END:VEVENT\n"
        
        content += "END:VCALENDAR\n"
        return content
    
    except Exception as e:
        # Final fallback
        return f"# AI Trip Planner Calendar\nDestination: {itinerary.get('destination', 'Unknown')}\nError generating calendar: {str(e)}"
