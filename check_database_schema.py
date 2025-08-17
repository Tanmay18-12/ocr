#!/usr/bin/env python3
"""
Check Database Schema Script
Shows the actual tables and columns in the databases
"""

import sqlite3
import os

def check_database_schema(db_path):
    """Check the schema of a database"""
    if not os.path.exists(db_path):
        print(f"❌ Database {db_path} not found")
        return
    
    print(f"\n🔍 Checking schema for {db_path}")
    print("=" * 60)
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"📋 Tables found: {len(tables)}")
            for table in tables:
                table_name = table[0]
                print(f"\n📄 Table: {table_name}")
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                print("  Columns:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    print(f"    - {col_name} ({col_type}){' PRIMARY KEY' if pk else ''}{' NOT NULL' if not_null else ''}")
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  Row count: {count}")
                
    except Exception as e:
        print(f"❌ Error checking {db_path}: {e}")

def main():
    """Check both databases"""
    print("🔍 Database Schema Check")
    print("=" * 60)
    
    # Check Aadhaar database
    check_database_schema("aadhaar_documents.db")
    
    # Check PAN database
    check_database_schema("pan_documents.db")
    
    print("\n" + "=" * 60)
    print("✅ Schema check completed")

if __name__ == "__main__":
    main()
