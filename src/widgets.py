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
