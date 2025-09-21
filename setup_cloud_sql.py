#!/usr/bin/env python3
"""
Cloud SQL Setup Script
This script helps set up the Cloud SQL database and test the connection
"""

import mysql.connector
from mysql.connector import Error
import os
import streamlit as st

def test_mysql_connection(host, port, database, user, password):
    """Test MySQL connection"""
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print(f"✅ Successfully connected to MySQL database '{database}' on {host}:{port}")
            connection.close()
            return True
        else:
            print("❌ Failed to connect to MySQL")
            return False
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False

def create_database_if_not_exists(host, port, user, password, database_name):
    """Create database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"✅ Database '{database_name}' created or already exists")
        
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_cloud_sql():
    """Main setup function"""
    print("🚀 Cloud SQL Setup for Trip Planner")
    print("=" * 50)
    
    # Get configuration from user
    print("Please provide your Cloud SQL configuration:")
    print()
    
    host = input("MySQL Host (default: 35.225.222.139): ").strip() or "35.225.222.139"
    port = input("MySQL Port (default: 3306): ").strip() or "3306"
    database = input("Database Name (default: trip_planner): ").strip() or "trip_planner"
    user = input("MySQL Username (default: root): ").strip() or "root"
    password = input("MySQL Password: ").strip()
    
    if not password:
        print("❌ Password is required!")
        return False
    
    try:
        port = int(port)
    except ValueError:
        print("❌ Invalid port number!")
        return False
    
    print()
    print("Testing connection...")
    
    # Create database if it doesn't exist
    if create_database_if_not_exists(host, port, user, password, database):
        # Test connection to the specific database
        if test_mysql_connection(host, port, database, user, password):
            print()
            print("✅ Cloud SQL setup successful!")
            print()
            print("Next steps:")
            print("1. Update your .streamlit/secrets.toml with these credentials:")
            print(f"   MYSQL_HOST=\"{host}\"")
            print(f"   MYSQL_PORT=\"{port}\"")
            print(f"   MYSQL_DATABASE=\"{database}\"")
            print(f"   MYSQL_USER=\"{user}\"")
            print(f"   MYSQL_PASSWORD=\"{password}\"")
            print()
            print("2. Run the migration script to transfer data:")
            print("   python migrate_to_mysql.py")
            print()
            print("3. Start your Streamlit app:")
            print("   streamlit run src/app.py")
            return True
        else:
            print("❌ Failed to connect to the database")
            return False
    else:
        print("❌ Failed to create database")
        return False

def update_secrets_file(host, port, database, user, password):
    """Update secrets.toml file with the provided credentials"""
    secrets_path = ".streamlit/secrets.toml"
    
    try:
        # Read current secrets file
        with open(secrets_path, 'r') as f:
            content = f.read()
        
        # Update MySQL configuration
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.startswith('MYSQL_HOST='):
                updated_lines.append(f'MYSQL_HOST="{host}"')
            elif line.startswith('MYSQL_PORT='):
                updated_lines.append(f'MYSQL_PORT="{port}"')
            elif line.startswith('MYSQL_DATABASE='):
                updated_lines.append(f'MYSQL_DATABASE="{database}"')
            elif line.startswith('MYSQL_USER='):
                updated_lines.append(f'MYSQL_USER="{user}"')
            elif line.startswith('MYSQL_PASSWORD='):
                updated_lines.append(f'MYSQL_PASSWORD="{password}"')
            else:
                updated_lines.append(line)
        
        # Write updated content
        with open(secrets_path, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"✅ Updated {secrets_path} with new credentials")
        return True
        
    except Exception as e:
        print(f"❌ Error updating secrets file: {e}")
        return False

if __name__ == "__main__":
    print("Cloud SQL Setup for Trip Planner")
    print("=" * 40)
    print()
    
    if setup_cloud_sql():
        print()
        response = input("Would you like to update the secrets.toml file automatically? (y/n): ")
        if response.lower() == 'y':
            # Get the same configuration again for updating secrets
            host = input("MySQL Host (default: 35.225.222.139): ").strip() or "35.225.222.139"
            port = input("MySQL Port (default: 3306): ").strip() or "3306"
            database = input("Database Name (default: trip_planner): ").strip() or "trip_planner"
            user = input("MySQL Username (default: root): ").strip() or "root"
            password = input("MySQL Password: ").strip()
            
            update_secrets_file(host, port, database, user, password)
    else:
        print("Setup failed. Please check your configuration and try again.")
