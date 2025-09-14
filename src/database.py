# database.py - Local Files + Git Storage
import json
import os
import bcrypt
from datetime import datetime
import streamlit as st

class DatabaseManager:
    def __init__(self):
        # Create data directories
        self.base_dir = "data"
        self.users_dir = f"{self.base_dir}/users"
        self.chats_dir = f"{self.base_dir}/chats"
        self.trips_dir = f"{self.base_dir}/trips"
        self.logs_dir = f"{self.base_dir}/logs"
        
        # Create all directories
        for dir_path in [self.base_dir, self.users_dir, self.chats_dir, self.trips_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize master index files
        self.users_index = f"{self.base_dir}/users_index.json"
        self.init_index_file(self.users_index)

    def init_index_file(self, file_path):
        """Initialize index file if it doesn't exist"""
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)

    def load_index(self, file_path):
        """Load index file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_index(self, file_path, data):
        """Save index file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def log_activity(self, activity_type, data):
        """Log all activities for debugging/analytics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = f"{self.logs_dir}/{activity_type}_{timestamp}.json"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity_type,
            "data": data
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2, default=str)
        
        print(f"📝 Logged: {activity_type} -> {log_file}")

    def create_user(self, username, email, password, name=None):
        """Create a new user"""
        try:
            # Load existing users index
            users_index = self.load_index(self.users_index)
            
            # Check if user exists
            for user_id, user_info in users_index.items():
                if user_info['email'] == email:
                    return False, "Email already exists"
                if user_info['username'] == username:
                    return False, "Username already exists"
            
            # Create new user
            user_id = f"user_{len(users_index) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "name": name,
                "password_hash": pw_hash,
                "login_method": "email",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
            
            # Save user data to individual file
            user_file = f"{self.users_dir}/{user_id}.json"
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2, default=str)
            
            # Update index
            users_index[user_id] = {
                "username": username,
                "email": email,
                "file_path": user_file,
                "created_at": user_data["created_at"]
            }
            self.save_index(self.users_index, users_index)
            
            # Log activity
            self.log_activity("user_created", {
                "user_id": user_id,
                "username": username,
                "email": email
            })
            
            return True, f"User created: {user_id}"
            
        except Exception as e:
            self.log_activity("user_creation_error", {"error": str(e)})
            return False, f"Error creating user: {str(e)}"

    def authenticate_user(self, identifier, password):
        """Authenticate user by email or username"""
        try:
            users_index = self.load_index(self.users_index)
            
            # Find user by email or username
            target_user_id = None
            for user_id, user_info in users_index.items():
                if user_info['email'] == identifier or user_info['username'] == identifier:
                    target_user_id = user_id
                    break
            
            if not target_user_id:
                self.log_activity("login_failed", {"identifier": identifier, "reason": "user_not_found"})
                return None
            
            # Load user data
            user_file = f"{self.users_dir}/{target_user_id}.json"
            with open(user_file, 'r') as f:
                user_data = json.load(f)
            
            # Verify password
            if bcrypt.checkpw(password.encode(), user_data["password_hash"].encode()):
                self.log_activity("login_success", {
                    "user_id": target_user_id,
                    "username": user_data["username"]
                })
                return user_data
            else:
                self.log_activity("login_failed", {"identifier": identifier, "reason": "wrong_password"})
                return None
                
        except Exception as e:
            self.log_activity("authentication_error", {"error": str(e)})
            return None

    def save_chat(self, user_id, message, response):
        """Save chat conversation"""
        try:
            timestamp = datetime.now()
            chat_id = f"chat_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
            
            chat_data = {
                "chat_id": chat_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "timestamp": timestamp.isoformat()
            }
            
            # Save to individual chat file
            chat_file = f"{self.chats_dir}/{chat_id}.json"
            with open(chat_file, 'w') as f:
                json.dump(chat_data, f, indent=2, default=str)
            
            # Log activity
            self.log_activity("chat_saved", {
                "user_id": user_id,
                "chat_id": chat_id,
                "message_length": len(message),
                "response_length": len(response)
            })
            
        except Exception as e:
            self.log_activity("chat_save_error", {"error": str(e)})

    def get_user_chats(self, user_id, limit=50):
        """Get user's chat history"""
        try:
            user_chats = []
            
            # Scan all chat files for this user
            for filename in os.listdir(self.chats_dir):
                if filename.startswith(f"chat_{user_id}_") and filename.endswith('.json'):
                    chat_file = f"{self.chats_dir}/{filename}"
                    with open(chat_file, 'r') as f:
                        chat_data = json.load(f)
                        chat_data['timestamp'] = datetime.fromisoformat(chat_data['timestamp'])
                        user_chats.append(chat_data)
            
            # Sort by timestamp (most recent first) and limit
            user_chats.sort(key=lambda x: x['timestamp'], reverse=True)
            return user_chats[:limit]
            
        except Exception as e:
            self.log_activity("get_chats_error", {"error": str(e)})
            return []

    def create_trip(self, user_id, destination, start_date, end_date, budget, preferences, ai_suggestions):
        """Create a new trip"""
        try:
            timestamp = datetime.now()
            trip_id = f"trip_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            trip_data = {
                "id": trip_id,
                "user_id": user_id,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "preferences": preferences,
                "ai_suggestions": ai_suggestions,
                "status": "planned",
                "created_at": timestamp.isoformat()
            }
            
            # Save to individual trip file
            trip_file = f"{self.trips_dir}/{trip_id}.json"
            with open(trip_file, 'w') as f:
                json.dump(trip_data, f, indent=2, default=str)
            
            # Log activity
            self.log_activity("trip_created", {
                "user_id": user_id,
                "trip_id": trip_id,
                "destination": destination
            })
            
            return True, f"Trip created: {trip_id}"
            
        except Exception as e:
            self.log_activity("trip_creation_error", {"error": str(e)})
            return False, f"Error creating trip: {str(e)}"

    def get_user_trips(self, user_id):
        """Get user's trips"""
        try:
            user_trips = []
            
            # Scan all trip files for this user
            for filename in os.listdir(self.trips_dir):
                if filename.startswith(f"trip_{user_id}_") and filename.endswith('.json'):
                    trip_file = f"{self.trips_dir}/{filename}"
                    with open(trip_file, 'r') as f:
                        trip_data = json.load(f)
                        user_trips.append(trip_data)
            
            # Sort by creation date (most recent first)
            user_trips.sort(key=lambda x: x['created_at'], reverse=True)
            return user_trips
            
        except Exception as e:
            self.log_activity("get_trips_error", {"error": str(e)})
            return []

    def get_stats(self):
        """Get application statistics"""
        try:
            users_count = len([f for f in os.listdir(self.users_dir) if f.endswith('.json')])
            chats_count = len([f for f in os.listdir(self.chats_dir) if f.endswith('.json')])
            trips_count = len([f for f in os.listdir(self.trips_dir) if f.endswith('.json')])
            
            return {
                "total_users": users_count,
                "total_chats": chats_count,
                "total_trips": trips_count,
                "data_directory": self.base_dir
            }
        except Exception as e:
            return {"error": str(e)}

# Global instance
db = DatabaseManager()
