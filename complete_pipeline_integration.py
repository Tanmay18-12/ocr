#!/usr/bin/env python3
"""
Complete Pipeline Integration: Extractor Agent → Validator Agent → Database Agent
- Uses actual PDF extractor for field extraction
- Validates all extracted fields
- Stores in persistent database (doesn't recreate tables)
- No OpenAI API required for validation and database operations
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import FieldValidator
from tools.pdf_extractor_tool import PDFExtractorTool

class CompletePipelineProcessor:
    """Complete pipeline processor that handles the entire workflow"""
    
    def __init__(self, db_path: str = "ocr_documents.db"):
        self.db_path = db_path
        self.pdf_extractor = PDFExtractorTool()
        self._init_persistent_database()
    
    def _init_persistent_database(self):
        """Initialize persistent database - only creates tables if they don't exist"""
        print("🗄️ Initializing persistent database...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables already exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            documents_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='validation_results'")
            validation_exists = cursor.fetchone() is not None
            
            if documents_exists and validation_exists:
                print("✅ Database tables already exist - using existing structure")
                # Show existing record count
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM validation_results")
                val_count = cursor.fetchone()[0]
                print(f"📊 Existing records: {doc_count} documents, {val_count} validation results")
            else:
                print("🔧 Creating new database tables...")
                
                # Main documents table - stores document metadata and overall results
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        extraction_confidence REAL,
                        validation_status TEXT NOT NULL,
                        is_valid BOOLEAN NOT NULL,
                        overall_score REAL,
                        error_count INTEGER DEFAULT 0,
                        warning_count INTEGER DEFAULT 0,
                        extracted_data TEXT,
                        validation_errors TEXT,
                        validation_warnings TEXT,
                        processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(file_path, processed_at)
                    )
                ''')
                
                # Validation results table - stores field-level validation details
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS validation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER NOT NULL,
                        
                        -- Aadhaar Number validation
                        aadhaar_number TEXT,
                        aadhaar_valid BOOLEAN,
                        aadhaar_reason TEXT,
                        aadhaar_type TEXT,
                        
                        -- Name validation
                        name TEXT,
                        name_valid BOOLEAN,
                        name_reason TEXT,
                        name_length INTEGER,
                        
                        -- Date of Birth validation
                        dob TEXT,
                        dob_valid BOOLEAN,
                        dob_reason TEXT,
                        dob_parsed_date TEXT,
                        
                        -- Gender validation
                        gender TEXT,
                        gender_valid BOOLEAN,
                        gender_reason TEXT,
                        
                        -- Address validation
                        address TEXT,
                        address_valid BOOLEAN,
                        address_reason TEXT,
                        address_length INTEGER,
                        
                        -- PAN Number validation (if present)
                        pan_number TEXT,
                        pan_valid BOOLEAN,
                        pan_reason TEXT,
                        
                        validation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                ''')
                
                # Processing logs table - for audit trail
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        agent_name TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT,
                        processing_time_ms INTEGER,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                ''')
                
                conn.commit()
                print("✅ Database tables created successfully")
    
    def process_document(self, file_path: str, show_details: bool = True) -> dict:
        """
        Complete pipeline: Extract → Validate → Store
        Returns processing result summary
        """
        start_time = datetime.now()
        processing_result = {
            "file_path": file_path,
            "status": "success",
            "document_id": None,
            "extraction_result": None,
            "validation_result": None,
            "database_result": None,
            "processing_time_ms": 0,
            "errors": [],
            "warnings": []
        }
        
        try:
            if show_details:
                print(f"\n{'='*100}")
                print(f"🔄 COMPLETE PIPELINE PROCESSING: {file_path}")
                print(f"{'='*100}")
            
            # Step 1: Extract fields using PDF Extractor Agent
            if show_details:
                print(f"\n1. 📄 EXTRACTOR AGENT - Extracting fields from document")
                print("-" * 80)
            
            extraction_start = datetime.now()
            extraction_result = self.pdf_extractor.extract_document_data(file_path)
            extraction_time = (datetime.now() - extraction_start).total_seconds() * 1000
            
            processing_result["extraction_result"] = extraction_result
            
            if extraction_result["status"] != "success":
                processing_result["status"] = "extraction_failed"
                processing_result["errors"].append(f"Extraction failed: {extraction_result.get('error', 'Unknown error')}")
                return processing_result
            
            if show_details:
                print(f"✅ Extraction completed in {extraction_time:.1f}ms")
                print(f"📊 Confidence: {extraction_result.get('extraction_confidence', 0):.2f}")
                print(f"🏷️ Document Type: {extraction_result.get('document_type', 'Unknown')}")
                print("📋 Extracted Fields:")
                for field, value in extraction_result.get("extracted_data", {}).items():
                    print(f"  • {field}: {value}")
            
            # Step 2: Validate extracted fields using Validator Agent
            if show_details:
                print(f"\n2. 🔍 VALIDATOR AGENT - Validating extracted fields")
                print("-" * 80)
            
            validation_start = datetime.now()
            validation_result = self._validate_extracted_fields(extraction_result)
            validation_time = (datetime.now() - validation_start).total_seconds() * 1000
            
            processing_result["validation_result"] = validation_result
            
            if show_details:
                print(f"✅ Validation completed in {validation_time:.1f}ms")
                print(f"📊 Overall Score: {validation_result['overall_score']:.2f}")
                print(f"🎯 Status: {validation_result['validation_status'].upper()}")
                print(f"⚠️ Errors: {len(validation_result['errors'])}")
                print("🔍 Field Validation Results:")
                for field_name, field_data in validation_result["validation_details"].items():
                    status = "✅ VALID" if field_data.get('valid', False) else "❌ INVALID"
                    reason = field_data.get('reason', 'N/A')
                    print(f"  • {field_name}: {status} ({reason})")
            
            # Step 3: Store results in database using Database Agent
            if show_details:
                print(f"\n3. 🗄️ DATABASE AGENT - Storing validation results")
                print("-" * 80)
            
            database_start = datetime.now()
            database_result = self._store_results_in_database(
                file_path, extraction_result, validation_result
            )
            database_time = (datetime.now() - database_start).total_seconds() * 1000
            
            processing_result["database_result"] = database_result
            processing_result["document_id"] = database_result.get("document_id")
            
            if show_details:
                print(f"✅ Database storage completed in {database_time:.1f}ms")
                print(f"🆔 Document ID: {database_result.get('document_id')}")
                print(f"💾 Tables updated: documents, validation_results, processing_logs")
            
            # Log processing activities
            self._log_processing_activity(
                database_result.get("document_id"),
                "ExtractorAgent", "extract_fields", "success", 
                {"confidence": extraction_result.get("extraction_confidence"), "time_ms": extraction_time}
            )
            self._log_processing_activity(
                database_result.get("document_id"),
                "ValidatorAgent", "validate_fields", "success",
                {"score": validation_result["overall_score"], "time_ms": validation_time}
            )
            self._log_processing_activity(
                database_result.get("document_id"),
                "DatabaseAgent", "store_results", "success",
                {"time_ms": database_time}
            )
            
            # Calculate total processing time
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            processing_result["processing_time_ms"] = total_time
            
            if show_details:
                print(f"\n4. ✅ PIPELINE COMPLETED")
                print("-" * 80)
                print(f"⏱️ Total Processing Time: {total_time:.1f}ms")
                print(f"🆔 Document stored with ID: {database_result.get('document_id')}")
                print(f"📊 Overall Result: {validation_result['validation_status'].upper()}")
            
            return processing_result
            
        except Exception as e:
            processing_result["status"] = "error"
            processing_result["errors"].append(str(e))
            processing_result["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            
            if show_details:
                print(f"❌ Pipeline failed: {e}")
            
            return processing_result
    
    def _validate_extracted_fields(self, extraction_result: dict) -> dict:
        """Validate all extracted fields using FieldValidator"""
        
        extracted_data = extraction_result.get("extracted_data", {})
        validation_details = {}
        
        # Validate each field that was extracted
        for field_name, field_value in extracted_data.items():
            if field_name == "Aadhaar Number":
                validation_details[field_name] = FieldValidator.validate_aadhaar_number(field_value)
            elif field_name == "Name":
                validation_details[field_name] = FieldValidator.validate_name(field_value)
            elif field_name == "DOB" or field_name == "Date of Birth":
                validation_details[field_name] = FieldValidator.validate_date(field_value)
            elif field_name == "Gender":
                validation_details[field_name] = FieldValidator.validate_gender(field_value)
            elif field_name == "Address":
                validation_details[field_name] = FieldValidator.validate_address(field_value)
            elif field_name == "PAN Number" or field_name == "PAN":
                validation_details[field_name] = FieldValidator.validate_pan_number(field_value)
            else:
                # Generic validation for unknown fields
                validation_details[field_name] = {
                    "valid": bool(field_value and str(field_value).strip()),
                    "type": "generic",
                    "reason": "present" if field_value else "missing"
                }
        
        # Calculate overall validation score
        valid_fields = sum(1 for result in validation_details.values() if result.get('valid', False))
        total_fields = len(validation_details)
        overall_score = valid_fields / total_fields if total_fields > 0 else 0.0
        
        # Collect errors and warnings
        errors = []
        warnings = []
        
        for field_name, field_result in validation_details.items():
            if not field_result.get('valid', False):
                errors.append(f"{field_name}: {field_result.get('reason', 'invalid')}")
        
        # Add warnings from extraction
        warnings.extend(extraction_result.get("warnings", []))
        
        return {
            "validation_status": "passed" if len(errors) == 0 else "failed",
            "document_type": extraction_result.get("document_type", "UNKNOWN"),
            "validation_details": validation_details,
            "errors": errors,
            "warnings": warnings,
            "overall_score": overall_score,
            "extracted_data": extracted_data,
            "is_valid": len(errors) == 0,
            "extraction_confidence": extraction_result.get("extraction_confidence", 0.0)
        }
    
    def _store_results_in_database(self, file_path: str, extraction_result: dict, validation_result: dict) -> dict:
        """Store extraction and validation results in persistent database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into documents table
                cursor.execute('''
                    INSERT INTO documents (
                        file_path, document_type, extraction_confidence,
                        validation_status, is_valid, overall_score,
                        error_count, warning_count, extracted_data,
                        validation_errors, validation_warnings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_path,
                    validation_result["document_type"],
                    validation_result["extraction_confidence"],
                    validation_result["validation_status"],
                    validation_result["is_valid"],
                    validation_result["overall_score"],
                    len(validation_result["errors"]),
                    len(validation_result["warnings"]),
                    json.dumps(validation_result["extracted_data"]),
                    json.dumps(validation_result["errors"]),
                    json.dumps(validation_result["warnings"])
                ))
                
                document_id = cursor.lastrowid
                
                # Insert into validation_results table
                validation_details = validation_result["validation_details"]
                extracted_data = validation_result["extracted_data"]
                
                cursor.execute('''
                    INSERT INTO validation_results (
                        document_id,
                        aadhaar_number, aadhaar_valid, aadhaar_reason, aadhaar_type,
                        name, name_valid, name_reason, name_length,
                        dob, dob_valid, dob_reason, dob_parsed_date,
                        gender, gender_valid, gender_reason,
                        address, address_valid, address_reason, address_length,
                        pan_number, pan_valid, pan_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    # Aadhaar
                    extracted_data.get("Aadhaar Number", ""),
                    validation_details.get("Aadhaar Number", {}).get("valid", False),
                    validation_details.get("Aadhaar Number", {}).get("reason", "N/A"),
                    validation_details.get("Aadhaar Number", {}).get("type", "unknown"),
                    # Name
                    extracted_data.get("Name", ""),
                    validation_details.get("Name", {}).get("valid", False),
                    validation_details.get("Name", {}).get("reason", "N/A"),
                    validation_details.get("Name", {}).get("length", 0),
                    # DOB
                    extracted_data.get("DOB", extracted_data.get("Date of Birth", "")),
                    validation_details.get("DOB", validation_details.get("Date of Birth", {})).get("valid", False),
                    validation_details.get("DOB", validation_details.get("Date of Birth", {})).get("reason", "N/A"),
                    validation_details.get("DOB", validation_details.get("Date of Birth", {})).get("parsed_date", ""),
                    # Gender
                    extracted_data.get("Gender", ""),
                    validation_details.get("Gender", {}).get("valid", False),
                    validation_details.get("Gender", {}).get("reason", "N/A"),
                    # Address
                    extracted_data.get("Address", ""),
                    validation_details.get("Address", {}).get("valid", False),
                    validation_details.get("Address", {}).get("reason", "N/A"),
                    validation_details.get("Address", {}).get("length", 0),
                    # PAN
                    extracted_data.get("PAN Number", extracted_data.get("PAN", "")),
                    validation_details.get("PAN Number", validation_details.get("PAN", {})).get("valid", False),
                    validation_details.get("PAN Number", validation_details.get("PAN", {})).get("reason", "N/A")
                ))
                
                conn.commit()
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "message": "Results stored successfully in persistent database"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to store results in database"
            }
    
    def _log_processing_activity(self, document_id: int, agent_name: str, action: str, status: str, details: dict):
        """Log processing activity for audit trail"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO processing_logs (
                        document_id, agent_name, action, status, details, processing_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    document_id, agent_name, action, status,
                    json.dumps(details), details.get('time_ms', 0)
                ))
                conn.commit()
        except Exception as e:
            print(f"Warning: Failed to log processing activity: {e}")
    
    def get_database_summary(self) -> dict:
        """Get summary of all documents in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total documents
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_docs = cursor.fetchone()[0]
                
                # Valid vs invalid
                cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 1")
                valid_docs = cursor.fetchone()[0]
                invalid_docs = total_docs - valid_docs
                
                # Average scores
                cursor.execute("SELECT AVG(overall_score), AVG(extraction_confidence) FROM documents")
                avg_scores = cursor.fetchone()
                
                # Document types
                cursor.execute("SELECT document_type, COUNT(*) FROM documents GROUP BY document_type")
                doc_types = dict(cursor.fetchall())
                
                # Recent documents
                cursor.execute('''
                    SELECT id, file_path, validation_status, overall_score, processed_at 
                    FROM documents 
                    ORDER BY processed_at DESC 
                    LIMIT 5
                ''')
                recent_docs = cursor.fetchall()
                
                return {
                    "total_documents": total_docs,
                    "valid_documents": valid_docs,
                    "invalid_documents": invalid_docs,
                    "average_validation_score": round(avg_scores[0] or 0, 3),
                    "average_extraction_confidence": round(avg_scores[1] or 0, 3),
                    "document_types": doc_types,
                    "recent_documents": [
                        {
                            "id": doc[0], "file": doc[1], "status": doc[2], 
                            "score": doc[3], "processed": doc[4]
                        } for doc in recent_docs
                    ]
                }
        except Exception as e:
            return {"error": str(e)}
    
    def view_document_details(self, document_id: int) -> dict:
        """Get detailed information about a specific document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get document info
                cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
                doc_row = cursor.fetchone()
                
                if not doc_row:
                    return {"error": "Document not found"}
                
                # Get validation details
                cursor.execute("SELECT * FROM validation_results WHERE document_id = ?", (document_id,))
                val_row = cursor.fetchone()
                
                # Get processing logs
                cursor.execute('''
                    SELECT agent_name, action, status, processing_time_ms, timestamp 
                    FROM processing_logs 
                    WHERE document_id = ? 
                    ORDER BY timestamp
                ''', (document_id,))
                logs = cursor.fetchall()
                
                return {
                    "document": {
                        "id": doc_row[0],
                        "file_path": doc_row[1],
                        "document_type": doc_row[2],
                        "extraction_confidence": doc_row[3],
                        "validation_status": doc_row[4],
                        "is_valid": bool(doc_row[5]),
                        "overall_score": doc_row[6],
                        "error_count": doc_row[7],
                        "warning_count": doc_row[8],
                        "extracted_data": json.loads(doc_row[9]) if doc_row[9] else {},
                        "validation_errors": json.loads(doc_row[10]) if doc_row[10] else [],
                        "validation_warnings": json.loads(doc_row[11]) if doc_row[11] else [],
                        "processed_at": doc_row[12]
                    },
                    "validation_details": {
                        "aadhaar": {"value": val_row[2], "valid": val_row[3], "reason": val_row[4]} if val_row else {},
                        "name": {"value": val_row[6], "valid": val_row[7], "reason": val_row[8]} if val_row else {},
                        "dob": {"value": val_row[10], "valid": val_row[11], "reason": val_row[12]} if val_row else {},
                        "gender": {"value": val_row[14], "valid": val_row[15], "reason": val_row[16]} if val_row else {},
                        "address": {"value": val_row[17], "valid": val_row[18], "reason": val_row[19]} if val_row else {},
                        "pan": {"value": val_row[21], "valid": val_row[22], "reason": val_row[23]} if val_row else {}
                    },
                    "processing_logs": [
                        {
                            "agent": log[0], "action": log[1], "status": log[2],
                            "time_ms": log[3], "timestamp": log[4]
                        } for log in logs
                    ]
                }
        except Exception as e:
            return {"error": str(e)}

def demonstrate_complete_pipeline():
    """Demonstrate the complete pipeline with sample documents"""
    
    print("🚀 COMPLETE PIPELINE DEMONSTRATION")
    print("=" * 100)
    print("Pipeline: PDF Extractor Agent → Validator Agent → Database Agent")
    print("Database: Persistent storage (tables created once, reused forever)")
    print("=" * 100)
    
    # Initialize pipeline processor
    processor = CompletePipelineProcessor()
    
    # Check if we have any sample documents
    sample_files = [
        "sample_aadhaar.pdf",
        "sample_pan.pdf", 
        "test_document.pdf",
        "aadhaar_sample.pdf"
    ]
    
    # Find available sample files
    available_files = [f for f in sample_files if os.path.exists(f)]
    
    if not available_files:
        print("\n⚠️ No sample PDF files found. Creating demo with simulated extraction...")
        
        # Demo with simulated extraction data
        print("\n" + "="*80)
        print("📋 DEMO: Processing simulated document")
        print("="*80)
        
        # Simulate extraction result
        simulated_extraction = {
            "status": "success",
            "document_type": "AADHAAR",
            "extraction_confidence": 0.92,
            "extracted_data": {
                "Aadhaar Number": "234567890123",
                "Name": "Rajesh Kumar", 
                "DOB": "25/12/1985",
                "Gender": "M",
                "Address": "House No 456, Sector 12, Gurgaon, Haryana 122001"
            },
            "warnings": []
        }
        
        # Process with validator and database
        validation_result = processor._validate_extracted_fields(simulated_extraction)
        database_result = processor._store_results_in_database(
            "simulated_document.pdf", simulated_extraction, validation_result
        )
        
        print(f"✅ Document processed and stored with ID: {database_result.get('document_id')}")
        
    else:
        print(f"\n📁 Found {len(available_files)} sample files to process")
        
        for file_path in available_files[:2]:  # Process first 2 files
            print(f"\n{'='*60}")
            print(f"Processing: {file_path}")
            print(f"{'='*60}")
            
            try:
                result = processor.process_document(file_path, show_details=True)
                if result["status"] == "success":
                    print(f"✅ Successfully processed {file_path}")
                else:
                    print(f"❌ Failed to process {file_path}: {result.get('errors', [])}")
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
    
    # Show database summary
    print(f"\n{'='*100}")
    print("📊 DATABASE SUMMARY")
    print(f"{'='*100}")
    
    summary = processor.get_database_summary()
    if "error" not in summary:
        print(f"📄 Total Documents: {summary['total_documents']}")
        print(f"✅ Valid Documents: {summary['valid_documents']}")
        print(f"❌ Invalid Documents: {summary['invalid_documents']}")
        print(f"📊 Average Validation Score: {summary['average_validation_score']:.3f}")
        print(f"🎯 Average Extraction Confidence: {summary['average_extraction_confidence']:.3f}")
        print(f"📋 Document Types: {summary['document_types']}")
        
        if summary['recent_documents']:
            print(f"\n📅 Recent Documents:")
            for doc in summary['recent_documents']:
                status_icon = "✅" if doc['status'] == 'passed' else "❌"
                print(f"  {status_icon} ID {doc['id']}: {doc['file']} (Score: {doc['score']:.2f})")
    else:
        print(f"❌ Error getting summary: {summary['error']}")
    
    print(f"\n💾 Database file: {processor.db_path}")
    print("🔍 Use DB Browser for SQLite or run view_tables.py to explore the data")

if __name__ == "__main__":
    demonstrate_complete_pipeline()