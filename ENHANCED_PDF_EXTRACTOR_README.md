# Enhanced PDF Extraction Tool

## Overview

The Enhanced PDF Extraction Tool is a comprehensive solution for extracting and processing identity documents (Aadhaar and PAN cards) from PDF files. It provides JSON output, integrates with a validation system, and automatically creates dynamic SQL tables for data storage.

## Key Features

### 🔍 **Advanced OCR Processing**
- High-quality image preprocessing using OpenCV
- Hindi gibberish removal and text cleaning
- Multiple OCR configurations for optimal results
- Adaptive thresholding and noise reduction

### 📊 **JSON Output Format**
- Structured JSON response with extraction results
- Confidence scoring for extraction quality
- Document type detection (Aadhaar/PAN)
- Timestamp and metadata tracking

### 🗄️ **Dynamic Database Integration**
- Automatic table creation based on extracted fields
- Integration with Database Agent for storage
- Support for validation results storage
- SQLite database with metadata tracking

### ✅ **Validation Integration**
- Seamless integration with Validator Agent
- Field-level validation with detailed results
- Confidence scoring and quality assessment
- Error and warning tracking

## Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Required System Dependencies**
```bash
# For Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng
sudo apt-get install poppler-utils

# For macOS
brew install tesseract
brew install poppler

# For Windows
# Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Usage

### Basic Usage

```python
from tools.pdf_extractor_tool import PDFExtractorTool

# Initialize the tool
extractor = PDFExtractorTool(db_path="documents.db")

# Extract data from PDF
result = extractor._run("path/to/document.pdf")

# Access the JSON output
print(json.dumps(result, indent=2))
```

### JSON Output Format

```json
{
  "status": "success",
  "file_path": "path/to/document.pdf",
  "document_type": "AADHAAR",
  "extraction_timestamp": "2024-01-15T10:30:00",
  "extracted_data": {
    "Name": "John Doe",
    "DOB": "15/01/1990",
    "Gender": "Male",
    "Address": "123 Main Street, City, State 123456",
    "Aadhaar Number": "123456789012",
    "PAN": null,
    "Father's Name": "John Doe Sr."
  },
  "raw_text": "Extracted raw text...",
  "extraction_confidence": 0.85
}
```

### Complete Pipeline Usage

```python
from enhanced_pipeline_demo import EnhancedPipeline

# Initialize the complete pipeline
pipeline = EnhancedPipeline("documents.db")

# Process a document through the complete workflow
result = pipeline.process_document("path/to/document.pdf")

# The result includes extraction, validation, and database storage
print(f"Document ID: {result['database']['document_id']}")
print(f"Validation Status: {result['validation']['validation_status']}")
```

## Database Schema

### Core Tables

#### `documents` Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    document_type TEXT NOT NULL,
    extraction_timestamp TEXT NOT NULL,
    validation_status TEXT DEFAULT 'pending',
    is_valid BOOLEAN DEFAULT FALSE,
    quality_score REAL DEFAULT 0.0,
    completeness_score REAL DEFAULT 0.0,
    raw_data TEXT,
    processed_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### `extracted_fields` Table
The system creates a specific table with the required column names:
```sql
CREATE TABLE extracted_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    "Name" TEXT,
    "DOB" TEXT,
    "Gender" TEXT,
    "Address" TEXT,
    "Aadhaar Number" TEXT,
    "PAN" TEXT,
    "Father's Name" TEXT,
    extraction_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES id_documents (id)
);
```

#### Dynamic Validation Tables
The system automatically creates tables based on validation results:
```sql
CREATE TABLE validation_results_YYYYMMDD_HHMMSS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    validation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    field_name TEXT,
    validation_result TEXT,
    confidence_score REAL
);
```

## Configuration

### Database Configuration
```python
# Custom database path
extractor = PDFExtractorTool(db_path="custom_database.db")
```

### OCR Configuration
The tool uses optimized OCR settings:
- DPI: 300 (high resolution)
- Language: English
- Preprocessing: Adaptive thresholding, noise reduction
- Text cleaning: Hindi gibberish removal

## Supported Document Types

### Aadhaar Card
- **Extracted Fields:**
  - Aadhaar Number (12 digits, masked/unmasked)
  - Name
  - Date of Birth
  - Gender
  - Address

### PAN Card
- **Extracted Fields:**
  - PAN Number (10 characters)
  - Name
  - Father's Name
  - Date of Birth

## Error Handling

The tool provides comprehensive error handling:

```python
result = extractor._run("invalid_file.pdf")

if result.get("status") == "error":
    print(f"Error: {result.get('error_message')}")
else:
    # Process successful result
    extracted_data = result.get("extracted_data")
```

## Testing

### Run the Test Suite
```bash
python test_enhanced_pdf_extractor.py
```

### Run the Complete Demo
```bash
python enhanced_pipeline_demo.py
```

## API Reference

### PDFExtractorTool Class

#### Methods

- `_run(pdf_path: str) -> Dict[str, Any]`
  - Main extraction method
  - Returns JSON output with extraction results

- `extract_text(pdf_path: str) -> str`
  - Legacy method for text extraction only
  - Returns raw extracted text

- `extract_fields(pdf_path: str) -> Dict[str, Any]`
  - Legacy method for field extraction only
  - Returns extracted fields dictionary

#### Properties

- `db_path: str` - Database file path
- `db_agent: DatabaseAgent` - Database agent instance

### EnhancedPipeline Class

#### Methods

- `process_document(pdf_path: str) -> dict`
  - Complete pipeline processing
  - Returns comprehensive result with extraction, validation, and database info

- `get_database_statistics() -> dict`
  - Returns database statistics

- `list_documents() -> list`
  - Returns list of all documents in database

## Performance Considerations

### Memory Usage
- Processes PDFs page by page to minimize memory usage
- Uses efficient image preprocessing algorithms
- Implements garbage collection for large documents

### Processing Speed
- Optimized OCR configurations for speed vs accuracy balance
- Parallel processing capabilities for batch operations
- Caching mechanisms for repeated operations

### Accuracy
- Multiple OCR configurations for best results
- Confidence scoring for quality assessment
- Validation integration for data verification

## Troubleshooting

### Common Issues

1. **Tesseract Not Found**
   ```
   Error: tesseract is not installed or not in PATH
   Solution: Install Tesseract OCR and add to system PATH
   ```

2. **PDF Conversion Error**
   ```
   Error: pdf2image conversion failed
   Solution: Install poppler-utils (Linux) or poppler (macOS)
   ```

3. **Database Permission Error**
   ```
   Error: Unable to create database
   Solution: Check write permissions for database directory
   ```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test files for usage examples
3. Open an issue on the repository

## Changelog

### Version 2.0.0 (Enhanced)
- ✅ JSON output format
- ✅ Database integration with dynamic table creation
- ✅ Validation agent integration
- ✅ Hindi gibberish removal
- ✅ Advanced image preprocessing
- ✅ Confidence scoring
- ✅ Complete pipeline workflow

### Version 1.0.0 (Original)
- Basic PDF extraction
- Simple field extraction
- Basic OCR processing
