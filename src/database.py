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
                preferences TEXT,
                ai_suggestions TEXT,
                status TEXT DEFAULT 'planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
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
    
    def create_trip(self, user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency='USD', currency_symbol='$'):
        """Create a new trip"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trips (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency, currency_symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency, currency_symbol))
            
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
                       ai_suggestions, status, created_at, updated_at, currency, currency_symbol
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
                    'status': trip[7],
                    'created_at': trip[8],
                    'updated_at': trip[9],
                    'currency': trip[10],
                    'currency_symbol': trip[11]
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
                       ai_suggestions, status, created_at, updated_at, currency, currency_symbol
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
                    'status': trip[7],
                    'created_at': trip[8],
                    'updated_at': trip[9],
                    'currency': trip[10],
                    'currency_symbol': trip[11]
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
            allowed_fields = ['destination', 'start_date', 'end_date', 'budget', 'preferences', 'ai_suggestions', 'status']
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields:
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

# Create global database instance
db = DatabaseManager()
