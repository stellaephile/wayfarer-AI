import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_database_config():
    """Get database configuration from Streamlit secrets (local) or env vars (Cloud Run)"""
    # --- Local dev: use st.secrets.toml ---
    try:
        if hasattr(st, 'secrets') and 'POSTGRES_USER' in st.secrets:
            return {
                "connection_name": st.secrets["CLOUDSQL_CONNECTION_NAME"],
                "database": st.secrets["POSTGRES_DB"],
                "user": st.secrets["POSTGRES_USER"],
                "password": st.secrets["MYSQL_PASSWORD"],  # Can rename to POSTGRES_PASSWORD if needed
            }
    except Exception:
        pass

    # --- Cloud Run: fallback to env vars ---
    return {
        "connection_name": os.getenv("CLOUDSQL_CONNECTION_NAME", ""),
        "database": os.getenv("POSTGRES_DB", "wayfarer-improv"),
        "user": os.getenv("POSTGRES_USER", "wayfarer-user"),
        "password": os.getenv("MYSQL_PASSWORD", ""),  # Can rename to POSTGRES_PASSWORD if desired
    }

def validate_postgres_config():
    """Validate that Cloud SQL config is complete"""
    config = get_database_config()

    if not config["connection_name"]:
        raise ValueError("CLOUDSQL_CONNECTION_NAME is not configured")
    if not config["user"]:
        raise ValueError("POSTGRES_USER is not configured")
    if not config["password"]:
        raise ValueError("MYSQL_PASSWORD is not configured")
    if not config["database"]:
        raise ValueError("POSTGRES_DB is not configured")

    return True

def get_database():
    """Factory function to get PostgresDatabaseManager instance"""
    validate_postgres_config()
    from cloudsql_database import db
    return db

