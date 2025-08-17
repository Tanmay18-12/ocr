#!/usr/bin/env python3
"""
Unit Tests for User Management System
Tests core services: UserIDManager, DuplicatePreventionService, DatabaseSchemaManager
"""

import unittest
import tempfile
import os
import sqlite3
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_management.user_id_manager import UserIDManager
from user_management.duplicate_prevention_service import DuplicatePreventionService
from user_management.database_schema_manager import DatabaseSchemaManager
from user_management.exceptions import (
    DuplicateAadhaarError, DuplicatePANError, UserNotFoundError,
    InvalidDocumentDataError, MigrationError
)

class TestUserIDManager(unittest.TestCase):
    """Test cases for UserIDManager"""
    
    def setUp(self):
        """Set up test databases"""
        self.test_dir = tempfile.mkdtemp()
        self.aadhaar_db = os.path.join(self.test_dir, "test_aadhaar.db")
        self.pan_db = os.path.join(self.test_dir, "test_pan.db")
        self.manager = UserIDManager(self.aadhaar_db, self.pan_db)
    
    def tearDown(self):
        """Clean up test databases"""
        shutil.rmtree(self.test_dir)
    
    def test_generate_user_id(self):
        """Test UUID generation"""
        user_id1 = self.manager.generate_user_id()
        user_id2 = self.manager.generate_user_id()
        
        # Should be different UUIDs
        self.assertNotEqual(user_id1, user_id2)
        
        # Should be valid UUID format
        self.assertEqual(len(user_id1), 36)  # UUID length
        self.assertIn('-', user_id1)
    
    def test_normalize_aadhaar(self):
        """Test Aadhaar number normalization"""
        test_cases = [
            ("1234 5678 9012", "123456789012"),
            ("1234-5678-9012", "123456789012"),
            ("1234 5678 901X", "123456789012"),  # X should remain
            ("  1234 5678 9012  ", "123456789012"),
            ("", "")
        ]
        
        for input_aadhaar, expected in test_cases:
            result = self.manager.normalize_aadhaar(input_aadhaar)
            self.assertEqual(result, expected)
    
    def test_create_user(self):
        """Test user creation"""
        aadhaar = "123456789012"
        name = "John Doe"
        
        user_id = self.manager.create_user(aadhaar, name, self.aadhaar_db)
        
        # Should return a valid UUID
        self.assertIsInstance(user_id, str)
        self.assertEqual(len(user_id), 36)
        
        # User should exist in database
        self.assertTrue(self.manager.user_exists(aadhaar))
        
        # Should be able to retrieve user
        user_data = self.manager.get_user_by_aadhaar(aadhaar)
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data['user_id'], user_id)
        self.assertEqual(user_data['primary_name'], name)
    
    def test_duplicate_user_creation(self):
        """Test that creating duplicate user returns existing user ID"""
        aadhaar = "123456789012"
        name = "John Doe"
        
        # Create user first time
        user_id1 = self.manager.create_user(aadhaar, name, self.aadhaar_db)
        
        # Create same user again
        user_id2 = self.manager.create_user(aadhaar, name, self.aadhaar_db)
        
        # Should return same user ID
        self.assertEqual(user_id1, user_id2)
    
    def test_get_or_create_user_id(self):
        """Test get or create user ID functionality"""
        aadhaar = "123456789012"
        name = "John Doe"
        
        # First call should create user
        user_id1 = self.manager.get_or_create_user_id(aadhaar, name)
        
        # Second call should return existing user
        user_id2 = self.manager.get_or_create_user_id(aadhaar, name)
        
        self.assertEqual(user_id1, user_id2)
    
    def test_user_statistics(self):
        """Test user statistics calculation"""
        # Create some test users
        self.manager.create_user("123456789012", "User 1", self.aadhaar_db)
        self.manager.create_user("123456789013", "User 2", self.aadhaar_db)
        
        stats = self.manager.get_user_statistics()
        
        self.assertIn('total_users', stats)
        self.assertIn('aadhaar_db_users', stats)
        self.assertIn('pan_db_users', stats)
        self.assertGreaterEqual(stats['aadhaar_db_users'], 2)
    
    def test_cache_functionality(self):
        """Test user caching"""
        aadhaar = "123456789012"
        name = "John Doe"
        
        # Create user
        user_id = self.manager.create_user(aadhaar, name, self.aadhaar_db)
        
        # First lookup should cache the user
        user_data1 = self.manager.get_user_by_aadhaar(aadhaar)
        
        # Second lookup should use cache
        user_data2 = self.manager.get_user_by_aadhaar(aadhaar)
        
        self.assertEqual(user_data1, user_data2)
        
        # Clear cache and verify
        self.manager.clear_cache()
        user_data3 = self.manager.get_user_by_aadhaar(aadhaar)
        self.assertEqual(user_data1['user_id'], user_data3['user_id'])

class TestDuplicatePreventionService(unittest.TestCase):
    """Test cases for DuplicatePreventionService"""
    
    def setUp(self):
        """Set up test databases with sample data"""
        self.test_dir = tempfile.mkdtemp()
        self.aadhaar_db = os.path.join(self.test_dir, "test_aadhaar.db")
        self.pan_db = os.path.join(self.test_dir, "test_pan.db")
        
        # Create test databases with sample data
        self._create_test_aadhaar_data()
        self._create_test_pan_data()
        
        self.service = DuplicatePreventionService(self.aadhaar_db, self.pan_db)
    
    def tearDown(self):
        """Clean up test databases"""
        shutil.rmtree(self.test_dir)
    
    def _create_test_aadhaar_data(self):
        """Create test Aadhaar database with sample data"""
        with sqlite3.connect(self.aadhaar_db) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE aadhaar_documents (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT,
                    document_type TEXT,
                    extraction_timestamp TEXT,
                    extraction_confidence REAL,
                    raw_text TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE extracted_fields (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER,
                    "Name" TEXT,
                    "DOB" TEXT,
                    "Gender" TEXT,
                    "Address" TEXT,
                    "Aadhaar Number" TEXT,
                    FOREIGN KEY (document_id) REFERENCES aadhaar_documents (id)
                )
            ''')
            
            # Insert sample data
            cursor.execute('''
                INSERT INTO aadhaar_documents (id, file_path, document_type, extraction_confidence)
                VALUES (1, 'test1.pdf', 'AADHAAR', 0.95)
            ''')
            
            cursor.execute('''
                INSERT INTO extracted_fields (document_id, "Name", "DOB", "Gender", "Address", "Aadhaar Number")
                VALUES (1, 'John Doe', '01/01/1990', 'Male', '123 Main St', '123456789012')
            ''')
            
            conn.commit()
    
    def _create_test_pan_data(self):
        """Create test PAN database with sample data"""
        with sqlite3.connect(self.pan_db) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE pan_documents (
                    id INTEGER PRIMARY KEY,
                    file_path TEXT,
                    document_type TEXT,
                    extraction_timestamp TEXT,
                    extraction_confidence REAL,
                    raw_text TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE extracted_fields (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER,
                    "Name" TEXT,
                    "Father's Name" TEXT,
                    "DOB" TEXT,
                    "PAN Number" TEXT,
                    FOREIGN KEY (document_id) REFERENCES pan_documents (id)
                )
            ''')
            
            # Insert sample data
            cursor.execute('''
                INSERT INTO pan_documents (id, file_path, document_type, extraction_confidence)
                VALUES (1, 'test_pan.pdf', 'PAN', 0.90)
            ''')
            
            cursor.execute('''
                INSERT INTO extracted_fields (document_id, "Name", "Father's Name", "DOB", "PAN Number")
                VALUES (1, 'Jane Smith', 'Robert Smith', '15/05/1985', 'ABCDE1234F')
            ''')
            
            conn.commit()
    
    def test_normalize_aadhaar(self):
        """Test Aadhaar normalization"""
        test_cases = [
            ("1234 5678 9012", "123456789012"),
            ("1234-5678-9012", "123456789012"),
            ("1234.5678.9012", "123456789012"),
            ("", "")
        ]
        
        for input_val, expected in test_cases:
            result = self.service.normalize_aadhaar(input_val)
            self.assertEqual(result, expected)
    
    def test_normalize_pan(self):
        """Test PAN normalization"""
        test_cases = [
            ("ABCDE1234F", "ABCDE1234F"),
            ("abcde1234f", "ABCDE1234F"),
            ("ABCDE-1234-F", "ABCDE1234F"),
            ("ABCDE 1234 F", "ABCDE1234F"),
            ("", "")
        ]
        
        for input_val, expected in test_cases:
            result = self.service.normalize_pan(input_val)
            self.assertEqual(result, expected)
    
    def test_check_aadhaar_exists(self):
        """Test Aadhaar existence check"""
        # Test existing Aadhaar
        existing_result = self.service.check_aadhaar_exists("123456789012")
        self.assertIsNotNone(existing_result)
        self.assertTrue(existing_result['exists'])
        self.assertEqual(existing_result['name'], 'John Doe')
        
        # Test non-existing Aadhaar
        non_existing_result = self.service.check_aadhaar_exists("999999999999")
        self.assertIsNone(non_existing_result)
    
    def test_check_pan_exists(self):
        """Test PAN existence check"""
        # Test existing PAN
        existing_result = self.service.check_pan_exists("ABCDE1234F")
        self.assertIsNotNone(existing_result)
        self.assertTrue(existing_result['exists'])
        self.assertEqual(existing_result['name'], 'Jane Smith')
        
        # Test non-existing PAN
        non_existing_result = self.service.check_pan_exists("ZZZZZ9999Z")
        self.assertIsNone(non_existing_result)
    
    def test_validate_document_uniqueness(self):
        """Test document uniqueness validation"""
        # Test duplicate Aadhaar
        aadhaar_data = {'Aadhaar Number': '123456789012', 'Name': 'John Doe'}
        is_unique, existing = self.service.validate_document_uniqueness('AADHAAR', aadhaar_data)
        self.assertFalse(is_unique)
        self.assertIsNotNone(existing)
        
        # Test unique Aadhaar
        unique_aadhaar_data = {'Aadhaar Number': '999999999999', 'Name': 'New User'}
        is_unique, existing = self.service.validate_document_uniqueness('AADHAAR', unique_aadhaar_data)
        self.assertTrue(is_unique)
        self.assertIsNone(existing)
        
        # Test duplicate PAN
        pan_data = {'PAN Number': 'ABCDE1234F', 'Name': 'Jane Smith'}
        is_unique, existing = self.service.validate_document_uniqueness('PAN', pan_data)
        self.assertFalse(is_unique)
        self.assertIsNotNone(existing)
    
    def test_data_quality_metrics(self):
        """Test data quality metrics calculation"""
        metrics = self.service.get_data_quality_metrics()
        
        self.assertIn('aadhaar_metrics', metrics)
        self.assertIn('pan_metrics', metrics)
        
        aadhaar_metrics = metrics['aadhaar_metrics']
        self.assertIn('total_records', aadhaar_metrics)
        self.assertIn('unique_numbers', aadhaar_metrics)
        self.assertIn('duplicate_records', aadhaar_metrics)
        
        # Should have at least 1 record from test data
        self.assertGreaterEqual(aadhaar_metrics['total_records'], 1)

class TestDatabaseSchemaManager(unittest.TestCase):
    """Test cases for DatabaseSchemaManager"""
    
    def setUp(self):
        """Set up test databases"""
        self.test_dir = tempfile.mkdtemp()
        self.aadhaar_db = os.path.join(self.test_dir, "test_aadhaar.db")
        self.pan_db = os.path.join(self.test_dir, "test_pan.db")
        
        # Create basic database structure
        self._create_basic_databases()
        
        self.manager = DatabaseSchemaManager(self.aadhaar_db, self.pan_db)
    
    def tearDown(self):
        """Clean up test databases"""
        shutil.rmtree(self.test_dir)
    
    def _create_basic_databases(self):
        """Create basic database structure for testing"""
        for db_path in [self.aadhaar_db, self.pan_db]:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                if 'aadhaar' in db_path:
                    cursor.execute('''
                        CREATE TABLE aadhaar_documents (
                            id INTEGER PRIMARY KEY,
                            file_path TEXT,
                            document_type TEXT,
                            extraction_timestamp TEXT,
                            extraction_confidence REAL,
                            raw_text TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE extracted_fields (
                            id INTEGER PRIMARY KEY,
                            document_id INTEGER,
                            "Name" TEXT,
                            "DOB" TEXT,
                            "Gender" TEXT,
                            "Address" TEXT,
                            "Aadhaar Number" TEXT,
                            FOREIGN KEY (document_id) REFERENCES aadhaar_documents (id)
                        )
                    ''')
                else:
                    cursor.execute('''
                        CREATE TABLE pan_documents (
                            id INTEGER PRIMARY KEY,
                            file_path TEXT,
                            document_type TEXT,
                            extraction_timestamp TEXT,
                            extraction_confidence REAL,
                            raw_text TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    cursor.execute('''
                        CREATE TABLE extracted_fields (
                            id INTEGER PRIMARY KEY,
                            document_id INTEGER,
                            "Name" TEXT,
                            "Father's Name" TEXT,
                            "DOB" TEXT,
                            "PAN Number" TEXT,
                            FOREIGN KEY (document_id) REFERENCES pan_documents (id)
                        )
                    ''')
                
                conn.commit()
    
    def test_create_users_table(self):
        """Test users table creation"""
        result = self.manager.create_users_table(self.aadhaar_db)
        self.assertTrue(result)
        
        # Verify table exists
        with sqlite3.connect(self.aadhaar_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_add_user_id_columns(self):
        """Test adding user_id columns"""
        result = self.manager.add_user_id_columns(
            self.aadhaar_db, 'aadhaar_documents', 'extracted_fields'
        )
        self.assertTrue(result)
        
        # Verify columns exist
        with sqlite3.connect(self.aadhaar_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(aadhaar_documents)")
            columns = [col[1] for col in cursor.fetchall()]
            self.assertIn('user_id', columns)
    
    def test_add_unique_constraints(self):
        """Test adding unique constraints"""
        result = self.manager.add_unique_constraints(
            self.aadhaar_db, 'extracted_fields', 'Aadhaar Number'
        )
        self.assertTrue(result)
        
        # Verify index exists
        with sqlite3.connect(self.aadhaar_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%unique%'")
            indexes = cursor.fetchall()
            self.assertGreater(len(indexes), 0)
    
    def test_verify_schema_changes(self):
        """Test schema verification"""
        # Apply some changes first
        self.manager.create_users_table(self.aadhaar_db)
        self.manager.add_user_id_columns(self.aadhaar_db, 'aadhaar_documents', 'extracted_fields')
        
        # Verify changes
        verification = self.manager.verify_schema_changes(self.aadhaar_db)
        
        self.assertIn('users_table_exists', verification)
        self.assertTrue(verification['users_table_exists'])
        self.assertIn('aadhaar_documents_has_user_id', verification)
        self.assertTrue(verification['aadhaar_documents_has_user_id'])
    
    def test_migration_logging(self):
        """Test migration logging functionality"""
        self.manager.log_migration('test_operation', 'success', {'test': 'data'})
        
        # Check if log file was created
        self.assertTrue(os.path.exists(self.manager.migration_log_path))
        
        # Read and verify log content
        with open(self.manager.migration_log_path, 'r') as f:
            log_data = json.load(f)
        
        self.assertIsInstance(log_data, list)
        self.assertGreater(len(log_data), 0)
        self.assertEqual(log_data[-1]['operation'], 'test_operation')
        self.assertEqual(log_data[-1]['status'], 'success')

class TestExceptions(unittest.TestCase):
    """Test cases for custom exceptions"""
    
    def test_duplicate_aadhaar_error(self):
        """Test DuplicateAadhaarError"""
        error = DuplicateAadhaarError(
            aadhaar_number="123456789012",
            existing_user_id="user-123",
            existing_document_id=456
        )
        
        self.assertEqual(error.aadhaar_number, "123456789012")
        self.assertEqual(error.existing_user_id, "user-123")
        self.assertEqual(error.existing_document_id, 456)
        self.assertIn("123456789012", str(error))
        
        # Test error dictionary
        error_dict = error.to_dict()
        self.assertIn('error_type', error_dict)
        self.assertIn('error_code', error_dict)
        self.assertEqual(error_dict['error_code'], 'DUPLICATE_AADHAAR')
    
    def test_duplicate_pan_error(self):
        """Test DuplicatePANError"""
        error = DuplicatePANError(
            pan_number="ABCDE1234F",
            existing_user_id="user-456"
        )
        
        self.assertEqual(error.pan_number, "ABCDE1234F")
        self.assertEqual(error.existing_user_id, "user-456")
        self.assertIn("ABCDE1234F", str(error))
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['error_code'], 'DUPLICATE_PAN')
    
    def test_invalid_document_data_error(self):
        """Test InvalidDocumentDataError"""
        error = InvalidDocumentDataError(
            document_type="AADHAAR",
            missing_fields=["Name", "Aadhaar Number"],
            invalid_fields={"DOB": "invalid date format"}
        )
        
        self.assertEqual(error.document_type, "AADHAAR")
        self.assertEqual(error.missing_fields, ["Name", "Aadhaar Number"])
        self.assertIn("AADHAAR", str(error))
        
        error_dict = error.to_dict()
        self.assertEqual(error_dict['error_code'], 'INVALID_DOCUMENT_DATA')

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestUserIDManager))
    test_suite.addTest(unittest.makeSuite(TestDuplicatePreventionService))
    test_suite.addTest(unittest.makeSuite(TestDatabaseSchemaManager))
    test_suite.addTest(unittest.makeSuite(TestExceptions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)