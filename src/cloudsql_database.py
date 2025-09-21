from google.cloud.sql.connector import Connector
import sqlalchemy
import bcrypt
import streamlit as st
from datetime import datetime
import os
import json
from contextlib import contextmanager

class MySQLDatabaseManager:
    def __init__(self):
        # DB settings from env vars (Cloud Run / Secret Manager)
        self.connection_name = os.getenv("CLOUDSQL_CONNECTION_NAME")  # e.g., project:region:instance
        self.database = os.getenv("MYSQL_DATABASE", "trip_planner")
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.connector = Connector()

        # SQLAlchemy engine using Cloud SQL Python Connector
        self.engine = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=self.getconn,
            pool_recycle=300,
            pool_pre_ping=True
        )

        self.init_database()

    def getconn(self):
        """Return a new Cloud SQL connection"""
        return self.connector.connect(
            self.connection_name,
            "pymysql",
            user=self.user,
            password=self.password,
            db=self.database
        )

    @contextmanager
    def get_connection(self):
        """Context manager for SQLAlchemy connection"""
        with self.engine.connect() as conn:
            yield conn

    def init_database(self):
        """Initialize tables"""
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text('''
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
                        login_method VARCHAR(50) DEFAULT 'email'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                '''))
                conn.execute(sqlalchemy.text('''
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
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                '''))
                conn.execute(sqlalchemy.text('''
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        trip_id INT,
                        transaction_type VARCHAR(100) NOT NULL,
                        credits_amount INT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                '''))
                conn.commit()
        except Exception as e:
            st.error(f"Error initializing database: {str(e)}")
            raise

    # ---------------- Authentication ---------------- #
    def authenticate_user(self, username_or_email: str, password: str):
        """Authenticate user by username/email + password"""
        try:
            if "@" in username_or_email:
                query = "SELECT * FROM users WHERE email=:input AND is_active=1"
            else:
                query = "SELECT * FROM users WHERE username=:input AND is_active=1"

            with self.get_connection() as conn:
                user = conn.execute(sqlalchemy.text(query), {"input": username_or_email}).mappings().first()
                if user and user['password_hash'] and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    self.update_last_login(user['id'])
                    return dict(user)
                return None
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return None

    def update_last_login(self, user_id):
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=:id"), {"id": user_id})
        except Exception as e:
            st.error(f"Error updating last login: {str(e)}")

    def create_user(self, username, email, password, name=None):
        """Create a new user"""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = """
                INSERT INTO users (username, email, password_hash, name, login_method)
                VALUES (:username, :email, :password_hash, :name, 'email')
            """
            with self.get_connection() as conn:
                result = conn.execute(sqlalchemy.text(query), {"username": username, "email": email, "password_hash": password_hash, "name": name})
                user_id = result.lastrowid
                self.initialize_user_credits(user_id)
                return True, f"User created successfully with ID: {user_id}"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"

    # ---------------- Trips ---------------- #
    def create_trip(self, user_id, destination, start_date=None, end_date=None, budget=0, preferences=None, ai_suggestions=None, currency='USD', currency_symbol='$'):
        try:
            preferences_json = json.dumps(preferences) if preferences else None
            ai_suggestions_json = json.dumps(ai_suggestions) if ai_suggestions else None
            query = """
                INSERT INTO trips (user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency, currency_symbol)
                VALUES (:user_id, :destination, :start_date, :end_date, :budget, :preferences, :ai_suggestions, :currency, :currency_symbol)
            """
            with self.get_connection() as conn:
                result = conn.execute(sqlalchemy.text(query), {
                    "user_id": user_id, "destination": destination, "start_date": start_date,
                    "end_date": end_date, "budget": budget, "preferences": preferences_json,
                    "ai_suggestions": ai_suggestions_json, "currency": currency, "currency_symbol": currency_symbol
                })
                return True, f"Trip created with ID: {result.lastrowid}"
        except Exception as e:
            return False, f"Error creating trip: {str(e)}"

    def get_user_trips(self, user_id):
        try:
            query = "SELECT * FROM trips WHERE user_id=:user_id ORDER BY created_at DESC"
            with self.get_connection() as conn:
                trips = conn.execute(sqlalchemy.text(query), {"user_id": user_id}).mappings().all()
                return [dict(trip) for trip in trips]
        except Exception as e:
            st.error(f"Error fetching trips: {str(e)}")
            return []

    # ---------------- Credits ---------------- #
    def initialize_user_credits(self, user_id):
        """Give new user initial credits"""
        self.add_credit_transaction(user_id, None, "welcome_bonus", 1000, "Welcome bonus 1000 credits")

    def add_credit_transaction(self, user_id, trip_id, transaction_type, credits_amount, description):
        try:
            query = """
                INSERT INTO credit_transactions (user_id, trip_id, transaction_type, credits_amount, description)
                VALUES (:user_id, :trip_id, :transaction_type, :credits_amount, :description)
            """
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text(query), {
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "transaction_type": transaction_type,
                    "credits_amount": credits_amount,
                    "description": description
                })
        except Exception as e:
            st.error(f"Error adding credit transaction: {str(e)}")

# ---------------- Global DB Instance ---------------- #
db = MySQLDatabaseManager()
