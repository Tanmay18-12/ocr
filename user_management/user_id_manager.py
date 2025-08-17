#!/usr/bin/env python3
"""
User ID Manager for Unique User Management System
Handles unique user ID generation, assignment, and lookup operations
"""

import sqlite3
import uuid
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging
import hashlib
import re

class UserIDManager:
    """Manages unique user ID generation and assignment"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        self.cache = {}
        self.cache_lock = threading.Lock()
        self.logger = self._setup_logging()
        
        # Initialize databases if they don't exist
        self._ensure_users_tables()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for user ID operations"""
        logger = logging.getLogger('UserIDManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _ensure_users_tables(self) -> None:
        """Ensure users tables exist in both databases"""
        for db_path in [self.aadhaar_db_path, self.pan_db_path]:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id TEXT PRIMARY KEY,
                            aadhaar_number TEXT UNIQUE,
                            primary_name TEXT NOT NULL,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            document_count INTEGER DEFAULT 0
                        )
                    ''')
                    conn.commit()
            except Exception as e:
                self.logger.error(f"Failed to ensure users table in {db_path}: {e}")
    
    def normalize_aadhaar(self, aadhaar_number: str) -> str:
        """Normalize Aadhaar number by removing spaces, hyphens, and converting to uppercase"""
        if not aadhaar_number:
            return ""
        
        # Remove all non-digit characters except X (for masked Aadhaar)
        normalized = re.sub(r'[^\dX]', '', str(aadhaar_number).upper())
        return normalized
    
    def generate_user_id(self) -> str:
        """Generate a unique UUID-based user ID"""
        return str(uuid.uuid4())
    
    def _get_user_from_cache(self, aadhaar_number: str) -> Optional[Dict]:
        """Get user from cache (thread-safe)"""
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        
        with self.cache_lock:
            return self.cache.get(normalized_aadhaar)
    
    def _add_user_to_cache(self, aadhaar_number: str, user_data: Dict) -> None:
        """Add user to cache (thread-safe)"""
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        
        with self.cache_lock:
            self.cache[normalized_aadhaar] = user_data
    
    def _clear_user_from_cache(self, aadhaar_number: str) -> None:
        """Remove user from cache (thread-safe)"""
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        
        with self.cache_lock:
            self.cache.pop(normalized_aadhaar, None)
    
    def user_exists(self, aadhaar_number: str) -> bool:
        """Check if user exists by Aadhaar number"""
        # Check cache first
        cached_user = self._get_user_from_cache(aadhaar_number)
        if cached_user:
            return True
        
        # Check database
        user_data = self.get_user_by_aadhaar(aadhaar_number)
        return user_data is not None
    
    def get_user_by_aadhaar(self, aadhaar_number: str) -> Optional[Dict]:
        """Get user data by Aadhaar number"""
        if not aadhaar_number:
            return None
        
        # Check cache first
        cached_user = self._get_user_from_cache(aadhaar_number)
        if cached_user:
            return cached_user
        
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        
        # Check both databases
        for db_path in [self.aadhaar_db_path, self.pan_db_path]:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT user_id, aadhaar_number, primary_name, created_at, 
                               updated_at, document_count
                        FROM users 
                        WHERE aadhaar_number = ?
                    ''', (normalized_aadhaar,))
                    
                    row = cursor.fetchone()
                    if row:
                        user_data = {
                            'user_id': row[0],
                            'aadhaar_number': row[1],
                            'primary_name': row[2],
                            'created_at': row[3],
                            'updated_at': row[4],
                            'document_count': row[5],
                            'source_db': db_path
                        }
                        
                        # Add to cache
                        self._add_user_to_cache(aadhaar_number, user_data)
                        return user_data
                        
            except Exception as e:
                self.logger.error(f"Error querying user from {db_path}: {e}")
        
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user data by user ID"""
        if not user_id:
            return None
        
        # Check both databases
        for db_path in [self.aadhaar_db_path, self.pan_db_path]:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT user_id, aadhaar_number, primary_name, created_at, 
                               updated_at, document_count
                        FROM users 
                        WHERE user_id = ?
                    ''', (user_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'user_id': row[0],
                            'aadhaar_number': row[1],
                            'primary_name': row[2],
                            'created_at': row[3],
                            'updated_at': row[4],
                            'document_count': row[5],
                            'source_db': db_path
                        }
                        
            except Exception as e:
                self.logger.error(f"Error querying user by ID from {db_path}: {e}")
        
        return None
    
    def create_user(self, aadhaar_number: str, name: str, db_path: str) -> str:
        """Create a new user and return user ID"""
        if not aadhaar_number or not name:
            raise ValueError("Aadhaar number and name are required")
        
        normalized_aadhaar = self.normalize_aadhaar(aadhaar_number)
        user_id = self.generate_user_id()
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (user_id, aadhaar_number, primary_name, document_count)
                    VALUES (?, ?, ?, 1)
                ''', (user_id, normalized_aadhaar, name.strip()))
                
                conn.commit()
                
                # Add to cache
                user_data = {
                    'user_id': user_id,
                    'aadhaar_number': normalized_aadhaar,
                    'primary_name': name.strip(),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'document_count': 1,
                    'source_db': db_path
                }
                self._add_user_to_cache(aadhaar_number, user_data)
                
                self.logger.info(f"Created new user {user_id} for Aadhaar {normalized_aadhaar}")
                return user_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                # User already exists, get existing user
                existing_user = self.get_user_by_aadhaar(aadhaar_number)
                if existing_user:
                    self.logger.info(f"User already exists for Aadhaar {normalized_aadhaar}: {existing_user['user_id']}")
                    return existing_user['user_id']
            raise Exception(f"Failed to create user: {e}")
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise
    
    def update_user_document_count(self, user_id: str, increment: int = 1) -> bool:
        """Update the document count for a user"""
        # Find which database contains the user
        user_data = self.get_user_by_id(user_id)
        if not user_data:
            self.logger.error(f"User {user_id} not found")
            return False
        
        db_path = user_data['source_db']
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET document_count = document_count + ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (increment, user_id))
                
                conn.commit()
                
                # Clear from cache to force refresh
                if user_data.get('aadhaar_number'):
                    self._clear_user_from_cache(user_data['aadhaar_number'])
                
                self.logger.info(f"Updated document count for user {user_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating user document count: {e}")
            return False
    
    def get_or_create_user_id(self, aadhaar_number: str, name: str, 
                             preferred_db: str = None) -> str:
        """Get existing user ID or create new one"""
        if not aadhaar_number or not name:
            raise ValueError("Aadhaar number and name are required")
        
        # Check if user already exists
        existing_user = self.get_user_by_aadhaar(aadhaar_number)
        if existing_user:
            # Update document count
            self.update_user_document_count(existing_user['user_id'])
            return existing_user['user_id']
        
        # Create new user
        db_path = preferred_db or self.aadhaar_db_path
        return self.create_user(aadhaar_number, name, db_path)
    
    def sync_user_across_databases(self, user_id: str) -> bool:
        """Sync user data across both databases"""
        user_data = self.get_user_by_id(user_id)
        if not user_data:
            return False
        
        source_db = user_data['source_db']
        target_db = self.pan_db_path if source_db == self.aadhaar_db_path else self.aadhaar_db_path
        
        try:
            with sqlite3.connect(target_db) as conn:
                cursor = conn.cursor()
                
                # Check if user already exists in target database
                cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
                if cursor.fetchone():
                    self.logger.info(f"User {user_id} already exists in {target_db}")
                    return True
                
                # Insert user into target database
                cursor.execute('''
                    INSERT INTO users (user_id, aadhaar_number, primary_name, 
                                     created_at, updated_at, document_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data['aadhaar_number'],
                    user_data['primary_name'],
                    user_data['created_at'],
                    user_data['updated_at'],
                    user_data['document_count']
                ))
                
                conn.commit()
                self.logger.info(f"Synced user {user_id} to {target_db}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error syncing user across databases: {e}")
            return False
    
    def get_user_statistics(self) -> Dict:
        """Get statistics about users across all databases"""
        stats = {
            'total_users': 0,
            'aadhaar_db_users': 0,
            'pan_db_users': 0,
            'users_with_multiple_docs': 0
        }
        
        for db_path in [self.aadhaar_db_path, self.pan_db_path]:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Count total users
                    cursor.execute('SELECT COUNT(*) FROM users')
                    count = cursor.fetchone()[0]
                    
                    if db_path == self.aadhaar_db_path:
                        stats['aadhaar_db_users'] = count
                    else:
                        stats['pan_db_users'] = count
                    
                    # Count users with multiple documents
                    cursor.execute('SELECT COUNT(*) FROM users WHERE document_count > 1')
                    multi_doc_count = cursor.fetchone()[0]
                    stats['users_with_multiple_docs'] += multi_doc_count
                    
            except Exception as e:
                self.logger.error(f"Error getting statistics from {db_path}: {e}")
        
        # Calculate total unique users (avoiding double counting)
        all_user_ids = set()
        for db_path in [self.aadhaar_db_path, self.pan_db_path]:
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM users')
                    user_ids = [row[0] for row in cursor.fetchall()]
                    all_user_ids.update(user_ids)
            except Exception as e:
                self.logger.error(f"Error counting unique users from {db_path}: {e}")
        
        stats['total_users'] = len(all_user_ids)
        return stats
    
    def clear_cache(self) -> None:
        """Clear the user cache"""
        with self.cache_lock:
            self.cache.clear()
        self.logger.info("User cache cleared")

def main():
    """Test the UserIDManager"""
    print("👤 User ID Manager Test")
    print("=" * 40)
    
    manager = UserIDManager()
    
    # Test user creation
    print("\n📝 Testing user creation...")
    try:
        user_id1 = manager.get_or_create_user_id("123456789012", "John Doe")
        print(f"Created/Retrieved user: {user_id1}")
        
        # Try to create same user again (should return existing)
        user_id2 = manager.get_or_create_user_id("123456789012", "John Doe")
        print(f"Second attempt: {user_id2}")
        print(f"Same user ID: {user_id1 == user_id2}")
        
        # Test user lookup
        print("\n🔍 Testing user lookup...")
        user_data = manager.get_user_by_aadhaar("123456789012")
        if user_data:
            print(f"Found user: {user_data['primary_name']} (ID: {user_data['user_id']})")
        
        # Test statistics
        print("\n📊 User statistics:")
        stats = manager.get_user_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()