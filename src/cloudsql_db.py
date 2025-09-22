# cloudsql_database.py

import os
import json
import logging
import bcrypt
from contextlib import contextmanager
from datetime import datetime, date

import sqlalchemy
from sqlalchemy.exc import IntegrityError
from google.cloud.sql.connector import Connector
import streamlit as st

# ---------------- Logger ---------------- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# ---------------- Database Manager ---------------- #
class PostgresDatabaseManager:
    def __init__(self):
        # DB settings from env vars
        self.connection_name = os.getenv("CLOUDSQL_CONNECTION_NAME")  # project:region:instance
        self.database = os.getenv("POSTGRES_DB", "trip_planner")
        self.user = os.getenv("POSTGRES_USER", "trip_planner")
        self.password = os.getenv("POSTGRES_PASSWORD", "")

        self.connector = Connector()

        # SQLAlchemy engine using Cloud SQL Python Connector
        self.engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=self.getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800
        )

        # Test connection
        try:
            with self.engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            logger.info("✅ PostgreSQL connection established successfully.")
        except Exception as e:
            logger.error(f"❌ Error connecting to PostgreSQL: {e}")
            raise e

        # Initialize tables
        self.init_database()

    def getconn(self):
        """Return a new Cloud SQL connection"""
        return self.connector.connect(
            self.connection_name,
            "pg8000",
            user=self.user,
            password=self.password,
            db=self.database
        )

    @contextmanager
    def get_connection(self):
        """Context manager for SQLAlchemy connection"""
        with self.engine.connect() as conn:
            yield conn

    # ---------------- Table Initialization ---------------- #
    def init_database(self):
        """Initialize tables for users, trips, credit_transactions"""
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
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
                    )
                """))

                conn.execute(sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS trips (
                        id SERIAL PRIMARY KEY,
                        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
                        booking_confirmation JSON,
                        credits_used INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                conn.execute(sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id SERIAL PRIMARY KEY,
                        user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        trip_id INT REFERENCES trips(id) ON DELETE SET NULL,
                        transaction_type VARCHAR(100) NOT NULL,
                        credits_amount INT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                logger.info("✅ Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise e

    # ---------------- Password Utilities ---------------- #
    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    # ---------------- Users ---------------- #
    def create_user(self, username, email, password_hash, name=None, login_method="email"):
        """
        Create a new user in the database.
        Returns (True, message) on success, (False, message) on failure.
        """
        try:
            # Password is already hashed before calling this function
            if password_hash:
                st.info(f"Password Hashed: {password_hash}")

            query = sqlalchemy.text("""
                INSERT INTO users (username, email, password_hash, name, login_method)
                VALUES (:username, :email, :password_hash, :name, :login_method)
            """)

            with self.get_connection() as conn:
                conn.execute(query, {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "name": name,
                    "login_method": login_method
                })
                conn.commit()

                # Fetch the newly created user ID
                user_id_query = sqlalchemy.text("SELECT id FROM users WHERE email = :email")
                user_id = conn.execute(user_id_query, {"email": email}).scalar()

            return True, "✅ User created successfully"

        except IntegrityError:
            return False, "⚠️ A user with this email already exists. Please log in instead."

        except Exception as e:
            return False, f"❌ Error creating user: {str(e)}"


    def get_user_by_email(self, email: str):
        """
        Fetch a single user by email.
        Returns a dict or None if not found.
        """
        try:
            query = sqlalchemy.text("SELECT * FROM users WHERE email = :email")
            with self.get_connection() as conn:
                user_row = conn.execute(query, {"email": email}).mappings().first()
                if user_row:
                    return dict(user_row)
            return None
        except Exception as e:
            st.error(f"Error fetching user by email: {str(e)}")
            return None


    def authenticate_user(self, username_or_email: str, password: str):
        """
        Authenticate user by username/email + raw password.
        Returns user dict if successful, else None.
        """
        try:
            query = sqlalchemy.text(
                "SELECT * FROM users WHERE email = :input AND is_active=1"
            ) if "@" in username_or_email else sqlalchemy.text(
                "SELECT * FROM users WHERE username = :input AND is_active=1"
            )

            with self.get_connection() as conn:
                user_row = conn.execute(query, {"input": username_or_email}).mappings().first()
                if user_row:
                    user = dict(user_row)
                    # Verify password using bcrypt
                    if password and user.get('password_hash') and self.verify_password(password, user['password_hash']):
                        self.update_last_login(user['id'])
                        return user
            return None

        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return None


    def update_last_login(self, user_id):
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=:id"), {"id": user_id})
        except Exception as e:
            logger.error(f"Error updating last login: {e}")

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
        """
        Create a new trip in the database.
        Returns (True, trip_id) on success, (False, None) on failure.
        """
        try:
            preferences_json = json.dumps(self._make_json_serializable(preferences)) if preferences else None
            ai_suggestions_json = json.dumps(self._make_json_serializable(ai_suggestions)) if ai_suggestions else None

            query = sqlalchemy.text("""
                INSERT INTO trips
                (user_id, destination, current_city, start_date, end_date, budget, preferences, itinerary_preference, ai_suggestions, currency, currency_symbol)
                VALUES
                (:user_id, :destination, :current_city, :start_date, :end_date, :budget, :preferences, :itinerary_preference, :ai_suggestions, :currency, :currency_symbol)
                RETURNING id
            """)

            with self.get_connection() as conn:
                result = conn.execute(query, {
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
                conn.commit()
                trip_id = result.scalar()

            return True, trip_id

        except Exception as e:
            st.error(f"❌ Error creating trip: {str(e)}")
            return False, None


    def get_user_trips(self, user_id):
        try:
            with self.get_connection() as conn:
                result = conn.execute(sqlalchemy.text("SELECT * FROM trips WHERE user_id=:uid"), {"uid": user_id})
                trips = []
                for row in result.mappings().all():
                    trip = dict(row)
                    for field in ["preferences", "ai_suggestions", "booking_confirmation"]:
                        if trip.get(field):
                            try:
                                trip[field] = json.loads(trip[field])
                            except json.JSONDecodeError:
                                pass
                    trips.append(trip)
                return trips
        except Exception as e:
            logger.error(f"Error fetching trips: {e}")
            return []


        # ---------------- Credits ---------------- #
    def initialize_user_credits(self, user_id):
        """Initialize a user's credits with a welcome bonus"""
        self.add_credit_transaction(
            user_id=user_id,
            trip_id=None,
            transaction_type="welcome_bonus",
            credits_amount=1000,
            description="Welcome bonus 1000 credits"
        )

    def add_credit_transaction(self, user_id, trip_id, transaction_type, credits_amount, description):
        """Add a credit transaction for a user"""
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("""
                    INSERT INTO credit_transactions (user_id, trip_id, transaction_type, credits_amount, description)
                    VALUES (:user_id, :trip_id, :transaction_type, :credits_amount, :description)
                """), {
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "transaction_type": transaction_type,
                    "credits_amount": credits_amount,
                    "description": description
                })
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Error adding credit transaction: {e}")


    def get_user_credits(self, user_id):
        """
        Get user's credit information safely.
        Returns a dict with total_credits, credits_used, credits_remaining, total_trips, avg_credits_per_trip.
        """
        try:
            with self.get_connection() as conn:
                # Total credits used in trips
                used_result = conn.execute(
                    sqlalchemy.text("""
                        SELECT COALESCE(SUM(credits_used), 0) AS total_used, COUNT(*) AS total_trips
                        FROM trips
                        WHERE user_id = :uid
                    """),
                    {"uid": user_id}
                ).first()

                total_used = int(used_result[0]) if used_result and used_result[0] is not None else 0
                total_trips = int(used_result[1]) if used_result and used_result[1] is not None else 0

                # Total credits from credit_transactions
                credits_result = conn.execute(
                    sqlalchemy.text("""
                        SELECT COALESCE(SUM(credits_amount), 0) AS total_credits
                        FROM credit_transactions
                        WHERE user_id = :uid
                        AND transaction_type IN ('welcome_bonus', 'purchase', 'refund')
                    """),
                    {"uid": user_id}
                ).first()

                total_credits = int(credits_result[0]) if credits_result and credits_result[0] is not None else 1000

                avg_credits_per_trip = total_used / total_trips if total_trips else 0

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


    def update_trip_credits(self, trip_id, credits_used):
        """Update credits used for a specific trip"""
        try:
            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text("""
                    UPDATE trips
                    SET credits_used = :credits_used
                    WHERE id = :trip_id
                """), {"credits_used": credits_used, "trip_id": trip_id})
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error updating trip credits: {e}")
            return False

    # ---------------- User Stats ---------------- #
    def get_user_stats(self, user_id):
        """Get basic statistics for a user"""
        try:
            with self.get_connection() as conn:
                # Trip count
                trip_count = conn.execute(sqlalchemy.text("""
                    SELECT COUNT(*) FROM trips WHERE user_id = :uid
                """), {"uid": user_id}).scalar() or 0

                # Total budget
                total_budget = conn.execute(sqlalchemy.text("""
                    SELECT COALESCE(SUM(budget),0) FROM trips WHERE user_id = :uid
                """), {"uid": user_id}).scalar() or 0.0

                # Most popular destination
                popular_dest_row = conn.execute(sqlalchemy.text("""
                    SELECT destination, COUNT(*) AS cnt
                    FROM trips
                    WHERE user_id = :uid
                    GROUP BY destination
                    ORDER BY cnt DESC
                    LIMIT 1
                """), {"uid": user_id}).fetchone()
                popular_destination = popular_dest_row[0] if popular_dest_row else "None"

                return {
                    "trip_count": trip_count,
                    "total_budget": float(total_budget),
                    "popular_destination": popular_destination
                }
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return {"trip_count": 0, "total_budget": 0, "popular_destination": "None"}

    # ---------------- Refactored / Missing Functions ---------------- #

    # Get user by email (SQLAlchemy version)
    def get_user_by_email(self, email: str):
        """Fetch a user by email"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    sqlalchemy.text("SELECT * FROM users WHERE email = :email"),
                    {"email": email}
                ).mappings().first()
                return dict(result) if result else None
        except Exception as e:
            st.error(f"Error fetching user by email: {str(e)}")
            return None


    # Update trip record (SQLAlchemy + JSON-safe)
    def update_trip(self, trip_id, user_id, **kwargs):
        """
        Update trip record with flexible fields.
        Automatically makes JSON fields serializable.
        Returns True if successful, False otherwise.
        """
        try:
            if not kwargs:
                return False

            fields = []
            params = {}

            for key, value in kwargs.items():
                # Make JSON fields serializable if needed
                if key in ["preferences", "ai_suggestions", "booking_confirmation"] and value is not None:
                    value = json.dumps(self._make_json_serializable(value))
                fields.append(f"{key} = :{key}")
                params[key] = value

            params.update({"trip_id": trip_id, "user_id": user_id})

            sql = f"""
                UPDATE trips
                SET {', '.join(fields)}
                WHERE id = :trip_id AND user_id = :user_id
            """

            with self.get_connection() as conn:
                conn.execute(sqlalchemy.text(sql), params)
                conn.commit()

            return True

        except Exception as e:
            st.error(f"❌ Error updating trip: {str(e)}")
            return False



    # Initialize user credits (unified)
    def initialize_user_credits(self, user_id):
        """Add welcome bonus credits to a new user"""
        self.add_credit_transaction(
            user_id=user_id,
            trip_id=None,
            transaction_type="welcome_bonus",
            credits_amount=1000,
            description="Welcome bonus 1000 credits"
        )


    # Add credit transaction (unified)
    def add_credit_transaction(self, user_id, trip_id, transaction_type, credits_amount, description):
        """Add a credit transaction for a user"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO credit_transactions
                        (user_id, trip_id, transaction_type, credits_amount, description)
                        VALUES (:user_id, :trip_id, :transaction_type, :credits_amount, :description)
                    """),
                    {
                        "user_id": user_id,
                        "trip_id": trip_id,
                        "transaction_type": transaction_type,
                        "credits_amount": credits_amount,
                        "description": description
                    }
                )
                conn.commit()
        except Exception as e:
            st.error(f"Error adding credit transaction: {str(e)}")

# ---------------- Global DB Instance ---------------- #
db = PostgresDatabaseManager()
