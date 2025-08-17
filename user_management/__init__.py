"""
User Management Package for Unique User Management System
Provides user ID management, duplicate prevention, and database schema management
"""

from .user_id_manager import UserIDManager
from .duplicate_prevention_service import DuplicatePreventionService
from .database_schema_manager import DatabaseSchemaManager
from .duplicate_data_identifier import DuplicateDataIdentifier
from .data_cleanup_migrator import DataCleanupMigrator
from .exceptions import (
    UserManagementError,
    DuplicateAadhaarError,
    DuplicatePANError,
    DatabaseConstraintError,
    MigrationError,
    UserNotFoundError,
    InvalidDocumentDataError,
    UserIDGenerationError,
    DataIntegrityError,
    ConcurrencyError,
    handle_sqlite_error,
    create_error_response
)

__version__ = "1.0.0"
__author__ = "User Management System"

__all__ = [
    'UserIDManager',
    'DuplicatePreventionService', 
    'DatabaseSchemaManager',
    'DuplicateDataIdentifier',
    'DataCleanupMigrator',
    'UserManagementError',
    'DuplicateAadhaarError',
    'DuplicatePANError',
    'DatabaseConstraintError',
    'MigrationError',
    'UserNotFoundError',
    'InvalidDocumentDataError',
    'UserIDGenerationError',
    'DataIntegrityError',
    'ConcurrencyError',
    'handle_sqlite_error',
    'create_error_response'
]