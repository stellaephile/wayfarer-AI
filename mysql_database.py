import mysql.connector
from mysql.connector import Error
import bcrypt
import streamlit as st
from datetime import datetime
import os
import json
from contextlib import contextmanager

class MySQLDatabaseManager:
    def __init__(self):
        self.host = os.getenv('MYSQL_HOST', '35.225.222.139')
        self.port = int(os.getenv('MYSQL_PORT', '3306'))
        self.database = os.getenv('MYSQL_DATABASE', 'trip_planner')
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True
            )
            yield conn
        except Error as e:
            st.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()
    
    def init_database(self):
        """Initialize the database with users and trips tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table with enhanced security, Google OAuth support, and user profile fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash TEXT,
                        name VARCHAR(255),
                        google_id VARCHAR(255) UNIQUE,
                        picture TEXT,
                        verified_email BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        login_method VARCHAR(50) DEFAULT 'email',
                        personal_number VARCHAR(20),
                        address TEXT,
                        pincode VARCHAR(10),
                        state VARCHAR(100),
                        alternate_number VARCHAR(20)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Trips table with JSON support for better data storage
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trips (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        destination VARCHAR(255) NOT NULL,
                        start_date DATE,
                        end_date DATE,
                        budget DECIMAL(10,2),
                        currency VARCHAR(10),
                        currency_symbol VARCHAR(5) DEFAULT '$',
                        preferences JSON,
                        ai_suggestions JSON,
                        status VARCHAR(50) DEFAULT 'planned',
                        booking_status VARCHAR(50) DEFAULT 'not_booked',
                        booking_id VARCHAR(255),
                        booking_confirmation TEXT,
                        credits_used INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Credit transactions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        trip_id INT,
                        transaction_type VARCHAR(100) NOT NULL,
                        credits_amount INT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                        FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Chat history table for trip modifications
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        trip_id INT NOT NULL,
                        user_id INT NOT NULL,
                        message_type VARCHAR(50) NOT NULL,
                        message_content TEXT NOT NULL,
                        ai_response TEXT,
                        credits_used INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                # Trip modifications table to track changes
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trip_modifications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        trip_id INT NOT NULL,
                        user_id INT NOT NULL,
                        modification_type VARCHAR(100) NOT NULL,
                        original_data JSON,
                        modified_data JSON,
                        modification_reason TEXT,
                        credits_used INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                ''')
                
                conn.commit()
                
        except Error as e:
            st.error(f"Error initializing database: {str(e)}")
            raise
    
    def create_user(self, username, email, password, name=None):
        """Create a new user with hashed password"""
        try:
            # Hash the password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, name, login_method)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (username, email, password_hash, name, 'email'))
                
                user_id = cursor.lastrowid
                
                # Initialize credits for new user
                self.initialize_user_credits(user_id)
                
                return True, f"User created successfully with ID: {user_id}"
                
        except Error as e:
            if e.errno == 1062:  # Duplicate entry
                if "username" in str(e):
                    return False, "Username already exists"
                elif "email" in str(e):
                    return False, "Email already exists"
                else:
                    return False, f"Database error: {str(e)}"
            else:
                return False, f"Error creating user: {str(e)}"
    
    def create_google_user(self, username, email, name, google_id, picture="", verified_email=False):
        """Create a new user from Google OAuth"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users (username, email, name, google_id, picture, verified_email, login_method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (username, email, name, google_id, picture, verified_email, 'google'))
                
                user_id = cursor.lastrowid
                
                # Initialize credits for new user
                self.initialize_user_credits(user_id)
                
                return True, f"Google user created successfully with ID: {user_id}"
                
        except Error as e:
            if e.errno == 1062:  # Duplicate entry
                if "username" in str(e):
                    return False, "Username already exists"
                elif "email" in str(e):
                    return False, "Email already exists"
                elif "google_id" in str(e):
                    return False, "Google ID already exists"
                else:
                    return False, f"Database error: {str(e)}"
            else:
                return False, f"Error creating Google user: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """Authenticate user with username/email and password"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if input is email or username
                if '@' in username_or_email:
                    cursor.execute('''
                        SELECT id, username, email, password_hash, name, is_active, login_method
                        FROM users WHERE email = %s AND is_active = 1
                    ''', (username_or_email,))
                else:
                    cursor.execute('''
                        SELECT id, username, email, password_hash, name, is_active, login_method
                        FROM users WHERE username = %s AND is_active = 1
                    ''', (username_or_email,))
                
                user = cursor.fetchone()
                
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
                    
        except Error as e:
            st.error(f"Authentication error: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, email, name, google_id, picture, verified_email, 
                           created_at, last_login, is_active, login_method, personal_number,
                           address, pincode, state, alternate_number
                    FROM users WHERE id = %s AND is_active = 1
                ''', (user_id,))
                
                user = cursor.fetchone()
                
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
                
        except Error as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, email, name, google_id, picture, verified_email, 
                           created_at, last_login, is_active, login_method, personal_number,
                           address, pincode, state, alternate_number
                    FROM users WHERE email = %s AND is_active = 1
                ''', (email,))
                
                user = cursor.fetchone()
                
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
                
        except Error as e:
            st.error(f"Error getting user: {str(e)}")
            return None
    
    def update_user_profile(self, user_id, **kwargs):
        """Update user profile information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                allowed_fields = ['name', 'personal_number', 'address', 'pincode', 'state', 'alternate_number']
                update_fields = []
                values = []
                
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                
                if not update_fields:
                    return False, "No valid fields to update"
                
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                
                cursor.execute(query, values)
                
                return True, "Profile updated successfully"
                
        except Error as e:
            return False, f"Error updating profile: {str(e)}"
    
    def update_last_login(self, user_id):
        """Update last login timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
                ''', (user_id,))
                
        except Error as e:
            st.error(f"Error updating last login: {str(e)}")
    
    def create_trip(self, user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency='USD', currency_symbol='$', current_city=None, itinerary_preference=None):
        """Create a new trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert preferences and ai_suggestions to JSON strings
                preferences_json = json.dumps(preferences) if preferences else None
                ai_suggestions_json = json.dumps(ai_suggestions) if ai_suggestions else None
                
                cursor.execute('''
                    INSERT INTO trips (user_id, destination, current_city, start_date, end_date, budget, preferences, itinerary_preference, ai_suggestions, currency, currency_symbol)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, destination, current_city, start_date, end_date, budget, preferences_json, itinerary_preference, ai_suggestions_json, currency, currency_symbol))
                
                trip_id = cursor.lastrowid
                
                return True, f"Trip created successfully with ID: {trip_id}"
                
        except Error as e:
            return False, f"Error creating trip: {str(e)}"
    
    def get_user_trips(self, user_id):
        """Get all trips for a user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, destination, start_date, end_date, budget, preferences, 
                           ai_suggestions, status, created_at, updated_at, currency, currency_symbol,
                           booking_status, booking_id, booking_confirmation
                    FROM trips WHERE user_id = %s ORDER BY created_at DESC
                ''', (user_id,))
                
                trips = cursor.fetchall()
                
                return [
                    {
                        'id': trip[0],
                        'destination': trip[1],
                        'start_date': trip[2],
                        'end_date': trip[3],
                        'budget': float(trip[4]) if trip[4] else 0,
                        'preferences': json.loads(trip[5]) if trip[5] else {},
                        'ai_suggestions': json.loads(trip[6]) if trip[6] else {},
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
                
        except Error as e:
            st.error(f"Error getting trips: {str(e)}")
            return []
    
    def get_trip_by_id(self, trip_id, user_id):
        """Get a specific trip by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, destination, start_date, end_date, budget, preferences, 
                           ai_suggestions, status, created_at, updated_at, currency, currency_symbol,
                           booking_status, booking_id, booking_confirmation
                    FROM trips WHERE id = %s AND user_id = %s
                ''', (trip_id, user_id))
                
                trip = cursor.fetchone()
                
                if trip:
                    return {
                        'id': trip[0],
                        'destination': trip[1],
                        'start_date': trip[2],
                        'end_date': trip[3],
                        'budget': float(trip[4]) if trip[4] else 0,
                        'preferences': json.loads(trip[5]) if trip[5] else {},
                        'ai_suggestions': json.loads(trip[6]) if trip[6] else {},
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
                
        except Error as e:
            st.error(f"Error getting trip: {str(e)}")
            return None
    
    def update_trip(self, trip_id, user_id, **kwargs):
        """Update a trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                allowed_fields = ['destination', 'start_date', 'end_date', 'budget', 'preferences', 'ai_suggestions', 'status', 'booking_status', 'booking_id', 'booking_confirmation']
                update_fields = []
                values = []
                
                for field, value in kwargs.items():
                    if field in allowed_fields:
                        if field in ['preferences', 'ai_suggestions']:
                            # Convert to JSON string
                            value = json.dumps(value) if value else None
                        update_fields.append(f"{field} = %s")
                        values.append(value)
                
                if not update_fields:
                    return False, "No valid fields to update"
                
                values.extend([trip_id, user_id])
                
                query = f"UPDATE trips SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
                
                cursor.execute(query, values)
                
                return True, "Trip updated successfully"
                
        except Error as e:
            return False, f"Error updating trip: {str(e)}"
    
    def delete_trip(self, trip_id, user_id):
        """Delete a trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM trips WHERE id = %s AND user_id = %s', (trip_id, user_id))
                
                return True, "Trip deleted successfully"
                
        except Error as e:
            return False, f"Error deleting trip: {str(e)}"
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get trip count
                cursor.execute('SELECT COUNT(*) FROM trips WHERE user_id = %s', (user_id,))
                trip_count = int(cursor.fetchone()[0])
                
                # Get total budget
                cursor.execute('SELECT SUM(budget) FROM trips WHERE user_id = %s', (user_id,))
                budget_result = cursor.fetchone()[0]
                total_budget = float(budget_result) if budget_result is not None else 0
                
                # Get most popular destination
                cursor.execute('''
                    SELECT destination, COUNT(*) as count 
                    FROM trips WHERE user_id = %s 
                    GROUP BY destination 
                    ORDER BY count DESC 
                    LIMIT 1
                ''', (user_id,))
                
                popular_destination = cursor.fetchone()
                popular_dest = popular_destination[0] if popular_destination else "None"
                
                return {
                    'trip_count': trip_count,
                    'total_budget': float(total_budget) if total_budget else 0,
                    'popular_destination': popular_dest
                }
                
        except Error as e:
            st.error(f"Error getting user stats: {str(e)}")
            return {
                'trip_count': 0,
                'total_budget': 0,
                'popular_destination': "None"
            }
    
    def initialize_user_credits(self, user_id):
        """Initialize credits for a new user"""
        try:
            # Add a welcome credit transaction
            self.add_credit_transaction(
                user_id=user_id,
                trip_id=None,
                transaction_type='welcome_bonus',
                credits_amount=1000,
                description='Welcome bonus - 1000 credits to get started!'
            )
        except Exception as e:
            # Don't fail user creation if credit initialization fails
            print(f"Warning: Could not initialize credits for user {user_id}: {str(e)}")

    def get_user_credits(self, user_id):
        """Get user's credit information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get user's total credits and credits used
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(credits_used), 0) as total_used,
                        COUNT(*) as total_trips
                    FROM trips 
                    WHERE user_id = %s
                ''', (user_id,))
                
                result = cursor.fetchone()
                total_used = float(result[0]) if result and result[0] is not None else 0
                total_trips = int(result[1]) if result and result[1] is not None else 0
                
                # Get total credits from credit transactions
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(credits_amount), 0) as total_credits
                    FROM credit_transactions 
                    WHERE user_id = %s AND transaction_type IN ('welcome_bonus', 'purchase', 'refund')
                ''', (user_id,))
                
                credit_result = cursor.fetchone()
                total_credits = float(credit_result[0]) if credit_result and credit_result[0] is not None and credit_result[0] > 0 else 1000
                
                return {
                    'total_credits': int(total_credits),
                    'credits_used': int(total_used),
                    'credits_remaining': int(total_credits - total_used),
                    'total_trips': total_trips
                }
                
        except Error as e:
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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO credit_transactions 
                    (user_id, trip_id, transaction_type, credits_amount, description)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, trip_id, transaction_type, credits_amount, description))
                
                return True
                
        except Error as e:
            st.error(f"Error adding credit transaction: {str(e)}")
            return False
    
    def get_credit_transactions(self, user_id, limit=10):
        """Get user's credit transaction history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ct.*, t.destination
                    FROM credit_transactions ct
                    LEFT JOIN trips t ON ct.trip_id = t.id
                    WHERE ct.user_id = %s
                    ORDER BY ct.created_at DESC
                    LIMIT %s
                ''', (user_id, limit))
                
                transactions = cursor.fetchall()
                
                return [
                    {
                        'id': int(t[0]),
                        'user_id': int(t[1]),
                        'trip_id': int(t[2]) if t[2] is not None else None,
                        'transaction_type': str(t[3]),
                        'credits_amount': int(t[4]),
                        'description': str(t[5]) if t[5] is not None else '',
                        'created_at': str(t[6]),
                        'destination': str(t[7]) if t[7] is not None else ''
                    }
                    for t in transactions
                ]
                
        except Error as e:
            st.error(f"Error getting credit transactions: {str(e)}")
            return []
    
    def update_trip_credits(self, trip_id, credits_used):
        """Update credits used for a specific trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE trips 
                    SET credits_used = %s
                    WHERE id = %s
                ''', (credits_used, trip_id))
                
                return True
                
        except Error as e:
            st.error(f"Error updating trip credits: {str(e)}")
            return False
    
    def save_chat_interaction(self, trip_id, user_id, message_type, message_content, ai_response=None, credits_used=0):
        """Save a chat interaction to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO chat_history 
                    (trip_id, user_id, message_type, message_content, ai_response, credits_used)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (trip_id, user_id, message_type, message_content, ai_response, credits_used))
                
                return True
                
        except Error as e:
            st.error(f"Error saving chat interaction: {str(e)}")
            return False
    
    def get_chat_history(self, trip_id, user_id):
        """Get chat history for a specific trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT message_type, message_content, ai_response, created_at, credits_used
                    FROM chat_history 
                    WHERE trip_id = %s AND user_id = %s
                    ORDER BY created_at ASC
                ''', (trip_id, user_id))
                
                history = cursor.fetchall()
                
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
                
        except Error as e:
            st.error(f"Error getting chat history: {str(e)}")
            return []
    
    def save_trip_modification(self, trip_id, user_id, modification_type, original_data, modified_data, modification_reason, credits_used=0):
        """Save a trip modification to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trip_modifications 
                    (trip_id, user_id, modification_type, original_data, modified_data, modification_reason, credits_used)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (trip_id, user_id, modification_type, json.dumps(original_data), json.dumps(modified_data), modification_reason, credits_used))
                
                return True
                
        except Error as e:
            st.error(f"Error saving trip modification: {str(e)}")
            return False
    
    def get_trip_modifications(self, trip_id, user_id):
        """Get modification history for a specific trip"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT modification_type, original_data, modified_data, modification_reason, created_at, credits_used
                    FROM trip_modifications 
                    WHERE trip_id = %s AND user_id = %s
                    ORDER BY created_at ASC
                ''', (trip_id, user_id))
                
                modifications = cursor.fetchall()
                
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
                
        except Error as e:
            st.error(f"Error getting trip modifications: {str(e)}")
            return []

# Create global database instance
db = MySQLDatabaseManager()
