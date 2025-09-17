import sqlite3
import bcrypt
import streamlit as st
from datetime import datetime
import os
import json

class DatabaseManager:
    def __init__(self, db_path="trip_planner.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with users and trips tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Users table with enhanced security, Google OAuth support, and user profile fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
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
            )
        ''')
        
        # Trips table with JSON support for better data storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                destination TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                budget REAL,
                currency TEXT,
                currency_symbol TEXT DEFAULT '$',
                preferences TEXT,
                ai_suggestions TEXT,
                weather_data TEXT,
                source TEXT DEFAULT 'user_input',
                status TEXT DEFAULT 'planned',
                booking_status TEXT DEFAULT 'not_booked',
                booking_id TEXT,
                booking_confirmation TEXT,
                credits_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Credit transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trip_id INTEGER,
                transaction_type TEXT NOT NULL,
                credits_amount INTEGER NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        ''')
        
        # Chat history table for trip modifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message_type TEXT NOT NULL,
                message_content TEXT NOT NULL,
                ai_response TEXT,
                credits_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trip_id) REFERENCES trips (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Trip modifications table to track changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trip_modifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                modification_type TEXT NOT NULL,
                original_data TEXT,
                modified_data TEXT,
                modification_reason TEXT,
                credits_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trip_id) REFERENCES trips (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        
        # Check and add missing booking columns if they don't exist
        self._ensure_booking_columns(conn)
        
        conn.close()
    
    def _ensure_booking_columns(self, conn):
        """Ensure booking-related columns exist in the trips table"""
        try:
            cursor = conn.cursor()
            
            # Check existing columns
            cursor.execute("PRAGMA table_info(trips)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns
            if 'booking_status' not in columns:
                cursor.execute("ALTER TABLE trips ADD COLUMN booking_status TEXT DEFAULT 'not_booked'")
            
            if 'booking_id' not in columns:
                cursor.execute("ALTER TABLE trips ADD COLUMN booking_id TEXT")
            
            if 'booking_confirmation' not in columns:
                cursor.execute("ALTER TABLE trips ADD COLUMN booking_confirmation TEXT")
            # Add weather_data column
            if "weather_data" not in columns:
                cursor.execute("ALTER TABLE trips ADD COLUMN weather_data TEXT")

    # Add source column
            if "source" not in columns:
                cursor.execute("ALTER TABLE trips ADD COLUMN source TEXT DEFAULT 'user_input'")    
            
            conn.commit()
            
        except Exception as e:
            # If there's an error, it might be because the table doesn't exist yet
            # This is handled by the CREATE TABLE IF NOT EXISTS above
            pass

    def _ensure_new_feature_columns(self, conn):
      """Ensure new feature columns exist in the trips table"""

      try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(trips)")

        columns = [column[1] for column in cursor.fetchall()]

# Add missing columns for new features

        if 'weather_data' not in columns:
          cursor.execute("ALTER TABLE trips ADD COLUMN weather_data TEXT")

        if 'source' not in columns:

          cursor.execute("ALTER TABLE trips ADD COLUMN source TEXT DEFAULT 'user_input'")

        conn.commit()

      except Exception as e:
        print(f"Warning: Could not add new feature columns: {e}")

        pass

    def create_user(self, username, email, password, name=None):
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, name, login_method)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, name, 'email'))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return True, f"User created successfully with ID: {user_id}"
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists"
            elif "email" in str(e):
                return False, "Email already exists"
            else:
                return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def create_google_user(self, username, email, name, google_id, picture="", verified_email=False):
        """Create a new user from Google OAuth"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, name, google_id, picture, verified_email, login_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, name, google_id, picture, verified_email, 'google'))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return True, f"Google user created successfully with ID: {user_id}"
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists"
            elif "email" in str(e):
                return False, "Email already exists"
            elif "google_id" in str(e):
                return False, "Google ID already exists"
            else:
                return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error creating Google user: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if input is email or username
            if '@' in username_or_email:
                cursor.execute('''
                    SELECT id, username, email, password_hash, name, is_active, login_method
                    FROM users WHERE email = ? AND is_active = 1
                ''', (username_or_email,))
            else:
                cursor.execute('''
                    SELECT id, username, email, password_hash, name, is_active, login_method
                    FROM users WHERE username = ? AND is_active = 1
                ''', (username_or_email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                # Update last login
                self.update_last_login(user[0])
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'name': user[4],
                    'is_active': user[5],
                    'login_method': user[6]
                }
            else:
                return None
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, name, google_id, picture, verified_email, 
                       created_at, last_login, is_active, login_method, personal_number,
                       address, pincode, state, alternate_number
                FROM users WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'name': user[3],
                    'google_id': user[4],
                    'picture': user[5],
                    'verified_email': user[6],
                    'created_at': user[7],
                    'last_login': user[8],
                    'is_active': user[9],
                    'login_method': user[10],
                    'personal_number': user[11],
                    'address': user[12],
                    'pincode': user[13],
                    'state': user[14],
                    'alternate_number': user[15]
                }
            return None
            
        except Exception as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, name, google_id, picture, verified_email, 
                       created_at, last_login, is_active, login_method, personal_number,
                       address, pincode, state, alternate_number
                FROM users WHERE email = ? AND is_active = 1
            ''', (email,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'name': user[3],
                    'google_id': user[4],
                    'picture': user[5],
                    'verified_email': user[6],
                    'created_at': user[7],
                    'last_login': user[8],
                    'is_active': user[9],
                    'login_method': user[10],
                    'personal_number': user[11],
                    'address': user[12],
                    'pincode': user[13],
                    'state': user[14],
                    'alternate_number': user[15]
                }
            return None
            
        except Exception as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user_profile(self, user_id, **kwargs):
        """Update user profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic update query
            allowed_fields = ['name', 'personal_number', 'address', 'pincode', 'state', 'alternate_number']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False, "No valid fields to update"
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return True, "Profile updated successfully"
            
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"
    
    def update_last_login(self, user_id):
        """Update last login timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Error updating last login: {str(e)}")
    
    def create_trip(self, user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency='USD', currency_symbol='$',weather_data=None, source='user_input'):
        """Create a new trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Convert weather_data to JSON string if it's a dict

            weather_json = json.dumps(weather_data) if weather_data else None
       
            
            cursor.execute('''
                INSERT INTO trips (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions,weather_data, source, currency, currency_symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, weather_json, source, currency, currency_symbol))
            
            conn.commit()
            trip_id = cursor.lastrowid
            conn.close()
            
            return True, f"Trip created successfully with ID: {trip_id}"
            
        except Exception as e:
            return False, f"Error creating trip: {str(e)}"
    
    def get_user_trips(self, user_id):
        """Get all trips for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, destination, start_date, end_date, budget, preferences, 
                       ai_suggestions, weather_data, source, status, created_at, updated_at, currency, currency_symbol,
                       booking_status, booking_id, booking_confirmation
                FROM trips WHERE user_id = ? ORDER BY created_at DESC
            ''', (user_id,))
            
            trips = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': trip[0],
                    'destination': trip[1],
                    'start_date': trip[2],
                    'end_date': trip[3],
                    'budget': trip[4],
                    'preferences': trip[5],
                    'ai_suggestions': trip[6],
                    'weather_data': json.loads(trip[7]) if trip[7] else None,
                    'source': trip[8] or 'user_input',
                    'status': trip[7],
                    'created_at': trip[8],
                    'updated_at': trip[9],
                    'currency': trip[10],
                    'currency_symbol': trip[11],
                    'booking_status': trip[12],
                    'booking_id': trip[13],
                    'booking_confirmation': trip[14]
                }
                for trip in trips
            ]
            
        except Exception as e:
            st.error(f"Error getting trips: {str(e)}")
            return []
    
    def get_trip_by_id(self, trip_id, user_id):
        """Get a specific trip by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, destination, start_date, end_date, budget, preferences, 
                       ai_suggestions,weather_data, source, status, created_at, updated_at, currency, currency_symbol,
                       booking_status, booking_id, booking_confirmation
                FROM trips WHERE id = ? AND user_id = ?
            ''', (trip_id, user_id))
            
            trip = cursor.fetchone()
            conn.close()
            
            if trip:
                return {
                    'id': trip[0],
                    'destination': trip[1],
                    'start_date': trip[2],
                    'end_date': trip[3],
                    'budget': trip[4],
                    'preferences': trip[5],
                    'ai_suggestions': trip[6],
                    'weather_data': json.loads(trip[7]) if trip[7] else None,
                    'source': trip[8] or 'user_input',
                    'status': trip[7],
                    'created_at': trip[8],
                    'updated_at': trip[9],
                    'currency': trip[10],
                    'currency_symbol': trip[11],
                    'booking_status': trip[12],
                    'booking_id': trip[13],
                    'booking_confirmation': trip[14]
                }
            return None
            
        except Exception as e:
            st.error(f"Error getting trip: {str(e)}")
            return None
    
    def update_trip(self, trip_id, user_id, **kwargs):
        """Update a trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic update query
            allowed_fields = ['destination', 'start_date', 'end_date', 'budget', 'preferences', 'ai_suggestions', 'weather_data', 'source','status', 'booking_status', 'booking_id', 'booking_confirmation']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                  if field == 'weather_data' and isinstance(value, dict):
                    value = json.dumps(value)
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False, "No valid fields to update"
            
            # Add updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.extend([trip_id, user_id])
            
            query = f"UPDATE trips SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            return True, "Trip updated successfully"
            
        except Exception as e:
            return False, f"Error updating trip: {str(e)}"
    
    def delete_trip(self, trip_id, user_id):
        """Delete a trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM trips WHERE id = ? AND user_id = ?', (trip_id, user_id))
            
            conn.commit()
            conn.close()
            
            return True, "Trip deleted successfully"
            
        except Exception as e:
            return False, f"Error deleting trip: {str(e)}"
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get trip count
            cursor.execute('SELECT COUNT(*) FROM trips WHERE user_id = ?', (user_id,))
            trip_count = cursor.fetchone()[0]
            
            # Get total budget
            cursor.execute('SELECT SUM(budget) FROM trips WHERE user_id = ?', (user_id,))
            total_budget = cursor.fetchone()[0] or 0
            
            # Get most popular destination
            cursor.execute('''
                SELECT destination, COUNT(*) as count 
                FROM trips WHERE user_id = ? 
                GROUP BY destination 
                ORDER BY count DESC 
                LIMIT 1
            ''', (user_id,))
            
            popular_destination = cursor.fetchone()
            popular_dest = popular_destination[0] if popular_destination else "None"
            
            conn.close()
            
            return {
                'trip_count': trip_count,
                'total_budget': total_budget,
                'popular_destination': popular_dest
            }
            
        except Exception as e:
            st.error(f"Error getting user stats: {str(e)}")
            return {
                'trip_count': 0,
                'total_budget': 0,
                'popular_destination': "None"
            }
    
    def get_user_credits(self, user_id):
        """Get user's credit information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user's total credits and credits used
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(credits_used), 0) as total_used,
                    COUNT(*) as total_trips
                FROM trips 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            total_used = result[0] if result else 0
            total_trips = result[1] if result else 0
            
            # Default credits (can be made configurable)
            total_credits = 1000
            
            conn.close()
            
            return {
                'total_credits': total_credits,
                'credits_used': total_used,
                'credits_remaining': total_credits - total_used,
                'total_trips': total_trips
            }
            
        except Exception as e:
            st.error(f"Error getting user credits: {str(e)}")
            return {
                'total_credits': 1000,
                'credits_used': 0,
                'credits_remaining': 1000,
                'total_trips': 0
            }
    
    def add_credit_transaction(self, user_id, trip_id, transaction_type, credits_amount, description):
        """Add a credit transaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO credit_transactions 
                (user_id, trip_id, transaction_type, credits_amount, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, trip_id, transaction_type, credits_amount, description))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error adding credit transaction: {str(e)}")
            return False
    
    def get_credit_transactions(self, user_id, limit=10):
        """Get user's credit transaction history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ct.*, t.destination
                FROM credit_transactions ct
                LEFT JOIN trips t ON ct.trip_id = t.id
                WHERE ct.user_id = ?
                ORDER BY ct.created_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            transactions = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': t[0],
                    'user_id': t[1],
                    'trip_id': t[2],
                    'transaction_type': t[3],
                    'credits_amount': t[4],
                    'description': t[5],
                    'created_at': t[6],
                    'destination': t[7]
                }
                for t in transactions
            ]
            
        except Exception as e:
            st.error(f"Error getting credit transactions: {str(e)}")
            return []
    
    def update_trip_credits(self, trip_id, credits_used):
        """Update credits used for a specific trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trips 
                SET credits_used = ?
                WHERE id = ?
            ''', (credits_used, trip_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error updating trip credits: {str(e)}")
            return False
    
    def save_chat_interaction(self, trip_id, user_id, message_type, message_content, ai_response=None, credits_used=0):
        """Save a chat interaction to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_history 
                (trip_id, user_id, message_type, message_content, ai_response, credits_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (trip_id, user_id, message_type, message_content, ai_response, credits_used))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error saving chat interaction: {str(e)}")
            return False
    
    def get_chat_history(self, trip_id, user_id):
        """Get chat history for a specific trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT message_type, message_content, ai_response, created_at, credits_used
                FROM chat_history 
                WHERE trip_id = ? AND user_id = ?
                ORDER BY created_at ASC
            ''', (trip_id, user_id))
            
            history = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'message_type': msg[0],
                    'message_content': msg[1],
                    'ai_response': msg[2],
                    'created_at': msg[3],
                    'credits_used': msg[4]
                }
                for msg in history
            ]
            
        except Exception as e:
            st.error(f"Error getting chat history: {str(e)}")
            return []
    
    def save_trip_modification(self, trip_id, user_id, modification_type, original_data, modified_data, modification_reason, credits_used=0):
        """Save a trip modification to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trip_modifications 
                (trip_id, user_id, modification_type, original_data, modified_data, modification_reason, credits_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (trip_id, user_id, modification_type, json.dumps(original_data), json.dumps(modified_data), modification_reason, credits_used))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error saving trip modification: {str(e)}")
            return False
    
    def get_trip_modifications(self, trip_id, user_id):
        """Get modification history for a specific trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT modification_type, original_data, modified_data, modification_reason, created_at, credits_used
                FROM trip_modifications 
                WHERE trip_id = ? AND user_id = ?
                ORDER BY created_at ASC
            ''', (trip_id, user_id))
            
            modifications = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'modification_type': mod[0],
                    'original_data': json.loads(mod[1]) if mod[1] else None,
                    'modified_data': json.loads(mod[2]) if mod[2] else None,
                    'modification_reason': mod[3],
                    'created_at': mod[4],
                    'credits_used': mod[5]
                }
                for mod in modifications
            ]
            
        except Exception as e:
            st.error(f"Error getting trip modifications: {str(e)}")
            return []

# Create global database instance
db = DatabaseManager()
