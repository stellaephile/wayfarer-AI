# widgets.py

import streamlit as st
import time,os,json
import threading
import random
from functools import wraps
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime

def get_fun_spinner_messages():
    messages = [
        "🧳 Packing your bags (don’t forget your socks)...",
        "🌍 Looking for cool places on the map...",
        "🕵️ Searching the internet for hidden gems...",
        "🍕 Checking where the best food is hiding...",
        "✈️ Booking imaginary flights (real ones soon!)...",
        "🏖️ Finding you the perfect beach spot...",
        "📸 Planning where you’ll take the best selfies...",
        "🚲 Testing fun ways to get around...",
        "🐒 Asking the locals (and a monkey) for ideas...",
        "🛏️ Making sure your hotel has comfy pillows...",
        "🗺️ Drawing your dream trip route with crayons...",
        "🌦️ Checking if the weather will behave...",
        "🎢 Looking for places that make your heart race...",
        "💸 Stretching your budget like magic...",
        "⏳ Just a sec… making travel magic happen...",
        "🧼 Making sure your trip is nice and smooth...",
        "📦 Wrapping up your adventure with a bow...",
        "🚀 Zooming around the world for ideas...",
        "🎧 Putting together the perfect travel playlist...",
        "🧁 Adding a sweet surprise to your journey...",
    ]
    random.shuffle(messages)
    return messages

def with_dynamic_spinner(messages=None, delay=1.5):
    """
    Decorator that shows rotating messages while a function runs.
    """
    if messages is None:
        messages = get_fun_spinner_messages()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            placeholder = st.empty()
            result = [None]

            def long_task():
                result[0] = func(*args, **kwargs)

            task_thread = threading.Thread(target=long_task)
            task_thread.start()

            i = 0
            while task_thread.is_alive():
                message = messages[i % len(messages)]
                placeholder.info(message)
                time.sleep(delay)
                i += 1

            task_thread.join()
            placeholder.empty()
            return result[0]

        return wrapper
    return decorator

from datetime import datetime

def get_day_suffix(day):
    """Return the day suffix for a given day number."""
    if 11 <= day <= 13:
        return 'th'
    last_digit = day % 10
    if last_digit == 1:
        return 'st'
    elif last_digit == 2:
        return 'nd'
    elif last_digit == 3:
        return 'rd'
    else:
        return 'th'

def format_date_pretty(date_input):
    """
    Accepts a datetime object or string (YYYY-MM-DD).
    Returns a pretty formatted date string like '23rd September, 2025'.
    """
    if isinstance(date_input, str):
        # Convert string to datetime
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
    else:
        date_obj = date_input

    day = date_obj.day
    suffix = get_day_suffix(day)
    return f"{day}{suffix} {date_obj.strftime('%B')}, {date_obj.year}"



def generate_trip_pdf(trip_data, ai_suggestions, weather_data=None):
    """Generate a polished A4 itinerary PDF with logo, cover page, and details"""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", fontSize=22, alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name="SubHeading", fontSize=14, textColor=colors.HexColor("#3b82f6"), spaceAfter=10))
    styles.add(ParagraphStyle(name="NormalJustify", fontSize=11, leading=14, alignment=4))

    elements = []

    # ---------------- Cover Page ----------------
    try:
        logo = os.getenv("LOGO_IMG")  # path to your uploaded logo
        img = Image(logo, width=180, height=180)
        img.hAlign = "CENTER"
        elements.append(Spacer(1, 100))
        elements.append(img)
    except Exception as e:
        print("Logo load error:", e)

    destination = trip_data.get('destination', 'Your Trip')
    start_date = trip_data.get('start_date', 'N/A')
    end_date = trip_data.get('end_date', 'N/A')

    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"<b>{destination} Itinerary</b>", styles["CenterTitle"]))
    elements.append(Paragraph(f"{start_date} ➝ {end_date}", styles["CenterTitle"]))
    elements.append(Spacer(1, 200))
    elements.append(Paragraph("Prepared with Wayfarer AI ✈️", styles["NormalJustify"]))

    elements.append(PageBreak())

    # ---------------- Itinerary Section ----------------
    elements.append(Paragraph("✨ Suggested Itinerary", styles["SubHeading"]))
    if isinstance(ai_suggestions, (dict, list)):
        pretty_itinerary = json.dumps(ai_suggestions, indent=2)  # convert to string
    else:
        pretty_itinerary = str(ai_suggestions)

    elements.append(Paragraph(pretty_itinerary.replace("\n", "<br/>"), styles["NormalJustify"]))
    elements.append(Spacer(1, 20))

    # ---------------- Weather Section ----------------
    if weather_data:
        elements.append(Paragraph("🌤️ Weather Forecast", styles["SubHeading"]))
        if isinstance(weather_data, (dict, list)):
            pretty_weather = json.dumps(weather_data, indent=2)
        else:
            pretty_weather = str(weather_data)
        elements.append(Paragraph(pretty_weather.replace("\n", "<br/>"), styles["NormalJustify"]))
        elements.append(Spacer(1, 20))

    # ---------------- Trip Details ----------------
    details_data = [
        ["Destination", destination],
        ["Start Date", start_date],
        ["End Date", end_date],
        ["Budget", trip_data.get("budget", "N/A")],
        ["Travelers", trip_data.get("travelers", "N/A")]
    ]
    table = Table(details_data, hAlign="LEFT", colWidths=[100, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#3b82f6")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    elements.append(Paragraph("📋 Trip Details", styles["SubHeading"]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf



def generate_and_display_pdf_options(trip_data, ai_suggestions, weather_data=None):
    """Generate and download PDF itinerary in one click"""

    st.subheader("📄 Download Detailed Itinerary")

    if st.button("📄 Generate PDF Itinerary", type="primary", use_container_width=True):
        try:
            with st.spinner("🔄 Generating detailed PDF itinerary..."):
                # ✅ Call your ReportLab generator
                pdf_content = generate_trip_pdf(
                    trip_data=trip_data,
                    ai_suggestions=ai_suggestions,
                    weather_data=weather_data
                )

                # ✅ Create filename
                destination = trip_data.get('destination', 'Trip').replace(' ', '_')
                start_date = trip_data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
                filename = f"{destination}_{start_date}_Itinerary.pdf"

                # ✅ Streamlit download button
                st.download_button(
                    label="📥 Click to Download",
                    data=pdf_content,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )

                st.success("✅ PDF generated successfully!")

        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
