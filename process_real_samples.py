#!/usr/bin/env python3
"""
Process Real Sample Documents with Complete Pipeline
Uses actual PDF extractor, validator, and database storage
"""

import sys
import os
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import FieldValidator

class RealPDFExtractor:
    """Real PDF extractor using OCR for actual documents"""
    
    def extract_document_data(self, file_path: str) -> dict:
        """Extract data from real PDF using OCR"""
        
        try:
            # Import OCR libraries
            from pdf2image import convert_from_path
            import pytesseract
            from PIL import Image, ImageEnhance
            import cv2
            import numpy as np
            
            print(f"📄 Processing PDF: {file_path}")
            
            # Convert PDF to images
            print("🔄 Converting PDF to images...")
            images = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)
            
            if not images:
                return {
                    "status": "error",
                    "error": "Could not convert PDF to images",
                    "extracted_data": {}
                }
            
            # Process first page
            image = images[0]
            print(f"✅ Image size: {image.size}")
            
            # Enhance image for better OCR
            print("🔧 Enhancing image for OCR...")
            enhanced = ImageEnhance.Contrast(image).enhance(1.5)
            enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.2)
            
            # Extract text using OCR
            print("🔍 Extracting text with OCR...")
            text = pytesseract.image_to_string(enhanced, lang='eng')
            
            print(f"📝 Extracted text length: {len(text)} characters")
            
            # Extract fields using pattern matching
            extracted_data = self._extract_fields_from_text(text)
            
            # Determine document type
            doc_type = self._classify_document(text, extracted_data)
            
            # Calculate confidence based on fields found
            confidence = self._calculate_confidence(extracted_data)
            
            result = {
                "status": "success",
                "document_type": doc_type,
                "extraction_confidence": confidence,
                "extracted_data": extracted_data,
                "warnings": [],
                "raw_text": text[:500] + "..." if len(text) > 500 else text  # First 500 chars for debugging
            }
            
            print(f"✅ Extraction completed - Found {len(extracted_data)} fields")
            return result
            
        except ImportError as e:
            print(f"❌ Missing dependencies: {e}")
            return {
                "status": "error", 
                "error": f"Missing dependencies: {e}",
                "extracted_data": {}
            }
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "extracted_data": {}
            }
    
    def _extract_fields_from_text(self, text: str) -> dict:
        """Extract specific fields from OCR text using patterns"""
        
        extracted = {}
        
        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # Remove extra spaces
        
        print(f"🔍 Searching for patterns in text...")
        
        # Aadhaar Number patterns
        aadhaar_patterns = [
            r'\b\d{4}\s*\d{4}\s*\d{4}\b',  # 1234 5678 9012
            r'\b\d{12}\b',  # 123456789012
            r'\b\d{4}-\d{4}-\d{4}\b',  # 1234-5678-9012
        ]
        
        for pattern in aadhaar_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Clean the match
                aadhaar = re.sub(r'[^\d]', '', matches[0])
                if len(aadhaar) == 12:
                    extracted["Aadhaar Number"] = aadhaar
                    print(f"✅ Found Aadhaar: {aadhaar}")
                    break
        
        # Name patterns - look for patterns after common keywords
        name_keywords = ['Name', 'NAME', 'नाम']
        for keyword in name_keywords:
            pattern = rf'{keyword}[:\s]*([A-Za-z\s]+?)(?:\s+(?:DOB|Date|Gender|Male|Female|M|F|\d))'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                name = matches[0].strip()
                if len(name) > 2 and len(name) < 50:
                    extracted["Name"] = name
                    print(f"✅ Found Name: {name}")
                    break
        
        # DOB patterns
        dob_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b',  # DD Month YYYY
        ]
        
        for pattern in dob_patterns:
            matches = re.findall(pattern, text)
            if matches:
                extracted["DOB"] = matches[0]
                print(f"✅ Found DOB: {matches[0]}")
                break
        
        # Gender patterns
        gender_patterns = [
            r'\b(Male|Female|M|F)\b',
            r'\b(MALE|FEMALE)\b'
        ]
        
        for pattern in gender_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                gender = matches[0].upper()
                if gender in ['MALE', 'M']:
                    extracted["Gender"] = "M"
                elif gender in ['FEMALE', 'F']:
                    extracted["Gender"] = "F"
                print(f"✅ Found Gender: {extracted.get('Gender', gender)}")
                break
        
        # Address - look for longer text segments
        # This is more complex, let's look for patterns after address keywords
        address_keywords = ['Address', 'ADDRESS', 'पता']
        for keyword in address_keywords:
            pattern = rf'{keyword}[:\s]*([A-Za-z0-9\s,.-]+?)(?:(?:PIN|Pincode|Date|DOB|\d{{6}})|\Z)'
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                address = matches[0].strip()
                if len(address) > 10 and len(address) < 200:
                    extracted["Address"] = address
                    print(f"✅ Found Address: {address[:50]}...")
                    break
        
        return extracted
    
    def _classify_document(self, text: str, extracted_data: dict) -> str:
        """Classify document type based on content"""
        
        text_lower = text.lower()
        
        if 'aadhaar' in text_lower or 'आधार' in text_lower or 'Aadhaar Number' in extracted_data:
            return "AADHAAR"
        elif 'pan' in text_lower or 'permanent account number' in text_lower:
            return "PAN"
        else:
            return "UNKNOWN"
    
    def _calculate_confidence(self, extracted_data: dict) -> float:
        """Calculate extraction confidence based on fields found"""
        
        expected_fields = ['Aadhaar Number', 'Name', 'DOB', 'Gender', 'Address']
        found_fields = len([f for f in expected_fields if f in extracted_data and extracted_data[f]])
        
        return found_fields / len(expected_fields)

class RealPipelineProcessor:
    """Pipeline processor using real PDF extraction"""
    
    def __init__(self, db_path: str = "real_documents.db"):
        self.db_path = db_path
        self.pdf_extractor = RealPDFExtractor()
        self._init_persistent_database()
    
    def _init_persistent_database(self):
        """Initialize persistent database"""
        print("🗄️ Initializing persistent database for real documents...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            documents_exists = cursor.fetchone() is not None
            
            if documents_exists:
                print("✅ Database tables already exist - using existing structure")
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                print(f"📊 Existing records: {doc_count} documents")
            else:
                print("🔧 Creating new database tables...")
                
                # Documents table
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
                        raw_text_preview TEXT,
                        processed_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Validation results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS validation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER NOT NULL,
                        aadhaar_number TEXT,
                        aadhaar_valid BOOLEAN,
                        aadhaar_reason TEXT,
                        aadhaar_type TEXT,
                        name TEXT,
                        name_valid BOOLEAN,
                        name_reason TEXT,
                        name_length INTEGER,
                        dob TEXT,
                        dob_valid BOOLEAN,
                        dob_reason TEXT,
                        dob_parsed_date TEXT,
                        gender TEXT,
                        gender_valid BOOLEAN,
                        gender_reason TEXT,
                        address TEXT,
                        address_valid BOOLEAN,
                        address_reason TEXT,
                        address_length INTEGER,
                        validation_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                ''')
                
                conn.commit()
                print("✅ Database tables created successfully")
    
    def process_document(self, file_path: str, show_details: bool = True) -> dict:
        """Process real document through complete pipeline"""
        
        start_time = datetime.now()
        
        if show_details:
            print(f"\n{'='*100}")
            print(f"🔄 PROCESSING REAL DOCUMENT: {file_path}")
            print(f"{'='*100}")
        
        try:
            # Step 1: Extract fields using real OCR
            if show_details:
                print(f"\n1. 📄 EXTRACTOR AGENT - OCR Processing")
                print("-" * 80)
            
            extraction_result = self.pdf_extractor.extract_document_data(file_path)
            
            if extraction_result["status"] != "success":
                return {
                    "status": "extraction_failed",
                    "error": extraction_result.get("error", "Unknown error"),
                    "file_path": file_path
                }
            
            if show_details:
                print(f"📊 Extraction Confidence: {extraction_result['extraction_confidence']:.2f}")
                print(f"🏷️ Document Type: {extraction_result['document_type']}")
                print("📋 Extracted Fields:")
                for field, value in extraction_result["extracted_data"].items():
                    print(f"  • {field}: {value}")
            
            # Step 2: Validate extracted fields
            if show_details:
                print(f"\n2. 🔍 VALIDATOR AGENT - Field Validation")
                print("-" * 80)
            
            validation_result = self._validate_extracted_fields(extraction_result)
            
            if show_details:
                print(f"📊 Overall Validation Score: {validation_result['overall_score']:.2f}")
                print(f"🎯 Validation Status: {validation_result['validation_status'].upper()}")
                print(f"⚠️ Errors: {len(validation_result['errors'])}")
                print("🔍 Field Validation Results:")
                for field_name, field_data in validation_result["validation_details"].items():
                    status = "✅ VALID" if field_data.get('valid', False) else "❌ INVALID"
                    reason = field_data.get('reason', 'N/A')
                    print(f"  • {field_name}: {status} ({reason})")
            
            # Step 3: Store in database
            if show_details:
                print(f"\n3. 🗄️ DATABASE AGENT - Storing Results")
                print("-" * 80)
            
            database_result = self._store_results(file_path, extraction_result, validation_result)
            
            if show_details:
                print(f"✅ Document stored with ID: {database_result.get('document_id')}")
                
                total_time = (datetime.now() - start_time).total_seconds() * 1000
                print(f"\n4. ✅ PROCESSING COMPLETED")
                print("-" * 80)
                print(f"⏱️ Total Processing Time: {total_time:.1f}ms")
                print(f"🆔 Document ID: {database_result.get('document_id')}")
                print(f"📊 Final Status: {validation_result['validation_status'].upper()}")
            
            return {
                "status": "success",
                "document_id": database_result.get("document_id"),
                "validation_result": validation_result,
                "extraction_result": extraction_result,
                "processing_time_ms": total_time
            }
            
        except Exception as e:
            if show_details:
                print(f"❌ Processing failed: {e}")
            
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    def _validate_extracted_fields(self, extraction_result: dict) -> dict:
        """Validate extracted fields using FieldValidator"""
        
        extracted_data = extraction_result.get("extracted_data", {})
        validation_details = {}
        
        # Validate each extracted field
        for field_name, field_value in extracted_data.items():
            if field_name == "Aadhaar Number":
                validation_details[field_name] = FieldValidator.validate_aadhaar_number(field_value)
            elif field_name == "Name":
                validation_details[field_name] = FieldValidator.validate_name(field_value)
            elif field_name == "DOB":
                validation_details[field_name] = FieldValidator.validate_date(field_value)
            elif field_name == "Gender":
                validation_details[field_name] = FieldValidator.validate_gender(field_value)
            elif field_name == "Address":
                validation_details[field_name] = FieldValidator.validate_address(field_value)
            else:
                validation_details[field_name] = {
                    "valid": bool(field_value and str(field_value).strip()),
                    "type": "generic",
                    "reason": "present" if field_value else "missing"
                }
        
        # Calculate overall score
        valid_fields = sum(1 for result in validation_details.values() if result.get('valid', False))
        total_fields = len(validation_details)
        overall_score = valid_fields / total_fields if total_fields > 0 else 0.0
        
        # Collect errors
        errors = []
        for field_name, field_result in validation_details.items():
            if not field_result.get('valid', False):
                errors.append(f"{field_name}: {field_result.get('reason', 'invalid')}")
        
        return {
            "validation_status": "passed" if len(errors) == 0 else "failed",
            "document_type": extraction_result.get("document_type", "UNKNOWN"),
            "validation_details": validation_details,
            "errors": errors,
            "warnings": extraction_result.get("warnings", []),
            "overall_score": overall_score,
            "extracted_data": extracted_data,
            "is_valid": len(errors) == 0,
            "extraction_confidence": extraction_result.get("extraction_confidence", 0.0)
        }
    
    def _store_results(self, file_path: str, extraction_result: dict, validation_result: dict) -> dict:
        """Store results in database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into documents table
                cursor.execute('''
                    INSERT INTO documents (
                        file_path, document_type, extraction_confidence,
                        validation_status, is_valid, overall_score,
                        error_count, warning_count, extracted_data,
                        validation_errors, validation_warnings, raw_text_preview
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(validation_result["warnings"]),
                    extraction_result.get("raw_text", "")[:500]
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
                        address, address_valid, address_reason, address_length
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    extracted_data.get("DOB", ""),
                    validation_details.get("DOB", {}).get("valid", False),
                    validation_details.get("DOB", {}).get("reason", "N/A"),
                    validation_details.get("DOB", {}).get("parsed_date", ""),
                    # Gender
                    extracted_data.get("Gender", ""),
                    validation_details.get("Gender", {}).get("valid", False),
                    validation_details.get("Gender", {}).get("reason", "N/A"),
                    # Address
                    extracted_data.get("Address", ""),
                    validation_details.get("Address", {}).get("valid", False),
                    validation_details.get("Address", {}).get("reason", "N/A"),
                    validation_details.get("Address", {}).get("length", 0)
                ))
                
                conn.commit()
                
                return {
                    "status": "success",
                    "document_id": document_id
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_database_summary(self) -> dict:
        """Get database summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM documents")
                total_docs = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM documents WHERE is_valid = 1")
                valid_docs = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(overall_score), AVG(extraction_confidence) FROM documents")
                avg_scores = cursor.fetchone()
                
                cursor.execute('''
                    SELECT file_path, validation_status, overall_score, extraction_confidence, processed_at 
                    FROM documents 
                    ORDER BY processed_at DESC
                ''')
                all_docs = cursor.fetchall()
                
                return {
                    "total_documents": total_docs,
                    "valid_documents": valid_docs,
                    "invalid_documents": total_docs - valid_docs,
                    "average_validation_score": round(avg_scores[0] or 0, 3),
                    "average_extraction_confidence": round(avg_scores[1] or 0, 3),
                    "all_documents": [
                        {
                            "file": doc[0], "status": doc[1], "val_score": doc[2], 
                            "ext_confidence": doc[3], "processed": doc[4]
                        } for doc in all_docs
                    ]
                }
        except Exception as e:
            return {"error": str(e)}

def process_sample_documents():
    """Process the actual sample documents"""
    
    print("🚀 PROCESSING REAL SAMPLE DOCUMENTS")
    print("=" * 100)
    print("Using: Real OCR → Field Validation → Persistent Database")
    print("=" * 100)
    
    # Initialize processor
    processor = RealPipelineProcessor()
    
    # Find sample documents
    sample_dir = "sample_documents"
    sample_files = []
    
    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if file.lower().endswith('.pdf'):
                sample_files.append(os.path.join(sample_dir, file))
    
    if not sample_files:
        print("❌ No PDF files found in sample_documents directory")
        return
    
    print(f"📁 Found {len(sample_files)} sample documents:")
    for file in sample_files:
        print(f"  • {file}")
    
    # Process each document
    results = []
    for i, file_path in enumerate(sample_files, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING DOCUMENT {i}/{len(sample_files)}: {os.path.basename(file_path)}")
        print(f"{'='*80}")
        
        result = processor.process_document(file_path, show_details=True)
        results.append(result)
        
        if result["status"] == "success":
            print(f"✅ Successfully processed {os.path.basename(file_path)}")
        else:
            print(f"❌ Failed to process {os.path.basename(file_path)}: {result.get('error', 'Unknown error')}")
    
    # Show final summary
    print(f"\n{'='*100}")
    print("📊 FINAL PROCESSING SUMMARY")
    print(f"{'='*100}")
    
    summary = processor.get_database_summary()
    if "error" not in summary:
        print(f"📄 Total Documents Processed: {summary['total_documents']}")
        print(f"✅ Valid Documents: {summary['valid_documents']}")
        print(f"❌ Invalid Documents: {summary['invalid_documents']}")
        print(f"📊 Average Validation Score: {summary['average_validation_score']:.3f}")
        print(f"🎯 Average Extraction Confidence: {summary['average_extraction_confidence']:.3f}")
        
        print(f"\n📋 Document Details:")
        for doc in summary['all_documents']:
            status_icon = "✅" if doc['status'] == 'passed' else "❌"
            print(f"  {status_icon} {os.path.basename(doc['file'])}: Val={doc['val_score']:.2f}, Ext={doc['ext_confidence']:.2f}")
    
    print(f"\n💾 Database: {processor.db_path}")
    print("🔍 All extraction and validation data stored persistently!")

if __name__ == "__main__":
    process_sample_documents()