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



def with_dynamic_spinner(messages=None, delay=1.5, color_pairs=None):
    """
    Decorator that shows rotating messages inside a readable colored box.
    Each text color is paired with a compatible light background.
    """
    if messages is None:
        messages = ["Processing...", "Almost there...", "Hang tight..."]

    # Define text color → readable background mapping
    if color_pairs is None:
        color_pairs = [
            ("#c10404ff", "#ffcccc"),  # red text, light red bg
            ("#0404c3ff", "#cce5ff"),  # blue text, light blue bg
            ("#028002FF", "#ccffcc"),  # green text, light green bg
            ("#ffa600ff", "#ffedcc"),  # orange text, light orange bg
            ("#B102B1", "#e6ccff"),  # purple text, light purple bg
            ("#3D3C3CFF", "#f5f5f5")   # dark gray text, light gray bg
        ]

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
                text_color, bg_color = color_pairs[i % len(color_pairs)]

                html = f"""
                <div style="
                    background-color:{bg_color};
                    color:{text_color};
                    padding: 15px;
                    border-radius: 12px;
                    text-align: center;
                    font-weight: bold;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                    transition: background-color 0.3s, color 0.3s;
                ">
                    {message}
                </div>
                """
                placeholder.markdown(html, unsafe_allow_html=True)
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



from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

def generate_trip_pdf(trip_data, itinerary, weather_data=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    elements = []

    destination = trip_data.get("destination", "Unknown").title()

    # --- COVER PAGE or fallback ---
    if not itinerary:
        elements.append(Spacer(1, 200))
        elements.append(Paragraph(f"<b>{destination} Itinerary</b>", styles["Title"]))
        elements.append(Paragraph("🗓️ Duration not available", styles["Heading2"]))
    else:
        start_date_str = itinerary[0].get("date", "")
        end_date_str = itinerary[-1].get("date", "")

        # Logo
        logo = os.getenv("LOGO_IMG")
        if logo and os.path.exists(logo):
            elements.append(Spacer(1, 120))
            img = Image(logo, width=200, height=200)
            img.hAlign = "CENTER"
            elements.append(img)

        elements.append(Spacer(1, 60))
        elements.append(Paragraph(f"<b>{destination} Itinerary</b>", styles["Title"]))
        elements.append(Paragraph(f"{format_date_pretty(start_date_str)} ➝ {format_date_pretty(end_date_str)}", styles["Heading2"]))

        # Duration
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            num_days = (end_dt - start_dt).days + 1
            num_nights = num_days - 1
            duration_str = f"{num_days} Days, {num_nights} Nights"
        except Exception:
            duration_str = "Duration not available"

        elements.append(Paragraph(f"🗓️ {duration_str}", styles["Heading3"]))
        elements.append(Spacer(1, 200))
        elements.append(Paragraph("Prepared with ❤️ by Wayfarer AI", styles["Normal"]))
        elements.append(PageBreak())

        # --- DAILY ITINERARY ---
        for day_plan in itinerary:
            day_title = f"Day {day_plan.get('day', '')} - {day_plan.get('day_name', '')} ({format_date_pretty(day_plan.get('date', ''))}"
            elements.append(Paragraph(day_title, styles["Heading2"]))

            activity_data = [["Time/Meal", "Plan"]]

            # Wrap activities in Paragraphs
            for act in day_plan.get("activities", []):
                activity_data.append(["Activity", Paragraph(act, styles["Normal"])])

            # Wrap meals in Paragraphs
            for meal, desc in day_plan.get("meals", {}).items():
                activity_data.append([meal.capitalize(), Paragraph(desc, styles["Normal"])])

            table = Table(activity_data, colWidths=[120, 360])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),  # keep text aligned top
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))


        # --- BUDGET BREAKDOWN ---
        if "budget_breakdown" in trip_data:
            elements.append(PageBreak())
            elements.append(Paragraph("💰 Budget Breakdown", styles["Heading2"]))
            budget_data = [["Category", "Amount (₹)"]]
            for k, v in trip_data["budget_breakdown"].items():
                budget_data.append([k.capitalize(), f"₹{v:,.0f}"])
            budget_data.append(["Total", f"₹{trip_data.get('budget', 0):,.0f}"])
            elements.append(Table(budget_data, colWidths=[200, 280]))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf




def generate_and_display_pdf_options(trip_data, ai_suggestions, weather_data=None):
    try:
        # ai_suggestions can be JSON string or dict
        if isinstance(ai_suggestions, str):
            ai_suggestions = json.loads(ai_suggestions)
        
        # ✅ Pull itinerary from ai_suggestions
        itinerary = ai_suggestions.get("itinerary", []) if ai_suggestions else []
        
        # If itinerary is missing, fall back
        if not itinerary:
            itinerary = trip_data.get("itinerary", [])
        
        # Now pass itinerary into PDF generator
        pdf_bytes = generate_trip_pdf(trip_data, itinerary, weather_data=None)

        st.download_button(
            label="📥 Download Itinerary PDF",
            data=pdf_bytes,
            file_name=f"trip_itinerary_{trip_data.get('destination','trip')}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")

