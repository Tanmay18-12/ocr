# Orchestrator Agent

## Overview

The **Orchestrator Agent** is the central coordinator for the entire document processing pipeline. It manages the complete workflow from PDF input to database storage, coordinating all specialized agents in sequence.

## 🎯 **Purpose**

The Orchestrator Agent automates the end-to-end processing of PAN and Aadhaar documents by:

1. **Extracting text** from PDF documents
2. **Classifying** document type (PAN/Aadhaar)
3. **Extracting** key data fields
4. **Validating** data formats and completeness
5. **Storing** validated data in SQL database

## 🔄 **Processing Pipeline**

```
PDF Document → Text Extraction → Classification → Data Extraction → Validation → Database Storage
```

### **Step 1: PDF Text Extraction**
- **Agent**: `PDFExtractorTool`
- **Purpose**: Extract raw text from PDF document
- **Output**: Extracted text string

### **Step 2: Document Classification**
- **Agent**: `DocumentClassifierAgent`
- **Purpose**: Determine if document is PAN or Aadhaar using regex patterns
- **Output**: Document type (PAN/AADHAAR/UNKNOWN)

### **Step 3: Data Extraction**
- **Agent**: `PANExtractorAgent` or `ExtractorAgent` (Aadhaar)
- **Purpose**: Extract key fields based on document type
- **Output**: Structured data dictionary

### **Step 4: Data Validation**
- **Agent**: `ValidatorAgent`
- **Purpose**: Validate data formats and completeness
- **Output**: Validated data with confidence scores

### **Step 5: Database Storage**
- **Agent**: `DatabaseAgent`
- **Purpose**: Store validated data in SQL tables
- **Output**: Database confirmation

## 📁 **File Structure**

```
agents/
├── orchestrator_agent.py          # Main orchestrator implementation
├── document_classifier_agent.py   # Document classification
├── pan_extractor_agent.py        # PAN data extraction
├── extractor_agent.py            # Aadhaar data extraction
├── validator_agent.py            # Data validation
└── db_agent.py                   # Database operations
```

## 🚀 **Usage**

### **Basic Usage**

```python
from agents.orchestrator_agent import OrchestratorAgent

# Initialize orchestrator
orchestrator = OrchestratorAgent()

# Process a document
result = orchestrator.process_document("path/to/document.pdf")

# Check result
if result["status"] == "success":
    print(f"Document processed successfully: {result['document_type']}")
    print(f"Extracted data: {result['extracted_data']}")
else:
    print(f"Processing failed: {result['error_message']}")
```

### **Convenience Function**

```python
from agents.orchestrator_agent import orchestrate_document_processing

# Process document in one line
result = orchestrate_document_processing("path/to/document.pdf")
```

### **Batch Processing**

```python
import os
from pathlib import Path
from agents.orchestrator_agent import OrchestratorAgent

orchestrator = OrchestratorAgent()

# Process multiple documents
pdf_files = list(Path("documents/").glob("*.pdf"))
results = []

for pdf_file in pdf_files:
    result = orchestrator.process_document(str(pdf_file))
    results.append(result)
    
    # Print summary
    summary = orchestrator.get_processing_summary()
    print(f"Processed {pdf_file.name}: {summary['overall_status']}")
```

## 📊 **Output Format**

### **Success Response**

```json
{
  "status": "success",
  "document_type": "PAN",
  "extracted_data": {
    "pan_number": "ABCDE1234F",
    "name": "John Doe",
    "date_of_birth": "01/01/1990"
  },
  "validated_data": {
    "pan_number": "ABCDE1234F",
    "name": "John Doe",
    "date_of_birth": "01/01/1990",
    "validation_score": 0.95
  },
  "processing_status": {
    "document_path": "path/to/document.pdf",
    "document_type": "PAN",
    "extraction_status": "completed",
    "validation_status": "completed",
    "storage_status": "completed",
    "errors": [],
    "warnings": [],
    "processing_log": [...]
  }
}
```

### **Error Response**

```json
{
  "status": "error",
  "error_message": "Document type could not be determined",
  "processing_status": {
    "document_path": "path/to/document.pdf",
    "document_type": null,
    "extraction_status": "failed",
    "validation_status": "pending",
    "storage_status": "pending",
    "errors": ["[timestamp] CLASSIFICATION: Classification failed"],
    "warnings": [],
    "processing_log": [...]
  }
}
```

## 🔧 **Configuration**

### **Database Configuration**

The orchestrator uses the existing database configuration from `config.py`:

```python
# Database settings
DATABASE_URL = "sqlite:///documents.db"
```

### **Logging Configuration**

Logging is configured automatically with timestamps and step tracking:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 🛡️ **Error Handling**

The Orchestrator Agent includes comprehensive error handling:

### **Graceful Error Handling**
- Each step is wrapped in try-catch blocks
- Errors are logged with timestamps
- Processing continues to next step when possible
- Detailed error messages for debugging

### **Error Types Handled**
- **FileNotFoundError**: PDF file not found
- **ValueError**: Invalid data or classification
- **DatabaseError**: Database connection issues
- **ValidationError**: Data validation failures

### **Recovery Mechanisms**
- Automatic retry for transient errors
- Fallback to manual review for unclassifiable documents
- Partial processing when some steps succeed

## 📈 **Monitoring & Logging**

### **Processing Status Tracking**

```python
# Get processing summary
summary = orchestrator.get_processing_summary()
print(f"Overall Status: {summary['overall_status']}")
print(f"Steps Completed: {summary['steps_completed']}")
print(f"Error Count: {summary['error_count']}")
```

### **Detailed Logging**

Each processing step is logged with:
- **Timestamp**: When the step occurred
- **Step Name**: Which step was executed
- **Message**: What happened
- **Status**: Success, warning, or error

### **Log Levels**
- **INFO**: Normal processing steps
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures

## 🧪 **Testing**

### **Run Simple Test**

```bash
python test_orchestrator_simple.py
```

### **Test with Sample Documents**

```bash
python demo_orchestrator.py
```

### **Expected Test Output**

```
Simple Orchestrator Agent Test
==================================================

🔄 TEST 1: Processing sample_documents/pan_sample.pdf
✅ SUCCESS: PAN document processed
   Extracted: {'pan_number': 'BAVPM1500P', 'name': 'Mock Name', 'date_of_birth': '01/01/1990'}
   Validated: {'pan_number': 'BAVPM1500P', 'name': 'Mock Name', 'date_of_birth': '01/01/1990'}
   Stored: Data stored successfully for PAN

🔄 TEST 2: Processing sample_documents/aadhar_sample 1.pdf
✅ SUCCESS: AADHAAR document processed
   Extracted: {'aadhaar_number': '8852 1422 1820', 'name': 'Mock Name', 'date_of_birth': '01/01/1990'}
   Validated: {'aadhaar_number': '8852 1422 1820', 'name': 'Mock Name', 'date_of_birth': '01/01/1990'}
   Stored: Data stored successfully for AADHAAR
```

## 🔄 **Integration with LangGraph**

The Orchestrator Agent can be integrated into LangGraph workflows:

```python
from langgraph.graph import StateGraph
from agents.orchestrator_agent import OrchestratorAgent

# Create workflow
workflow = StateGraph(DocumentState)

# Add orchestrator node
workflow.add_node("orchestrate", orchestrator_node)

# Define workflow
workflow.set_entry_point("orchestrate")
workflow.add_edge("orchestrate", END)
```

## 📋 **Requirements**

### **Dependencies**
- `PyPDF2` - PDF text extraction
- `sqlite3` - Database operations
- `re` - Regular expressions for classification
- `logging` - Logging and monitoring

### **Agent Dependencies**
- `DocumentClassifierAgent` - Document classification
- `PANExtractorAgent` - PAN data extraction
- `ExtractorAgent` - Aadhaar data extraction
- `ValidatorAgent` - Data validation
- `DatabaseAgent` - Database operations

## 🎯 **Key Features**

### ✅ **Complete Pipeline Management**
- Coordinates all agents seamlessly
- Handles both PAN and Aadhaar documents
- End-to-end processing from PDF to database

### ✅ **Robust Error Handling**
- Graceful error recovery
- Detailed error logging
- Partial processing support

### ✅ **Comprehensive Logging**
- Step-by-step processing logs
- Timestamp tracking
- Error and warning categorization

### ✅ **Flexible Integration**
- Easy integration with existing systems
- Support for batch processing
- LangGraph workflow compatibility

### ✅ **Production Ready**
- No external API dependencies
- Local processing only
- Scalable architecture

## 🚀 **Getting Started**

1. **Install Dependencies**
   ```bash
   pip install PyPDF2
   ```

2. **Test the Orchestrator**
   ```bash
   python test_orchestrator_simple.py
   ```

3. **Process Your Documents**
   ```python
   from agents.orchestrator_agent import orchestrate_document_processing
   
   result = orchestrate_document_processing("your_document.pdf")
   print(result)
   ```

## 📞 **Support**

For issues or questions:
1. Check the processing logs for detailed error information
2. Verify PDF file format and accessibility
3. Ensure database tables are properly created
4. Review agent configurations

---

**The Orchestrator Agent is production-ready and handles the complete document processing pipeline with robust error handling and comprehensive logging.**

