#!/usr/bin/env python3
"""
Custom Exception Classes for Unique User Management System
Defines specific exceptions for duplicate detection, database constraints, and migration errors
"""

from typing import Dict, Optional, Any
from datetime import datetime

class UserManagementError(Exception):
    """Base exception class for user management system errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "USER_MGMT_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """Convert exception to dictionary for logging/serialization"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }

class DuplicateAadhaarError(UserManagementError):
    """Exception raised when attempting to insert duplicate Aadhaar number"""
    
    def __init__(self, aadhaar_number: str, existing_user_id: str = None, 
                 existing_document_id: int = None, existing_record: Dict = None):
        self.aadhaar_number = aadhaar_number
        self.existing_user_id = existing_user_id
        self.existing_document_id = existing_document_id
        self.existing_record = existing_record or {}
        
        # Create detailed message
        message = f"Aadhaar number {aadhaar_number} already exists in the system"
        if existing_user_id:
            message += f" for user {existing_user_id}"
        if existing_document_id:
            message += f" (Document ID: {existing_document_id})"
        
        details = {
            'aadhaar_number': aadhaar_number,
            'existing_user_id': existing_user_id,
            'existing_document_id': existing_document_id,
            'existing_record': existing_record,
            'suggested_action': 'Use existing user ID or verify if this is a legitimate duplicate'
        }
        
        super().__init__(message, "DUPLICATE_AADHAAR", details)

class DuplicatePANError(UserManagementError):
    """Exception raised when attempting to insert duplicate PAN number"""
    
    def __init__(self, pan_number: str, existing_user_id: str = None, 
                 existing_document_id: int = None, existing_record: Dict = None):
        self.pan_number = pan_number
        self.existing_user_id = existing_user_id
        self.existing_document_id = existing_document_id
        self.existing_record = existing_record or {}
        
        # Create detailed message
        message = f"PAN number {pan_number} already exists in the system"
        if existing_user_id:
            message += f" for user {existing_user_id}"
        if existing_document_id:
            message += f" (Document ID: {existing_document_id})"
        
        details = {
            'pan_number': pan_number,
            'existing_user_id': existing_user_id,
            'existing_document_id': existing_document_id,
            'existing_record': existing_record,
            'suggested_action': 'Use existing user ID or verify if this is a legitimate duplicate'
        }
        
        super().__init__(message, "DUPLICATE_PAN", details)

class DatabaseConstraintError(UserManagementError):
    """Exception raised when database constraint violations occur"""
    
    def __init__(self, constraint_type: str, table_name: str, column_name: str = None, 
                 value: str = None, original_error: str = None):
        self.constraint_type = constraint_type
        self.table_name = table_name
        self.column_name = column_name
        self.value = value
        self.original_error = original_error
        
        message = f"Database constraint violation: {constraint_type} constraint failed"
        if table_name:
            message += f" on table '{table_name}'"
        if column_name:
            message += f" for column '{column_name}'"
        if value:
            message += f" with value '{value}'"
        
        details = {
            'constraint_type': constraint_type,
            'table_name': table_name,
            'column_name': column_name,
            'value': value,
            'original_error': original_error,
            'suggested_action': 'Check for existing records or validate input data'
        }
        
        super().__init__(message, "DB_CONSTRAINT_ERROR", details)

class MigrationError(UserManagementError):
    """Exception raised during database migration operations"""
    
    def __init__(self, migration_step: str, database_path: str, 
                 rollback_available: bool = False, backup_path: str = None, 
                 original_error: str = None):
        self.migration_step = migration_step
        self.database_path = database_path
        self.rollback_available = rollback_available
        self.backup_path = backup_path
        self.original_error = original_error
        
        message = f"Migration failed at step '{migration_step}' for database '{database_path}'"
        if rollback_available:
            message += " (rollback available)"
        
        details = {
            'migration_step': migration_step,
            'database_path': database_path,
            'rollback_available': rollback_available,
            'backup_path': backup_path,
            'original_error': original_error,
            'suggested_action': 'Check migration logs and consider rollback if backup is available'
        }
        
        super().__init__(message, "MIGRATION_ERROR", details)

class UserNotFoundError(UserManagementError):
    """Exception raised when a user cannot be found"""
    
    def __init__(self, identifier: str, identifier_type: str = "user_id"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        
        message = f"User not found with {identifier_type}: {identifier}"
        
        details = {
            'identifier': identifier,
            'identifier_type': identifier_type,
            'suggested_action': 'Verify the identifier or create a new user'
        }
        
        super().__init__(message, "USER_NOT_FOUND", details)

class InvalidDocumentDataError(UserManagementError):
    """Exception raised when document data is invalid or incomplete"""
    
    def __init__(self, document_type: str, missing_fields: list = None, 
                 invalid_fields: Dict = None, validation_errors: list = None):
        self.document_type = document_type
        self.missing_fields = missing_fields or []
        self.invalid_fields = invalid_fields or {}
        self.validation_errors = validation_errors or []
        
        message = f"Invalid {document_type} document data"
        if missing_fields:
            message += f" - Missing fields: {', '.join(missing_fields)}"
        if invalid_fields:
            message += f" - Invalid fields: {', '.join(invalid_fields.keys())}"
        
        details = {
            'document_type': document_type,
            'missing_fields': missing_fields,
            'invalid_fields': invalid_fields,
            'validation_errors': validation_errors,
            'suggested_action': 'Provide all required fields with valid data'
        }
        
        super().__init__(message, "INVALID_DOCUMENT_DATA", details)

class UserIDGenerationError(UserManagementError):
    """Exception raised when user ID generation fails"""
    
    def __init__(self, reason: str, attempts: int = 1, original_error: str = None):
        self.reason = reason
        self.attempts = attempts
        self.original_error = original_error
        
        message = f"Failed to generate unique user ID: {reason}"
        if attempts > 1:
            message += f" (after {attempts} attempts)"
        
        details = {
            'reason': reason,
            'attempts': attempts,
            'original_error': original_error,
            'suggested_action': 'Check database connectivity and UUID generation system'
        }
        
        super().__init__(message, "USER_ID_GENERATION_ERROR", details)

class DataIntegrityError(UserManagementError):
    """Exception raised when data integrity issues are detected"""
    
    def __init__(self, integrity_type: str, affected_records: int = 0, 
                 details_list: list = None, severity: str = "HIGH"):
        self.integrity_type = integrity_type
        self.affected_records = affected_records
        self.details_list = details_list or []
        self.severity = severity
        
        message = f"Data integrity issue detected: {integrity_type}"
        if affected_records > 0:
            message += f" affecting {affected_records} records"
        
        details = {
            'integrity_type': integrity_type,
            'affected_records': affected_records,
            'details_list': details_list,
            'severity': severity,
            'suggested_action': 'Run data validation and cleanup procedures'
        }
        
        super().__init__(message, "DATA_INTEGRITY_ERROR", details)

class ConcurrencyError(UserManagementError):
    """Exception raised when concurrent access issues occur"""
    
    def __init__(self, operation: str, resource: str, conflict_type: str = "WRITE_CONFLICT"):
        self.operation = operation
        self.resource = resource
        self.conflict_type = conflict_type
        
        message = f"Concurrency conflict during {operation} on {resource}: {conflict_type}"
        
        details = {
            'operation': operation,
            'resource': resource,
            'conflict_type': conflict_type,
            'suggested_action': 'Retry operation or implement proper locking mechanism'
        }
        
        super().__init__(message, "CONCURRENCY_ERROR", details)

# Exception handler utility functions

def handle_sqlite_error(error: Exception, context: Dict = None) -> UserManagementError:
    """Convert SQLite errors to appropriate custom exceptions"""
    error_str = str(error).lower()
    context = context or {}
    
    if "unique constraint failed" in error_str:
        # Determine which field caused the constraint violation
        if "aadhaar" in error_str:
            return DuplicateAadhaarError(
                aadhaar_number=context.get('aadhaar_number', 'unknown'),
                existing_record=context.get('existing_record', {})
            )
        elif "pan" in error_str:
            return DuplicatePANError(
                pan_number=context.get('pan_number', 'unknown'),
                existing_record=context.get('existing_record', {})
            )
        else:
            return DatabaseConstraintError(
                constraint_type="UNIQUE",
                table_name=context.get('table_name', 'unknown'),
                original_error=str(error)
            )
    
    elif "foreign key constraint failed" in error_str:
        return DatabaseConstraintError(
            constraint_type="FOREIGN_KEY",
            table_name=context.get('table_name', 'unknown'),
            original_error=str(error)
        )
    
    elif "not null constraint failed" in error_str:
        return DatabaseConstraintError(
            constraint_type="NOT_NULL",
            table_name=context.get('table_name', 'unknown'),
            original_error=str(error)
        )
    
    else:
        return UserManagementError(
            message=f"Database error: {str(error)}",
            error_code="DB_ERROR",
            details={'original_error': str(error), 'context': context}
        )

def log_exception(exception: UserManagementError, logger) -> None:
    """Log exception with full details"""
    exception_dict = exception.to_dict()
    logger.error(f"Exception occurred: {exception_dict}")

def create_error_response(exception: UserManagementError) -> Dict:
    """Create standardized error response for API/UI"""
    return {
        'success': False,
        'error': {
            'type': exception.__class__.__name__,
            'code': exception.error_code,
            'message': exception.message,
            'timestamp': exception.timestamp,
            'suggested_action': exception.details.get('suggested_action', 'Contact system administrator')
        },
        'details': {k: v for k, v in exception.details.items() if k != 'suggested_action'}
    }

def main():
    """Test the custom exception classes"""
    print("⚠️  Custom Exception Classes Test")
    print("=" * 45)
    
    # Test DuplicateAadhaarError
    print("\n📝 Testing DuplicateAadhaarError...")
    try:
        raise DuplicateAadhaarError(
            aadhaar_number="123456789012",
            existing_user_id="user-123",
            existing_document_id=456,
            existing_record={'name': 'John Doe', 'file_path': 'doc1.pdf'}
        )
    except DuplicateAadhaarError as e:
        print(f"Exception: {e}")
        print(f"Error dict: {e.to_dict()}")
        print(f"Error response: {create_error_response(e)}")
    
    # Test DatabaseConstraintError
    print("\n📝 Testing DatabaseConstraintError...")
    try:
        raise DatabaseConstraintError(
            constraint_type="UNIQUE",
            table_name="users",
            column_name="aadhaar_number",
            value="123456789012"
        )
    except DatabaseConstraintError as e:
        print(f"Exception: {e}")
    
    # Test MigrationError
    print("\n📝 Testing MigrationError...")
    try:
        raise MigrationError(
            migration_step="add_constraints",
            database_path="aadhaar_documents.db",
            rollback_available=True,
            backup_path="backup_20241201.db"
        )
    except MigrationError as e:
        print(f"Exception: {e}")
    
    # Test SQLite error handling
    print("\n📝 Testing SQLite error handling...")
    import sqlite3
    try:
        # Simulate a unique constraint error
        sqlite_error = sqlite3.IntegrityError("UNIQUE constraint failed: users.aadhaar_number")
        custom_error = handle_sqlite_error(
            sqlite_error, 
            {'aadhaar_number': '123456789012', 'table_name': 'users'}
        )
        print(f"Converted error: {custom_error}")
    except Exception as e:
        print(f"Error in test: {e}")
    
    print("\n" + "=" * 45)

if __name__ == "__main__":
    main()