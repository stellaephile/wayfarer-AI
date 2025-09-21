from google.cloud.sql.connector import Connector
import sqlalchemy
from sqlalchemy.exc import IntegrityError
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

        def create_user(self, username, email, password_hash, name=None, login_method="email"):
            """
            Create a new user in the database.
            Prevents duplicate users by catching IntegrityError (duplicate email).
            """
            try:
                with self.get_connection() as conn:
                    conn.execute(sqlalchemy.text("""
                        INSERT INTO users (username, email, password_hash, name, login_method)
                        VALUES (:username, :email, :password_hash, :name, :login_method)
                    """), {
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                        "name": name,
                        "login_method": login_method
                    })
                    conn.commit()

                return True, "✅ User created successfully"

            except IntegrityError:
                # Duplicate email (or unique constraint violation)
                return False, "⚠️ A user with this email already exists. Please log in instead."

            except Exception as e:
                return False, f"❌ Error creating user: {str(e)}"

    # ---------------- Trips ---------------- #
    def create_trip(
        self,
        user_id,
        destination,
        start_date=None,
        end_date=None,
        budget=None,
        preferences=None,
        ai_suggestions=None,
        currency='USD',
        currency_symbol='$',
        current_city=None,
        itinerary_preference=None
    ):
        """Create a new trip in Cloud SQL"""
        try:
            preferences_json = json.dumps(preferences) if preferences else None
            ai_suggestions_json = json.dumps(ai_suggestions) if ai_suggestions else None

            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO trips
                    (user_id, destination, current_city, start_date, end_date, budget, preferences, itinerary_preference, ai_suggestions, currency, currency_symbol)
                    VALUES
                    (:user_id, :destination, :current_city, :start_date, :end_date, :budget, :preferences, :itinerary_preference, :ai_suggestions, :currency, :currency_symbol)
                """), {
                    "user_id": user_id,
                    "destination": destination,
                    "current_city": current_city,
                    "start_date": start_date,
                    "end_date": end_date,
                    "budget": budget,
                    "preferences": preferences_json,
                    "itinerary_preference": itinerary_preference,
                    "ai_suggestions": ai_suggestions_json,
                    "currency": currency,
                    "currency_symbol": currency_symbol
                })

            return True, "Trip created successfully"

        except Exception as e:
            st.error(f"Error creating trip: {str(e)}")
            return False, f"Error creating trip: {str(e)}"


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

    def get_user_credits(self, user_id):
        """Get user's credit information safely"""
        try:
            with self.get_connection() as conn:
                # Get total credits used in trips
                credits_used_result = conn.execute(
                    sqlalchemy.text("""
                        SELECT COALESCE(SUM(credits_used), 0) AS total_used, COUNT(*) AS total_trips
                        FROM trips
                        WHERE user_id = :uid
                    """),
                    {"uid": user_id}
                )
                row = credits_used_result.fetchone()
                total_used = int(row[0]) if row and row[0] is not None else 0
                total_trips = int(row[1]) if row and row[1] is not None else 0

                # Get total credits from credit transactions
                total_credits_result = conn.execute(
                    sqlalchemy.text("""
                        SELECT COALESCE(SUM(credits_amount), 0) AS total_credits
                        FROM credit_transactions
                        WHERE user_id = :uid
                        AND transaction_type IN ('welcome_bonus', 'purchase', 'refund')
                    """),
                    {"uid": user_id}
                )
                total_credits_row = total_credits_result.fetchone()
                total_credits = int(total_credits_row[0]) if total_credits_row and total_credits_row[0] is not None else 1000

                # Avoid division by zero
                avg_credits_per_trip = (total_used / total_trips) if total_trips > 0 else 0

                return {
                    'total_credits': total_credits,
                    'credits_used': total_used,
                    'credits_remaining': total_credits - total_used,
                    'total_trips': total_trips,
                    'avg_credits_per_trip': avg_credits_per_trip
                }

        except Exception as e:
            st.error(f"Error getting user credits: {str(e)}")
            return {
                'total_credits': 1000,
                'credits_used': 0,
                'credits_remaining': 1000,
                'total_trips': 0,
                'avg_credits_per_trip': 0
            }

        
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            with self.get_connection() as conn:
                # Get trip count
                trip_count_result = conn.execute(
                    sqlalchemy.text("SELECT COUNT(*) FROM trips WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                trip_count = trip_count_result.scalar() or 0

                # Get total budget
                total_budget_result = conn.execute(
                    sqlalchemy.text("SELECT SUM(budget) FROM trips WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                total_budget = float(total_budget_result.scalar() or 0)

                # Get most popular destination
                popular_dest_result = conn.execute(
                    sqlalchemy.text("""
                        SELECT destination, COUNT(*) as count
                        FROM trips
                        WHERE user_id = :uid
                        GROUP BY destination
                        ORDER BY count DESC
                        LIMIT 1
                    """),
                    {"uid": user_id}
                )
                popular_destination_row = popular_dest_result.fetchone()
                popular_dest = popular_destination_row[0] if popular_destination_row else "None"

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
        
    def update_trip(self, trip_id, user_id, **kwargs):
        """Update a trip with dynamic fields and return updated trip dict"""
        allowed_fields = [
            "destination", "start_date", "end_date", "budget",
            "preferences", "ai_suggestions", "status",
            "booking_status", "booking_id", "booking_confirmation",
            "current_city", "itinerary_preference"
        ]
        update_fields = []
        params = {"trip_id": trip_id, "user_id": user_id}

        for key, value in kwargs.items():
            if key in allowed_fields:
                if key in ["preferences", "ai_suggestions"]:
                    value = json.dumps(value) if value else None
                update_fields.append(f"{key} = :{key}")
                params[key] = value

        if not update_fields:
            return False, "No valid fields to update"

        query = f"""
            UPDATE trips
            SET {', '.join(update_fields)}
            WHERE id = :trip_id AND user_id = :user_id
        """

        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text(query), params)

                # fetch updated row
                updated = conn.execute(
                    sqlalchemy.text("SELECT * FROM trips WHERE id = :trip_id AND user_id = :user_id"),
                    {"trip_id": trip_id, "user_id": user_id}
                ).mappings().first()

                if updated:
                    trip = dict(updated)
                    for field in ["preferences", "ai_suggestions"]:
                        if trip.get(field):
                            try:
                                trip[field] = json.loads(trip[field])
                            except json.JSONDecodeError:
                                pass
                    return True, trip
                return False, "Trip not found"
        except Exception as e:
            st.error(f"Error updating trip: {str(e)}")
            return False, f"Error updating trip: {str(e)}"


    def get_user_trips(self, user_id):
        """Get all trips for a user with JSON fields deserialized"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    sqlalchemy.text("SELECT * FROM trips WHERE user_id = :uid"),
                    {"uid": user_id}
                )
                trips = []
                for row in result.mappings().all():
                    trip = dict(row)
                    # Deserialize JSON fields if they exist
                    for field in ["preferences", "ai_suggestions"]:
                        if trip.get(field):
                            try:
                                trip[field] = json.loads(trip[field])
                            except json.JSONDecodeError:
                                pass
                    trips.append(trip)
            return trips
        except Exception as e:
            st.error(f"Error fetching trips: {str(e)}")
            return []



# ---------------- Global DB Instance ---------------- #
db = MySQLDatabaseManager()
