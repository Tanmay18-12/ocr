#!/usr/bin/env python3
"""
Enhanced Pipeline Demo
Demonstrates the complete workflow:
1. PDF Extraction with JSON output
2. Validation using Validator Agent
3. Database storage with dynamic table creation
"""

import json
import os
from datetime import datetime
from tools.pdf_extractor_tool import PDFExtractorTool
from agents.validator_agent import ValidatorAgent
from agents.db_agent import DatabaseAgent

class EnhancedPipeline:
    """Complete pipeline for document processing"""
    
    def __init__(self, db_path: str = "enhanced_documents.db"):
        self.db_path = db_path
        self.extractor = PDFExtractorTool(db_path)
        self.validator = ValidatorAgent()
        self.db_agent = DatabaseAgent(db_path)
        
    def process_document(self, pdf_path: str) -> dict:
        """Process a document through the complete pipeline"""
        print(f"\n{'='*60}")
        print(f"PROCESSING DOCUMENT: {pdf_path}")
        print(f"{'='*60}")
        
        # Step 1: Extract data from PDF
        print("\n1. EXTRACTING DATA FROM PDF...")
        extraction_result = self.extractor._run(pdf_path)
        
        if extraction_result.get("status") == "error":
            print(f"❌ Extraction failed: {extraction_result.get('error_message')}")
            return extraction_result
        
        print("✅ Extraction completed successfully")
        print(f"Document Type: {extraction_result.get('document_type')}")
        print(f"Confidence: {extraction_result.get('extraction_confidence')}")
        
        # Display extracted fields
        extracted_data = extraction_result.get("extracted_data", {})
        print("\nExtracted Fields:")
        for field, value in extracted_data.items():
            print(f"  {field}: {value}")
        
        # Step 2: Validate extracted data
        print("\n2. VALIDATING EXTRACTED DATA...")
        validation_result = self.validator.validate(extraction_result)
        
        print(f"Validation Status: {validation_result.get('validation_status')}")
        print(f"Is Valid: {validation_result.get('is_valid')}")
        print(f"Overall Score: {validation_result.get('overall_score')}")
        
        # Display validation details
        validation_details = validation_result.get("validation_details", {})
        if validation_details:
            print("\nValidation Details:")
            for field, details in validation_details.items():
                if isinstance(details, dict):
                    status = "✅" if details.get("valid") else "❌"
                    reason = details.get("reason", "N/A")
                    print(f"  {status} {field}: {reason}")
        
        # Step 3: Store in database with dynamic table creation
        print("\n3. STORING IN DATABASE...")
        
        # Prepare data for database storage
        storage_data = {
            "file_path": pdf_path,
            "document_type": extraction_result.get("document_type", "UNKNOWN"),
            "extraction_timestamp": extraction_result.get("extraction_timestamp"),
            "validation_status": validation_result.get("validation_status", "UNKNOWN"),
            "is_valid": validation_result.get("is_valid", False),
            "overall_score": validation_result.get("overall_score", 0.0),
            "completeness_score": validation_result.get("overall_score", 0.0),
            "extracted_data": extracted_data,
            "validation_details": validation_details
        }
        
        db_result = self.db_agent.store_validation_result(storage_data)
        
        if db_result.get("status") == "success":
            print("✅ Successfully stored in database")
            print(f"Document ID: {db_result.get('document_id')}")
            if db_result.get("table_name"):
                print(f"Dynamic Table: {db_result.get('table_name')}")
        else:
            print(f"❌ Database storage failed: {db_result.get('error_message')}")
        
        # Return complete result
        return {
            "extraction": extraction_result,
            "validation": validation_result,
            "database": db_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_database_statistics(self) -> dict:
        """Get database statistics"""
        return self.db_agent.get_statistics()
    
    def list_documents(self) -> list:
        """List all documents in the database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, file_path, document_type, validation_status, 
                           is_valid, quality_score, created_at 
                    FROM documents 
                    ORDER BY created_at DESC
                """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []

def demo_single_document():
    """Demo processing a single document"""
    pipeline = EnhancedPipeline("demo_documents.db")
    
    # Test with a sample PDF (update path as needed)
    pdf_path = "sample_documents/aadhar_sample 1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please provide a valid PDF file path.")
        return
    
    # Process the document
    result = pipeline.process_document(pdf_path)
    
    # Save complete result to JSON file
    with open("pipeline_result.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Complete result saved to 'pipeline_result.json'")

def demo_database_operations():
    """Demo database operations"""
    print(f"\n{'='*60}")
    print("DATABASE OPERATIONS DEMO")
    print(f"{'='*60}")
    
    pipeline = EnhancedPipeline("demo_documents.db")
    
    # Get statistics
    print("\n📊 DATABASE STATISTICS:")
    stats = pipeline.get_database_statistics()
    print(json.dumps(stats, indent=2))
    
    # List documents
    print("\n📋 DOCUMENTS IN DATABASE:")
    documents = pipeline.list_documents()
    if documents:
        for doc in documents:
            doc_id, file_path, doc_type, status, is_valid, score, created = doc
            status_icon = "✅" if is_valid else "❌"
            print(f"  {status_icon} ID: {doc_id} | Type: {doc_type} | Status: {status} | Score: {score}")
    else:
        print("  No documents found in database")

def demo_json_output_format():
    """Demo the JSON output format"""
    print(f"\n{'='*60}")
    print("JSON OUTPUT FORMAT DEMO")
    print(f"{'='*60}")
    
    # Sample JSON output structure
    sample_output = {
        "status": "success",
        "file_path": "sample_documents/sample_aadhaar.pdf",
        "document_type": "AADHAAR",
        "extraction_timestamp": "2024-01-15T10:30:00",
        "extracted_data": {
            "Aadhaar Number": "123456789012",
            "Name": "John Doe",
            "DOB": "15/01/1990",
            "Gender": "Male",
            "Address": "123 Main Street, City, State 123456"
        },
        "raw_text": "Sample extracted text...",
        "extraction_confidence": 0.85
    }
    
    print("Sample JSON Output Structure:")
    print(json.dumps(sample_output, indent=2))

if __name__ == "__main__":
    print("🚀 ENHANCED PDF EXTRACTION PIPELINE DEMO")
    print("This demo shows the complete workflow with JSON output and database integration")
    
    # Demo JSON output format
    demo_json_output_format()
    
    # Demo single document processing
    demo_single_document()
    
    # Demo database operations
    demo_database_operations()
    
    print(f"\n{'='*60}")
    print("🎉 DEMO COMPLETED")
    print("Check the following files:")
    print("  - demo_documents.db (SQLite database)")
    print("  - pipeline_result.json (Complete result)")
    print(f"{'='*60}")
