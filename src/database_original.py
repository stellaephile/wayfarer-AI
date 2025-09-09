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
    
    def init_database(self):
        """Initialize the database with users and trips tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with enhanced security and Google OAuth support
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
                login_method TEXT DEFAULT 'email'
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
                preferences TEXT,
                ai_suggestions TEXT,
                status TEXT DEFAULT 'planned',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                preference_type TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, preference_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt for better security"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def create_user(self, username, email, password):
        """Create a new user with enhanced validation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if username or email already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return False, "Username or email already exists"
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, login_method)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, 'email'))
            conn.commit()
            return True, "User created successfully"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
        finally:
            conn.close()
    
    def create_google_user(self, username, email, name, google_id, picture="", verified_email=False):
        """Create a new user from Google OAuth"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if email already exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return False, "Email already exists"
            
            # Check if Google ID already exists
            cursor.execute('SELECT id FROM users WHERE google_id = ?', (google_id,))
            if cursor.fetchone():
                return False, "Google account already linked"
            
            cursor.execute('''
                INSERT INTO users (username, email, name, google_id, picture, verified_email, login_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, name, google_id, picture, verified_email, 'google'))
            conn.commit()
            return True, "Google user created successfully"
        except Exception as e:
            return False, f"Error creating Google user: {str(e)}"
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        """Authenticate user login with enhanced security"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, email, password_hash, is_active, login_method FROM users 
                WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            if user and user[5] == 'email' and self.verify_password(password, user[3]):
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'login_method': user[5]
                }
            return None
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, name, created_at, last_login, login_method FROM users 
            WHERE email = ? AND is_active = 1
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'name': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'login_method': user[6]
            }
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, name, created_at, last_login, login_method FROM users 
            WHERE id = ? AND is_active = 1
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'name': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'login_method': user[6]
            }
        return None
    
    def save_trip(self, user_id, destination, start_date=None, end_date=None, budget=None, preferences=None, ai_suggestions=None):
        """Save a trip plan with enhanced data handling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Convert ai_suggestions to JSON string if it's a dict
            if isinstance(ai_suggestions, dict):
                ai_suggestions = json.dumps(ai_suggestions)
            
            cursor.execute('''
                INSERT INTO trips (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions))
            
            conn.commit()
            trip_id = cursor.lastrowid
            return trip_id
        except Exception as e:
            st.error(f"Error saving trip: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_user_trips(self, user_id):
        """Get all trips for a user with enhanced data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, destination, start_date, end_date, budget, preferences, ai_suggestions, 
                   status, created_at, updated_at
            FROM trips WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        
        trips = cursor.fetchall()
        conn.close()
        
        return trips
    
    def get_trip_by_id(self, trip_id, user_id):
        """Get a specific trip by ID for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, destination, start_date, end_date, budget, preferences, ai_suggestions, 
                   status, created_at, updated_at
            FROM trips WHERE id = ? AND user_id = ?
        ''', (trip_id, user_id))
        
        trip = cursor.fetchone()
        conn.close()
        
        return trip
    
    def update_trip_status(self, trip_id, user_id, status):
        """Update trip status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trips SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ? AND user_id = ?
        ''', (status, trip_id, user_id))
        
        conn.commit()
        conn.close()
    
    def save_user_preference(self, user_id, preference_type, preference_value):
        """Save user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_id, preference_type, preference_value)
            VALUES (?, ?, ?)
        ''', (user_id, preference_type, preference_value))
        
        conn.commit()
        conn.close()
    
    def get_user_preferences(self, user_id):
        """Get user preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT preference_type, preference_value FROM user_preferences WHERE user_id = ?
        ''', (user_id,))
        
        preferences = dict(cursor.fetchall())
        conn.close()
        
        return preferences

# Initialize database
db = DatabaseManager()
