# widgets.py

import streamlit as st
import time
import threading
import random
from functools import wraps

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

