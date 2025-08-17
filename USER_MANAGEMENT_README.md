# Unique User Management System

A comprehensive system that ensures each user gets only one unique user ID across all database tables and prevents duplicate Aadhar/PAN entries from being inserted into the system.

## 🎯 Key Features

- **Unique User IDs**: UUID-based user identification system
- **Duplicate Prevention**: Prevents duplicate Aadhar and PAN entries
- **Database Constraints**: Enforces uniqueness at database level
- **Data Migration**: Cleans up existing duplicates
- **Cross-Database Linking**: Links users across Aadhar and PAN databases
- **Comprehensive Logging**: Audit trails for all operations
- **Error Handling**: Structured error responses with actionable feedback

## 📁 Project Structure

```
user_management/
├── __init__.py                     # Package initialization
├── user_id_manager.py             # User ID generation and management
├── duplicate_prevention_service.py # Duplicate detection and prevention
├── database_schema_manager.py     # Database schema migrations
├── duplicate_data_identifier.py   # Duplicate data scanning
├── data_cleanup_migrator.py       # Data cleanup and migration
└── exceptions.py                   # Custom exception classes

tests/
└── test_user_management.py        # Comprehensive unit tests

Enhanced Extraction Tools:
├── aadhaar_extractor_with_sql.py  # Enhanced Aadhar extractor
├── pan_extractor_with_sql.py      # Enhanced PAN extractor
└── user_management_demo.py        # Complete system demo
```

## 🚀 Quick Start

### 1. System Setup

```bash
# Run the complete system setup
python user_management_demo.py --setup

# Force migration if needed
python user_management_demo.py --setup --force-migration
```

### 2. Process Documents

```bash
# Process an Aadhar document
python user_management_demo.py --process "sample_documents/aadhar_sample.pdf" --document-type AADHAAR

# Process a PAN document
python user_management_demo.py --process "sample_documents/pan_sample.pdf" --document-type PAN
```

### 3. Check System Status

```bash
# View system statistics
python user_management_demo.py --stats

# Run data quality check
python user_management_demo.py --quality-check

# Check if document exists
python user_management_demo.py --check-exists "123456789012" --document-type AADHAAR
```

## 🔧 Core Components

### UserIDManager

Manages unique user ID generation and assignment:

```python
from user_management import UserIDManager

manager = UserIDManager()

# Create or get existing user ID
user_id = manager.get_or_create_user_id("123456789012", "John Doe")

# Check if user exists
exists = manager.user_exists("123456789012")

# Get user data
user_data = manager.get_user_by_aadhaar("123456789012")
```

### DuplicatePreventionService

Prevents duplicate document entries:

```python
from user_management import DuplicatePreventionService

service = DuplicatePreventionService()

# Check for duplicates
is_unique, existing = service.validate_document_uniqueness(
    "AADHAAR", {"Aadhaar Number": "123456789012", "Name": "John Doe"}
)

# Get duplicate report
report = service.get_duplicate_report()
```

### DatabaseSchemaManager

Manages database schema updates:

```python
from user_management import DatabaseSchemaManager

manager = DatabaseSchemaManager()

# Run complete migration
success = manager.migrate_all_databases()

# Verify schema changes
verification = manager.verify_schema_changes("aadhaar_documents.db")
```

## 🗄️ Database Schema

### Users Table (Central Registry)

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,           -- UUID format
    aadhaar_number TEXT UNIQUE,         -- Normalized Aadhaar (can be empty for PAN-only users)
    primary_name TEXT NOT NULL,         -- Primary name from first document
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    document_count INTEGER DEFAULT 0    -- Number of documents for this user
);
```

### Enhanced Document Tables

Both `aadhaar_documents` and `pan_documents` tables now include:
- `user_id` column linking to the users table
- Foreign key constraints for data integrity

### Cross-Reference Table

```sql
CREATE TABLE user_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    document_type TEXT NOT NULL,        -- 'AADHAAR' or 'PAN'
    document_id INTEGER NOT NULL,       -- Reference to specific document table
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, document_type)      -- One document type per user
);
```

## 🛡️ Error Handling

The system provides structured error handling with specific exception types:

### DuplicateAadhaarError
```python
try:
    result = extractor.extract_and_store("document.pdf")
except DuplicateAadhaarError as e:
    print(f"Duplicate detected: {e.aadhaar_number}")
    print(f"Existing user: {e.existing_user_id}")
    print(f"Suggested action: {e.details['suggested_action']}")
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "type": "DuplicateAadhaarError",
    "code": "DUPLICATE_AADHAAR",
    "message": "Aadhaar number 123456789012 already exists in the system",
    "timestamp": "2024-12-01T10:30:00",
    "suggested_action": "Use existing user ID or verify if this is a legitimate duplicate"
  },
  "details": {
    "aadhaar_number": "123456789012",
    "existing_user_id": "user-123",
    "existing_document_id": 456
  }
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all unit tests
python tests/test_user_management.py

# Run specific test class
python -m unittest tests.test_user_management.TestUserIDManager

# Run with verbose output
python tests/test_user_management.py -v
```

## 📊 Data Migration

### Pre-Migration Analysis

```bash
# Identify duplicate data
python user_management/duplicate_data_identifier.py --json-report --csv-summary

# Run dry-run migration
python user_management/data_cleanup_migrator.py --dry-run
```

### Migration Execution

```bash
# Run complete migration
python user_management/data_cleanup_migrator.py

# Cleanup only (no schema changes)
python user_management/data_cleanup_migrator.py --cleanup-only

# Save detailed report
python user_management/data_cleanup_migrator.py --save-report
```

## 🔍 Monitoring and Reporting

### System Statistics

```python
# Get user statistics
stats = user_manager.get_user_statistics()
print(f"Total users: {stats['total_users']}")
print(f"Users with multiple docs: {stats['users_with_multiple_docs']}")

# Get data quality metrics
metrics = duplicate_service.get_data_quality_metrics()
aadhaar_metrics = metrics['aadhaar_metrics']
print(f"Duplicate percentage: {aadhaar_metrics['duplicate_percentage']:.1f}%")
```

### Duplicate Reports

```python
# Generate comprehensive duplicate report
identifier = DuplicateDataIdentifier()
report = identifier.run_full_scan()

print(f"Aadhaar duplicate groups: {report['summary']['aadhaar_duplicate_groups']}")
print(f"PAN duplicate groups: {report['summary']['pan_duplicate_groups']}")

# Save reports
identifier.save_json_report()
identifier.save_csv_summary()
```

## 🔧 Configuration

### Environment Variables

```bash
# Database paths
export AADHAAR_DB_PATH="aadhaar_documents.db"
export PAN_DB_PATH="pan_documents.db"

# Backup directory
export BACKUP_DIR="database_backups"

# Logging level
export LOG_LEVEL="INFO"
```

### Custom Configuration

```python
# Initialize with custom paths
manager = UserIDManager(
    aadhaar_db_path="custom_aadhaar.db",
    pan_db_path="custom_pan.db"
)

# Configure backup directory
migrator = DataCleanupMigrator(
    backup_dir="custom_backups"
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Migration Fails**
   ```bash
   # Check database permissions
   ls -la *.db
   
   # Verify database integrity
   sqlite3 aadhaar_documents.db "PRAGMA integrity_check;"
   
   # Restore from backup
   cp database_backups/aadhaar_documents_backup_*.db aadhaar_documents.db
   ```

2. **Duplicate Detection Not Working**
   ```python
   # Check normalization
   service = DuplicatePreventionService()
   normalized = service.normalize_aadhaar("1234 5678 9012")
   print(f"Normalized: {normalized}")
   
   # Verify constraints
   manager = DatabaseSchemaManager()
   verification = manager.verify_schema_changes("aadhaar_documents.db")
   print(verification)
   ```

3. **Performance Issues**
   ```sql
   -- Check indexes
   SELECT name FROM sqlite_master WHERE type='index';
   
   -- Analyze query performance
   EXPLAIN QUERY PLAN SELECT * FROM extracted_fields WHERE "Aadhaar Number" = '123456789012';
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose logging
manager = UserIDManager()
manager.logger.setLevel(logging.DEBUG)
```

## 📈 Performance Considerations

- **Indexing**: Unique indexes on Aadhaar and PAN numbers for fast lookups
- **Caching**: User data caching in UserIDManager for improved performance
- **Batch Processing**: Efficient batch operations for large datasets
- **Connection Pooling**: Proper database connection management

## 🔒 Security Features

- **Data Normalization**: Consistent data formatting prevents bypass attempts
- **Constraint Enforcement**: Database-level constraints as last line of defense
- **Audit Logging**: Complete audit trail of all operations
- **Error Sanitization**: Sensitive data excluded from error messages

## 📝 API Reference

### UserIDManager Methods

- `get_or_create_user_id(aadhaar_number, name, preferred_db=None)` → str
- `user_exists(aadhaar_number)` → bool
- `get_user_by_aadhaar(aadhaar_number)` → Optional[Dict]
- `get_user_by_id(user_id)` → Optional[Dict]
- `get_user_statistics()` → Dict

### DuplicatePreventionService Methods

- `check_aadhaar_exists(aadhaar_number)` → Optional[Dict]
- `check_pan_exists(pan_number)` → Optional[Dict]
- `validate_document_uniqueness(document_type, document_data)` → Tuple[bool, Optional[Dict]]
- `get_duplicate_report()` → Dict
- `get_data_quality_metrics()` → Dict

### Enhanced Extraction Tools

Both `AadhaarExtractionTool` and `PANExtractionTool` now include:
- `extract_and_store(pdf_path)` → Dict (with duplicate prevention)
- `check_aadhaar_exists(aadhaar_number)` / `check_pan_exists(pan_number)` → Dict
- `get_user_documents(user_id)` → Dict

## 🎉 Success Metrics

After implementing this system, you should see:

- ✅ **Zero duplicate Aadhar entries** in the database
- ✅ **Consistent user IDs** across all tables
- ✅ **Proper error handling** for duplicate attempts
- ✅ **Clean data migration** from existing duplicates
- ✅ **Comprehensive audit trails** for all operations
- ✅ **Improved data integrity** with database constraints

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test suite to verify system integrity
3. Review the migration logs for detailed error information
4. Use the debug mode for detailed operation logging

---

**Note**: This system is designed to be production-ready with comprehensive error handling, logging, and data integrity features. Always test in a development environment before deploying to production.