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
        # Get DB settings from env (Cloud Run -> set via Secret Manager / env vars)
        self.connection_name = os.getenv("CLOUDSQL_CONNECTION_NAME")  # e.g. trip-planner-demo-471815:us-central1:trip-db
        self.database = os.getenv("MYSQL_DATABASE", "trip_planner")
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.connector = Connector()

        # Create SQLAlchemy engine (lazy connections)
        self.engine = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=self.getconn,
            pool_recycle=300,
            pool_pre_ping=True
        )
        self.init_database()

    def getconn(self):
        """Return a new database connection via Cloud SQL Python Connector"""
        conn = self.connector.connect(
            self.connection_name,
            "pymysql",
            user=self.user,
            password=self.password,
            db=self.database
        )
        return conn

    @contextmanager
    def get_connection(self):
        """Get SQLAlchemy connection for queries"""
        with self.engine.connect() as conn:
            yield conn

    def init_database(self):
        """Initialize tables if not exists"""
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
                conn.commit()
        except Exception as e:
            st.error(f"Error initializing database: {str(e)}")
            raise

# Create global db instance
db = MySQLDatabaseManager()
