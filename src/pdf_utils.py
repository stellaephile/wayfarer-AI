# pdf_utils.py
import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import base64

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Service for generating PDF itineraries from trip data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        # Subheading style
        self.subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Body style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Highlight style
        self.highlight_style = ParagraphStyle(
            'Highlight',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )

    def generate_trip_pdf(self, trip_data: Dict, ai_suggestions: Dict, weather_data: Dict = None) -> bytes:
        """
        Generate a comprehensive PDF itinerary
        
        Args:
            trip_data: Trip data including dates, destination, budget
            ai_suggestions: AI-generated suggestions including itinerary
            weather_data: Weather forecast data (optional)
            
        Returns:
            bytes: PDF content as bytes
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Add title page
            self._add_title_page(story, trip_data, ai_suggestions)
            
            # Add trip overview
            self._add_trip_overview(story, trip_data, ai_suggestions)
            
            # Add weather information
            if weather_data:
                self._add_weather_section(story, weather_data)
            
            # Add detailed itinerary
            if 'itinerary' in ai_suggestions and ai_suggestions['itinerary']:
                self._add_detailed_itinerary(story, ai_suggestions['itinerary'], weather_data)
            
            # Add accommodations
            if 'accommodations' in ai_suggestions and ai_suggestions['accommodations']:
                self._add_accommodations_section(story, ai_suggestions['accommodations'])
            
            # Add activities
            if 'activities' in ai_suggestions and ai_suggestions['activities']:
                self._add_activities_section(story, ai_suggestions['activities'])
            
            # Add restaurants
            if 'restaurants' in ai_suggestions and ai_suggestions['restaurants']:
                self._add_restaurants_section(story, ai_suggestions['restaurants'])
            
            # Add transportation
            if 'transportation' in ai_suggestions and ai_suggestions['transportation']:
                self._add_transportation_section(story, ai_suggestions['transportation'])
            
            # Add budget breakdown
            if 'budget_breakdown' in ai_suggestions:
                self._add_budget_section(story, ai_suggestions['budget_breakdown'], trip_data)
            
            # Add tips and packing list
            self._add_tips_and_packing(story, ai_suggestions)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return self._create_basic_pdf(trip_data)

    def _add_title_page(self, story: List, trip_data: Dict, ai_suggestions: Dict):
        """Add title page to PDF"""
        try:
            destination = trip_data.get('destination', 'Unknown Destination')
            start_date = trip_data.get('start_date', '')
            end_date = trip_data.get('end_date', '')
            
            # Title
            title = Paragraph(f"Trip to {destination}", self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Subtitle with dates
            if start_date and end_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                duration = (end_dt - start_dt).days + 1
                
                subtitle = Paragraph(
                    f"{start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}<br/>({duration} days)",
                    ParagraphStyle('Subtitle', parent=self.body_style, fontSize=14, alignment=TA_CENTER, spaceAfter=30)
                )
                story.append(subtitle)
            
            # Generated info
            generated_text = Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y')}<br/>by AI Trip Planner",
                ParagraphStyle('Generated', parent=self.body_style, fontSize=10, alignment=TA_CENTER, textColor=colors.grey)
            )
            story.append(generated_text)
            
            story.append(PageBreak())
            
        except Exception as e:
            logger.error(f"Error adding title page: {str(e)}")

    def _add_trip_overview(self, story: List, trip_data: Dict, ai_suggestions: Dict):
        """Add trip overview section"""
        try:
            story.append(Paragraph("Trip Overview", self.heading_style))
            
            # Create overview table
            overview_data = []
            
            # Destination
            overview_data.append(['Destination:', trip_data.get('destination', 'N/A')])
            
            # Dates
            if trip_data.get('start_date') and trip_data.get('end_date'):
                start_dt = datetime.strptime(trip_data['start_date'], '%Y-%m-%d')
                end_dt = datetime.strptime(trip_data['end_date'], '%Y-%m-%d')
                duration = (end_dt - start_dt).days + 1
                overview_data.append(['Travel Dates:', f"{start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}"])
                overview_data.append(['Duration:', f"{duration} days"])
            
            # Budget
            if trip_data.get('budget'):
                currency_symbol = trip_data.get('currency_symbol', '$')
                overview_data.append(['Budget:', f"{currency_symbol}{trip_data['budget']:,.2f}"])
            
            # Preferences
            if trip_data.get('preferences'):
                overview_data.append(['Preferences:', trip_data['preferences']])
            
            # Create table
            overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
            overview_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(overview_table)
            story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error adding trip overview: {str(e)}")

    def _add_weather_section(self, story: List, weather_data: Dict):
        """Add weather information section"""
        try:
            story.append(Paragraph("Weather Forecast", self.heading_style))
            
            summary = weather_data.get('summary', {})
            
            # Weather summary
            weather_info = []
            weather_info.append(['Temperature Range:', summary.get('avg_temperature', 'N/A')])
            weather_info.append(['Conditions:', summary.get('conditions', 'N/A')])
            
            weather_table = Table(weather_info, colWidths=[2*inch, 4*inch])
            weather_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(weather_table)
            story.append(Spacer(1, 12))
            
            # Weather recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Weather Recommendations:", self.subheading_style))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", self.body_style))
            
            story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error adding weather section: {str(e)}")

    def _add_detailed_itinerary(self, story: List, itinerary: List[Dict], weather_data: Dict = None):
        """Add detailed daily itinerary"""
        try:
            story.append(Paragraph("Daily Itinerary", self.heading_style))
            
            # Get daily weather forecasts if available
            daily_weather = {}
            if weather_data and 'daily_forecast' in weather_data:
                for day_weather in weather_data['daily_forecast']:
                    date = day_weather.get('date', '')
                    daily_weather[date] = day_weather
            
            for day_plan in itinerary:
                if not isinstance(day_plan, dict):
                    continue
                
                date_str = day_plan.get('date', '')
                day_num = day_plan.get('day', '')
                day_name = day_plan.get('day_name', '')
                activities = day_plan.get('activities', [])
                meals = day_plan.get('meals', {})
                
                # Day header
                day_header = f"Day {day_num}"
                if day_name and date_str:
                    formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
                    day_header += f" - {day_name}, {formatted_date}"
                
                story.append(Paragraph(day_header, self.subheading_style))
                
                # Add weather for this day
                if date_str in daily_weather:
                    day_weather = daily_weather[date_str]
                    temp_high = day_weather.get('temperature', {}).get('high', 'N/A')
                    temp_low = day_weather.get('temperature', {}).get('low', 'N/A')
                    description = day_weather.get('description', 'N/A')
                    icon = day_weather.get('icon', '')
                    
                    weather_text = f"{icon} {description} | High: {temp_high}°C, Low: {temp_low}°C"
                    story.append(Paragraph(weather_text, self.highlight_style))
                    
                    # Weather recommendations for the day
                    day_recommendations = day_weather.get('recommendations', [])
                    if day_recommendations:
                        rec_text = "Weather tips: " + " | ".join(day_recommendations[:2])
                        story.append(Paragraph(rec_text, ParagraphStyle('WeatherTip', parent=self.body_style, fontSize=10, textColor=colors.blue)))
                
                # Activities
                if activities:
                    story.append(Paragraph("Activities:", ParagraphStyle('ActivityHeader', parent=self.body_style, fontName='Helvetica-Bold')))
                    for activity in activities:
                        if isinstance(activity, str):
                            story.append(Paragraph(f"• {activity}", self.body_style))
                
                # Meals
                if meals:
                    story.append(Paragraph("Meals:", ParagraphStyle('MealHeader', parent=self.body_style, fontName='Helvetica-Bold')))
                    for meal_type, meal_desc in meals.items():
                        if meal_desc:
                            story.append(Paragraph(f"• {meal_type.title()}: {meal_desc}", self.body_style))
                
                story.append(Spacer(1, 15))
            
        except Exception as e:
            logger.error(f"Error adding detailed itinerary: {str(e)}")

    def _add_accommodations_section(self, story: List, accommodations: List[Dict]):
        """Add accommodations section"""
        try:
            story.append(Paragraph("Recommended Accommodations", self.heading_style))
            
            for i, hotel in enumerate(accommodations):
                if not isinstance(hotel, dict):
                    continue
                
                name = hotel.get('name', f'Hotel {i+1}')
                hotel_type = hotel.get('type', 'Hotel')
                price_range = hotel.get('price_range', 'N/A')
                rating = hotel.get('rating', 'N/A')
                location = hotel.get('location', 'N/A')
                description = hotel.get('description', '')
                amenities = hotel.get('amenities', [])
                
                # Hotel header
                story.append(Paragraph(f"{name} ({hotel_type})", self.subheading_style))
                
                # Hotel details table
                hotel_data = []
                hotel_data.append(['Price Range:', price_range])
                hotel_data.append(['Rating:', f"{rating}/5" if rating != 'N/A' else 'N/A'])
                hotel_data.append(['Location:', location])
                
                if amenities:
                    amenities_text = ', '.join(amenities[:5])  # Limit to 5 amenities
                    hotel_data.append(['Amenities:', amenities_text])
                
                hotel_table = Table(hotel_data, colWidths=[1.5*inch, 4.5*inch])
                hotel_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(hotel_table)
                
                if description:
                    story.append(Paragraph(description, self.body_style))
                
                story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error adding accommodations section: {str(e)}")

    def _add_activities_section(self, story: List, activities: List[Dict]):
        """Add activities section"""
        try:
            story.append(Paragraph("Recommended Activities", self.heading_style))
            
            for activity in activities:
                if not isinstance(activity, dict):
                    continue
                
                name = activity.get('name', 'Activity')
                activity_type = activity.get('type', 'Activity')
                duration = activity.get('duration', 'N/A')
                cost = activity.get('cost', 'N/A')
                description = activity.get('description', '')
                rating = activity.get('rating', 'N/A')
                best_time = activity.get('best_time', 'N/A')
                
                # Activity header
                story.append(Paragraph(f"{name} ({activity_type})", self.subheading_style))
                
                # Activity details
                activity_details = []
                activity_details.append(['Duration:', duration])
                activity_details.append(['Cost:', cost])
                activity_details.append(['Rating:', f"{rating}/5" if rating != 'N/A' else 'N/A'])
                activity_details.append(['Best Time:', best_time])
                
                activity_table = Table(activity_details, colWidths=[1.5*inch, 4.5*inch])
                activity_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(activity_table)
                
                if description:
                    story.append(Paragraph(description, self.body_style))
                
                story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error adding activities section: {str(e)}")

    def _add_restaurants_section(self, story: List, restaurants: List[Dict]):
        """Add restaurants section"""
        try:
            story.append(Paragraph("Recommended Restaurants", self.heading_style))
            
            for restaurant in restaurants:
                if not isinstance(restaurant, dict):
                    continue
                
                name = restaurant.get('name', 'Restaurant')
                cuisine = restaurant.get('cuisine', 'N/A')
                price_range = restaurant.get('price_range', 'N/A')
                rating = restaurant.get('rating', 'N/A')
                location = restaurant.get('location', 'N/A')
                specialties = restaurant.get('specialties', [])
                reservation_required = restaurant.get('reservation_required', False)
                
                # Restaurant header
                story.append(Paragraph(f"{name}", self.subheading_style))
                
                # Restaurant details
                restaurant_details = []
                restaurant_details.append(['Cuisine:', cuisine])
                restaurant_details.append(['Price Range:', price_range])
                restaurant_details.append(['Rating:', f"{rating}/5" if rating != 'N/A' else 'N/A'])
                restaurant_details.append(['Location:', location])
                restaurant_details.append(['Reservation:', 'Required' if reservation_required else 'Not Required'])
                
                if specialties:
                    specialties_text = ', '.join(specialties[:3])
                    restaurant_details.append(['Specialties:', specialties_text])
                
                restaurant_table = Table(restaurant_details, colWidths=[1.5*inch, 4.5*inch])
                restaurant_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(restaurant_table)
                story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error adding restaurants section: {str(e)}")

    def _add_transportation_section(self, story: List, transportation: List[Dict]):
        """Add transportation section"""
        try:
            story.append(Paragraph("Transportation Options", self.heading_style))
            
            for transport in transportation:
                if not isinstance(transport, dict):
                    continue
                
                transport_type = transport.get('type', 'Transportation')
                option = transport.get('option', 'N/A')
                cost = transport.get('cost', 'N/A')
                duration = transport.get('duration', 'N/A')
                description = transport.get('description', '')
                booking_required = transport.get('booking_required', False)
                
                # Transport header
                story.append(Paragraph(f"{transport_type} - {option}", self.subheading_style))
                
                # Transport details
                transport_details = []
                transport_details.append(['Cost:', cost])
                transport_details.append(['Duration:', duration])
                transport_details.append(['Booking Required:', 'Yes' if booking_required else 'No'])
                
                transport_table = Table(transport_details, colWidths=[1.5*inch, 4.5*inch])
                transport_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(transport_table)
                
                if description:
                    story.append(Paragraph(description, self.body_style))
                
                story.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error adding transportation section: {str(e)}")

    def _add_budget_section(self, story: List, budget_breakdown: Dict, trip_data: Dict):
        """Add budget breakdown section"""
        try:
            story.append(Paragraph("Budget Breakdown", self.heading_style))
            
            currency_symbol = trip_data.get('currency_symbol', '$')
            
            # Create budget table
            budget_data = [['Category', 'Amount']]
            
            for category, amount in budget_breakdown.items():
                # Clean up category name
                category_clean = category.replace('_', ' ').title()
                budget_data.append([category_clean, str(amount)])
            
            # Add total
            total_budget = trip_data.get('budget', 0)
            if total_budget:
                budget_data.append(['TOTAL', f"{currency_symbol}{total_budget:,.2f}"])
            
            budget_table = Table(budget_data, colWidths=[3*inch, 3*inch])
            budget_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            story.append(budget_table)
            story.append(Spacer(1, 20))
            
        except Exception as e:
            logger.error(f"Error adding budget section: {str(e)}")

    def _add_tips_and_packing(self, story: List, ai_suggestions: Dict):
        """Add tips and packing list section"""
        try:
            # Tips section
            tips = ai_suggestions.get('tips', [])
            if tips:
                story.append(Paragraph("Travel Tips", self.heading_style))
                for tip in tips:
                    story.append(Paragraph(f"• {tip}", self.body_style))
                story.append(Spacer(1, 15))
            
            # Packing list
            packing_list = ai_suggestions.get('packing_list', [])
            if packing_list:
                story.append(Paragraph("Packing List", self.heading_style))
                for item in packing_list:
                    story.append(Paragraph(f"• {item}", self.body_style))
                story.append(Spacer(1, 15))
            
        except Exception as e:
            logger.error(f"Error adding tips and packing: {str(e)}")

    def _create_basic_pdf(self, trip_data: Dict) -> bytes:
        """Create basic PDF with minimal information"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            destination = trip_data.get('destination', 'Trip')
            story.append(Paragraph(f"Trip to {destination}", self.title_style))
            story.append(Paragraph("Basic itinerary information", self.body_style))
            
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error creating basic PDF: {str(e)}")
            return b"PDF generation failed"

    def create_pdf_download_link(self, pdf_content: bytes, filename: str) -> str:
        """Create a download link for PDF content"""
        try:
            b64 = base64.b64encode(pdf_content).decode()
            return f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
        except Exception as e:
            logger.error(f"Error creating download link: {str(e)}")
            return ""

# Global PDF generator instance
pdf_generator = PDFGenerator()