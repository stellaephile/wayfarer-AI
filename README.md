# ![Wayfarer AI Logo](misc/logo.png)

# Wayfarer AI

**Your AI-powered travel planner for effortless, sustainable, and personalized trips.**

---

## 🚀 About

Wayfarer AI is an intelligent trip planning platform that leverages Google GenAI to generate curated itineraries, integrate real-time booking options, and streamline the travel experience from inspiration to confirmation.

- **Hackathon:** Google GenAI Exchange 2025  
- **Team Name:** [Your Team Name Here]
- **Team Members:**  
  - [Sonal Ganvir](https://github.com/sonalgan)  
  - [Bhupendra Choudhary](https://github.com/Bhupendrachaudhary2001)
  - [Pratik Dongre](https://github.com/cosmic-ash)

---

## ✨ Features

- **Trip Preferences Form:** Collects user preferences (destination, dates, budget, travel type, interests, accommodation, etc.).
- **AI-Powered Itinerary Generation:** Uses Vertex AI to create sustainable, time-efficient, or cost-efficient travel plans.
- **Google OAuth & Email Login:** Secure authentication for a personalized experience.
- **Iterative Planning:** Users can modify preferences and regenerate itineraries until satisfied.
- **Export Options:** Download itineraries as PDF or add to calendar (.ics).
- **Real-Time Booking Integration:** View and book flights/hotels via EaseMyTrip; bookings reflected in your itinerary.
- **Credit System:** Track and display usage credits for AI and booking features.
- **User Dashboard:** Manage trips, bookings, and profile.
- **Modern UI:** Built with Streamlit for a seamless, interactive experience.

---

## 🏗️ Project Structure

```
src/
  app.py                  # Main Streamlit app
  trip_planner.py         # Trip planning logic and UI
  booking_interface.py    # Booking options and integration
  booking_system.py       # Booking system logic
  credit_widget.py        # Credit display and management
  google_auth.py          # Google OAuth authentication
  vertex_ai_utils.py      # Vertex AI integration
  ... (other modules)
misc/
  logo.png                # App logo
  uml.text                # UML diagrams and notes
```

---

## 🛠️ Getting Started

1. **Clone the repository:**
   ```
   git clone https://github.com/your-team/wayfarer-ai.git
   cd wayfarer-ai
   ```

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Set up secrets:**
   - Add your credentials in `.streamlit/secrets.toml` as per the template.

4. **Run the app:**
   ```
   streamlit run src/app.py
   ```


---

## 🤝 Team

| Name           | GitHub                                      |
|----------------|---------------------------------------------|
| Sonal Ganvir   | [sonalgan](https://github.com/sonalgan)     |
| Bhupendra Choudhary     | [GitHub](https://github.com/username)       |

---

## 🏆 Hackathon

- **Event:** Google GenAI Exchange 2025
- **Track:** Personalized Trip Planner with AI

---

## 📄 License

[MIT License](LICENSE)

---

*Happy Travels with Wayfarer AI!*