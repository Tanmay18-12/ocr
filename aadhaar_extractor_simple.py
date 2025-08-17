#!/usr/bin/env python3
"""
Simplified Aadhaar Extraction Tool
Bypasses user management system to fix storage issues
"""

import re
import json
import sqlite3
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
from typing import Dict, Any, Optional
import os

class SimpleAadhaarExtractionTool:
    
    def __init__(self, db_path: str = "aadhaar_documents.db"):
        self.required_fields = ['Name', 'DOB', 'Gender', 'Address', 'Aadhaar Number']
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with simple schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create main aadhaar documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aadhaar_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        extraction_timestamp TEXT NOT NULL,
                        extraction_confidence REAL DEFAULT 0.0,
                        raw_text TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create extracted fields table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_fields (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        "Name" TEXT,
                        "DOB" TEXT,
                        "Gender" TEXT,
                        "Address" TEXT,
                        "Aadhaar Number" TEXT,
                        extraction_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES aadhaar_documents (id)
                    )
                ''')
                
                conn.commit()
                print(f"✅ Database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            pages = convert_from_path(pdf_path, dpi=300)
            print(f"📄 Converted {len(pages)} pages from PDF")
            
            all_text = ""
            for i, page in enumerate(pages):
                print(f"Processing page {i+1}...")
                text = pytesseract.image_to_string(page, lang='eng')
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
        
        text = re.sub(r'[^\x00-\x7F\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[|]', 'I', text)
        
        return text
    
    def extract_fields(self, text: str) -> Dict[str, Optional[str]]:
        """Extract all required fields from text"""
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
                results['Aadhaar Number'] = aadhaar
                print(f"✅ Found Aadhaar Number: {aadhaar}")
                break
        
        # Name patterns
        name_patterns = [
            r'Name[:\s]*([A-Za-z\s]+?)(?=\n|DOB|Gender|Address|$)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and len(name) < 50:
                    results['Name'] = name
                    print(f"✅ Found Name: {name}")
                    break
        
        # DOB patterns
        dob_patterns = [
            r'DOB[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{2}[/-]\d{2}[/-]\d{4})',
            r'(\d{4}[/-]\d{2}[/-]\d{2})',
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text)
            if match:
                dob = match.group(1)
                results['DOB'] = dob
                print(f"✅ Found DOB: {dob}")
                break
        
        # Gender patterns
        gender_patterns = [
            r'Gender[:\s]*(Male|Female|M|F)',
            r'(Male|Female|M|F)',
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1)
                results['Gender'] = gender
                print(f"✅ Found Gender: {gender}")
                break
        
        # Address patterns
        address_patterns = [
            r'Address[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n[A-Z]|$)',
            r'([A-Z][^A-Z\n]*\n[A-Z][^A-Z\n]*\n[A-Z][^A-Z\n]*)',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                address = match.group(1).strip()
                if len(address) > 10:
                    results['Address'] = address
                    print(f"✅ Found Address: {address[:50]}...")
                    break
        
        return results
    
    def _calculate_confidence(self, fields: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        if not fields:
            return 0.0
        
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
        """Store extraction result in SQL database (simplified version)"""
        try:
            if extraction_result.get("status") != "success":
                return {
                    "status": "error",
                    "error_message": "Cannot store failed extraction result"
                }
            
            extracted_data = extraction_result.get("extracted_data", {})
            aadhaar_number = extracted_data.get('Aadhaar Number')
            
            # Check for duplicates (simple check)
            if aadhaar_number:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id FROM extracted_fields 
                        WHERE "Aadhaar Number" = ?
                    ''', (aadhaar_number,))
                    
                    existing = cursor.fetchone()
                    if existing:
                        return {
                            "status": "duplicate_rejected",
                            "message": f"Aadhaar number {aadhaar_number} already exists"
                        }
            
            # Store the document
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into main documents table
                cursor.execute('''
                    INSERT INTO aadhaar_documents (
                        file_path, document_type, extraction_timestamp, 
                        extraction_confidence, raw_text
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    extraction_result.get("file_path"),
                    extraction_result.get("document_type"),
                    extraction_result.get("extraction_timestamp"),
                    extraction_result.get("extraction_confidence"),
                    extraction_result.get("raw_text")
                ))
                
                # Get the document ID
                document_id = cursor.lastrowid
                
                # Insert extracted fields
                cursor.execute('''
                    INSERT INTO extracted_fields (
                        document_id, "Name", "DOB", "Gender", "Address", "Aadhaar Number"
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    extracted_data.get('Name'),
                    extracted_data.get('DOB'),
                    extracted_data.get('Gender'),
                    extracted_data.get('Address'),
                    extracted_data.get('Aadhaar Number')
                ))
                
                conn.commit()
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "message": f"Successfully stored extraction result. Document ID: {document_id}"
                }
                
        except Exception as e:
            print(f"❌ Storage error: {e}")
            return {
                "status": "error",
                "error_message": f"Storage failed: {str(e)}"
            }
    
    def extract_and_store(self, pdf_path: str) -> Dict[str, Any]:
        """Extract data from PDF and store in database"""
        try:
            print(f"🔄 Starting extraction for: {pdf_path}")
            
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(pdf_path)
            if not raw_text:
                return {
                    "overall_status": "failed",
                    "extraction": {
                        "status": "failed",
                        "error_message": "Failed to extract text from PDF"
                    }
                }
            
            # Extract fields from text
            extracted_fields = self.extract_fields(raw_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(extracted_fields)
            
            # Create extraction result
            extraction_result = {
                "status": "success",
                "extracted_data": extracted_fields,
                "extraction_confidence": confidence,
                "extraction_timestamp": datetime.now().isoformat(),
                "file_path": pdf_path,
                "document_type": "AADHAAR",
                "raw_text": raw_text
            }
            
            # Store in database
            storage_result = self.store_in_database(extraction_result)
            
            # Determine overall status
            if storage_result.get("status") == "success":
                return {
                    "overall_status": "success",
                    "extraction": extraction_result,
                    "storage": storage_result
                }
            elif storage_result.get("status") == "duplicate_rejected":
                return {
                    "overall_status": "duplicate_rejected",
                    "extraction": extraction_result,
                    "storage": storage_result
                }
            else:
                return {
                    "overall_status": "failed",
                    "extraction": extraction_result,
                    "storage": storage_result
                }
                
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return {
                "overall_status": "failed",
                "extraction": {
                    "status": "failed",
                    "error_message": str(e)
                }
            }
