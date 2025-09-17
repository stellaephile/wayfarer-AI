import streamlit as st
import json
from datetime import datetime, timedelta
from database import db
from vertex_ai_utils import VertexAITripPlanner
from css_styles import inject_floating_button
from credit_widget import credit_widget
from pdf_utils import pdf_generator
from calendar_utils import calendar_service
import base64
import io
import json

def display_weather_info(weather_data, ai_suggestions):
    """Display weather information in the itinerary"""
    if not weather_data:
        return
    
    st.subheader("🌤️ Weather Forecast")
    
    summary = weather_data.get('summary', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Temperature Range",
            value=summary.get('avg_temperature', 'N/A')
        )
    
    with col2:
        st.metric(
            label="Conditions",
            value=summary.get('conditions', 'N/A')
        )
    
    # Weather recommendations
    recommendations = summary.get('recommendations', [])
    if recommendations:
        st.write("**Weather Recommendations:**")
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # Daily forecast (show first 7 days)
    daily_forecast = weather_data.get('daily_forecast', [])
    if daily_forecast:
        st.write("**Daily Forecast:**")
        
        # Create a more compact daily forecast display
        forecast_data = []
        for day in daily_forecast[:7]:  # Show only first 7 days
            date_str = day.get('date', '')
            if date_str:
                formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%b %d')
                day_name = day.get('day_name', '')[:3]  # Abbreviate day name
                temp_high = day.get('temperature', {}).get('high', 'N/A')
                temp_low = day.get('temperature', {}).get('low', 'N/A')
                icon = day.get('icon', '☀️')
                description = day.get('description', 'N/A')
                
                forecast_data.append([
                    f"{day_name} {formatted_date}",
                    f"{icon} {description}",
                    f"{temp_high}°C / {temp_low}°C"
                ])
        
        if forecast_data:
            forecast_df = pd.DataFrame(forecast_data, columns=['Date', 'Weather', 'Temperature'])
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
    
    st.divider()

# Add this function to handle PDF generation
def generate_and_display_pdf_options(trip_data, ai_suggestions, weather_data=None):
    """Generate PDF download options for the itinerary"""
    
    st.subheader("📄 Download Detailed Itinerary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("🔄 Generating detailed PDF itinerary..."):
                    # Generate PDF content
                    pdf_content = pdf_generator.generate_trip_pdf(
                        trip_data=trip_data,
                        ai_suggestions=ai_suggestions,
                        weather_data=weather_data
                    )
                    
                    # Create download filename
                    destination = trip_data.get('destination', 'Trip').replace(' ', '_')
                    start_date = trip_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                    filename = f"{destination}_{start_date}_Itinerary.pdf"
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download PDF Itinerary",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.success("✅ PDF generated successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
                logger.error(f"PDF generation error: {str(e)}")
    
    with col2:
        st.info("📋 The PDF includes:\n• Complete itinerary with weather info\n• Accommodation recommendations\n• Activities & restaurants\n• Packing list & tips\n• Budget breakdown")

# Add this function to handle calendar integration
def generate_and_display_calendar_options(trip_data, ai_suggestions):
    """Generate calendar integration options"""
    
    st.subheader("📅 Add to Calendar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📅 Download Calendar (.ics)", type="secondary", use_container_width=True):
            try:
                with st.spinner("🔄 Creating calendar events..."):
                    # Generate ICS calendar content
                    calendar_content = calendar_service.create_calendar_from_itinerary(
                        trip_data=trip_data,
                        ai_suggestions=ai_suggestions
                    )
                    
                    # Create download filename
                    destination = trip_data.get('destination', 'Trip').replace(' ', '_')
                    start_date = trip_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                    filename = f"{destination}_{start_date}_Calendar.ics"
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download Calendar File",
                        data=calendar_content,
                        file_name=filename,
                        mime="text/calendar",
                        use_container_width=True
                    )
                    
                    st.success("✅ Calendar file created successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error creating calendar: {str(e)}")
                logger.error(f"Calendar creation error: {str(e)}")
    
    with col2:
        # Google Calendar quick add option
        try:
            google_calendar_url = calendar_service.create_google_calendar_url(
                trip_data=trip_data,
                ai_suggestions=ai_suggestions
            )
            
            st.markdown(
                f'<a href="{google_calendar_url}" target="_blank">'
                '<button style="background-color: #4285f4; color: white; border: none; '
                'padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%;">'
                '🗓️ Add to Google Calendar'
                '</button></a>',
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.button("🗓️ Add to Google Calendar", disabled=True, help="Calendar integration temporarily unavailable")

def display_trip_source_info(trip_data):
    """Display source information for the trip"""
    source = trip_data.get('source', 'user_input')
    
    source_info = {
        'user_input': ('👤', 'Created by you'),
        'ai_generated': ('🤖', 'AI Generated'),
        'imported': ('📁', 'Imported'),
        'api': ('🔗', 'API Integration'),
        'template': ('📋', 'From Template')
    }
    
    icon, description = source_info.get(source, ('❓', 'Unknown Source'))
    
    st.caption(f"{icon} {description}")
    
def validate_trip_dates(start_date, end_date):
    """Validate trip dates to ensure they are not in the past and end date is after start date"""
    today = datetime.now().date()
    
    if start_date < today:
        st.error("❌ Start date cannot be in the past!")
        return False
    
    if end_date < today:
        st.error("❌ End date cannot be in the past!")
        return False
        
    if start_date >= end_date:
        st.error("❌ End date must be after start date!")
        return False
    
    return True

def calculate_credits_used(suggestions):
    """Calculate credits used based on AI suggestions complexity"""
    try:
        base_credits = 5  # Base credits for trip generation
        
        # Additional credits based on content complexity
        additional_credits = 0
        
        # Check itinerary complexity
        if 'itinerary' in suggestions and suggestions['itinerary']:
            if isinstance(suggestions['itinerary'], list):
                additional_credits += len(suggestions['itinerary']) * 0.5
            else:
                additional_credits += 2
        
        # Check accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
            additional_credits += len(suggestions['accommodations']) * 0.3
        
        # Check activities
        if 'activities' in suggestions and suggestions['activities']:
            additional_credits += len(suggestions['activities']) * 0.4
        
        # Check restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
            additional_credits += len(suggestions['restaurants']) * 0.3
        
        # Check transportation
        if 'transportation' in suggestions and suggestions['transportation']:
            additional_credits += len(suggestions['transportation']) * 0.2
        
        total_credits = base_credits + additional_credits
        
        # Cap at maximum 20 credits per trip
        return min(int(total_credits), 20)
        
    except Exception as e:
        # Default to 5 credits if calculation fails
        return 5

def get_currency_options():
    """Get list of popular currencies with their symbols and codes"""
    return {
        "USD": {"symbol": "$", "name": "US Dollar"},
        "EUR": {"symbol": "€", "name": "Euro"},
        "GBP": {"symbol": "£", "name": "British Pound"},
        "JPY": {"symbol": "¥", "name": "Japanese Yen"},
        "CAD": {"symbol": "C$", "name": "Canadian Dollar"},
        "AUD": {"symbol": "A$", "name": "Australian Dollar"},
        "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
        "CNY": {"symbol": "¥", "name": "Chinese Yuan"},
        "INR": {"symbol": "₹", "name": "Indian Rupee"},
        "BRL": {"symbol": "R$", "name": "Brazilian Real"},
        "MXN": {"symbol": "$", "name": "Mexican Peso"},
        "SGD": {"symbol": "S$", "name": "Singapore Dollar"},
        "HKD": {"symbol": "HK$", "name": "Hong Kong Dollar"},
        "NZD": {"symbol": "NZ$", "name": "New Zealand Dollar"},
        "SEK": {"symbol": "kr", "name": "Swedish Krona"},
        "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
        "DKK": {"symbol": "kr", "name": "Danish Krone"},
        "PLN": {"symbol": "zł", "name": "Polish Zloty"},
        "CZK": {"symbol": "Kč", "name": "Czech Koruna"},
        "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
        "RUB": {"symbol": "₽", "name": "Russian Ruble"},
        "ZAR": {"symbol": "R", "name": "South African Rand"},
        "KRW": {"symbol": "₩", "name": "South Korean Won"},
        "THB": {"symbol": "฿", "name": "Thai Baht"},
        "MYR": {"symbol": "RM", "name": "Malaysian Ringgit"},
        "IDR": {"symbol": "Rp", "name": "Indonesian Rupiah"},
        "PHP": {"symbol": "₱", "name": "Philippine Peso"},
        "VND": {"symbol": "₫", "name": "Vietnamese Dong"},
        "TRY": {"symbol": "₺", "name": "Turkish Lira"},
        "AED": {"symbol": "د.إ", "name": "UAE Dirham"},
        "SAR": {"symbol": "﷼", "name": "Saudi Riyal"},
        "EGP": {"symbol": "£", "name": "Egyptian Pound"},
        "ILS": {"symbol": "₪", "name": "Israeli Shekel"},
        "QAR": {"symbol": "﷼", "name": "Qatari Riyal"},
        "KWD": {"symbol": "د.ك", "name": "Kuwaiti Dinar"},
        "BHD": {"symbol": "د.ب", "name": "Bahraini Dinar"},
        "OMR": {"symbol": "﷼", "name": "Omani Rial"},
        "JOD": {"symbol": "د.ا", "name": "Jordanian Dinar"},
        "LBP": {"symbol": "ل.ل", "name": "Lebanese Pound"},
        "PKR": {"symbol": "₨", "name": "Pakistani Rupee"},
        "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
        "LKR": {"symbol": "₨", "name": "Sri Lankan Rupee"},
        "NPR": {"symbol": "₨", "name": "Nepalese Rupee"},
        "AFN": {"symbol": "؋", "name": "Afghan Afghani"},
        "AMD": {"symbol": "֏", "name": "Armenian Dram"},
        "AZN": {"symbol": "₼", "name": "Azerbaijani Manat"},
        "GEL": {"symbol": "₾", "name": "Georgian Lari"},
        "KZT": {"symbol": "₸", "name": "Kazakhstani Tenge"},
        "KGS": {"symbol": "лв", "name": "Kyrgyzstani Som"},
        "TJS": {"symbol": "ЅМ", "name": "Tajikistani Somoni"},
        "TMT": {"symbol": "T", "name": "Turkmenistani Manat"},
        "UZS": {"symbol": "лв", "name": "Uzbekistani Som"},
        "MNT": {"symbol": "₮", "name": "Mongolian Tugrik"},
        "LAK": {"symbol": "₭", "name": "Lao Kip"},
        "KHR": {"symbol": "៛", "name": "Cambodian Riel"},
        "MMK": {"symbol": "K", "name": "Myanmar Kyat"},
        "BND": {"symbol": "B$", "name": "Brunei Dollar"},
        "FJD": {"symbol": "FJ$", "name": "Fijian Dollar"},
        "PGK": {"symbol": "K", "name": "Papua New Guinea Kina"},
        "SBD": {"symbol": "SI$", "name": "Solomon Islands Dollar"},
        "VUV": {"symbol": "Vt", "name": "Vanuatu Vatu"},
        "WST": {"symbol": "WS$", "name": "Samoan Tala"},
        "TOP": {"symbol": "T$", "name": "Tongan Pa'anga"},
        "XPF": {"symbol": "₣", "name": "CFP Franc"},
        "NPR": {"symbol": "₨", "name": "Nepalese Rupee"},
        "BTN": {"symbol": "Nu.", "name": "Bhutanese Ngultrum"},
        "MVR": {"symbol": "Rf", "name": "Maldivian Rufiyaa"},
        "SCR": {"symbol": "₨", "name": "Seychellois Rupee"},
        "MUR": {"symbol": "₨", "name": "Mauritian Rupee"},
        "KMF": {"symbol": "CF", "name": "Comorian Franc"},
        "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
        "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
        "KES": {"symbol": "KSh", "name": "Kenyan Shilling"},
        "TZS": {"symbol": "TSh", "name": "Tanzanian Shilling"},
        "UGX": {"symbol": "USh", "name": "Ugandan Shilling"},
        "RWF": {"symbol": "RF", "name": "Rwandan Franc"},
        "BIF": {"symbol": "FBu", "name": "Burundian Franc"},
        "MWK": {"symbol": "MK", "name": "Malawian Kwacha"},
        "ZMW": {"symbol": "ZK", "name": "Zambian Kwacha"},
        "BWP": {"symbol": "P", "name": "Botswana Pula"},
        "SZL": {"symbol": "L", "name": "Swazi Lilangeni"},
        "LSL": {"symbol": "L", "name": "Lesotho Loti"},
        "NAD": {"symbol": "N$", "name": "Namibian Dollar"},
        "MZN": {"symbol": "MT", "name": "Mozambican Metical"},
        "AOA": {"symbol": "Kz", "name": "Angolan Kwanza"},
        "XOF": {"symbol": "CFA", "name": "West African CFA Franc"},
        "XAF": {"symbol": "FCFA", "name": "Central African CFA Franc"},
        "CDF": {"symbol": "FC", "name": "Congolese Franc"},
        "GMD": {"symbol": "D", "name": "Gambian Dalasi"},
        "GHS": {"symbol": "₵", "name": "Ghanaian Cedi"},
        "GNF": {"symbol": "FG", "name": "Guinean Franc"},
        "LRD": {"symbol": "L$", "name": "Liberian Dollar"},
        "SLL": {"symbol": "Le", "name": "Sierra Leonean Leone"},
        "NGN": {"symbol": "₦", "name": "Nigerian Naira"},
        "XOF": {"symbol": "CFA", "name": "West African CFA Franc"},
        "XAF": {"symbol": "FCFA", "name": "Central African CFA Franc"},
        "TND": {"symbol": "د.ت", "name": "Tunisian Dinar"},
        "DZD": {"symbol": "د.ج", "name": "Algerian Dinar"},
        "MAD": {"symbol": "د.م.", "name": "Moroccan Dirham"},
        "LYD": {"symbol": "ل.د", "name": "Libyan Dinar"},
        "SDG": {"symbol": "ج.س.", "name": "Sudanese Pound"},
        "SSP": {"symbol": "£", "name": "South Sudanese Pound"},
        "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
        "SOS": {"symbol": "S", "name": "Somali Shilling"},
        "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
        "ERN": {"symbol": "Nfk", "name": "Eritrean Nakfa"},
        "SYP": {"symbol": "£", "name": "Syrian Pound"},
        "LBP": {"symbol": "ل.ل", "name": "Lebanese Pound"},
        "JOD": {"symbol": "د.ا", "name": "Jordanian Dinar"},
        "IQD": {"symbol": "ع.د", "name": "Iraqi Dinar"},
        "IRR": {"symbol": "﷼", "name": "Iranian Rial"},
        "YER": {"symbol": "﷼", "name": "Yemeni Rial"},
        "OMR": {"symbol": "﷼", "name": "Omani Rial"},
        "QAR": {"symbol": "﷼", "name": "Qatari Riyal"},
        "BHD": {"symbol": "د.ب", "name": "Bahraini Dinar"},
        "KWD": {"symbol": "د.ك", "name": "Kuwaiti Dinar"},
        "AED": {"symbol": "د.إ", "name": "UAE Dirham"},
        "SAR": {"symbol": "﷼", "name": "Saudi Riyal"},
        "ILS": {"symbol": "₪", "name": "Israeli Shekel"},
        "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
        "CRC": {"symbol": "₡", "name": "Costa Rican Colón"},
        "GTQ": {"symbol": "Q", "name": "Guatemalan Quetzal"},
        "HNL": {"symbol": "L", "name": "Honduran Lempira"},
        "NIO": {"symbol": "C$", "name": "Nicaraguan Córdoba"},
        "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
        "SVC": {"symbol": "₡", "name": "Salvadoran Colón"},
        "BZD": {"symbol": "BZ$", "name": "Belize Dollar"},
        "JMD": {"symbol": "J$", "name": "Jamaican Dollar"},
        "TTD": {"symbol": "TT$", "name": "Trinidad and Tobago Dollar"},
        "BBD": {"symbol": "Bds$", "name": "Barbadian Dollar"},
        "XCD": {"symbol": "EC$", "name": "East Caribbean Dollar"},
        "AWG": {"symbol": "ƒ", "name": "Aruban Florin"},
        "ANG": {"symbol": "ƒ", "name": "Netherlands Antillean Guilder"},
        "SRD": {"symbol": "$", "name": "Surinamese Dollar"},
        "GYD": {"symbol": "G$", "name": "Guyanese Dollar"},
        "VES": {"symbol": "Bs.S", "name": "Venezuelan Bolívar"},
        "COP": {"symbol": "$", "name": "Colombian Peso"},
        "PEN": {"symbol": "S/", "name": "Peruvian Sol"},
        "BOB": {"symbol": "Bs", "name": "Bolivian Boliviano"},
        "CLP": {"symbol": "$", "name": "Chilean Peso"},
        "ARS": {"symbol": "$", "name": "Argentine Peso"},
        "UYU": {"symbol": "$U", "name": "Uruguayan Peso"},
        "PYG": {"symbol": "₲", "name": "Paraguayan Guarani"},
        "BRL": {"symbol": "R$", "name": "Brazilian Real"},
        "FKP": {"symbol": "£", "name": "Falkland Islands Pound"},
        "GBP": {"symbol": "£", "name": "British Pound"},
        "EUR": {"symbol": "€", "name": "Euro"},
        "CHF": {"symbol": "CHF", "name": "Swiss Franc"},
        "SEK": {"symbol": "kr", "name": "Swedish Krona"},
        "NOK": {"symbol": "kr", "name": "Norwegian Krone"},
        "DKK": {"symbol": "kr", "name": "Danish Krone"},
        "ISK": {"symbol": "kr", "name": "Icelandic Krona"},
        "PLN": {"symbol": "zł", "name": "Polish Zloty"},
        "CZK": {"symbol": "Kč", "name": "Czech Koruna"},
        "HUF": {"symbol": "Ft", "name": "Hungarian Forint"},
        "RON": {"symbol": "lei", "name": "Romanian Leu"},
        "BGN": {"symbol": "лв", "name": "Bulgarian Lev"},
        "HRK": {"symbol": "kn", "name": "Croatian Kuna"},
        "RSD": {"symbol": "дин", "name": "Serbian Dinar"},
        "MKD": {"symbol": "ден", "name": "Macedonian Denar"},
        "ALL": {"symbol": "L", "name": "Albanian Lek"},
        "BAM": {"symbol": "КМ", "name": "Bosnia and Herzegovina Convertible Mark"},
        "MNT": {"symbol": "₮", "name": "Mongolian Tugrik"},
        "KZT": {"symbol": "₸", "name": "Kazakhstani Tenge"},
        "KGS": {"symbol": "лв", "name": "Kyrgyzstani Som"},
        "TJS": {"symbol": "ЅМ", "name": "Tajikistani Somoni"},
        "TMT": {"symbol": "T", "name": "Turkmenistani Manat"},
        "UZS": {"symbol": "лв", "name": "Uzbekistani Som"},
        "AFN": {"symbol": "؋", "name": "Afghan Afghani"},
        "PKR": {"symbol": "₨", "name": "Pakistani Rupee"},
        "BDT": {"symbol": "৳", "name": "Bangladeshi Taka"},
        "LKR": {"symbol": "₨", "name": "Sri Lankan Rupee"},
        "NPR": {"symbol": "₨", "name": "Nepalese Rupee"},
        "BTN": {"symbol": "Nu.", "name": "Bhutanese Ngultrum"},
        "MVR": {"symbol": "Rf", "name": "Maldivian Rufiyaa"},
        "SCR": {"symbol": "₨", "name": "Seychellois Rupee"},
        "MUR": {"symbol": "₨", "name": "Mauritian Rupee"},
        "KMF": {"symbol": "CF", "name": "Comorian Franc"},
        "DJF": {"symbol": "Fdj", "name": "Djiboutian Franc"},
        "ETB": {"symbol": "Br", "name": "Ethiopian Birr"},
        "KES": {"symbol": "KSh", "name": "Kenyan Shilling"},
        "TZS": {"symbol": "TSh", "name": "Tanzanian Shilling"},
        "UGX": {"symbol": "USh", "name": "Ugandan Shilling"},
        "RWF": {"symbol": "RF", "name": "Rwandan Franc"},
        "BIF": {"symbol": "FBu", "name": "Burundian Franc"},
        "MWK": {"symbol": "MK", "name": "Malawian Kwacha"},
        "ZMW": {"symbol": "ZK", "name": "Zambian Kwacha"},
        "BWP": {"symbol": "P", "name": "Botswana Pula"},
        "SZL": {"symbol": "L", "name": "Swazi Lilangeni"},
        "LSL": {"symbol": "L", "name": "Lesotho Loti"},
        "NAD": {"symbol": "N$", "name": "Namibian Dollar"},
        "MZN": {"symbol": "MT", "name": "Mozambican Metical"},
        "AOA": {"symbol": "Kz", "name": "Angolan Kwanza"},
        "XOF": {"symbol": "CFA", "name": "West African CFA Franc"},
        "XAF": {"symbol": "FCFA", "name": "Central African CFA Franc"},
        "CDF": {"symbol": "FC", "name": "Congolese Franc"},
        "GMD": {"symbol": "D", "name": "Gambian Dalasi"},
        "GHS": {"symbol": "₵", "name": "Ghanaian Cedi"},
        "GNF": {"symbol": "FG", "name": "Guinean Franc"},
        "LRD": {"symbol": "L$", "name": "Liberian Dollar"},
        "SLL": {"symbol": "Le", "name": "Sierra Leonean Leone"},
        "NGN": {"symbol": "₦", "name": "Nigerian Naira"},
        "TND": {"symbol": "د.ت", "name": "Tunisian Dinar"},
        "DZD": {"symbol": "د.ج", "name": "Algerian Dinar"},
        "MAD": {"symbol": "د.م.", "name": "Moroccan Dirham"},
        "LYD": {"symbol": "ل.د", "name": "Libyan Dinar"},
        "SDG": {"symbol": "ج.س.", "name": "Sudanese Pound"},
        "SSP": {"symbol": "£", "name": "South Sudanese Pound"},
        "SOS": {"symbol": "S", "name": "Somali Shilling"},
        "ERN": {"symbol": "Nfk", "name": "Eritrean Nakfa"},
        "SYP": {"symbol": "£", "name": "Syrian Pound"},
        "IQD": {"symbol": "ع.د", "name": "Iraqi Dinar"},
        "IRR": {"symbol": "﷼", "name": "Iranian Rial"},
        "YER": {"symbol": "﷼", "name": "Yemeni Rial"},
        "PAB": {"symbol": "B/.", "name": "Panamanian Balboa"},
        "CRC": {"symbol": "₡", "name": "Costa Rican Colón"},
        "GTQ": {"symbol": "Q", "name": "Guatemalan Quetzal"},
        "HNL": {"symbol": "L", "name": "Honduran Lempira"},
        "NIO": {"symbol": "C$", "name": "Nicaraguan Córdoba"},
        "SVC": {"symbol": "₡", "name": "Salvadoran Colón"},
        "BZD": {"symbol": "BZ$", "name": "Belize Dollar"},
        "JMD": {"symbol": "J$", "name": "Jamaican Dollar"},
        "TTD": {"symbol": "TT$", "name": "Trinidad and Tobago Dollar"},
        "BBD": {"symbol": "Bds$", "name": "Barbadian Dollar"},
        "XCD": {"symbol": "EC$", "name": "East Caribbean Dollar"},
        "AWG": {"symbol": "ƒ", "name": "Aruban Florin"},
        "ANG": {"symbol": "ƒ", "name": "Netherlands Antillean Guilder"},
        "SRD": {"symbol": "$", "name": "Surinamese Dollar"},
        "GYD": {"symbol": "G$", "name": "Guyanese Dollar"},
        "VES": {"symbol": "Bs.S", "name": "Venezuelan Bolívar"},
        "COP": {"symbol": "$", "name": "Colombian Peso"},
        "PEN": {"symbol": "S/", "name": "Peruvian Sol"},
        "BOB": {"symbol": "Bs", "name": "Bolivian Boliviano"},
        "CLP": {"symbol": "$", "name": "Chilean Peso"},
        "ARS": {"symbol": "$", "name": "Argentine Peso"},
        "UYU": {"symbol": "$U", "name": "Uruguayan Peso"},
        "PYG": {"symbol": "₲", "name": "Paraguayan Guarani"},
        "FKP": {"symbol": "£", "name": "Falkland Islands Pound"},
        "ISK": {"symbol": "kr", "name": "Icelandic Krona"},
        "RON": {"symbol": "lei", "name": "Romanian Leu"},
        "BGN": {"symbol": "лв", "name": "Bulgarian Lev"},
        "HRK": {"symbol": "kn", "name": "Croatian Kuna"},
        "RSD": {"symbol": "дин", "name": "Serbian Dinar"},
        "MKD": {"symbol": "ден", "name": "Macedonian Denar"},
        "ALL": {"symbol": "L", "name": "Albanian Lek"},
        "BAM": {"symbol": "КМ", "name": "Bosnia and Herzegovina Convertible Mark"}
    }

# # Configure page FIRST - before any other Streamlit commands
# st.set_page_config(
#     page_title="AI Trip Planner",
#     page_icon="🗺️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# Now import other modules
from auth import  check_auth
# from trip_planner import show_trip_planner

def logout():
    """Logout user and clear session state"""
    # Clear all session state variables
    keys_to_clear = [
        'logged_in', 'user', 'current_trip', 'trip_id', 
        'active_profile_tab', 'trip_planner_page', 'form_data'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any Google OAuth related session state
    google_keys = [key for key in st.session_state.keys() if key.startswith('google_')]
    for key in google_keys:
        del st.session_state[key]
    
    st.success("✅ Successfully logged out!")
    st.rerun()

def check_auth():
    """Check if user is authenticated"""
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        return False
    return True

def show_dashboard():
    """Show user dashboard with overview"""
    st.title("🏠 Dashboard")
    
    if 'user' not in st.session_state:
        st.error("❌ Please log in to view dashboard!")
        return
    
    user = st.session_state.user
    
    # Welcome message
    st.markdown(f"### 👋 Welcome back, {user['name'] or user['username']}!")
    st.markdown("Here's your trip planning overview")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📅 Total Trips",
            value=len(db.get_user_trips(user['id'])),
            delta=None
        )
    
    with col2:
        st.metric(
            label="🗺️ Active Trips",
            value=len([trip for trip in db.get_user_trips(user['id']) if trip['status'] == 'active']),
            delta=None
        )
    
    with col3:
        st.metric(
            label="✅ Completed Trips",
            value=len([trip for trip in db.get_user_trips(user['id']) if trip['status'] == 'completed']),
            delta=None
        )
    
    with col4:
        # Calculate total budget with mixed currencies
        user_trips = db.get_user_trips(user['id'])
        total_budget = sum(trip['budget'] for trip in user_trips)
        # For mixed currencies, show total with note
        if user_trips:
            currencies = set(trip.get('currency', 'USD') for trip in user_trips)
            if len(currencies) == 1:
                currency_symbol = user_trips[0].get('currency_symbol', '$')
                st.metric(
                    label="💰 Total Budget",
                    value=f"{currency_symbol}{total_budget:,.0f}",
                    delta=None
                )
            else:
                st.metric(
                    label="💰 Total Budget",
                    value=f"${total_budget:,.0f}",
                    delta=None
                )
                st.caption("Mixed currencies - showing USD equivalent")
        else:
            st.metric(
                label="💰 Total Budget",
                value="$0",
                delta=None
            )
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗺️ Plan New Trip", type="primary", use_container_width=True):
            # Set navigation target and rerun
            st.session_state.navigation_target = "🗺️ Plan Trip"
            st.rerun()
    
    with col2:
        if st.button("📚 View My Trips", type="secondary", use_container_width=True):
            st.session_state.navigation_target = "📚 My Trips"
            st.rerun()
    
    with col3:
        if st.button("👤 Edit Profile", type="secondary", use_container_width=True):
            st.session_state.navigation_target = "👤 Profile"
            st.rerun()
    
    # Recent trips
    st.subheader("📜 Recent Trips")
    trips = db.get_user_trips(user['id'])
    
    if trips:
        # Show last 3 trips
        for trip in trips[:3]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{trip['destination']}**")
                    st.write(f"📅 {trip['start_date']} to {trip['end_date']}")
                    currency_symbol = trip.get('currency_symbol', '$')
                    st.write(f"💰 {currency_symbol}{trip['budget']:,.2f}")
                
                with col2:
                    #st.write(f"Status: {trip['status'].title()}")
                    status = trip.get('status') or 'unknown'
                    st.write(f"Status: {status.title()}")

                
                with col3:
                    if st.button("View", key=f"view_{trip['id']}"):
                        st.session_state.selected_trip = trip
                        st.session_state.navigation_target = "📚 My Trips"
                        st.rerun()
                
                st.divider()
    else:
        st.info("No trips found. Start planning your first trip!")
    
    # Tips and suggestions
    st.subheader("💡 Tips & Suggestions")
    
    tips = [
        "🗺️ Use the AI trip planner to get personalized recommendations",
        "📚 Save your favorite trips for future reference",
        "📊 Check your analytics to see your travel patterns",
        "👤 Keep your profile updated for better recommendations"
    ]
    
    for tip in tips:
        st.write(tip)

def show_trip_planner():
    """Main trip planner interface with optimized sidebar"""
    
    # Check for navigation target from dashboard
    if 'navigation_target' in st.session_state:
        target = st.session_state.navigation_target
        del st.session_state.navigation_target
        st.session_state.trip_planner_page = target
    
    # Check if we're in modification mode
    if 'modification_mode' in st.session_state and st.session_state.modification_mode:
        show_trip_modification_interface()
        return
    
    # Check if we're in booking mode
    if 'show_booking_interface' in st.session_state and st.session_state.show_booking_interface:
        from booking_interface import booking_interface
        booking_interface.show_booking_interface()
        return
    
    # Optimized sidebar
    inject_floating_button()
    with st.sidebar:
        # Compact header with app name and icon
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem; margin-right: 0.5rem;">🗺️</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #1e293b;">Wayfarer</h1>
            </div>
            <div style="width: 100%; height: 2px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 1px;"></div>
        </div>
        
        """, unsafe_allow_html=True)
        
        # Compact user info
        if 'user' in st.session_state:
            user = st.session_state.user
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <div style="display: flex; align-items: center;">
                    <div style="width: 35px; height: 35px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 0.75rem; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);">
                        <span style="color: white; font-weight: 600; font-size: 0.9rem;">{(user['name'] or user['username'])[0].upper()}</span>
                    </div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: #1e293b; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user['name'] or user['username']}</div>
                        <div style="font-size: 0.8rem; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">@{user['username']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            credit_widget.show_credit_sidebar(st.session_state.user['id'])
       
        else:
            st.error("Please log in first!")
            return
        
        # Compact navigation menu
        st.markdown("### 🎯 Menu")
        page = st.radio(
            "",
            [
                "🏠 Dashboard", 
                "🗺️ Plan Trip", 
                "📚 My Trips", 
                "💳 Credits",
                "📊 Analytics", 
                "👤 Profile"
            ],
            key="trip_planner_page",
            label_visibility="collapsed"
        )
        
        # Compact divider
        st.markdown("---")
        
        # Compact logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True, key="logout_btn"):
            logout()
    
    # Main content area
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🗺️ Plan Trip":
        plan_new_trip()
    elif page == "📚 My Trips":
        show_my_trips()
    elif page == "💳 Credits":
        show_credits_page()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "👤 Profile":
        show_profile()

def plan_new_trip():
    """Plan a new trip with AI assistance"""
    st.title("🗺️ Plan Your Perfect Trip")
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        st.error("❌ Please log in to plan a trip!")
        return
    
    # Initialize Vertex AI
    vertex_ai = VertexAITripPlanner()
    
    # Check if we have a trip to display
    if 'current_trip' in st.session_state and st.session_state.current_trip:
        # Display the generated trip
        suggestions = st.session_state.current_trip
        trip_id = st.session_state.get('trip_id', 'Unknown')
        
        st.success("🎉 Trip plan generated successfully!")
        st.subheader("📋 Your Trip Plan")
        
        # Show trip details
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Destination:** {suggestions.get('destination', 'N/A')}")
            st.write(f"**Duration:** {suggestions.get('duration', 'N/A')} days")
        with col2:
            currency_symbol = suggestions.get('currency_symbol', '$')
            st.write(f"**Budget:** {currency_symbol}{suggestions.get('budget', 'N/A')}")
            st.write(f"**Trip ID:** {trip_id}")
        
        # Show itinerary
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("📅 Daily Itinerary")
            if isinstance(suggestions['itinerary'], list):
                for day_info in suggestions['itinerary']:
                    with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')}"):
                        if 'activities' in day_info:
                            st.write("**Activities:**")
                            for activity in day_info['activities']:
                                st.write(f"• {activity}")
                        if 'meals' in day_info:
                            st.write("**Meals:**")
                            for meal in day_info['meals']:
                                st.write(f"🍽️ {meal}")
            else:
                for day, activities in suggestions['itinerary'].items():
                    with st.expander(f"Day {day}"):
                        for activity in activities:
                            st.write(f"• {activity}")
        
        # Show accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
            st.subheader("🏨 Recommended Accommodations")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for hotel in suggestions['accommodations']:
                price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                if isinstance(price_info, str) and price_info != 'Price not available':
                    # If price contains dollar sign, replace with correct currency
                    if '$' in price_info:
                        price_info = price_info.replace('$', currency_symbol)
                st.write(f"**{hotel['name']}** - {price_info}")
                if 'description' in hotel:
                    st.write(f"*{hotel['description']}*")
        
        # Show additional info
        if 'additional_info' in suggestions and suggestions['additional_info']:
            st.subheader("ℹ️ Additional Information")
            st.write(suggestions['additional_info'])
        
        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("🔄 Generate New Trip", type="secondary"):
                # Clear current trip and show form again
                if 'current_trip' in st.session_state:
                    del st.session_state.current_trip
                if 'trip_id' in st.session_state:
                    del st.session_state.trip_id
                st.rerun()
        
        with col2:
            if st.button("💬 Modify Trip", type="primary"):
                st.session_state.modification_mode = True
                st.session_state.modification_trip_id = trip_id
                st.rerun()
        
        with col3:
            if st.button("👁️ View in My Trips", type="secondary"):
                st.session_state.page = "my_trips"
                st.rerun()
        
        with col4:
            if st.button("💾 Save & Continue", type="secondary"):
                st.success("✅ Trip saved! You can view it in 'My Trips' anytime.")
        
        with col5:
            # Import booking interface
            from booking_interface import booking_interface
            
            # Show booking button
            if booking_interface.show_booking_button(suggestions, st.session_state.user):
                st.rerun()
        
        return
    
    # Create form for new trip planning
    with st.form("trip_planning_form", clear_on_submit=False):
        st.subheader("Trip Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "Destination *", 
                placeholder="e.g., Paris, France",
                help="Enter your travel destination"
            )
            today = datetime.now().date()
            start_date = st.date_input(
                "Start Date *", 
                value=today,
                min_value=today,
                help=f"When does your trip start? (Earliest: {today.strftime('%B %d, %Y')})"
            )
            end_date = st.date_input(
                "End Date *", 
                value=today + timedelta(days=7),
                min_value=today,
                help=f"When does your trip end? (Earliest: {today.strftime('%B %d, %Y')})"
            )
            # Currency and Budget selection - Original layout with flags
            col_budget, col_currency = st.columns([2, 1])
            
            with col_currency:
                currency_options = get_currency_options()
                
                # Popular currencies with flags for better UX
                popular_currencies_display = [
                    ("INR", "🇮🇳 Indian Rupee (₹)"),
                    ("USD", "🇺🇸 US Dollar ($)"),
                    ("EUR", "🇪🇺 Euro (€)"),
                    ("GBP", "🇬🇧 British Pound (£)"),
                    ("JPY", "🇯🇵 Japanese Yen (¥)"),
                    ("CAD", "🇨🇦 Canadian Dollar (C$)"),
                    ("AUD", "🇦🇺 Australian Dollar (A$)"),
                    ("CHF", "🇨🇭 Swiss Franc (CHF)"),
                    ("BRL", "🇧🇷 Brazilian Real (R$)"),
                    ("MXN", "🇲🇽 Mexican Peso ($)"),
                    ("SGD", "🇸🇬 Singapore Dollar (S$)"),
                    ("HKD", "🇭🇰 Hong Kong Dollar (HK$)"),
                    ("NZD", "🇳🇿 New Zealand Dollar (NZ$)"),
                    ("CNY", "🇨🇳 Chinese Yuan (¥)"),
                    ("KRW", "🇰🇷 South Korean Won (₩)"),
                    ("THB", "🇹🇭 Thai Baht (฿)"),
                    ("MYR", "🇲🇾 Malaysian Ringgit (RM)"),
                    ("IDR", "🇮🇩 Indonesian Rupiah (Rp)"),
                    ("PHP", "🇵🇭 Philippine Peso (₱)"),
                    ("VND", "🇻🇳 Vietnamese Dong (₫)"),
                    ("TRY", "🇹🇷 Turkish Lira (₺)"),
                    ("AED", "🇦🇪 UAE Dirham (د.إ)"),
                    ("SAR", "🇸🇦 Saudi Riyal (ر.س)"),
                    ("ILS", "🇮🇱 Israeli Shekel (₪)"),
                    ("QAR", "🇶🇦 Qatari Riyal (ر.ق)"),
                    ("KWD", "🇰🇼 Kuwaiti Dinar (د.ك)"),
                    ("BHD", "🇧🇭 Bahraini Dinar (د.ب)"),
                    ("OMR", "🇴🇲 Omani Rial (ر.ع.)"),
                    ("JOD", "🇯🇴 Jordanian Dinar (د.ا)"),
                    ("LBP", "🇱🇧 Lebanese Pound (ل.ل)"),
                    ("PKR", "🇵🇰 Pakistani Rupee (₨)"),
                    ("BDT", "🇧🇩 Bangladeshi Taka (৳)"),
                    ("LKR", "🇱🇰 Sri Lankan Rupee (₨)"),
                    ("NPR", "🇳🇵 Nepalese Rupee (₨)")
                ]
                
                # Create currency options for selectbox
                currency_choices = [display for code, display in popular_currencies_display]
                currency_codes = [code for code, display in popular_currencies_display]
                
                selected_currency_display = st.selectbox(
                    "Currency",
                    currency_choices,
                    index=0,  # Default to INR
                    help="Select your preferred currency",
                    key="currency_selectbox"
                )
                
                # Extract currency code from selection
                selected_index = currency_choices.index(selected_currency_display)
                selected_currency = currency_codes[selected_index]
                currency_symbol = currency_options[selected_currency]["symbol"]
                
                # Show selected currency with flag
                #st.caption(f"Selected: {selected_currency_display}")
            
            with col_budget:
                budget = st.number_input(
                    f"Budget ({selected_currency}) *", 
                    min_value=0, 
                    step=100, 
                    help=f"Your total trip budget in {selected_currency}"
                )
        
        with col2:
            travel_type = st.selectbox(
                "Travel Type",
                ["Solo", "Couple", "Family", "Friends", "Business"],
                help="Who are you traveling with?"
            )
            
            preferences = st.multiselect(
                "Interests",
                ["Adventure", "Culture", "Food", "History", "Nature", "Nightlife", "Shopping", "Relaxation"],
                help="Select your interests"
            )
            
            accommodation_type = st.selectbox(
                "Accommodation Preference",
                ["Budget", "Mid-range", "Luxury", "Hostel", "Airbnb"],
                help="What type of accommodation do you prefer?"
            )
        
        # Additional preferences
        additional_preferences = st.text_area(
            "Additional Preferences",
            placeholder="Any specific requirements or interests...",
            help="Any other preferences or special requirements"
        )
        
        # Submit button
        submitted = st.form_submit_button(
            "🤖 Generate Trip Plan", 
            type="primary",
            use_container_width=True
        )
        
        # Handle form submission INSIDE the form context
        if submitted:
            # Validation
            if not destination or not destination.strip():
                st.error("❌ Please enter a destination")
                return
            
            # Validate dates
            if not validate_trip_dates(start_date, end_date):
                return
            
            if budget <= 0:
                st.error("❌ Please enter a valid budget")
                return
            
            
            st.success("✅ Form validation passed!")
            
            # Prepare preferences string
            preferences_str = ", ".join(preferences) if preferences else "General travel"
            if additional_preferences and additional_preferences.strip():
                preferences_str += f" | Additional: {additional_preferences.strip()}"
            
            # Store form data in session state
            st.session_state.form_data = {
                'destination': destination.strip(),
                'start_date': start_date.strftime("%Y-%m-%d"),
                'end_date': end_date.strftime("%Y-%m-%d"),
                'budget': float(budget),
                'currency': selected_currency,
                'currency_symbol': currency_symbol,
                'preferences': preferences_str,
                'travel_type': travel_type,
                'accommodation_type': accommodation_type
            }
            
            # Generate suggestions
            try:
                with st.spinner("🤖 AI is planning your perfect trip... This may take a moment."):
                    suggestions = vertex_ai.generate_trip_suggestions(
                        destination=destination.strip(),
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        budget=float(budget),
                        preferences=preferences_str,
                        currency=selected_currency,
                        currency_symbol=currency_symbol
                    )
                
                if not suggestions:
                    st.error("❌ Failed to generate trip suggestions. Please try again.")
                    return
                
                
                st.success("✅ Trip suggestions generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating suggestions: {str(e)}")
                return
            
            # Save trip to database
            try:
                success, message = db.create_trip(
                    st.session_state.user['id'],
                    destination.strip(),
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                    float(budget),
                    preferences_str,
                    json.dumps(suggestions),
                    selected_currency,
                    currency_symbol
                )
                
                if success:
                    # Extract trip_id from message
                    trip_id = int(message.split("ID: ")[1])
                    
                    # Calculate and track credits used
                    credits_used = calculate_credits_used(suggestions)
                    db.update_trip_credits(trip_id, credits_used)
                    db.add_credit_transaction(
                        st.session_state.user['id'],
                        trip_id,
                        'usage',
                        credits_used,
                        f"AI trip generation for {destination}"
                    )
                    
                    st.session_state.current_trip = suggestions
                    st.session_state.trip_id = trip_id
                    st.success(f"🎉 Trip plan generated and saved successfully! (Used {credits_used} credits)")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save trip: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error saving trip: {str(e)}")
                st.write(f"Debug info: {str(e)}")

def show_my_trips():
    """Display user's saved trips"""
    st.title("🗺️ My Trips")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view your trips")
        return
    
    user_id = st.session_state.user['id']
    trips = db.get_user_trips(user_id)
    
    if not trips:
        st.info("No trips found. Start planning your first trip!")
        return
    
    # Display trips
    for trip in trips:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(f"🗺️ {trip['destination']}")
                st.write(f"📅 {trip['start_date']} to {trip['end_date']}")
                currency_symbol = trip.get('currency_symbol', '$')
                st.write(f"💰 Budget: {currency_symbol}{trip['budget']:,.2f}")
                
                # Show status with booking information
                status = trip['status'].title()
                booking_status = trip.get('booking_status', 'not_booked')
                
                if booking_status == 'confirmed':
                    st.write(f"📊 Status: {status} ✅ Booked")
                elif booking_status == 'pending':
                    st.write(f"📊 Status: {status} ⏳ Booking Pending")
                else:
                    st.write(f"📊 Status: {status}")
            
            with col2:
                col_view, col_modify, col_book = st.columns(3)
                with col_view:
                    if st.button("View", key=f"view_{trip['id']}"):
                        st.session_state.selected_trip = trip
                        st.rerun()
                with col_modify:
                    if st.button("Modify", key=f"modify_{trip['id']}"):
                        st.session_state.modification_mode = True
                        st.session_state.modification_trip_id = trip['id']
                        st.rerun()
                with col_book:
                    # Import booking interface
                    from booking_interface import booking_interface
                    
                    # Show booking button for trips with AI suggestions
                    try:
                        ai_suggestions = trip.get('ai_suggestions', {})
                        if isinstance(ai_suggestions, str):
                            ai_suggestions = json.loads(ai_suggestions)
                        
                        if ai_suggestions and trip['status'] != 'booked':
                            if st.button("Book", key=f"book_{trip['id']}"):
                                # Prepare trip data for booking
                                trip_data = {
                                    'trip_id': trip['id'],
                                    'destination': trip['destination'],
                                    'start_date': trip['start_date'],
                                    'end_date': trip['end_date'],
                                    'budget': trip['budget'],
                                    'currency': trip.get('currency', 'INR'),
                                    'currency_symbol': trip.get('currency_symbol', '₹'),
                                    'preferences': trip['preferences'],
                                    'ai_suggestions': ai_suggestions
                                }
                                
                                # Store booking data in session state
                                st.session_state.booking_trip_data = trip_data
                                st.session_state.booking_user_data = st.session_state.user
                                st.session_state.show_booking_interface = True
                                st.rerun()
                    except Exception as e:
                        st.write("N/A")
            
            with col3:
                if st.button("Delete", key=f"delete_{trip['id']}"):
                    success, message = db.delete_trip(trip['id'], user_id)
                    if success:
                        st.success("Trip deleted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error deleting trip: {message}")
            
            st.write("---")
    
    # Show selected trip details
    if 'selected_trip' in st.session_state:
        st.subheader("Trip Details")
        show_trip_details(st.session_state.selected_trip)
        
        if st.button("Close Details"):
            del st.session_state.selected_trip
            st.rerun()

def show_trip_details(trip_data):
    """Display detailed trip information"""
    try:
        suggestions = json.loads(trip_data['ai_suggestions']) if isinstance(trip_data['ai_suggestions'], str) else trip_data['ai_suggestions']
    except Exception as e:
        st.error(f"Error loading trip details: {str(e)}")
        return
    
    st.subheader(f"🗺️ {trip_data['destination']}")
    
    # Trip overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Duration", f"{trip_data['start_date']} to {trip_data['end_date']}")
    with col2:
        currency_symbol = trip_data.get('currency_symbol', '$')
        st.metric("Budget", f"{currency_symbol}{trip_data['budget']:,.2f}")
    with col3:
        status = trip_data['status'].title()
        booking_status = trip_data.get('booking_status', 'not_booked')
        
        if booking_status == 'confirmed':
            st.metric("Status", f"{status} ✅ Booked")
        elif booking_status == 'pending':
            st.metric("Status", f"{status} ⏳ Booking Pending")
        else:
            st.metric("Status", status)
    
    # AI suggestions
    if suggestions:
        st.subheader("📋 AI Recommendations")
        
        # Itinerary
        if 'itinerary' in suggestions and suggestions['itinerary']:
            st.subheader("📅 Daily Itinerary")
            # Handle itinerary as list of dictionaries
            if isinstance(suggestions['itinerary'], list):
                for day_info in suggestions['itinerary']:
                    with st.expander(f"Day {day_info.get('day', 'N/A')} - {day_info.get('day_name', '')} ({day_info.get('date', '')})"):
                        if 'activities' in day_info:
                            st.write("**Activities:**")
                            for activity in day_info['activities']:
                                st.write(f"• {activity}")
                        if 'meals' in day_info:
                            st.write("**Meals:**")
                            for meal in day_info['meals']:
                                st.write(f"🍽️ {meal}")
            else:
                # Fallback for dictionary format
                for day, activities in suggestions['itinerary'].items():
                    with st.expander(f"Day {day}"):
                        for activity in activities:
                            st.write(f"• {activity}")
        
        # Accommodations
        if 'accommodations' in suggestions and suggestions['accommodations']:
            st.subheader("🏨 Accommodations")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for hotel in suggestions['accommodations']:
                with st.container():
                    st.write(f"**{hotel['name']}**")
                    st.write(f"📍 {hotel.get('location', 'Location not specified')}")
                    # Use price_range instead of price and fix currency
                    price_info = hotel.get('price_range', hotel.get('price', 'Price not available'))
                    if isinstance(price_info, str) and price_info != 'Price not available':
                        # If price contains dollar sign, replace with correct currency
                        if '$' in price_info:
                            price_info = price_info.replace('$', currency_symbol)
                    st.write(f"💰 {price_info}")
                    if 'rating' in hotel:
                        st.write(f"⭐ {hotel['rating']}/5")
                    if 'type' in hotel:
                        st.write(f"🏷️ {hotel['type']}")
                    if 'amenities' in hotel:
                        st.write(f"✨ Amenities: {', '.join(hotel['amenities'])}")
                    st.write("---")
        
        # Activities
        if 'activities' in suggestions and suggestions['activities']:
            st.subheader("🎯 Activities")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for activity in suggestions['activities']:
                with st.container():
                    st.write(f"**{activity['name']}**")
                    st.write(f"📍 {activity.get('location', 'Location not specified')}")
                    # Display cost with correct currency symbol
                    cost = activity.get('cost', 'Cost not specified')
                    if isinstance(cost, str) and cost != 'Cost not specified':
                        # If cost contains dollar sign, replace with correct currency
                        if '$' in cost:
                            cost = cost.replace('$', currency_symbol)
                    st.write(f"💰 {cost}")
                    st.write(f"⏰ {activity.get('duration', 'Duration not specified')}")
                    if 'description' in activity:
                        st.write(f"📝 {activity['description']}")
                    st.write("---")
        
        # Restaurants
        if 'restaurants' in suggestions and suggestions['restaurants']:
            st.subheader("🍽️ Restaurants")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for restaurant in suggestions['restaurants']:
                with st.container():
                    st.write(f"**{restaurant['name']}**")
                    st.write(f"📍 {restaurant.get('location', 'Location not specified')}")
                    # Display price range with correct currency symbol
                    price_range = restaurant.get('price_range', 'Price not available')
                    if isinstance(price_range, str) and price_range != 'Price not available':
                        # If price contains dollar sign, replace with correct currency
                        if '$' in price_range:
                            price_range = price_range.replace('$', currency_symbol)
                    st.write(f"💰 {price_range}")
                    if 'cuisine' in restaurant:
                        st.write(f"🍴 {restaurant['cuisine']}")
                    st.write("---")
        
        # Transportation
        if 'transportation' in suggestions and suggestions['transportation']:
            st.subheader("🚗 Transportation")
            currency_symbol = suggestions.get('currency_symbol', '$')
            for transport in suggestions['transportation']:
                with st.container():
                    st.write(f"**{transport['type']}**")
                    st.write(f"📍 {transport.get('route', 'Route not specified')}")
                    # Display cost with correct currency symbol
                    cost = transport.get('cost', 'Cost not specified')
                    if isinstance(cost, str) and cost != 'Cost not specified':
                        # If cost contains dollar sign, replace with correct currency
                        if '$' in cost:
                            cost = cost.replace('$', currency_symbol)
                    st.write(f"💰 {cost}")
                    st.write("---")
        
        # Tips
        if 'tips' in suggestions and suggestions['tips']:
            st.subheader("💡 Travel Tips")
            for tip in suggestions['tips']:
                st.write(f"• {tip}")
        
        # Weather
        if 'weather' in suggestions and suggestions['weather']:
            st.subheader("🌤️ Weather Information")
            weather = suggestions['weather']
            st.write(f"**Temperature:** {weather.get('temperature', 'N/A')}")
            st.write(f"**Conditions:** {weather.get('conditions', 'N/A')}")
            st.write(f"**Packing:** {weather.get('packing', 'N/A')}")
    
    # Booking information
    if trip_data.get('booking_status') == 'confirmed' and trip_data.get('booking_confirmation'):
        st.subheader("🎫 Booking Information")
        
        try:
            booking_confirmation = json.loads(trip_data['booking_confirmation']) if isinstance(trip_data['booking_confirmation'], str) else trip_data['booking_confirmation']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Booking ID:** {booking_confirmation.get('booking_id', 'N/A')}")
                st.write(f"**Confirmation Number:** {booking_confirmation.get('confirmation_number', 'N/A')}")
                st.write(f"**Booking Date:** {booking_confirmation.get('booking_date', 'N/A')[:10]}")
            
            with col2:
                st.write(f"**Total Amount:** ₹{booking_confirmation.get('total_amount', 0):,}")
                st.write(f"**Payment Status:** {booking_confirmation.get('payment_status', 'N/A').title()}")
                st.write(f"**Status:** {booking_confirmation.get('status', 'N/A').title()}")
            
            # Show booking details
            if 'booking_details' in booking_confirmation:
                st.subheader("📋 Booking Details")
                details = booking_confirmation['booking_details']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Customer Name:** {details.get('customer_name', 'N/A')}")
                    st.write(f"**Email:** {details.get('customer_email', 'N/A')}")
                
                with col2:
                    st.write(f"**Phone:** {details.get('customer_phone', 'N/A')}")
                    st.write(f"**Travel Dates:** {details.get('travel_dates', {}).get('start', 'N/A')} to {details.get('travel_dates', {}).get('end', 'N/A')}")
            
            # Show support contact
            if 'support_contact' in booking_confirmation:
                st.subheader("📞 Support Contact")
                support = booking_confirmation['support_contact']
                st.write(f"**Phone:** {support.get('phone', 'N/A')}")
                st.write(f"**Email:** {support.get('email', 'N/A')}")
            
            # Show next steps
            if 'next_steps' in booking_confirmation:
                st.subheader("📝 Next Steps")
                for step in booking_confirmation['next_steps']:
                    st.write(f"• {step}")
                    
        except Exception as e:
            st.error(f"Error loading booking information: {str(e)}")

def show_analytics():
    """Show trip analytics and statistics"""
    st.title("📊 Trip Analytics")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view analytics")
        return
    
    user_id = st.session_state.user['id']
    stats = db.get_user_stats(user_id)
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trips", stats['trip_count'])
    with col2:
        # For stats, we'll show USD as default since it's a summary
        st.metric("Total Budget", f"${stats['total_budget']:,.2f}")
    with col3:
        st.metric("Favorite Destination", stats['popular_destination'])

def show_profile():
    """Show user profile and settings with edit functionality"""
    st.title("👤 Profile")
    
    if 'user' not in st.session_state:
        st.error("Please log in to view profile")
        return
    
    user = st.session_state.user
    
    # Initialize active tab in session state
    if 'active_profile_tab' not in st.session_state:
        st.session_state.active_profile_tab = 0  # 0 = View Profile, 1 = Edit Profile
    
    # Create tabs for viewing and editing profile
    tab1, tab2 = st.tabs(["👀 View Profile", "✏️ Edit Profile"])
    
    # Use session state to control which tab content is shown
    if st.session_state.active_profile_tab == 0:
        # View Profile Tab
        st.subheader("Profile Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Username:** {user['username']}")
            st.write(f"**Email:** {user['email']}")
            st.write(f"**Name:** {user.get('name', 'Not set')}")
            st.write(f"**Login Method:** {user.get('login_method', 'email').title()}")
        
        with col2:
            st.write(f"**Member Since:** {user.get('created_at', 'Unknown')}")
            st.write(f"**Last Login:** {user.get('last_login', 'Unknown')}")
            st.write(f"**Status:** {'Active' if user.get('is_active', True) else 'Inactive'}")
        
        # Contact Information
        st.subheader("📞 Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Personal Number:** {user.get('personal_number', 'Not provided')}")
            st.write(f"**Alternate Number:** {user.get('alternate_number', 'Not provided')}")
        with col2:
            st.write(f"**Address:** {user.get('address', 'Not provided')}")
            st.write(f"**Pincode:** {user.get('pincode', 'Not provided')}")
            st.write(f"**State:** {user.get('state', 'Not provided')}")
        
        # Button to switch to edit tab
        if st.button("✏️ Edit Profile", type="primary"):
            st.session_state.active_profile_tab = 1
            st.rerun()
    
    else:
        # Edit Profile Tab
        st.subheader("Edit Profile Information")
        st.info("💡 You can update your personal information below. Fields marked with * are required.")
        
        with st.form("edit_profile_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basic Information**")
                name = st.text_input(
                    "Full Name *",
                    value=user.get('name', ''),
                    help="Enter your full name"
                )
                
                personal_number = st.text_input(
                    "Personal Number",
                    value=user.get('personal_number', ''),
                    help="Your primary contact number"
                )
                
                alternate_number = st.text_input(
                    "Alternate Number",
                    value=user.get('alternate_number', ''),
                    help="Secondary contact number (optional)"
                )
            
            with col2:
                st.write("**Address Information**")
                address = st.text_area(
                    "Address",
                    value=user.get('address', ''),
                    help="Your complete address",
                    height=100
                )
                
                pincode = st.text_input(
                    "Pincode",
                    value=user.get('pincode', ''),
                    help="Postal/ZIP code"
                )
                
                state = st.text_input(
                    "State",
                    value=user.get('state', ''),
                    help="State or Province"
                )
            
            # Submit button
            submitted = st.form_submit_button(
                "💾 Update Profile",
                type="primary",
                use_container_width=True
            )
            
            # Handle form submission
            if submitted:
                # Validation
                if not name or not name.strip():
                    st.error("❌ Please enter your full name")
                else:
                    # Prepare update data
                    update_data = {
                        'name': name.strip(),
                        'personal_number': personal_number.strip() if personal_number else None,
                        'address': address.strip() if address else None,
                        'pincode': pincode.strip() if pincode else None,
                        'state': state.strip() if state else None,
                        'alternate_number': alternate_number.strip() if alternate_number else None
                    }
                    
                    # Update profile in database
                    try:
                        success, message = db.update_user_profile(user['id'], **update_data)
                        
                        if success:
                            # Update session state with new data
                            st.session_state.user.update(update_data)
                            
                            # Refresh user data from database
                            updated_user = db.get_user_by_id(user['id'])
                            if updated_user:
                                st.session_state.user = updated_user
                            
                            # Switch to view profile tab
                            st.session_state.active_profile_tab = 0
                            st.success("✅ Profile updated successfully! Redirecting to view profile...")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update profile: {message}")
                    
                    except Exception as e:
                        st.error(f"❌ Error updating profile: {str(e)}")
        
        # Button to switch back to view tab
        if st.button("👀 View Profile", type="secondary"):
            st.session_state.active_profile_tab = 0
            st.rerun()
    
    # Account Actions (removed logout button)
    st.subheader("👥 Account Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Profile", type="secondary"):
            # Refresh user data from database
            updated_user = db.get_user_by_id(user['id'])
            if updated_user:
                st.session_state.user = updated_user
                st.success("✅ Profile refreshed!")
                st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", type="secondary"):
            st.session_state.trip_planner_page = "📊 Analytics"
            st.rerun()
    
    with col3:
        if st.button("🗺️ Plan New Trip", type="secondary"):
            st.session_state.trip_planner_page = "🗺️ Plan New Trip"
            st.rerun()
    
    # Security Information
    with st.expander("🔒 Security Information"):
        st.write("**Account Security:**")
        st.write(f"• Login Method: {user.get('login_method', 'email').title()}")
        st.write(f"• Email Verified: {'Yes' if user.get('verified_email') else 'No'}")
        st.write(f"• Account Status: {'Active' if user.get('is_active', True) else 'Inactive'}")
        st.write(f"• Last Login: {user.get('last_login', 'Unknown')}")
        
        if user.get('login_method') == 'google':
            st.info("🔐 This account is secured with Google OAuth. Your password is managed by Google.")
        else:
            st.info("🔐 This account uses email/password authentication. Keep your password secure.")

def show_trip_modification_interface():
    """Show the trip modification interface with chat"""
    from trip_modification_chat import TripModificationChat
    
    st.title("🗺️ Trip Modification Center")
    
    if 'user' not in st.session_state:
        st.error("❌ Please log in to modify trips!")
        return
    
    if 'modification_trip_id' not in st.session_state:
        st.error("❌ No trip selected for modification!")
        return
    
    trip_id = st.session_state.modification_trip_id
    user_id = st.session_state.user['id']
    
    # Get trip data
    trip_data = db.get_trip_by_id(trip_id, user_id)
    if not trip_data:
        st.error("❌ Trip not found!")
        return
    
    # Parse AI suggestions
    try:
        current_trip_data = json.loads(trip_data['ai_suggestions']) if isinstance(trip_data['ai_suggestions'], str) else trip_data['ai_suggestions']
    except Exception as e:
        st.error(f"❌ Error loading trip data: {str(e)}")
        return
    
    # Add trip metadata to current_trip_data
    current_trip_data.update({
        'trip_id': trip_id,
        'user_id': user_id,
        'destination': trip_data['destination'],
        'start_date': trip_data['start_date'],
        'end_date': trip_data['end_date'],
        'budget': trip_data['budget'],
        'currency': trip_data['currency'],
        'currency_symbol': trip_data['currency_symbol'],
        'preferences': trip_data['preferences']
    })
    
    # Initialize and show modification interface
    modification_chat = TripModificationChat()
    modification_chat.show_modification_interface(trip_id, user_id, current_trip_data)
    
    # Back button
    if st.button("← Back to Trip Planner", type="secondary"):
        del st.session_state.modification_mode
        if 'modification_trip_id' in st.session_state:
            del st.session_state.modification_trip_id
        st.rerun()

def show_credits_page():
    """Show credits management page"""
    if 'user' not in st.session_state:
        st.error("Please log in first!")
        return
    
    st.title("💳 AI Credits")
    
    # Import credit widget
    from credit_widget import credit_widget
    
    # Show credit card
    credit_widget.show_credit_card(st.session_state.user['id'])
    
    # Show upgrade prompt if credits are low
    credit_widget.show_upgrade_prompt(st.session_state.user['id'])
    
    # Tabs for different credit views
    tab1, tab2, tab3 = st.tabs(["📊 Usage Breakdown", "📋 Transaction History", "ℹ️ About Credits"])
    
    with tab1:
        credit_widget.show_credit_usage_breakdown(st.session_state.user['id'])
    
    with tab2:
        credit_widget.show_credit_history(st.session_state.user['id'])
    
    with tab3:
        st.subheader("ℹ️ About AI Credits")
        
        st.markdown("""
        ### How Credits Work
        
        **AI Credits** are used to generate personalized trip recommendations using our advanced AI system.
        
        #### Credit Usage:
        - **Base Trip Generation**: 5 credits
        - **Additional Credits**: Based on content complexity
          - Itinerary items: +0.5 credits each
          - Accommodations: +0.3 credits each  
          - Activities: +0.4 credits each
          - Restaurants: +0.3 credits each
          - Transportation: +0.2 credits each
        
        #### Credit Limits:
        - **Maximum per trip**: 20 credits
        - **Starting credits**: 1000 credits
        - **Refill options**: Coming soon!
        
        #### Tips to Save Credits:
        - Be specific in your preferences
        - Choose shorter trip durations
        - Focus on fewer destinations
        - Use the budget calculator wisely
        
        ### Need More Credits?
        
        Contact our support team to discuss credit packages and upgrade options!
        """)

# Update the save trip function to include weather data and source
def save_trip_to_database(user_id, destination, start_date, end_date, budget, preferences, 
                         ai_suggestions, currency, currency_symbol, weather_data=None, source="user_input"):
    """Save trip to database with weather data and source tracking"""
    try:
        # Calculate credits used
        credits_used = calculate_credits_used(ai_suggestions)
        
        # Create trip in database
        success, message = db.create_trip(
            user_id=user_id,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            preferences=preferences,
            ai_suggestions=json.dumps(ai_suggestions),
            currency=currency,
            currency_symbol=currency_symbol,
            weather_data=weather_data,
            source=source
        )
        
        if success:
            # Update user credits
            db.update_trip_credits(
                trip_id=success.split(":")[-1].strip() if ":" in message else None,
                credits_used=credits_used
            )
            
        return success, message
        
    except Exception as e:
        logger.error(f"Error saving trip: {str(e)}")
        return False, f"Failed to save trip: {str(e)}"

# Add this function to display weather information
def display_weather_info(weather_data, ai_suggestions):
    """Display weather information in the itinerary"""
    if not weather_data:
        return
    
    st.subheader("🌤️ Weather Forecast")
    
    summary = weather_data.get('summary', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Temperature Range",
            value=summary.get('avg_temperature', 'N/A')
        )
    
    with col2:
        st.metric(
            label="Conditions",
            value=summary.get('conditions', 'N/A')
        )
    
    # Weather recommendations
    recommendations = summary.get('recommendations', [])
    if recommendations:
        st.write("**Weather Recommendations:**")
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # Daily forecast (show first 7 days)
    daily_forecast = weather_data.get('daily_forecast', [])
    if daily_forecast:
        st.write("**Daily Forecast:**")
        
        # Create a more compact daily forecast display
        forecast_data = []
        for day in daily_forecast[:7]:  # Show only first 7 days
            date_str = day.get('date', '')
            if date_str:
                formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%b %d')
                day_name = day.get('day_name', '')[:3]  # Abbreviate day name
                temp_high = day.get('temperature', {}).get('high', 'N/A')
                temp_low = day.get('temperature', {}).get('low', 'N/A')
                icon = day.get('icon', '☀️')
                description = day.get('description', 'N/A')
                
                forecast_data.append([
                    f"{day_name} {formatted_date}",
                    f"{icon} {description}",
                    f"{temp_high}°C / {temp_low}°C"
                ])
        
        if forecast_data:
            forecast_df = pd.DataFrame(forecast_data, columns=['Date', 'Weather', 'Temperature'])
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
    
    st.divider()

# Add this function to handle PDF generation
def generate_and_display_pdf_options(trip_data, ai_suggestions, weather_data=None):
    """Generate PDF download options for the itinerary"""
    
    st.subheader("📄 Download Detailed Itinerary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("🔄 Generating detailed PDF itinerary..."):
                    # Generate PDF content
                    pdf_content = pdf_generator.generate_trip_pdf(
                        trip_data=trip_data,
                        ai_suggestions=ai_suggestions,
                        weather_data=weather_data
                    )
                    
                    # Create download filename
                    destination = trip_data.get('destination', 'Trip').replace(' ', '_')
                    start_date = trip_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                    filename = f"{destination}_{start_date}_Itinerary.pdf"
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download PDF Itinerary",
                        data=pdf_content,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.success("✅ PDF generated successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
                logger.error(f"PDF generation error: {str(e)}")
    
    with col2:
        st.info("📋 The PDF includes:\n• Complete itinerary with weather info\n• Accommodation recommendations\n• Activities & restaurants\n• Packing list & tips\n• Budget breakdown")

# Add this function to handle calendar integration
def generate_and_display_calendar_options(trip_data, ai_suggestions):
    """Generate calendar integration options"""
    
    st.subheader("📅 Add to Calendar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📅 Download Calendar (.ics)", type="secondary", use_container_width=True):
            try:
                with st.spinner("🔄 Creating calendar events..."):
                    # Generate ICS calendar content
                    calendar_content = calendar_service.create_calendar_from_itinerary(
                        trip_data=trip_data,
                        ai_suggestions=ai_suggestions
                    )
                    
                    # Create download filename
                    destination = trip_data.get('destination', 'Trip').replace(' ', '_')
                    start_date = trip_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                    filename = f"{destination}_{start_date}_Calendar.ics"
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download Calendar File",
                        data=calendar_content,
                        file_name=filename,
                        mime="text/calendar",
                        use_container_width=True
                    )
                    
                    st.success("✅ Calendar file created successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error creating calendar: {str(e)}")
                logger.error(f"Calendar creation error: {str(e)}")
    
    with col2:
        # Google Calendar quick add option
        try:
            google_calendar_url = calendar_service.create_google_calendar_url(
                trip_data=trip_data,
                ai_suggestions=ai_suggestions
            )
            
            st.markdown(
                f'<a href="{google_calendar_url}" target="_blank">'
                '<button style="background-color: #4285f4; color: white; border: none; '
                'padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%;">'
                '🗓️ Add to Google Calendar'
                '</button></a>',
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.button("🗓️ Add to Google Calendar", disabled=True, help="Calendar integration temporarily unavailable")

# Add this function to display the source information
def display_trip_source_info(trip_data):
    """Display source information for the trip"""
    source = trip_data.get('source', 'user_input')
    
    source_info = {
        'user_input': ('👤', 'Created by you'),
        'ai_generated': ('🤖', 'AI Generated'),
        'imported': ('📁', 'Imported'),
        'api': ('🔗', 'API Integration'),
        'template': ('📋', 'From Template')
    }
    
    icon, description = source_info.get(source, ('❓', 'Unknown Source'))
    
    st.caption(f"{icon} {description}")

# Update the main display_trip_suggestions function
def display_trip_suggestions(suggestions, trip_data, user_data):
    """Display trip suggestions with new features"""
    
    if not suggestions:
        st.error("❌ No suggestions available")
        return
    
    # Display source information
    display_trip_source_info(trip_data)
    
    # Display weather information if available
    weather_data = suggestions.get('weather_data') or trip_data.get('weather_data')
    if weather_data:
        display_weather_info(weather_data, suggestions)
    
    # Display main trip information
    destination = suggestions.get('destination', 'Unknown')
    duration = suggestions.get('duration', 'Unknown')
    budget = suggestions.get('budget', 0)
    currency_symbol = suggestions.get('currency_symbol', '$')
    
    # Trip overview
    st.subheader("🗺️ Trip Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Destination", destination)
    with col2:
        st.metric("Duration", duration)
    with col3:
        st.metric("Budget", f"{currency_symbol}{budget:,.2f}")
    
    # Budget breakdown
    if 'budget_breakdown' in suggestions:
        st.subheader("💰 Budget Breakdown")
        budget_breakdown = suggestions['budget_breakdown']
        
        breakdown_cols = st.columns(len(budget_breakdown))
        for i, (category, amount) in enumerate(budget_breakdown.items()):
            with breakdown_cols[i]:
                category_clean = category.replace('_', ' ').title()
                st.metric(category_clean, str(amount))
    
    # Daily itinerary with weather integration
    if 'itinerary' in suggestions and suggestions['itinerary']:
        st.subheader("📅 Daily Itinerary")
        
        for day_plan in suggestions['itinerary']:
            if not isinstance(day_plan, dict):
                continue
                
            day_num = day_plan.get('day', '')
            date_str = day_plan.get('date', '')
            day_name = day_plan.get('day_name', '')
            activities = day_plan.get('activities', [])
            meals = day_plan.get('meals', {})
            weather_conditions = day_plan.get('weather_conditions', '')
            weather_tips = day_plan.get('weather_tips', [])
            
            # Day header
            with st.expander(f"Day {day_num} - {day_name} ({date_str})", expanded=True):
                
                # Weather information for the day
                if weather_conditions:
                    st.info(f"🌤️ Weather: {weather_conditions}")
                
                # Weather tips
                if weather_tips:
                    st.write("**Weather Tips:**")
                    for tip in weather_tips:
                        st.write(f"• {tip}")
                
                # Activities
                if activities:
                    st.write("**Activities:**")
                    for activity in activities:
                        if isinstance(activity, str):
                            st.write(f"• {activity}")
                
                # Meals
                if meals:
                    st.write("**Meals:**")
                    meal_cols = st.columns(len(meals))
                    for i, (meal_type, meal_desc) in enumerate(meals.items()):
                        if meal_desc:
                            with meal_cols[i]:
                                st.write(f"**{meal_type.title()}:** {meal_desc}")
    
    # Display other sections (accommodations, activities, restaurants, etc.)
    display_other_suggestions(suggestions)
    
    # Weather adaptations section
    if 'weather_adaptations' in suggestions:
        st.subheader("🌦️ Weather Adaptations")
        weather_adaptations = suggestions['weather_adaptations']
        
        if weather_adaptations.get('rainy_day_activities'):
            st.write("**Rainy Day Activities:**")
            for activity in weather_adaptations['rainy_day_activities']:
                st.write(f"• {activity}")
        
        if weather_adaptations.get('hot_weather_tips'):
            st.write("**Hot Weather Tips:**")
            for tip in weather_adaptations['hot_weather_tips']:
                st.write(f"• {tip}")
        
        if weather_adaptations.get('cold_weather_tips'):
            st.write("**Cold Weather Tips:**")
            for tip in weather_adaptations['cold_weather_tips']:
                st.write(f"• {tip}")
    
    st.divider()
    
    # Action buttons section
    st.subheader("📋 Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Save trip button
        if st.button("💾 Save This Trip", type="primary", use_container_width=True):
            try:
                # Include weather data and source when saving
                success, message = save_trip_to_database(
                    user_id=user_data['id'],
                    destination=destination,
                    start_date=trip_data.get('start_date'),
                    end_date=trip_data.get('end_date'),
                    budget=budget,
                    preferences=trip_data.get('preferences', ''),
                    ai_suggestions=suggestions,
                    currency=suggestions.get('currency', 'USD'),
                    currency_symbol=currency_symbol,
                    weather_data=weather_data,
                    source=trip_data.get('source', 'ai_generated')
                )
                
                if success:
                    st.success("✅ Trip saved successfully!")
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Error saving trip: {str(e)}")
    
    with col2:
        # Modify trip button
        if st.button("✏️ Modify This Trip", type="secondary", use_container_width=True):
            # Set up modification mode
            st.session_state.modification_mode = True
            st.session_state.current_trip_suggestions = suggestions
            st.session_state.current_trip_data = trip_data
            st.rerun()
    
    # PDF and Calendar options
    generate_and_display_pdf_options(trip_data, suggestions, weather_data)
    generate_and_display_calendar_options(trip_data, suggestions)

def display_other_suggestions(suggestions):
    """Display accommodations, activities, restaurants, and transportation"""
    
    # Accommodations
    if 'accommodations' in suggestions and suggestions['accommodations']:
        st.subheader("🏨 Recommended Accommodations")
        
        for hotel in suggestions['accommodations']:
            if not isinstance(hotel, dict):
                continue
                
            name = hotel.get('name', 'Hotel')
            hotel_type = hotel.get('type', 'Hotel')
            price_range = hotel.get('price_range', 'N/A')
            rating = hotel.get('rating', 'N/A')
            location = hotel.get('location', 'N/A')
            amenities = hotel.get('amenities', [])
            description = hotel.get('description', '')
            weather_suitability = hotel.get('weather_suitability', '')
            
            with st.container():
                st.write(f"**{name}** ({hotel_type})")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📍 Location: {location}")
                    st.write(f"💰 Price: {price_range}")
                    st.write(f"⭐ Rating: {rating}/5" if rating != 'N/A' else f"⭐ Rating: {rating}")
                
                with col2:
                    if amenities:
                        st.write(f"🏨 Amenities: {', '.join(amenities[:4])}")
                    if weather_suitability:
                        st.write(f"🌤️ Weather: {weather_suitability}")
                
                if description:
                    st.write(f"📝 {description}")
                
                st.divider()
    
    # Activities
    if 'activities' in suggestions and suggestions['activities']:
        st.subheader("🎯 Recommended Activities")
        
        for activity in suggestions['activities']:
            if not isinstance(activity, dict):
                continue
                
            name = activity.get('name', 'Activity')
            activity_type = activity.get('type', 'Activity')
            duration = activity.get('duration', 'N/A')
            cost = activity.get('cost', 'N/A')
            description = activity.get('description', '')
            rating = activity.get('rating', 'N/A')
            best_time = activity.get('best_time', 'N/A')
            weather_dependency = activity.get('weather_dependency', 'N/A')
            alternative = activity.get('alternative_if_bad_weather', '')
            
            with st.container():
                st.write(f"**{name}** ({activity_type})")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"⏱️ Duration: {duration}")
                    st.write(f"💰 Cost: {cost}")
                    st.write(f"⭐ Rating: {rating}/5" if rating != 'N/A' else f"⭐ Rating: {rating}")
                
                with col2:
                    st.write(f"🕐 Best Time: {best_time}")
                    st.write(f"🌤️ Weather Dependency: {weather_dependency}")
                
                if description:
                    st.write(f"📝 {description}")
                    
                if alternative:
                    st.write(f"☔ Backup Plan: {alternative}")
                
                st.divider()
    
    # Restaurants
    if 'restaurants' in suggestions and suggestions['restaurants']:
        st.subheader("🍽️ Recommended Restaurants")
        
        for restaurant in suggestions['restaurants']:
            if not isinstance(restaurant, dict):
                continue
                
            name = restaurant.get('name', 'Restaurant')
            cuisine = restaurant.get('cuisine', 'N/A')
            price_range = restaurant.get('price_range', 'N/A')
            rating = restaurant.get('rating', 'N/A')
            location = restaurant.get('location', 'N/A')
            specialties = restaurant.get('specialties', [])
            reservation_required = restaurant.get('reservation_required', False)
            weather_notes = restaurant.get('weather_notes', '')
            
            with st.container():
                st.write(f"**{name}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"🍽️ Cuisine: {cuisine}")
                    st.write(f"💰 Price: {price_range}")
                    st.write(f"📍 Location: {location}")
                
                with col2:
                    st.write(f"⭐ Rating: {rating}/5" if rating != 'N/A' else f"⭐ Rating: {rating}")
                    st.write(f"📞 Reservation: {'Required' if reservation_required else 'Not Required'}")
                    if weather_notes:
                        st.write(f"🌤️ {weather_notes}")
                
                if specialties:
                    st.write(f"👨‍🍳 Specialties: {', '.join(specialties)}")
                
                st.divider()
    
    # Transportation
    if 'transportation' in suggestions and suggestions['transportation']:
        st.subheader("🚗 Transportation Options")
        
        for transport in suggestions['transportation']:
            if not isinstance(transport, dict):
                continue
                
            transport_type = transport.get('type', 'Transportation')
            option = transport.get('option', 'N/A')
            cost = transport.get('cost', 'N/A')
            duration = transport.get('duration', 'N/A')
            description = transport.get('description', '')
            booking_required = transport.get('booking_required', False)
            weather_considerations = transport.get('weather_considerations', '')
            
            with st.container():
                st.write(f"**{transport_type} - {option}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"💰 Cost: {cost}")
                    st.write(f"⏱️ Duration: {duration}")
                
                with col2:
                    st.write(f"📞 Booking: {'Required' if booking_required else 'Not Required'}")
                    if weather_considerations:
                        st.write(f"🌤️ {weather_considerations}")
                
                if description:
                    st.write(f"📝 {description}")
                
                st.divider()
    
    # Tips and Packing List
    col1, col2 = st.columns(2)
    
    with col1:
        if 'tips' in suggestions and suggestions['tips']:
            st.subheader("💡 Travel Tips")
            for tip in suggestions['tips']:
                st.write(f"• {tip}")
    
    with col2:
        if 'packing_list' in suggestions and suggestions['packing_list']:
            st.subheader("🎒 Packing List")
            for item in suggestions['packing_list']:
                st.write(f"• {item}")

# Add this to the main trip planner interface
def show_trip_planner_with_new_features():
    """Enhanced trip planner with weather integration and new features"""
    
    # ... existing code for form inputs ...
    
    # Add source field to the form
    with st.sidebar:
        st.subheader("📊 Trip Source")
        source_options = {
            'user_input': '👤 Manual Input',
            'ai_generated': '🤖 AI Generated',
            'template': '📋 From Template',
            'imported': '📁 Imported'
        }
        
        selected_source = st.selectbox(
            "How was this trip created?",
            options=list(source_options.keys()),
            format_func=lambda x: source_options[x],
            index=0
        )
    
    # When generating suggestions, pass the source
    if st.button("🗺️ Generate Trip Plan", type="primary", use_container_width=True):
        if validate_inputs(destination, start_date, end_date, budget):
            with st.spinner("🤖 Creating your personalized trip plan with weather forecast..."):
                trip_data = {
                    'destination': destination,
                    'start_date': start_date,
                    'end_date': end_date,
                    'budget': budget,
                    'preferences': preferences,
                    'currency': selected_currency,
                    'currency_symbol': currency_info['symbol'],
                    'source': selected_source  # Add source to trip data
                }
                
                # Generate suggestions (this will automatically include weather data)
                suggestions = trip_planner.generate_trip_suggestions(
                    destination=destination,
                    start_date=start_date,
                    end_date=end_date,
                    budget=budget,
                    preferences=preferences,
                    currency=selected_currency,
                    currency_symbol=currency_info['symbol']
                )
                
                if suggestions:
                    st.session_state.current_suggestions = suggestions
                    st.session_state.current_trip_data = trip_data
                    st.session_state.current_user_data = user_data
                    
                    # Display with new features
                    display_trip_suggestions(suggestions, trip_data, user_data)
                else:
                    st.error("❌ Unable to generate trip suggestions. Please try again.")      

# Initialize the trip planner
if __name__ == "__main__":
    show_trip_planner()
