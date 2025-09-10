# 🗺️ AI Trip Planner

A modern, AI-powered trip planning application built with Streamlit and Google Vertex AI. Plan your perfect vacation with personalized recommendations, beautiful UI, and comprehensive trip management.

## ✨ Features

### 🎯 Core Functionality
- **AI-Powered Trip Planning**: Generate personalized trip suggestions using Google Vertex AI
- **Modern UI/UX**: Beautiful, responsive interface with gradient designs and smooth animations
- **User Authentication**: Secure login/signup with password hashing and Google OAuth
- **Trip Management**: Save, view, edit, and delete your trip plans
- **Budget Planning**: Set and track trip budgets with cost breakdowns
- **Profile Management**: Complete user profile with contact information and preferences

### 🏨 Trip Recommendations
- **Daily Itineraries**: Day-by-day activity suggestions with detailed breakdowns
- **Accommodation Options**: Hotel and B&B recommendations with pricing and ratings
- **Restaurant Suggestions**: Local dining recommendations with cuisine types
- **Activity Planning**: Sightseeing, cultural, and adventure activities
- **Transportation**: Travel options and cost estimates
- **Weather Information**: Climate data and packing suggestions
- **Travel Tips**: Local insights and recommendations

### 👤 User Experience
- **Dashboard**: Overview of your travel statistics and recent trips
- **Profile Management**: Edit personal information, contact details, and preferences
- **Analytics**: Visualize your travel patterns and spending
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Modern Styling**: Gradient backgrounds, smooth animations, and professional design

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
- **Google OAuth**: Optional Google sign-in integration
- **Security**: Passwords are securely hashed with bcrypt

### 2. Dashboard
- **Overview**: Quick statistics of your trips and budget
- **Recent Trips**: View your latest trip plans
- **Quick Actions**: Fast access to planning and management features
- **Tips & Suggestions**: Helpful travel advice and recommendations

### 3. Plan a Trip
- **Trip Details**: Enter destination, dates, and budget
- **Preferences**: Specify interests (adventure, culture, food, etc.)
- **Travel Type**: Select solo, couple, family, or business travel
- **AI Generation**: Get personalized trip suggestions
- **Real-time Preview**: See your trip plan immediately after generation

### 4. Trip Management
- **My Trips**: View all saved trip plans with status indicators
- **Trip Details**: Comprehensive view of itinerary, accommodations, and activities
- **Edit/Delete**: Manage your trip plans
- **Analytics**: Visualize your travel patterns and spending

### 5. Profile Management
- **Personal Info**: Update name, email, and contact details
- **Address**: Add personal number, address, pincode, and state
- **Security**: View account security information
- **Preferences**: Manage travel preferences and settings

## 🎨 UI/UX Features

### Modern Design
- **Gradient Backgrounds**: Beautiful color schemes throughout the app
- **Smooth Animations**: Hover effects and transitions for better UX
- **Responsive Layout**: Optimized for all screen sizes
- **Professional Typography**: Inter font family for clean readability

### Enhanced Components
- **Interactive Cards**: Hover effects and visual feedback
- **Smart Forms**: Real-time validation and user-friendly inputs
- **Status Indicators**: Clear visual cues for trip status and progress
- **Compact Sidebar**: Optimized navigation with minimal space usage

### User Experience
- **Intuitive Navigation**: Easy-to-use menu system
- **Quick Actions**: Fast access to common tasks
- **Visual Feedback**: Clear success/error messages
- **Loading States**: Smooth progress indicators

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
│   ├── app.py                 # Main Streamlit application with modern UI
│   ├── auth.py                # Authentication logic
│   ├── database.py            # Database operations
│   ├── google_auth.py         # Google OAuth integration
│   ├── trip_planner.py        # Trip planning interface with optimized sidebar
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
- ✅ Modern UI/UX with gradient designs and animations
- ✅ User authentication and profile management
- ✅ AI-powered trip planning with mock data
- ✅ Database integration with SQLite
- ✅ Responsive UI with Streamlit
- ✅ Trip management and analytics
- ✅ Google OAuth integration (optional)
- ✅ Docker support for deployment
- ✅ Optimized sidebar and navigation
- ✅ Enhanced form validation and user feedback

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

- **Frontend**: Streamlit with custom CSS and animations
- **Backend**: Python 3.8+
- **Database**: SQLite with enhanced schema
- **AI/ML**: Google Vertex AI (Gemini Pro)
- **Authentication**: bcrypt, Google OAuth2
- **Styling**: Custom CSS with Google Fonts (Inter)
- **Deployment**: Docker, Docker Compose

## 🎯 Recent Updates

### UI/UX Improvements
- **Modern Design System**: Gradient backgrounds, smooth animations, and professional styling
- **Optimized Sidebar**: Compact navigation with proper icon and app name placement
- **Enhanced Components**: Better buttons, cards, forms, and visual feedback
- **Responsive Design**: Improved mobile and tablet experience
- **Clean Codebase**: Removed test files and backup files for better organization

### New Features
- **Dashboard Overview**: Quick statistics and recent trips display
- **Profile Management**: Complete user profile editing with contact information
- **Enhanced Trip Display**: Better visualization of trip details and recommendations
- **Improved Navigation**: Streamlined menu system with quick actions

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
