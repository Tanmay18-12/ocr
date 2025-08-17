# PAN Card Extraction System with SQL Integration

## Overview

This PAN card extraction system provides comprehensive functionality for extracting, validating, and storing PAN card information from PDF documents. It's designed to work alongside the existing Aadhaar card extraction system, providing a complete document processing solution.

## Features

### 🔍 **PAN Card Extraction**
- **Field Extraction**: Name, Father's Name, Date of Birth, PAN Number
- **Pattern Recognition**: Advanced regex patterns for accurate field extraction
- **OCR Integration**: PDF to text conversion with Tesseract OCR
- **Text Cleaning**: Automatic removal of OCR artifacts and formatting

### 🗄️ **SQL Database Integration**
- **Separate Database**: `pan_documents.db` for PAN-specific data
- **Structured Tables**: Organized storage with proper relationships
- **Data Retrieval**: Easy querying and reporting capabilities
- **Audit Trail**: Timestamp tracking and confidence scoring

### ✅ **Validation System**
- **PAN Number Validation**: 10-character format validation (5 letters + 4 digits + 1 letter)
- **Pattern Detection**: Identifies invalid patterns and suspicious data
- **Comprehensive Rules**: Multiple validation layers for data quality
- **Error Reporting**: Detailed validation results with reasons

### 🤖 **Agent-Based Architecture**
- **PAN Extractor Agent**: LLM-powered extraction with pattern matching
- **Validator Agent**: Enhanced validation with PAN-specific rules
- **Confidence Scoring**: Field-level and overall confidence assessment
- **Integration Ready**: Works with existing agent system

## Installation

### Prerequisites
```bash
pip install -r requirements.txt
```

### Dependencies
- `pytesseract` - OCR processing
- `pdf2image` - PDF to image conversion
- `sqlite3` - Database operations
- `langchain_openai` - LLM integration
- `re` - Regular expressions

## Usage

### 1. Basic PAN Extraction

```python
from pan_extractor_with_sql import PANExtractionTool

# Initialize extractor
extractor = PANExtractionTool("pan_documents.db")

# Extract and store data
result = extractor.extract_and_store("path/to/pan_card.pdf")

# View results
print(result["extraction"]["extracted_data"])
```

### 2. Using PAN Extractor Agent

```python
from agents.pan_extractor_agent import PANExtractorAgent

# Initialize agent
agent = PANExtractorAgent()

# Extract from text
sample_text = """
PERMANENT ACCOUNT NUMBER CARD
Name: John Doe
Father's Name: Robert Doe
Date of Birth: 15/03/1985
PAN: ABCDE1234F
"""

result = agent.extract_pan_fields(sample_text)
print(result["extracted_data"])
```

### 3. Validation

```python
from agents.validator_agent import ValidatorAgent

# Initialize validator
validator = ValidatorAgent()

# Validate PAN number
pan_validation = validator.validate_pan_number("ABCDE1234F")
print(pan_validation)
```

### 4. Database Operations

```python
# Get all extracted data
all_data = extractor.get_all_extracted_data()
for record in all_data["data"]:
    print(f"Document ID: {record['document_id']}")
    print(f"PAN: {record['extracted_data']['PAN Number']}")
    print(f"Name: {record['extracted_data']['Name']}")
```

## Database Schema

### Main Documents Table
```sql
CREATE TABLE pan_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    document_type TEXT NOT NULL,
    extraction_timestamp TEXT NOT NULL,
    extraction_confidence REAL DEFAULT 0.0,
    raw_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Extracted Fields Table
```sql
CREATE TABLE extracted_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    "Name" TEXT,
    "Father's Name" TEXT,
    "DOB" TEXT,
    "PAN Number" TEXT,
    extraction_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES pan_documents (id)
);
```

## PAN Number Validation Rules

### Format Requirements
- **Length**: Exactly 10 characters
- **Structure**: 5 letters + 4 digits + 1 letter
- **Example**: `ABCDE1234F`

### Validation Checks
1. **Length Validation**: Must be exactly 10 characters
2. **Format Validation**: Must match `[A-Z]{5}[0-9]{4}[A-Z]` pattern
3. **Structure Validation**: 
   - First 5 characters must be letters
   - Middle 4 characters must be digits
   - Last character must be a letter
4. **Pattern Detection**: Identifies suspicious patterns
5. **Common Invalid Patterns**: Rejects known invalid combinations

### Invalid Pattern Examples
- `ABCD1234E` - Wrong length (9 characters)
- `ABCDE12345F` - Wrong length (11 characters)
- `ABCD1234EF` - Wrong format
- `AAAAA0000A` - Common invalid pattern
- `ABCDE1234F` - Sequential pattern

## Testing

### Run PAN Validation Tests
```bash
python test_pan_validation.py
```

### Run Comprehensive Demo
```bash
python pan_aadhaar_demo.py
```

### Test Individual Components
```python
# Test PAN number validation
from agents.validator_agent import FieldValidator

# Test various patterns
test_results = FieldValidator.test_invalid_pan_patterns()
print(test_results)
```

## Integration with Aadhaar System

The PAN extraction system is designed to work seamlessly with the existing Aadhaar extraction system:

### Combined Workflow
```python
from pan_aadhaar_demo import DocumentProcessingDemo

# Initialize demo
demo = DocumentProcessingDemo()

# Run full demo with both systems
demo.run_full_demo(
    aadhaar_pdf="path/to/aadhaar.pdf",
    pan_pdf="path/to/pan.pdf"
)
```

### Shared Components
- **Validator Agent**: Handles both Aadhaar and PAN validation
- **Database Structure**: Similar schema for consistency
- **Agent Architecture**: Compatible agent system
- **Error Handling**: Unified error reporting

## Configuration

### Environment Variables
```bash
# OpenAI API for LLM integration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo
```

### Database Configuration
```python
# Custom database paths
aadhaar_db = "aadhaar_documents.db"
pan_db = "pan_documents.db"
```

## Error Handling

### Common Issues
1. **PDF Processing Errors**: Check if PDF is readable and not corrupted
2. **OCR Errors**: Ensure Tesseract is properly installed
3. **Database Errors**: Verify database permissions and disk space
4. **Validation Errors**: Check input format and data quality

### Error Recovery
```python
try:
    result = extractor.extract_and_store(pdf_path)
    if result["extraction"]["status"] == "error":
        print(f"Extraction failed: {result['extraction']['error_message']}")
except Exception as e:
    print(f"System error: {e}")
```

## Performance Optimization

### Best Practices
1. **Batch Processing**: Process multiple documents in sequence
2. **Database Indexing**: Add indexes for frequently queried fields
3. **Memory Management**: Process large PDFs in chunks
4. **Caching**: Cache validation results for repeated patterns

### Performance Monitoring
```python
# Monitor extraction performance
import time

start_time = time.time()
result = extractor.extract_and_store(pdf_path)
end_time = time.time()

print(f"Extraction time: {end_time - start_time:.2f} seconds")
print(f"Confidence score: {result['extraction']['extraction_confidence']}")
```

## Security Considerations

### Data Protection
- **Local Storage**: All data stored locally in SQLite databases
- **No External Transmission**: No data sent to external services (except OpenAI API)
- **Input Validation**: All inputs validated before processing
- **Error Sanitization**: Error messages don't expose sensitive data

### Best Practices
1. **Secure File Handling**: Validate file paths and permissions
2. **Database Security**: Use appropriate database permissions
3. **API Key Management**: Store API keys securely
4. **Data Retention**: Implement data retention policies

## Troubleshooting

### Common Problems

#### 1. OCR Not Working
```bash
# Install Tesseract
sudo apt-get install tesseract-ocr
# or
brew install tesseract
```

#### 2. PDF Processing Issues
```python
# Check PDF readability
from pdf2image import convert_from_path
try:
    pages = convert_from_path(pdf_path, dpi=300)
    print(f"PDF has {len(pages)} pages")
except Exception as e:
    print(f"PDF processing error: {e}")
```

#### 3. Database Connection Issues
```python
# Test database connection
import sqlite3
try:
    conn = sqlite3.connect("pan_documents.db")
    print("Database connection successful")
    conn.close()
except Exception as e:
    print(f"Database error: {e}")
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings for all functions
- Include type hints
- Write comprehensive tests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information
4. Include error messages and system information

## Changelog

### Version 1.0.0
- Initial PAN card extraction system
- SQL database integration
- Comprehensive validation rules
- Agent-based architecture
- Integration with Aadhaar system



