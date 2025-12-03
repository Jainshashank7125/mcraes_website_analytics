#!/usr/bin/env python3
"""
Script to create a user in the v2 authentication system
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.user_service import create_user
from app.core.password_utils import hash_password

def main():
    email = "shashank.jain@theagilemorph.com"
    password = "Test@1234"
    full_name = "Shashank Jain"
    
    db = SessionLocal()
    try:
        # Check if user already exists
        from app.services.user_service import get_user_by_email
        existing_user = get_user_by_email(email, db)
        if existing_user:
            print(f"❌ User with email '{email}' already exists!")
            print(f"   User ID: {existing_user.id}")
            return 1
        
        # Create user
        user = create_user(
            email=email,
            password=password,
            full_name=full_name,
            db=db
        )
        
        print(f"✅ User created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Created At: {user.created_at}")
        
        return 0
    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    exit(main())

