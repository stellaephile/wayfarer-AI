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
   # Copy example configuration files
   cp .env.example .env
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   
   # Edit the configuration files with your settings
   ```

5. **Run the application**
   ```bash 
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 🔧 Configuration

### Vertex AI Setup (Optional but Recommended)

For AI-powered trip planning, you'll need to set up Google Vertex AI:

1. **Follow the detailed setup guide**: [VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md)
2. **Quick setup**:
   - Create a Google Cloud project
   - Enable Vertex AI API
   - Set up authentication
   - Configure environment variables

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

### 3. AI Trip Planning
- **Smart Recommendations**: AI-powered suggestions based on your preferences
- **Budget Optimization**: Intelligent budget allocation across categories
- **Personalized Itineraries**: Custom daily schedules tailored to your interests
- **Real-time Planning**: Get instant trip plans with detailed recommendations

### 4. Trip Management
- **Save Trips**: Store your favorite trip plans
- **Edit Details**: Modify existing trip information
- **Delete Trips**: Remove unwanted trip plans
- **View Analytics**: Track your travel patterns and spending

### 5. Profile Management
- **Personal Information**: Update your contact details and preferences
- **Travel Preferences**: Set your interests and travel style
- **Account Settings**: Manage your account security and preferences

## 🏗️ Architecture

### Backend
- **Streamlit**: Web application framework
- **SQLite**: Local database for user data and trip storage
- **Vertex AI**: Google's AI platform for trip planning
- **Google OAuth**: Authentication and user management

### Frontend
- **Streamlit Components**: Interactive UI elements
- **Custom CSS**: Modern styling and responsive design
- **Plotly**: Data visualization and analytics

### AI Integration
- **Vertex AI Gemini**: Large language model for trip planning
- **Structured Prompts**: Optimized prompts for consistent JSON responses
- **Error Handling**: Graceful fallback to mock data when AI is unavailable
- **Response Parsing**: Robust JSON parsing with validation

## 🔒 Security

- **Password Hashing**: bcrypt for secure password storage
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: Secure error messages without sensitive information

## 🚀 Deployment

### Local Development
```bash
streamlit run src/app.py
```

### Docker Deployment
```bash
# Build the image
docker build -t ai-trip-planner .

# Run the container
docker run -p 8501:8501 ai-trip-planner
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 📊 Features in Detail

### AI Trip Planning
- **Destination Analysis**: AI analyzes your destination and provides contextual recommendations
- **Budget Optimization**: Smart allocation of budget across accommodation, food, activities, and transportation
- **Preference Matching**: Recommendations tailored to your interests (adventure, culture, food, etc.)
- **Seasonal Considerations**: Weather and seasonal factors included in planning
- **Local Insights**: Authentic local recommendations and hidden gems

### User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern Styling**: Gradient backgrounds, smooth animations, and professional design
- **Intuitive Navigation**: Easy-to-use sidebar navigation and quick actions
- **Real-time Updates**: Instant feedback and updates throughout the application

### Data Management
- **Persistent Storage**: All trips and user data saved locally
- **Data Export**: Export trip plans and analytics
- **Backup Options**: Easy backup and restore functionality
- **Privacy Focused**: All data stored locally, no external data sharing

## 🛠️ Development

### Project Structure
```
streamlit-vertexai-demo/
├── src/
│   ├── app.py              # Main application entry point
│   ├── auth.py             # Authentication and user management
│   ├── database.py         # Database operations
│   ├── trip_planner.py     # Trip planning interface
│   ├── vertex_ai_utils.py  # Vertex AI integration
│   └── google_auth.py      # Google OAuth integration
├── credentials/            # Service account keys (not in git)
├── data/                   # SQLite database files
├── logs/                   # Application logs
├── .streamlit/             # Streamlit configuration
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image definition
└── requirements.txt        # Python dependencies
```

### Adding New Features
1. **Backend Logic**: Add new functions in appropriate modules
2. **UI Components**: Create new Streamlit components
3. **Database Schema**: Update database.py for new data structures
4. **AI Integration**: Extend vertex_ai_utils.py for new AI features

### Testing
```bash
# Run the application in test mode
STREAMLIT_SERVER_HEADLESS=true streamlit run src/app.py

# Test with mock data (no AI required)
VERTEX_AI_PROJECT_ID=your-project-id streamlit run src/app.py
```

## 📈 Performance

### Optimization Features
- **Lazy Loading**: Components loaded only when needed
- **Caching**: Intelligent caching of AI responses
- **Efficient Queries**: Optimized database queries
- **Resource Management**: Proper cleanup and memory management

### Monitoring
- **Logging**: Comprehensive logging for debugging
- **Error Tracking**: Detailed error reporting and handling
- **Performance Metrics**: Track response times and resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Streamlit**: For the amazing web framework
- **Google Vertex AI**: For powerful AI capabilities
- **Open Source Community**: For various Python packages and tools

## 📞 Support

If you encounter any issues:

1. Check the [troubleshooting guide](VERTEX_AI_SETUP.md#troubleshooting)
2. Review the application logs
3. Verify your configuration
4. Create an issue on GitHub

## 🔄 Changelog

### Version 2.0.0
- ✅ Full Vertex AI integration
- ✅ Enhanced AI trip planning
- ✅ Improved error handling
- ✅ Better fallback mechanisms
- ✅ Comprehensive documentation

### Version 1.0.0
- ✅ Basic trip planning functionality
- ✅ User authentication
- ✅ Mock data integration
- ✅ Modern UI design

---

**Happy Traveling! 🗺️✈️**
