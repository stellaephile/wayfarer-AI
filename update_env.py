#!/usr/bin/env python3
"""
Script to update .env file with relative paths
"""

import os
import shutil

def update_env_file():
    """Update .env file with relative paths"""
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    # Backup original .env
    if os.path.exists('.env.backup'):
        print("⚠️  .env.backup already exists, skipping backup")
    else:
        shutil.copy('.env', '.env.backup')
        print("✅ Created backup: .env.backup")
    
    # Read the relative paths template
    if not os.path.exists('env_relative.txt'):
        print("❌ env_relative.txt not found!")
        return False
    
    # Replace .env with relative paths
    shutil.copy('env_relative.txt', '.env')
    print("✅ Updated .env with relative paths")
    
    # Clean up
    os.remove('env_relative.txt')
    print("✅ Cleaned up temporary files")
    
    print("\n🎉 .env file updated successfully!")
    print("All paths are now relative and will work on any machine.")
    
    return True

if __name__ == "__main__":
    update_env_file()
