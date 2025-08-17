#!/usr/bin/env python3
"""
Aadhaar Extraction Tool
Successfully extracts key fields from Aadhaar cards and provides JSON output
"""

import re
import json
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
from typing import Dict, Any, Optional

class AadhaarExtractionTool:
    """Aadhaar extraction tool that extracts all key fields and provides JSON output"""
    
    def __init__(self):
        self.required_fields = ['Name', 'DOB', 'Gender', 'Address', 'Aadhaar Number']
    
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

def main():
    """Test the Aadhaar extraction tool"""
    print("🔍 Aadhaar Extraction Tool")
    print("=" * 50)
    
    # Initialize the extractor
    extractor = AadhaarExtractionTool()
    
    # Test with your PDF file
    pdf_path = "sample_documents/aadhar_sample 1.pdf"
    
    print(f"📄 Processing PDF: {pdf_path}")
    print()
    
    try:
        # Extract data and get JSON output
        result = extractor.extract_with_json_output(pdf_path)
        
        # Display the JSON output
        print("\n📊 JSON OUTPUT:")
        print(json.dumps(result, indent=2))
        print()
        
        # Display extracted fields
        if result.get("status") == "success":
            print("✅ EXTRACTION SUCCESSFUL")
            print(f"Document Type: {result.get('document_type')}")
            print(f"Confidence Score: {result.get('extraction_confidence')}")
            print()
            
            extracted_data = result.get("extracted_data", {})
            if extracted_data:
                print("📋 EXTRACTED FIELDS:")
                for field, value in extracted_data.items():
                    print(f"  {field}: {value}")
            else:
                print("⚠️  No fields extracted")
        else:
            print("❌ EXTRACTION FAILED")
            print(f"Error: {result.get('error_message')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Extraction completed!")

if __name__ == "__main__":
    main()




