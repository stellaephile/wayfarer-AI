import os
import streamlit as st

def get_database_config():
    """Get database configuration from environment variables or Streamlit secrets"""
    
    # Try to get from Streamlit secrets first (for local development)
    try:
        if hasattr(st, 'secrets') and 'MYSQL_HOST' in st.secrets:
            return {
                'host': st.secrets['MYSQL_HOST'],
                'port': int(st.secrets.get('MYSQL_PORT', '3306')),
                'database': st.secrets['MYSQL_DATABASE'],
                'user': st.secrets['MYSQL_USER'],
                'password': st.secrets['MYSQL_PASSWORD']
            }
    except Exception as e:
        # In production, st.secrets might not be available
        pass
    
    # Fallback to environment variables (for production)
    return {
        'host': os.getenv('MYSQL_HOST', '35.225.222.139'),
        'port': int(os.getenv('MYSQL_PORT', '3306')),
        'database': os.getenv('MYSQL_DATABASE', 'trip_planner'),
        'user': os.getenv('MYSQL_USER', 'trip_planner'),
        'password': os.getenv('MYSQL_PASSWORD', '')
    }

def validate_mysql_config():
    """Validate that MySQL configuration is complete"""
    config = get_database_config()
    
    if not config['host']:
        raise ValueError("MYSQL_HOST is not configured")
    if not config['user']:
        raise ValueError("MYSQL_USER is not configured")
    if not config['password']:
        raise ValueError("MYSQL_PASSWORD is not configured")
    if not config['database']:
        raise ValueError("MYSQL_DATABASE is not configured")
    
    return True

# Database factory function
def get_database():
    """Get the MySQL database instance - no fallback to SQLite"""
    # Validate MySQL configuration
    validate_mysql_config()
    
    # Import and return MySQL database
    from mysql_database import db
    return db
