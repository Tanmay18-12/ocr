#!/usr/bin/env python3
"""
Database Migration Script
Adds missing user_id columns to existing database tables
"""

import sqlite3
import os
from datetime import datetime

def migrate_aadhaar_database():
    """Migrate Aadhaar database to add user_id columns"""
    db_path = "aadhaar_documents.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"🔧 Migrating {db_path}...")
            
            # Check if user_id column exists in aadhaar_documents table
            cursor.execute("PRAGMA table_info(aadhaar_documents)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                print("  ➕ Adding user_id column to aadhaar_documents table...")
                cursor.execute('ALTER TABLE aadhaar_documents ADD COLUMN user_id TEXT')
            
            # Check if user_id column exists in extracted_fields table
            cursor.execute("PRAGMA table_info(extracted_fields)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                print("  ➕ Adding user_id column to extracted_fields table...")
                cursor.execute('ALTER TABLE extracted_fields ADD COLUMN user_id TEXT')
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    aadhaar_number TEXT UNIQUE,
                    primary_name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_documents table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_documents (
                    user_id TEXT,
                    document_type TEXT,
                    document_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, document_type, document_id)
                )
            ''')
            
            conn.commit()
            print(f"✅ Successfully migrated {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error migrating {db_path}: {e}")
        return False

def migrate_pan_database():
    """Migrate PAN database to add user_id columns"""
    db_path = "pan_documents.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print(f"🔧 Migrating {db_path}...")
            
            # Check if user_id column exists in pan_documents table
            cursor.execute("PRAGMA table_info(pan_documents)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                print("  ➕ Adding user_id column to pan_documents table...")
                cursor.execute('ALTER TABLE pan_documents ADD COLUMN user_id TEXT')
            
            # Check if user_id column exists in extracted_fields table
            cursor.execute("PRAGMA table_info(extracted_fields)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                print("  ➕ Adding user_id column to extracted_fields table...")
                cursor.execute('ALTER TABLE extracted_fields ADD COLUMN user_id TEXT')
            
            # Create users table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    aadhaar_number TEXT,
                    primary_name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_documents table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_documents (
                    user_id TEXT,
                    document_type TEXT,
                    document_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, document_type, document_id)
                )
            ''')
            
            conn.commit()
            print(f"✅ Successfully migrated {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error migrating {db_path}: {e}")
        return False

def main():
    """Run database migrations"""
    print("🚀 Starting Database Migration")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Migrate both databases
    aadhaar_success = migrate_aadhaar_database()
    print()
    pan_success = migrate_pan_database()
    
    print()
    print("=" * 50)
    print("📊 MIGRATION SUMMARY")
    print("=" * 50)
    
    if aadhaar_success:
        print("✅ Aadhaar database migrated successfully")
    else:
        print("❌ Aadhaar database migration failed")
    
    if pan_success:
        print("✅ PAN database migrated successfully")
    else:
        print("❌ PAN database migration failed")
    
    if aadhaar_success and pan_success:
        print("\n🎉 All databases migrated successfully!")
        print("🔄 Please restart the backend server to apply changes.")
    else:
        print("\n⚠️ Some migrations failed. Please check the errors above.")

if __name__ == "__main__":
    main()
