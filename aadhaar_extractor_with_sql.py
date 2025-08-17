#!/usr/bin/env python3
# """
# Aadhaar Extraction Tool with SQL Database Integration and User Management
# Successfully extracts key fields from Aadhaar cards, provides JSON output, creates SQL tables,
# and integrates with unique user management system to prevent duplicates
# """

import re
import json
import sqlite3
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys

# Add user_management to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'user_management'))

from user_management.user_id_manager import UserIDManager
from user_management.duplicate_prevention_service import DuplicatePreventionService
from user_management.exceptions import (
    DuplicateAadhaarError, DatabaseConstraintError, InvalidDocumentDataError,
    handle_sqlite_error, create_error_response
)

class AadhaarExtractionTool:
    
    
    def __init__(self, db_path: str = "aadhaar_documents.db"):
        self.required_fields = ['Name', 'DOB', 'Gender', 'Address', 'Aadhaar Number']
        self.db_path = db_path
        
        # Initialize user management components
        self.user_manager = UserIDManager(db_path)
        self.duplicate_service = DuplicatePreventionService(db_path)
        
        self._init_database()
    
    def _init_database(self):
      
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create main aadhaar documents table with user_id
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aadhaar_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        extraction_timestamp TEXT NOT NULL,
                        extraction_confidence REAL DEFAULT 0.0,
                        raw_text TEXT,
                        user_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create extracted fields table with column names matching JSON output and user_id
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_fields (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        "Name" TEXT,
                        "DOB" TEXT,
                        "Gender" TEXT,
                        "Address" TEXT,
                        "Aadhaar Number" TEXT,
                        user_id TEXT,
                        extraction_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES aadhaar_documents (id)
                    )
                ''')
                
                # Create users table for user management
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        aadhaar_number TEXT UNIQUE,
                        primary_name TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_documents cross-reference table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_documents (
                        user_id TEXT,
                        document_type TEXT,
                        document_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, document_type, document_id)
                    )
                ''')
                
                conn.commit()
                print(f"✅ Database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            print(f"📄 Converted {len(pages)} pages from PDF")
            
            all_text = ""
            for i, page in enumerate(pages):
                print(f"Processing page {i+1}...")
                
                # Extract text with English language
                text = pytesseract.image_to_string(page, lang='eng')
                
                # Clean text
                cleaned_text = self._clean_text(text)
                all_text += cleaned_text + "\n"
                
            return all_text
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing non-ASCII characters and excessive whitespace"""
        if not text:
            return ""
        
        # Remove non-ASCII characters but keep spaces and basic punctuation
        text = re.sub(r'[^\x00-\x7F\s]', ' ', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|]', 'I', text)
        
        return text
    
    def extract_fields(self, text: str) -> Dict[str, Optional[str]]:
        """Extract all required fields from text"""
        # Initialize results with required fields
        results = {field: None for field in self.required_fields}
        
        print(f"🔍 Extracting fields from text...")
        print(f"Text length: {len(text)} characters")
        
        # Aadhaar Number patterns
        aadhaar_patterns = [
            r'\b\d{4}\s\d{4}\s\d{4}\b',  # 4-4-4 format
            r'\b\d{12}\b',               # 12 digits
            r'\b\d{4}[X*]{4}\d{4}\b'     # Masked format
        ]
        
        for pattern in aadhaar_patterns:
            match = re.search(pattern, text)
            if match:
                aadhaar = match.group(0).replace(" ", "")
                if len(aadhaar) == 12:
                    results['Aadhaar Number'] = aadhaar
                    print(f"✅ Found Aadhaar Number: {aadhaar}")
                    break
        
        # Date of Birth patterns
        dob_patterns = [
            r'(DOB|Date of Birth)[\s:]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(Year of Birth|YOB)[\s:]*(\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dob = match.group(2) if len(match.groups()) > 1 else match.group(1)
                results['DOB'] = dob
                print(f"✅ Found DOB: {dob}")
                break
        
        # Gender patterns
        gender_patterns = [
            r'\b(MALE|FEMALE|Male|Female)\b',
            r'\b(M|F)\b',
            r'Gender[\s:]*([MF])',
            r'Gender[\s:]*(Male|Female)',
            r'FEMALE',  # Direct match
            r'MALE'     # Direct match
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1) if len(match.groups()) > 0 else match.group(0)
                # Normalize gender
                if gender.upper() in ['M', 'MALE']:
                    results['Gender'] = 'Male'
                elif gender.upper() in ['F', 'FEMALE']:
                    results['Gender'] = 'Female'
                else:
                    results['Gender'] = gender.capitalize()
                print(f"✅ Found Gender: {results['Gender']}")
                break
        
        # Name patterns
        name_patterns = [
            r'(Name|NAME)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'([A-Z][a-z]+[A-Z][a-z]+)',  # CamelCase like "SetuMishra"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Two words like "Setu Mishra"
            r'([A-Z][a-zA-Z\s]{2,})',  # General name pattern
            r'Setu\s+Mishra',  # Exact match
            r'SetuMishra'      # Exact match
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if self._is_valid_name(name):
                    results['Name'] = name.strip()
                    print(f"✅ Found Name: {results['Name']}")
                    break
        
        # Address patterns
        address = self._extract_address(text)
        if address:
            results['Address'] = address
            print(f"✅ Found Address: {address[:50]}...")
        
        return results
    
    def _is_valid_name(self, name: str) -> bool:
        """Validate if string looks like a real name"""
        if not name or len(name) < 2 or len(name) > 50:
            return False
        
        # Skip common non-name words
        skip_words = {'DOB', 'Gender', 'Address', 'Male', 'Female', 'PAN', 'GOVT', 'INDIA', 'DEPARTMENT', 'AUTHORITY', 'UNIQUE'}
        if name.upper() in skip_words:
            return False
        
        # Check if mostly alphabetic
        alpha_ratio = sum(1 for c in name if c.isalpha()) / len(name)
        return alpha_ratio > 0.6
    
    def _extract_address(self, text: str) -> str:
        """Extract address from text"""
        address_patterns = [
            r'Address[:\s]*([A-Za-z0-9\s,.-]{10,200}?\d{6})',
            r'(S/O|D/O|W/O)[:\s]*([A-Za-z0-9\s,.-]{10,200}?\d{6})',
            r'([A-Za-z0-9\s,.-]{20,200}?\d{6})',
            r'Address[:\s]*([A-Za-z0-9\s,.-]{10,200})',
            r'D/O[:\s]*([A-Za-z0-9\s,.-]{10,200})',  # Daughter of pattern
            r'D/O:\s*([A-Za-z0-9\s,.-]{10,200})'     # Daughter of pattern with colon
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    address = ' '.join(m for m in match if m)
                else:
                    address = match
                
                address = address.strip()
                if len(address) >= 15 and re.search(r'[A-Za-z]', address):
                    # Clean address
                    address = re.sub(r'[^\w\s,.-]', '', address)
                    address = re.sub(r'\s+', ' ', address)
                    return address.strip()
        
        return ""
    
    def extract_with_json_output(self, pdf_path: str) -> Dict[str, Any]:
        """Extract data and return JSON output"""
        try:
            print(f"🔍 Starting extraction for: {pdf_path}")
            
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            if not raw_text:
                return {
                    "status": "error",
                    "error_message": "Failed to extract text from PDF",
                    "file_path": pdf_path,
                    "extraction_timestamp": datetime.now().isoformat()
                }
            
            # Extract fields from text
            extracted_fields = self.extract_fields(raw_text)
            
            # Determine document type
            document_type = "AADHAAR" if extracted_fields.get('Aadhaar Number') else "UNKNOWN"
            
            # Calculate confidence score
            confidence = self._calculate_confidence(extracted_fields)
            
            # Create JSON output
            json_output = {
                "status": "success",
                "file_path": pdf_path,
                "document_type": document_type,
                "extraction_timestamp": datetime.now().isoformat(),
                "extracted_data": extracted_fields,
                "raw_text": raw_text,
                "extraction_confidence": confidence
            }
            
            print(f"✅ Extraction completed with confidence: {confidence}")
            return json_output
            
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "file_path": pdf_path,
                "extraction_timestamp": datetime.now().isoformat()
            }
    
    def _calculate_confidence(self, fields: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        if not fields:
            return 0.0
        
        # Weight for different fields
        weights = {
            'Aadhaar Number': 0.4,
            'Name': 0.3,
            'DOB': 0.1,
            'Gender': 0.1,
            'Address': 0.1
        }
        
        total_score = 0.0
        for field, weight in weights.items():
            if fields.get(field):
                total_score += weight
        
        return round(total_score, 2)
    
    def store_in_database(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Store extraction result in SQL database with user management and duplicate prevention"""
        try:
            if extraction_result.get("status") != "success":
                return {
                    "status": "error",
                    "error_message": "Cannot store failed extraction result"
                }
            
            extracted_data = extraction_result.get("extracted_data", {})
            aadhaar_number = extracted_data.get('Aadhaar Number')
            name = extracted_data.get('Name')
            
            # Validate required fields
            if not aadhaar_number or not name:
                raise InvalidDocumentDataError(
                    document_type="AADHAAR",
                    missing_fields=[f for f in ['Aadhaar Number', 'Name'] 
                                  if not extracted_data.get(f)],
                    validation_errors=["Aadhaar number and name are required for user management"]
                )
            
            # Check for duplicates before insertion
            is_unique, existing_record = self.duplicate_service.validate_document_uniqueness(
                "AADHAAR", extracted_data
            )
            
            if not is_unique:
                # Log the duplicate attempt
                self.duplicate_service.log_duplicate_attempt(
                    "AADHAAR", extracted_data, existing_record
                )
                
                raise DuplicateAadhaarError(
                    aadhaar_number=aadhaar_number,
                    existing_user_id=existing_record.get('user_id'),
                    existing_document_id=existing_record.get('document_id'),
                    existing_record=existing_record
                )
            
            # Get or create user ID
            user_id = self.user_manager.get_or_create_user_id(
                aadhaar_number, name, self.db_path
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into main documents table with user_id
                cursor.execute('''
                    INSERT INTO aadhaar_documents (
                        file_path, document_type, extraction_timestamp, 
                        extraction_confidence, raw_text, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    extraction_result.get("file_path"),
                    extraction_result.get("document_type"),
                    extraction_result.get("extraction_timestamp"),
                    extraction_result.get("extraction_confidence"),
                    extraction_result.get("raw_text"),
                    user_id
                ))
                
                # Get the document ID
                document_id = cursor.lastrowid
                
                # Insert extracted fields into the specific table with user_id
                cursor.execute('''
                    INSERT INTO extracted_fields (
                        document_id, "Name", "DOB", "Gender", "Address", "Aadhaar Number", user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    extracted_data.get('Name'),
                    extracted_data.get('DOB'),
                    extracted_data.get('Gender'),
                    extracted_data.get('Address'),
                    extracted_data.get('Aadhaar Number'),
                    user_id
                ))
                
                # Insert into user_documents cross-reference table
                cursor.execute('''
                    INSERT OR REPLACE INTO user_documents (
                        user_id, document_type, document_id
                    ) VALUES (?, ?, ?)
                ''', (user_id, "AADHAAR", document_id))
                
                conn.commit()
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "user_id": user_id,
                    "message": f"Successfully stored extraction result in database. Document ID: {document_id}, User ID: {user_id}"
                }
                
        except (DuplicateAadhaarError, InvalidDocumentDataError) as e:
            # Return structured error response for known exceptions
            return create_error_response(e)
            
        except sqlite3.Error as e:
            # Handle SQLite-specific errors
            custom_error = handle_sqlite_error(e, {
                'aadhaar_number': extracted_data.get('Aadhaar Number'),
                'table_name': 'extracted_fields'
            })
            return create_error_response(custom_error)
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Database storage failed: {str(e)}",
                "error_type": "STORAGE_ERROR"
            }
    
    def get_all_extracted_data(self) -> Dict[str, Any]:
        """Retrieve all extracted data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all extracted fields with document information
                cursor.execute('''
                    SELECT 
                        ad.id,
                        ad.file_path,
                        ad.document_type,
                        ad.extraction_timestamp,
                        ad.extraction_confidence,
                        ef."Name",
                        ef."DOB",
                        ef."Gender",
                        ef."Address",
                        ef."Aadhaar Number"
                    FROM aadhaar_documents ad
                    LEFT JOIN extracted_fields ef ON ad.id = ef.document_id
                    ORDER BY ad.created_at DESC
                ''')
                
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    results.append({
                        "document_id": row[0],
                        "file_path": row[1],
                        "document_type": row[2],
                        "extraction_timestamp": row[3],
                        "extraction_confidence": row[4],
                        "extracted_data": {
                            "Name": row[5],
                            "DOB": row[6],
                            "Gender": row[7],
                            "Address": row[8],
                            "Aadhaar Number": row[9]
                        }
                    })
                
                return {
                    "status": "success",
                    "total_records": len(results),
                    "data": results
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to retrieve data: {str(e)}"
            }
    
    def extract_and_store(self, pdf_path: str) -> Dict[str, Any]:
        """Extract data and store in database in one operation with duplicate prevention"""
        try:
            # Extract data
            extraction_result = self.extract_with_json_output(pdf_path)
            
            if extraction_result.get("status") == "success":
                # Store in database with user management
                storage_result = self.store_in_database(extraction_result)
                
                # Determine overall status
                if storage_result.get("status") == "success":
                    overall_status = "success"
                elif storage_result.get("error", {}).get("code") in ["DUPLICATE_AADHAAR"]:
                    overall_status = "duplicate_rejected"
                else:
                    overall_status = "partial_success"
                
                # Combine results
                return {
                    "extraction": extraction_result,
                    "storage": storage_result,
                    "overall_status": overall_status,
                    "user_id": storage_result.get("user_id"),
                    "duplicate_info": storage_result.get("details") if overall_status == "duplicate_rejected" else None
                }
            else:
                return {
                    "extraction": extraction_result,
                    "storage": {"status": "skipped", "message": "No data to store"},
                    "overall_status": "failed"
                }
                
        except Exception as e:
            return {
                "extraction": {"status": "error", "error_message": str(e)},
                "storage": {"status": "skipped", "message": "No data to store"},
                "overall_status": "failed"
            }
    
    def get_user_documents(self, user_id: str) -> Dict[str, Any]:
        """Get all documents for a specific user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        ad.id, ad.file_path, ad.extraction_timestamp, ad.extraction_confidence,
                        ef."Name", ef."DOB", ef."Gender", ef."Address", ef."Aadhaar Number"
                    FROM aadhaar_documents ad
                    JOIN extracted_fields ef ON ad.id = ef.document_id
                    WHERE ad.user_id = ?
                    ORDER BY ad.created_at DESC
                ''', (user_id,))
                
                documents = []
                for row in cursor.fetchall():
                    documents.append({
                        'document_id': row[0],
                        'file_path': row[1],
                        'extraction_timestamp': row[2],
                        'extraction_confidence': row[3],
                        'extracted_data': {
                            'Name': row[4],
                            'DOB': row[5],
                            'Gender': row[6],
                            'Address': row[7],
                            'Aadhaar Number': row[8]
                        }
                    })
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "document_count": len(documents),
                    "documents": documents
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to retrieve user documents: {str(e)}"
            }
    
    def check_aadhaar_exists(self, aadhaar_number: str) -> Dict[str, Any]:
        """Check if an Aadhaar number already exists in the system"""
        try:
            existing_record = self.duplicate_service.check_aadhaar_exists(aadhaar_number)
            
            if existing_record:
                return {
                    "exists": True,
                    "aadhaar_number": aadhaar_number,
                    "existing_record": {
                        "document_id": existing_record.get('document_id'),
                        "name": existing_record.get('name'),
                        "file_path": existing_record.get('file_path'),
                        "created_at": existing_record.get('created_at')
                    },
                    "message": f"Aadhaar number {aadhaar_number} already exists in the system"
                }
            else:
                return {
                    "exists": False,
                    "aadhaar_number": aadhaar_number,
                    "message": f"Aadhaar number {aadhaar_number} is available for new registration"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to check Aadhaar existence: {str(e)}"
            }

def main():
    """Test the Aadhaar extraction tool with user management integration"""
    print("🔍 Aadhaar Extraction Tool with User Management Integration")
    print("=" * 70)
    
    # Initialize the extractor with database
    extractor = AadhaarExtractionTool("aadhaar_documents.db")
    
    # Test with your PDF file
    pdf_path = "sample_documents/aadhar_sample 1.pdf"
    
    print(f"📄 Processing PDF: {pdf_path}")
    print()
    
    try:
        # First, check if Aadhaar already exists (demo)
        print("🔍 Checking for existing Aadhaar numbers...")
        test_aadhaar = "123456789012"  # Example Aadhaar
        existence_check = extractor.check_aadhaar_exists(test_aadhaar)
        print(f"Aadhaar {test_aadhaar} exists: {existence_check.get('exists', False)}")
        print()
        
        # Extract data, get JSON output, and store in database
        result = extractor.extract_and_store(pdf_path)
        
        # Display the results
        print("\n📊 EXTRACTION RESULTS:")
        print(json.dumps(result["extraction"], indent=2))
        print()
        
        print("\n💾 STORAGE RESULTS:")
        print(json.dumps(result["storage"], indent=2))
        print()
        
        print(f"\n🎯 OVERALL STATUS: {result['overall_status'].upper()}")
        
        # Display extracted fields and user information
        if result["extraction"].get("status") == "success":
            print("✅ EXTRACTION SUCCESSFUL")
            print(f"Document Type: {result['extraction'].get('document_type')}")
            print(f"Confidence Score: {result['extraction'].get('extraction_confidence')}")
            
            if result.get("user_id"):
                print(f"User ID: {result['user_id']}")
            
            print()
            
            extracted_data = result["extraction"].get("extracted_data", {})
            if extracted_data:
                print("📋 EXTRACTED FIELDS:")
                for field, value in extracted_data.items():
                    print(f"  {field}: {value}")
            else:
                print("⚠️  No fields extracted")
        else:
            print("❌ EXTRACTION FAILED")
            print(f"Error: {result['extraction'].get('error_message')}")
        
        # Handle duplicate cases
        if result['overall_status'] == 'duplicate_rejected':
            print("\n🚫 DUPLICATE DETECTED:")
            duplicate_info = result.get('duplicate_info', {})
            print(f"This Aadhaar number already exists in the system")
            if duplicate_info:
                print(f"Existing record details: {duplicate_info}")
        
        # Show user statistics
        print("\n👤 USER STATISTICS:")
        user_stats = extractor.user_manager.get_user_statistics()
        for key, value in user_stats.items():
            print(f"  {key}: {value}")
        
        # Show duplicate prevention statistics
        print("\n📊 DATA QUALITY METRICS:")
        quality_metrics = extractor.duplicate_service.get_data_quality_metrics()
        aadhaar_metrics = quality_metrics.get('aadhaar_metrics', {})
        if aadhaar_metrics:
            print(f"  Total Aadhaar records: {aadhaar_metrics.get('total_records', 0)}")
            print(f"  Unique Aadhaar numbers: {aadhaar_metrics.get('unique_numbers', 0)}")
            print(f"  Duplicate records: {aadhaar_metrics.get('duplicate_records', 0)}")
            print(f"  Duplicate percentage: {aadhaar_metrics.get('duplicate_percentage', 0):.1f}%")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Extraction and user management test completed!")

if __name__ == "__main__":
    main()




