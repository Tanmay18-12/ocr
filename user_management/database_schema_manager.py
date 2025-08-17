#!/usr/bin/env python3
"""
Database Schema Manager for Unique User Management System
Handles database schema updates, migrations, and constraint management
"""

import sqlite3
import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

class DatabaseSchemaManager:
    """Manages database schema updates and migrations for user management system"""
    
    def __init__(self, aadhaar_db_path: str = "aadhaar_documents.db", 
                 pan_db_path: str = "pan_documents.db"):
        self.aadhaar_db_path = aadhaar_db_path
        self.pan_db_path = pan_db_path
        self.backup_dir = "database_backups"
        self.migration_log_path = "migration_log.json"
        self.logger = self._setup_logging()
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for database operations"""
        logger = logging.getLogger('DatabaseSchemaManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def create_backup(self, db_path: str) -> str:
        """Create backup of database before migration"""
        if not os.path.exists(db_path):
            self.logger.warning(f"Database {db_path} does not exist, skipping backup")
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = Path(db_path).stem
        backup_path = os.path.join(self.backup_dir, f"{db_name}_backup_{timestamp}.db")
        
        try:
            shutil.copy2(db_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str, target_db_path: str) -> bool:
        """Restore database from backup"""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, target_db_path)
                self.logger.info(f"Restored database from backup: {backup_path}")
                return True
            else:
                self.logger.error(f"Backup file not found: {backup_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def create_users_table(self, db_path: str) -> bool:
        """Create the central users table"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        aadhaar_number TEXT UNIQUE NOT NULL,
                        primary_name TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        document_count INTEGER DEFAULT 0
                    )
                ''')
                
                # Create unique index on aadhaar_number
                cursor.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_aadhaar 
                    ON users(aadhaar_number)
                ''')
                
                # Create user_documents cross-reference table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        document_id INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        UNIQUE(user_id, document_type)
                    )
                ''')
                
                conn.commit()
                self.logger.info(f"Created users table in {db_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create users table: {e}")
            return False
    
    def add_user_id_columns(self, db_path: str, document_table: str, fields_table: str) -> bool:
        """Add user_id columns to existing tables"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user_id column already exists in document table
                cursor.execute(f"PRAGMA table_info({document_table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'user_id' not in columns:
                    cursor.execute(f'ALTER TABLE {document_table} ADD COLUMN user_id TEXT')
                    self.logger.info(f"Added user_id column to {document_table}")
                
                # Check if user_id column already exists in fields table
                cursor.execute(f"PRAGMA table_info({fields_table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'user_id' not in columns:
                    cursor.execute(f'ALTER TABLE {fields_table} ADD COLUMN user_id TEXT')
                    self.logger.info(f"Added user_id column to {fields_table}")
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add user_id columns: {e}")
            return False
    
    def add_unique_constraints(self, db_path: str, fields_table: str, unique_field: str) -> bool:
        """Add unique constraints to prevent duplicate documents"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create unique index on the specified field
                index_name = f"idx_{fields_table}_{unique_field.replace(' ', '_').replace(chr(39), '').lower()}_unique"
                
                # Check if index already exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name=?
                ''', (index_name,))
                
                if not cursor.fetchone():
                    # Use square brackets for column names with spaces or special characters
                    cursor.execute(f'''
                        CREATE UNIQUE INDEX {index_name} 
                        ON {fields_table}([{unique_field}])
                    ''')
                    self.logger.info(f"Created unique index {index_name}")
                else:
                    self.logger.info(f"Unique index {index_name} already exists")
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add unique constraints: {e}")
            return False
    
    def add_foreign_key_constraints(self, db_path: str, table_name: str) -> bool:
        """Add foreign key constraints (Note: SQLite has limited FK support)"""
        try:
            with sqlite3.connect(db_path) as conn:
                # Enable foreign key support
                conn.execute("PRAGMA foreign_keys = ON")
                self.logger.info(f"Enabled foreign key constraints for {db_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to enable foreign key constraints: {e}")
            return False
    
    def verify_schema_changes(self, db_path: str) -> Dict[str, bool]:
        """Verify that all schema changes were applied correctly"""
        verification_results = {}
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if users table exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='users'
                ''')
                verification_results['users_table_exists'] = bool(cursor.fetchone())
                
                # Check if user_documents table exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='user_documents'
                ''')
                verification_results['user_documents_table_exists'] = bool(cursor.fetchone())
                
                # Check for unique indexes
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name LIKE '%unique%'
                ''')
                unique_indexes = cursor.fetchall()
                verification_results['unique_indexes_count'] = len(unique_indexes)
                
                # Check for user_id columns in main tables
                tables_to_check = []
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                all_tables = [row[0] for row in cursor.fetchall()]
                
                # Check specific tables for user_id columns
                specific_tables = ['aadhaar_documents', 'pan_documents', 'extracted_fields']
                for table in specific_tables:
                    if table in all_tables:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]
                        verification_results[f'{table}_has_user_id'] = 'user_id' in columns
                    else:
                        verification_results[f'{table}_has_user_id'] = False
                
                self.logger.info(f"Schema verification results: {verification_results}")
                return verification_results
                
        except Exception as e:
            self.logger.error(f"Schema verification failed: {e}")
            return {'error': str(e)}
    
    def log_migration(self, operation: str, status: str, details: Dict) -> None:
        """Log migration operations for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'details': details
        }
        
        # Load existing log
        migration_log = []
        if os.path.exists(self.migration_log_path):
            try:
                with open(self.migration_log_path, 'r') as f:
                    migration_log = json.load(f)
            except:
                migration_log = []
        
        # Add new entry
        migration_log.append(log_entry)
        
        # Save updated log
        try:
            with open(self.migration_log_path, 'w') as f:
                json.dump(migration_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to log migration: {e}")
    
    def migrate_aadhaar_database(self) -> bool:
        """Migrate Aadhaar database schema"""
        self.logger.info("Starting Aadhaar database migration")
        
        try:
            # Create backup
            backup_path = self.create_backup(self.aadhaar_db_path)
            
            # Create users table
            if not self.create_users_table(self.aadhaar_db_path):
                raise Exception("Failed to create users table")
            
            # Add user_id columns
            if not self.add_user_id_columns(self.aadhaar_db_path, 'aadhaar_documents', 'extracted_fields'):
                raise Exception("Failed to add user_id columns")
            
            # Add unique constraints
            if not self.add_unique_constraints(self.aadhaar_db_path, 'extracted_fields', 'Aadhaar Number'):
                self.logger.warning("Failed to add unique constraint - may already exist or have duplicates")
            
            # Enable foreign keys
            self.add_foreign_key_constraints(self.aadhaar_db_path)
            
            # Verify changes
            verification = self.verify_schema_changes(self.aadhaar_db_path)
            
            # Log migration
            self.log_migration('aadhaar_migration', 'success', {
                'backup_path': backup_path,
                'verification': verification
            })
            
            self.logger.info("Aadhaar database migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Aadhaar database migration failed: {e}")
            self.log_migration('aadhaar_migration', 'failed', {'error': str(e)})
            return False
    
    def migrate_pan_database(self) -> bool:
        """Migrate PAN database schema"""
        self.logger.info("Starting PAN database migration")
        
        try:
            # Create backup
            backup_path = self.create_backup(self.pan_db_path)
            
            # Create users table
            if not self.create_users_table(self.pan_db_path):
                raise Exception("Failed to create users table")
            
            # Add user_id columns
            if not self.add_user_id_columns(self.pan_db_path, 'pan_documents', 'extracted_fields'):
                raise Exception("Failed to add user_id columns")
            
            # Add unique constraints
            if not self.add_unique_constraints(self.pan_db_path, 'extracted_fields', 'PAN Number'):
                self.logger.warning("Failed to add unique constraint - may already exist or have duplicates")
            
            # Enable foreign keys
            self.add_foreign_key_constraints(self.pan_db_path)
            
            # Verify changes
            verification = self.verify_schema_changes(self.pan_db_path)
            
            # Log migration
            self.log_migration('pan_migration', 'success', {
                'backup_path': backup_path,
                'verification': verification
            })
            
            self.logger.info("PAN database migration completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"PAN database migration failed: {e}")
            self.log_migration('pan_migration', 'failed', {'error': str(e)})
            return False
    
    def migrate_all_databases(self) -> bool:
        """Migrate all databases"""
        self.logger.info("Starting complete database migration")
        
        aadhaar_success = self.migrate_aadhaar_database()
        pan_success = self.migrate_pan_database()
        
        if aadhaar_success and pan_success:
            self.logger.info("All database migrations completed successfully")
            return True
        else:
            self.logger.error("Some database migrations failed")
            return False

def main():
    """Test the database schema manager"""
    print("🗄️ Database Schema Manager Test")
    print("=" * 50)
    
    manager = DatabaseSchemaManager()
    
    # Test migration
    print("\n📋 Starting database migration...")
    success = manager.migrate_all_databases()
    
    if success:
        print("✅ Migration completed successfully!")
        
        # Show verification results
        print("\n📊 Aadhaar Database Verification:")
        aadhaar_verification = manager.verify_schema_changes(manager.aadhaar_db_path)
        for key, value in aadhaar_verification.items():
            print(f"  {key}: {value}")
        
        print("\n📊 PAN Database Verification:")
        pan_verification = manager.verify_schema_changes(manager.pan_db_path)
        for key, value in pan_verification.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Migration failed!")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()