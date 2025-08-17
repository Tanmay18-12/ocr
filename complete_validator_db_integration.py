#!/usr/bin/env python3
"""
Complete Validator to Database Integration Demo
Shows exactly how validator JSON output is stored in database
(No OpenAI API key required)
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

class SimpleValidatorToDatabase:
    """Simple validator to database integration without OpenAI dependency"""
    
    def __init__(self, db_path: str = "validator_demo.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    overall_score REAL,
                    extracted_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Dynamic validation results table
            # This table structure is created based on validator JSON output
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    aadhaar_number_valid BOOLEAN,
                    aadhaar_number_reason TEXT,
                    name_valid BOOLEAN,
                    name_reason TEXT,
                    dob_valid BOOLEAN,
                    dob_reason TEXT,
                    gender_valid BOOLEAN,
                    gender_reason TEXT,
                    address_valid BOOLEAN,
                    address_reason TEXT,
                    validation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            ''')
            
            conn.commit()
            print("✅ Database initialized successfully")
    
    def process_and_store_document(self, extraction_data: dict, file_path: str = "sample_document.pdf"):
        """Process document through validator and store in database"""
        
        print(f"\n{'='*80}")
        print("🔄 COMPLETE VALIDATOR TO DATABASE WORKFLOW")
        print(f"{'='*80}")
        
        # Step 1: Show input extraction data
        print(f"\n1. 📄 INPUT EXTRACTION DATA")
        print("-" * 60)
        print("Sample data from PDFExtractorTool:")
        print(json.dumps(extraction_data, indent=2))
        
        # Step 2: Run validator agent
        print(f"\n2. 🔍 VALIDATOR AGENT PROCESSING")
        print("-" * 60)
        
        validation_details = {}
        extracted_data = extraction_data["extracted_data"]
        
        # Validate each field
        validation_details["Aadhaar Number"] = FieldValidator.validate_aadhaar_number(
            extracted_data["Aadhaar Number"]
        )
        validation_details["Name"] = FieldValidator.validate_name(
            extracted_data["Name"]
        )
        validation_details["DOB"] = FieldValidator.validate_date(
            extracted_data["DOB"]
        )
        validation_details["Gender"] = FieldValidator.validate_gender(
            extracted_data["Gender"]
        )
        validation_details["Address"] = FieldValidator.validate_address(
            extracted_data["Address"]
        )
        
        # Calculate overall score
        valid_fields = sum(1 for result in validation_details.values() if result.get('valid', False))
        total_fields = len(validation_details)
        overall_score = valid_fields / total_fields if total_fields > 0 else 0.0
        
        # Create complete validator JSON output
        validator_json_output = {
            "validation_status": "passed" if valid_fields == total_fields else "failed",
            "document_type": extraction_data["document_type"],
            "validation_details": validation_details,
            "errors": [],
            "warnings": [],
            "overall_score": overall_score,
            "extracted_data": extracted_data,
            "is_valid": valid_fields == total_fields
        }
        
        # Add errors
        for field_name, field_result in validation_details.items():
            if not field_result.get('valid', False):
                validator_json_output["errors"].append(f"{field_name}: {field_result.get('reason', 'invalid')}")
        
        print("Validator Agent JSON Output:")
        print(json.dumps(validator_json_output, indent=2))
        
        # Step 3: Store in database
        print(f"\n3. 🗄️ DATABASE AGENT PROCESSING")
        print("-" * 60)
        
        document_id = self._store_in_database(validator_json_output, file_path)
        
        print(f"✅ Document stored with ID: {document_id}")
        
        # Step 4: Show database content
        print(f"\n4. 📊 DATABASE CONTENT VERIFICATION")
        print("-" * 60)
        
        self._show_database_content(document_id)
        
        return document_id
    
    def _store_in_database(self, validator_output: dict, file_path: str) -> int:
        """Store validator output in database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert into documents table
            cursor.execute('''
                INSERT INTO documents (
                    file_path, document_type, validation_status, 
                    is_valid, overall_score, extracted_data
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                validator_output["document_type"],
                validator_output["validation_status"],
                validator_output["is_valid"],
                validator_output["overall_score"],
                json.dumps(validator_output["extracted_data"])
            ))
            
            document_id = cursor.lastrowid
            
            # Insert into validation_results table
            # Extract validation details for each field
            validation_details = validator_output["validation_details"]
            
            cursor.execute('''
                INSERT INTO validation_results (
                    document_id,
                    aadhaar_number_valid, aadhaar_number_reason,
                    name_valid, name_reason,
                    dob_valid, dob_reason,
                    gender_valid, gender_reason,
                    address_valid, address_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                document_id,
                validation_details.get("Aadhaar Number", {}).get("valid", False),
                validation_details.get("Aadhaar Number", {}).get("reason", "N/A"),
                validation_details.get("Name", {}).get("valid", False),
                validation_details.get("Name", {}).get("reason", "N/A"),
                validation_details.get("DOB", {}).get("valid", False),
                validation_details.get("DOB", {}).get("reason", "N/A"),
                validation_details.get("Gender", {}).get("valid", False),
                validation_details.get("Gender", {}).get("reason", "N/A"),
                validation_details.get("Address", {}).get("valid", False),
                validation_details.get("Address", {}).get("reason", "N/A")
            ))
            
            conn.commit()
            
            print("✅ Data stored in both 'documents' and 'validation_results' tables")
            return document_id
    
    def _show_database_content(self, document_id: int):
        """Show the actual database content"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Show documents table content
            print("📋 DOCUMENTS Table:")
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            doc_row = cursor.fetchone()
            
            if doc_row:
                print(f"  ID: {doc_row[0]}")
                print(f"  File Path: {doc_row[1]}")
                print(f"  Document Type: {doc_row[2]}")
                print(f"  Validation Status: {doc_row[3]}")
                print(f"  Is Valid: {doc_row[4]}")
                print(f"  Overall Score: {doc_row[5]}")
                print(f"  Extracted Data: {doc_row[6]}")
                print(f"  Created At: {doc_row[7]}")
            
            # Show validation_results table content
            print("\n📊 VALIDATION_RESULTS Table:")
            cursor.execute("SELECT * FROM validation_results WHERE document_id = ?", (document_id,))
            val_row = cursor.fetchone()
            
            if val_row:
                print(f"  ID: {val_row[0]}")
                print(f"  Document ID: {val_row[1]}")
                print(f"  Aadhaar Valid: {val_row[2]} (Reason: {val_row[3]})")
                print(f"  Name Valid: {val_row[4]} (Reason: {val_row[5]})")
                print(f"  DOB Valid: {val_row[6]} (Reason: {val_row[7]})")
                print(f"  Gender Valid: {val_row[8]} (Reason: {val_row[9]})")
                print(f"  Address Valid: {val_row[10]} (Reason: {val_row[11]})")
                print(f"  Validation Timestamp: {val_row[12]}")

def demonstrate_database_logic():
    """Explain the database logic clearly"""
    
    print(f"\n{'='*80}")
    print("💡 DATABASE LOGIC EXPLANATION")
    print(f"{'='*80}")
    
    print("""
🎯 KEY CONCEPT: Smart Table Reuse (Not Creating New Tables Every Time)

1. 📋 FIXED SCHEMA APPROACH:
   - The 'validation_results' table has a FIXED schema
   - Columns are predefined based on common document fields:
     * aadhaar_number_valid, aadhaar_number_reason
     * name_valid, name_reason  
     * dob_valid, dob_reason
     * gender_valid, gender_reason
     * address_valid, address_reason
   
   ✅ ADVANTAGE: Same table is reused for all documents
   ✅ NO new table creation for each document
   ✅ Easy querying and reporting

2. 🔄 WORKFLOW:
   Validator Agent → JSON Output → Database Agent → Store in EXISTING table
   
   The JSON structure from validator:
   {
     "validation_details": {
       "Aadhaar Number": {"valid": true, "reason": "valid format"},
       "Name": {"valid": true, "reason": "valid name"},
       ...
     }
   }
   
   Maps to database columns:
   - "Aadhaar Number" → aadhaar_number_valid, aadhaar_number_reason
   - "Name" → name_valid, name_reason
   - etc.

3. 🗄️ TABLE STRUCTURE:
   documents table: Main document info
   validation_results table: Detailed field validation results
   
   One document can have one validation_results record
   (1:1 relationship via document_id foreign key)

4. 🚀 WHY THIS APPROACH:
   ❌ BAD: Creating validation_results_20241201, validation_results_20241202...
   ✅ GOOD: Single validation_results table with all data
   
   Benefits:
   - Consistent schema
   - Easy aggregation queries
   - Better performance
   - Simpler maintenance
""")

def run_complete_demo():
    """Run the complete demonstration"""
    
    # Explain the logic first
    demonstrate_database_logic()
    
    # Initialize the database system
    db_system = SimpleValidatorToDatabase()
    
    # Demo 1: Valid document
    print(f"\n{'='*80}")
    print("📋 DEMO 1: VALID DOCUMENT")
    print(f"{'='*80}")
    
    valid_extraction = {
        "status": "success",
        "document_type": "AADHAAR",
        "extraction_confidence": 0.95,
        "extracted_data": {
            "Aadhaar Number": "123456789012",
            "Name": "John Doe",
            "DOB": "15/03/1990",
            "Gender": "M",
            "Address": "123 Main Street, City, State 12345"
        },
        "warnings": []
    }
    
    doc1_id = db_system.process_and_store_document(valid_extraction, "valid_aadhaar.pdf")
    
    # Demo 2: Invalid document
    print(f"\n{'='*80}")
    print("📋 DEMO 2: INVALID DOCUMENT")
    print(f"{'='*80}")
    
    invalid_extraction = {
        "status": "success",
        "document_type": "AADHAAR",
        "extraction_confidence": 0.80,
        "extracted_data": {
            "Aadhaar Number": "12345678901",  # 11 digits (invalid)
            "Name": "John123",  # Contains numbers (invalid)
            "DOB": "32/13/1990",  # Invalid date
            "Gender": "X",  # Invalid gender
            "Address": "Short"  # Too short (invalid)
        },
        "warnings": []
    }
    
    doc2_id = db_system.process_and_store_document(invalid_extraction, "invalid_aadhaar.pdf")
    
    # Show database summary
    print(f"\n{'='*80}")
    print("📊 FINAL DATABASE SUMMARY")
    print(f"{'='*80}")
    
    with sqlite3.connect(db_system.db_path) as conn:
        cursor = conn.cursor()
        
        # Show all documents
        cursor.execute("SELECT id, file_path, validation_status, is_valid, overall_score FROM documents")
        docs = cursor.fetchall()
        
        print("📋 All Documents:")
        for doc in docs:
            status = "✅ VALID" if doc[3] else "❌ INVALID"
            print(f"  ID {doc[0]}: {doc[1]} - {status} (Score: {doc[4]:.2f})")
        
        # Show validation statistics
        cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 1")
        valid_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 0")
        invalid_count = cursor.fetchone()[0]
        
        print(f"\n📊 Validation Statistics:")
        print(f"  Valid Documents: {valid_count}")
        print(f"  Invalid Documents: {invalid_count}")
        print(f"  Total Documents: {valid_count + invalid_count}")
    
    print(f"\n✅ Database file created: {db_system.db_path}")
    print("   You can inspect it using SQLite browser or command line tools")

if __name__ == "__main__":
    run_complete_demo()