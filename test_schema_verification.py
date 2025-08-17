#!/usr/bin/env python3
"""
Test Schema Verification Script
Tests the database schema verification directly
"""

import sqlite3
import os
import sys

# Add user_management to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_management'))

from user_management.database_schema_manager import DatabaseSchemaManager

def test_schema_verification():
    """Test schema verification directly"""
    print("🔍 Testing Schema Verification")
    print("=" * 50)
    
    # Create schema manager
    manager = DatabaseSchemaManager()
    
    print(f"Aadhaar DB Path: {manager.aadhaar_db_path}")
    print(f"PAN DB Path: {manager.pan_db_path}")
    print()
    
    # Check if files exist
    print("📁 Checking database files:")
    print(f"  Aadhaar DB exists: {os.path.exists(manager.aadhaar_db_path)}")
    print(f"  PAN DB exists: {os.path.exists(manager.pan_db_path)}")
    print()
    
    # Test schema verification for Aadhaar database
    print("🔍 Testing Aadhaar database schema verification:")
    try:
        verification = manager.verify_schema_changes(manager.aadhaar_db_path)
        print(f"  Verification result: {verification}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()
    
    # Test schema verification for PAN database
    print("🔍 Testing PAN database schema verification:")
    try:
        verification = manager.verify_schema_changes(manager.pan_db_path)
        print(f"  Verification result: {verification}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()
    
    # Test direct database access
    print("🔍 Testing direct database access:")
    
    # Test Aadhaar database
    try:
        with sqlite3.connect(manager.aadhaar_db_path) as conn:
            cursor = conn.cursor()
            
            # Check aadhaar_documents table
            cursor.execute("PRAGMA table_info(aadhaar_documents)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  Aadhaar documents columns: {columns}")
            print(f"  Has user_id: {'user_id' in columns}")
            
            # Check extracted_fields table
            cursor.execute("PRAGMA table_info(extracted_fields)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  Extracted fields columns: {columns}")
            print(f"  Has user_id: {'user_id' in columns}")
            
    except Exception as e:
        print(f"  ❌ Error accessing Aadhaar DB: {e}")
    
    # Test PAN database
    try:
        with sqlite3.connect(manager.pan_db_path) as conn:
            cursor = conn.cursor()
            
            # Check pan_documents table
            cursor.execute("PRAGMA table_info(pan_documents)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  PAN documents columns: {columns}")
            print(f"  Has user_id: {'user_id' in columns}")
            
            # Check extracted_fields table
            cursor.execute("PRAGMA table_info(extracted_fields)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"  Extracted fields columns: {columns}")
            print(f"  Has user_id: {'user_id' in columns}")
            
    except Exception as e:
        print(f"  ❌ Error accessing PAN DB: {e}")

if __name__ == "__main__":
    test_schema_verification()
