import re
import json
import pytesseract
from pdf2image import convert_from_path
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from PIL import Image
import numpy as np
import cv2
import sqlite3
import os
from datetime import datetime

class PDFExtractorTool(BaseTool):
    name = "PDFExtractorTool"
    description = "Extracts fields from ID documents (Aadhaar/PAN) and stores them in database with dynamic table creation"

    def __init__(self, db_path: str = "documents.db"):
        super().__init__()
        self.db_path = db_path
        self.db_agent = None  # Initialize lazily to avoid circular import
        self._init_database()

    def _init_database(self):
        """Initialize the database with core tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create core documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS id_documents (
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
                    )
                ''')
                
                # Create table with specific column names for extracted fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS extracted_fields (
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
                    )
                ''')
                
                conn.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")

    def _run(self, pdf_path: str) -> Dict[str, Any]:
        """Main extraction method that returns JSON output"""
        try:
            # Extract text from PDF
            text = self._extract_text_from_pdf(pdf_path)
            
            # Extract fields from text
            extracted_fields = self._extract_fields(text)
            
            # Determine document type
            document_type = self._determine_document_type(extracted_fields)
            
            # Create JSON output
            json_output = {
                "status": "success",
                "file_path": pdf_path,
                "document_type": document_type,
                "extraction_timestamp": datetime.now().isoformat(),
                "extracted_data": extracted_fields,
                "raw_text": text,
                "extraction_confidence": self._calculate_extraction_confidence(extracted_fields)
            }
            
            # Store in database using database agent
            self._store_in_database(json_output)
            
            return json_output
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "file_path": pdf_path,
                "extraction_timestamp": datetime.now().isoformat()
            }

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF with preprocessing"""
        try:
            pages = convert_from_path(pdf_path, dpi=300)
        except Exception as e:
            print(f"Error converting PDF: {e}")
            return ""

        all_text = ""
        for page in pages:
            # Preprocess image for better OCR
            preprocessed_image = self._preprocess_image(np.array(page))
            text = pytesseract.image_to_string(preprocessed_image, lang='eng')
            
            # Clean text - remove Hindi gibberish and non-ASCII characters
            cleaned_text = self._clean_text(text)
            all_text += cleaned_text + "\n"
        
        return all_text

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def _clean_text(self, text: str) -> str:
        """Clean text by removing Hindi gibberish and non-ASCII characters"""
        if not text:
            return ""
        
        # Remove non-ASCII characters (Hindi gibberish removal)
        text = re.sub(r'[^\x00-\x7F]', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|]', 'I', text)  # Replace | with I
        text = re.sub(r'[0]', 'O', text)  # Replace 0 with O in certain contexts
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Filter lines with meaningful content
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if self._is_meaningful_line(line):
                lines.append(line)
        
        return '\n'.join(lines)

    def _is_meaningful_line(self, line: str) -> bool:
        """Check if line contains meaningful content"""
        if not line or len(line) < 2:
            return False
        
        # Skip obvious gibberish patterns
        gibberish_patterns = [
            'aeufafa', 'afgat', 'ATAreaie', 'BONAR', 'PoeRb', 'Yepuipeeae',
            'aeufafa', 'afgat', 'ATAreaie', 'BONAR', 'PoeRb', 'Yepuipeeae'
        ]
        
        if any(pattern in line.lower() for pattern in gibberish_patterns):
            return False
        
        # Check English content ratio
        english_chars = sum(1 for c in line if c.isascii() and (c.isalnum() or c.isspace()))
        return english_chars / len(line) >= 0.6 if line else False

    def _extract_fields(self, text: str) -> Dict[str, Optional[str]]:
        """Extract fields from cleaned text"""
        # Initialize with all required fields as None
        results = {
            'Name': None,
            'DOB': None,
            'Gender': None,
            'Address': None,
            'Aadhaar Number': None
        }

        # Aadhaar Number (12 digits, with or without spaces)
        aadhaar_patterns = [
            r'\b\d{4}\s\d{4}\s\d{4}\b',
            r'\b\d{12}\b',
            r'\b\d{4}[X*]{4}\d{4}\b'
        ]
        
        for pattern in aadhaar_patterns:
            match = re.search(pattern, text)
            if match:
                results['Aadhaar Number'] = match.group(0).replace(" ", "")
                break

        # PAN Number (10 characters: 5 letters + 4 digits + 1 letter)
        pan_match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text)
        if pan_match:
            results['PAN'] = pan_match.group(1)

        # Date of Birth
        dob_patterns = [
            r'(DOB|Date of Birth)[\s:]*([\d]{2}[-/][\d]{2}[-/][\d]{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(Year of Birth|YOB)[\s:]*(\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                results['DOB'] = match.group(2) if len(match.groups()) > 1 else match.group(1)
                break

        # Gender
        gender_match = re.search(r'\b(MALE|FEMALE|Male|Female|M|F)\b', text)
        if gender_match:
            results['Gender'] = gender_match.group(1).capitalize()

        # Name
        name_patterns = [
            r'(Name|NAME)[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'([A-Z][a-z]+[A-Z][a-z]+)',  # CamelCase
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)'  # Two words
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if self._is_valid_name(name):
                    results['Name'] = name.strip()
                    break

        # Father's Name (additional field)
        father_patterns = [
            r"Father's Name[:\s]*([A-Z][a-zA-Z\s]{2,})",
            r'Father[:\s]*([A-Z][a-zA-Z\s]{2,})',
            r'S/O[:\s]*([A-Z][a-zA-Z\s]{2,})'
        ]
        
        for pattern in father_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(1).strip()
                if self._is_valid_name(father_name):
                    results["Father's Name"] = father_name
                    break

        # Address
        address = self._extract_address(text)
        if address:
            results['Address'] = address

        return results

    def _is_valid_name(self, name: str) -> bool:
        """Validate if string looks like a real name"""
        if not name or len(name) < 2 or len(name) > 50:
            return False
        
        # Skip common non-name words
        skip_words = {'DOB', 'Gender', 'Address', 'Male', 'Female', 'PAN', 'GOVT', 'INDIA', 'DEPARTMENT'}
        if name.upper() in skip_words:
            return False
        
        # Check if mostly alphabetic
        return sum(1 for c in name if c.isalpha()) / len(name) > 0.7

    def _extract_address(self, text: str) -> str:
        """Extract address from text"""
        address_patterns = [
            r'Address[:\s]*([A-Za-z0-9\s,.-]{10,200}?\d{6})',
            r'(S/O|D/O|W/O)[:\s]*([A-Za-z0-9\s,.-]{10,200}?\d{6})',
            r'([A-Za-z0-9\s,.-]{20,200}?\d{6})'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    address = ' '.join(m for m in match if m)
                else:
                    address = match
                
                address = address.strip()
                if len(address) >= 20 and re.search(r'[A-Za-z]', address):
                    # Clean address
                    address = re.sub(r'[^\w\s,.-]', '', address)
                    address = re.sub(r'\s+', ' ', address)
                    return address.strip()
        
        return ""

    def _determine_document_type(self, fields: Dict[str, Any]) -> str:
        """Determine document type based on extracted fields"""
        if 'Aadhaar Number' in fields:
            return "AADHAAR"
        elif 'PAN' in fields:
            return "PAN"
        else:
            return "UNKNOWN"

    def _calculate_extraction_confidence(self, fields: Dict[str, Any]) -> float:
        """Calculate confidence score for extraction"""
        if not fields:
            return 0.0
        
        # Required fields for different document types
        if 'Aadhaar Number' in fields:
            required = ['Aadhaar Number', 'Name']
            optional = ['DOB', 'Gender', 'Address']
        elif 'PAN' in fields:
            required = ['PAN', 'Name']
            optional = ["Father's Name", 'DOB']
        else:
            return 0.1  # Unknown document type
        
        # Calculate scores
        required_score = sum(1 for field in required if field in fields and fields[field]) / len(required)
        optional_score = sum(1 for field in optional if field in fields and fields[field]) / len(optional)
        
        return round(required_score * 0.8 + optional_score * 0.2, 2)

    def _store_in_database(self, extraction_result: Dict[str, Any]):
        """Store extraction result in database using database agent"""
        try:
            # Initialize database agent lazily to avoid circular import
            if self.db_agent is None:
                from agents.db_agent import DatabaseAgent
                self.db_agent = DatabaseAgent(self.db_path)
            
            # First, store in the main documents table using database agent
            storage_data = {
                "file_path": extraction_result.get("file_path", ""),
                "document_type": extraction_result.get("document_type", "UNKNOWN"),
                "extraction_timestamp": extraction_result.get("extraction_timestamp", datetime.now().isoformat()),
                "validation_status": "pending",
                "is_valid": False,
                "overall_score": extraction_result.get("extraction_confidence", 0.0),
                "completeness_score": extraction_result.get("extraction_confidence", 0.0),
                "extracted_data": extraction_result.get("extracted_data", {}),
                "validation_details": {}  # Will be populated by validator
            }
            
            # Use database agent to store the result
            db_result = self.db_agent.store_validation_result(storage_data)
            
            if db_result.get("status") == "success":
                print(f"Successfully stored extraction result in database. Document ID: {db_result.get('document_id')}")
                
                # Also store in the specific extracted_fields table
                self._store_extracted_fields(db_result.get('document_id'), extraction_result.get("extracted_data", {}))
            else:
                print(f"Database storage failed: {db_result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            print(f"Error storing in database: {e}")
    
    def _store_extracted_fields(self, document_id: int, extracted_data: Dict[str, Any]):
        """Store extracted fields in the specific table with required column names"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert into extracted_fields table with specific column names
                cursor.execute('''
                    INSERT INTO extracted_fields (
                        document_id, "Name", "DOB", "Gender", "Address", 
                        "Aadhaar Number", "PAN", "Father's Name"
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    document_id,
                    extracted_data.get('Name'),
                    extracted_data.get('DOB'),
                    extracted_data.get('Gender'),
                    extracted_data.get('Address'),
                    extracted_data.get('Aadhaar Number'),
                    extracted_data.get('PAN'),
                    extracted_data.get("Father's Name")
                ))
                
                conn.commit()
                print(f"Successfully stored extracted fields in specific table")
                
        except Exception as e:
            print(f"Error storing extracted fields: {e}")

    def extract_text(self, pdf_file_path: str) -> str:
        """Legacy method for backward compatibility"""
        return self._extract_text_from_pdf(pdf_file_path)

    def extract_fields(self, pdf_file_path: str) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        result = self._run(pdf_file_path)
        return result.get("extracted_data", {})
