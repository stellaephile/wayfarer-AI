# 🗺️ AI Trip Planner

A comprehensive AI-powered trip planning application built with Streamlit and Google Vertex AI. Plan your perfect vacation with personalized recommendations, itinerary generation, and budget management.

## ✨ Features

### 🎯 Core Functionality
- **AI-Powered Trip Planning**: Generate personalized trip suggestions using Google Vertex AI
- **User Authentication**: Secure login/signup with password hashing
- **Trip Management**: Save, view, edit, and delete your trip plans
- **Budget Planning**: Set and track trip budgets with cost breakdowns
- **Interactive UI**: Modern, responsive interface built with Streamlit

### 🏨 Trip Recommendations
- **Daily Itineraries**: Day-by-day activity suggestions
- **Accommodation Options**: Hotel and B&B recommendations with pricing
- **Restaurant Suggestions**: Local dining recommendations
- **Activity Planning**: Sightseeing, cultural, and adventure activities
- **Transportation**: Travel options and cost estimates
- **Weather Information**: Climate data and packing suggestions
- **Travel Tips**: Local insights and recommendations

### 👤 User Profile Management
- **Personal Information**: Name, email, contact details
- **Profile Fields**: Personal number, address, pincode, state, alternate number
- **Trip Analytics**: Statistics and insights about your travels
- **Trip History**: View all your saved trips

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud Account (optional, for Vertex AI)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sonalgan/trip-planner-genAI.git
   cd trip-planner-genAI
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure secrets (optional)**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml with your Google Cloud credentials
   ```

5. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 🔧 Configuration

### Google Cloud Setup (Optional)

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Vertex AI API**
   - Navigate to APIs & Services > Library
   - Search for "Vertex AI API" and enable it

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account with Vertex AI permissions
   - Download the JSON key file

4. **Set Environment Variables**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
   export VERTEX_AI_PROJECT_ID="your-project-id"
   export VERTEX_AI_LOCATION="us-central1"
   ```

### Streamlit Secrets (Alternative)

Create `.streamlit/secrets.toml`:
```toml
# Google OAuth Configuration (Optional)
GOOGLE_CLIENT_ID = "your-client-id"
GOOGLE_CLIENT_SECRET = "your-client-secret"
GOOGLE_REDIRECT_URI = "http://localhost:8501"

# Vertex AI Configuration (Optional)
VERTEX_AI_PROJECT_ID = "your-project-id"
VERTEX_AI_LOCATION = "us-central1"
VERTEX_AI_MODEL = "gemini-pro"
```

## 📱 Usage

### 1. Authentication
- **Sign Up**: Create a new account with username, email, and password
- **Login**: Access your account with credentials
- **Security**: Passwords are securely hashed with bcrypt

### 2. Plan a Trip
- Enter destination, dates, and budget
- Specify travel preferences (adventure, culture, food, etc.)
- Select travel type (solo, couple, family, etc.)
- Generate AI-powered trip suggestions

### 3. View Trip Details
- **Itinerary**: Day-by-day activity breakdown
- **Accommodations**: Hotel and B&B recommendations
- **Activities**: Sightseeing and experience suggestions
- **Restaurants**: Dining recommendations with ratings
- **Transportation**: Travel options and costs
- **Tips**: Travel advice and local insights
- **Weather**: Climate information and packing suggestions

### 4. Manage Trips
- **My Trips**: View all saved trip plans
- **Analytics**: Visualize trip data and preferences
- **Profile**: Account information and statistics

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    name TEXT,
    google_id TEXT UNIQUE,
    picture TEXT,
    verified_email BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    login_method TEXT DEFAULT 'email',
    personal_number TEXT,
    address TEXT,
    pincode TEXT,
    state TEXT,
    alternate_number TEXT
);
```

### Trips Table
```sql
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    destination TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    budget REAL,
    preferences TEXT,
    ai_suggestions TEXT,
    status TEXT DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 🛠️ Development

### Project Structure
```
trip-planner-genAI/
├── src/
│   ├── app.py                 # Main Streamlit application
│   ├── auth.py                # Authentication logic
│   ├── database.py            # Database operations
│   ├── google_auth.py         # Google OAuth integration
│   ├── trip_planner.py        # Trip planning interface
│   └── vertex_ai_utils.py     # Vertex AI integration
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml           # Secrets (not in git)
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
└── README.md                  # This file
```

### Key Features Implemented
- ✅ User authentication and profile management
- ✅ AI-powered trip planning with mock data
- ✅ Database integration with SQLite
- ✅ Responsive UI with Streamlit
- ✅ Trip management and analytics
- ✅ Google OAuth integration (optional)
- ✅ Docker support for deployment

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Using Docker
```bash
docker build -t trip-planner .
docker run -p 8501:8501 trip-planner
```

## 📊 Technologies Used

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Database**: SQLite
- **AI/ML**: Google Vertex AI (Gemini Pro)
- **Authentication**: bcrypt, Google OAuth2
- **Deployment**: Docker, Docker Compose

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Vertex AI for AI capabilities
- Streamlit for the amazing web framework
- The open-source community for various Python packages

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Check the documentation
- Contact the maintainers

---

**Happy Traveling! 🗺️✈️**
