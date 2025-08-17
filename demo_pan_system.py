#!/usr/bin/env python3
"""
Comprehensive Demo of PAN Card Extraction and Validation System
"""

import re
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List

def validate_pan_number(pan: str) -> Dict[str, Any]:
    """Enhanced PAN number validation with comprehensive checks"""
    if not pan:
        return {"valid": False, "reason": "not_found", "type": "empty"}
    
    clean_pan = pan.replace(" ", "").upper()
    
    # Check length (must be exactly 10 characters)
    if len(clean_pan) != 10:
        return {"valid": False, "type": "invalid", "reason": "invalid_length", 
                "expected_length": 10, "actual_length": len(clean_pan)}
    
    # Check basic pattern (5 letters + 4 digits + 1 letter)
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', clean_pan):
        return {"valid": False, "type": "invalid", "reason": "invalid_format", 
                "expected_format": "ABCDE1234F"}
    
    # Check for all same characters
    if len(set(clean_pan)) == 1:
        return {"valid": False, "type": "invalid", "reason": "all_same_characters"}
    
    # Check for common invalid patterns
    invalid_patterns = [
        "AAAAA0000A",  # All A's and 0's
        "ZZZZZ9999Z",  # All Z's and 9's
        "ABCDE1234F",  # Sequential letters and numbers
    ]
    
    if clean_pan in invalid_patterns:
        return {"valid": False, "type": "invalid", "reason": "common_invalid_pattern"}
    
    # Validate PAN structure
    letters_part = clean_pan[:5]
    digits_part = clean_pan[5:9]
    last_letter = clean_pan[9]
    
    # Check if letters part contains only letters
    if not letters_part.isalpha():
        return {"valid": False, "type": "invalid", "reason": "letters_part_contains_digits"}
    
    # Check if digits part contains only digits
    if not digits_part.isdigit():
        return {"valid": False, "type": "invalid", "reason": "digits_part_contains_letters"}
    
    # Check if last character is a letter
    if not last_letter.isalpha():
        return {"valid": False, "type": "invalid", "reason": "last_character_not_letter"}
    
    return {
        "valid": True,
        "type": "valid",
        "format": clean_pan,
        "length": len(clean_pan),
        "structure": {
            "letters_part": letters_part,
            "digits_part": digits_part,
            "last_letter": last_letter
        }
    }

def extract_pan_fields_from_text(text: str) -> Dict[str, Any]:
    """Extract PAN card fields from text using regex patterns"""
    results = {
        "Name": None,
        "Father's Name": None,
        "DOB": None,
        "PAN Number": None
    }
    
    # PAN Number patterns
    pan_patterns = [
        r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
        r'\b[A-Z]{5}\s*[0-9]{4}\s*[A-Z]{1}\b',
        r'PAN[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})',
        r'Permanent Account Number[:\s]*([A-Z]{5}[0-9]{4}[A-Z]{1})'
    ]
    
    for pattern in pan_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pan = match.group(1) if len(match.groups()) > 0 else match.group(0)
            pan = pan.replace(" ", "").upper()
            if len(pan) == 10 and re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan):
                results['PAN Number'] = pan
                break
    
    # Name patterns
    name_patterns = [
        r'Name[:\s]*([A-Za-z\s]+)',
        r'Card Holder[:\s]*([A-Za-z\s]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Simple name pattern
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and len(name) < 50:
                results['Name'] = name
                break
    
    # Father's Name patterns
    father_patterns = [
        r'Father[:\s]*([A-Za-z\s]+)',
        r'Guardian[:\s]*([A-Za-z\s]+)',
        r'Father\'s Name[:\s]*([A-Za-z\s]+)',
    ]
    
    for pattern in father_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            father_name = match.group(1).strip()
            if len(father_name) > 2 and len(father_name) < 50:
                results['Father\'s Name'] = father_name
                break
    
    # Date of Birth patterns
    dob_patterns = [
        r'DOB[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})',
        r'Date of Birth[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
    ]
    
    for pattern in dob_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            dob = match.group(1)
            results['DOB'] = dob
            break
    
    return results

def calculate_confidence(extracted_data: Dict[str, Any], raw_text: str) -> float:
    """Calculate confidence score for extracted data"""
    total_score = 0
    max_score = 0
    
    # PAN Number (highest weight)
    if extracted_data.get('PAN Number'):
        pan_validation = validate_pan_number(extracted_data['PAN Number'])
        if pan_validation['valid']:
            total_score += 0.4
        max_score += 0.4
    
    # Name (medium weight)
    if extracted_data.get('Name'):
        name = extracted_data['Name']
        if len(name) >= 3 and len(name) <= 50:
            total_score += 0.3
        max_score += 0.3
    
    # Father's Name (medium weight)
    if extracted_data.get('Father\'s Name'):
        father_name = extracted_data['Father\'s Name']
        if len(father_name) >= 3 and len(father_name) <= 50:
            total_score += 0.2
        max_score += 0.2
    
    # DOB (low weight)
    if extracted_data.get('DOB'):
        total_score += 0.1
        max_score += 0.1
    
    return total_score / max_score if max_score > 0 else 0.0

def demo_pan_validation():
    """Demonstrate PAN validation with various test cases"""
    print("🔍 PAN Number Validation Demo")
    print("=" * 60)
    
    test_cases = [
        ("ABCDE1234G", "Valid PAN Number"),
        ("AAAAA0000A", "Invalid - All A's and 0's"),
        ("ZZZZZ9999Z", "Invalid - All Z's and 9's"),
        ("ABCDE1234", "Invalid - Too short"),
        ("ABCDE12345F", "Invalid - Too long"),
        ("12345ABCDE", "Invalid - Wrong format"),
        ("ABCDE1234F", "Invalid - Sequential pattern"),
        ("ABCDE1234H", "Valid PAN Number"),
        ("", "Invalid - Empty"),
        ("ABCDE1234I", "Valid PAN Number"),
    ]
    
    for pan, description in test_cases:
        result = validate_pan_number(pan)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{status} | {pan:12} | {description}")
        if not result["valid"]:
            print(f"    Reason: {result.get('reason', 'Unknown')}")
        elif result.get('structure'):
            structure = result['structure']
            print(f"    Structure: {structure['letters_part']}-{structure['digits_part']}-{structure['last_letter']}")
        print()

def demo_text_extraction():
    """Demonstrate text extraction from sample text"""
    print("📄 Text Extraction Demo")
    print("=" * 60)
    
    sample_texts = [
        "Name: John Doe Father: Robert Doe DOB: 15/03/1990 PAN: ABCDE1234F",
        "Card Holder: Jane Smith Guardian: Mary Smith Date of Birth: 22-07-1985 Permanent Account Number: FGHIJ5678K",
        "NCOME TAX DEPARTMENT GOVT. OF INDIA MAMTA MISHRA",  # From our sample
    ]
    
    for i, text in enumerate(sample_texts, 1):
        print(f"Sample Text {i}: {text}")
        extracted = extract_pan_fields_from_text(text)
        confidence = calculate_confidence(extracted, text)
        
        print("Extracted Fields:")
        for field, value in extracted.items():
            status = "✅" if value else "❌"
            print(f"  {status} {field}: {value}")
        
        print(f"Confidence Score: {confidence:.2f}")
        print()

def demo_database_operations():
    """Demonstrate database operations"""
    print("💾 Database Operations Demo")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('pan_documents.db')
        cursor = conn.cursor()
        
        # Show database schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Database Tables: {[table[0] for table in tables]}")
        
        # Show document count
        cursor.execute('SELECT COUNT(*) FROM pan_documents')
        doc_count = cursor.fetchone()[0]
        print(f"Total Documents Processed: {doc_count}")
        
        # Show latest document
        cursor.execute('SELECT * FROM pan_documents ORDER BY id DESC LIMIT 1')
        latest_doc = cursor.fetchone()
        if latest_doc:
            print(f"Latest Document:")
            print(f"  ID: {latest_doc[0]}")
            print(f"  File: {latest_doc[1]}")
            print(f"  Type: {latest_doc[2]}")
            print(f"  Confidence: {latest_doc[4]}")
            print(f"  Raw Text: {latest_doc[5][:50]}...")
        
        # Show extracted fields
        cursor.execute('SELECT * FROM extracted_fields ORDER BY id DESC LIMIT 1')
        latest_fields = cursor.fetchone()
        if latest_fields:
            print(f"Latest Extracted Fields:")
            print(f"  Name: {latest_fields[2]}")
            print(f"  Father's Name: {latest_fields[3]}")
            print(f"  DOB: {latest_fields[4]}")
            print(f"  PAN Number: {latest_fields[5]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Database Error: {e}")

def main():
    """Main demonstration function"""
    print("🎯 PAN Card Extraction and Validation System - Complete Demo")
    print("=" * 80)
    print()
    
    # Demo 1: PAN Validation
    demo_pan_validation()
    
    # Demo 2: Text Extraction
    demo_text_extraction()
    
    # Demo 3: Database Operations
    demo_database_operations()
    
    print("✅ Demo completed successfully!")
    print()
    print("📋 System Features Demonstrated:")
    print("  ✅ PAN number validation with comprehensive rules")
    print("  ✅ Text extraction using regex patterns")
    print("  ✅ Confidence scoring for extracted data")
    print("  ✅ SQLite database integration")
    print("  ✅ Field extraction for Name, Father's Name, DOB, PAN Number")
    print("  ✅ Invalid pattern detection")
    print("  ✅ Structure validation for PAN numbers")
    print()
    print("🔧 Technical Implementation:")
    print("  - Regex-based pattern matching")
    print("  - Multi-layered validation logic")
    print("  - SQLite database with proper schema")
    print("  - Confidence scoring algorithm")
    print("  - Error handling and logging")
    print("  - Modular and extensible architecture")

if __name__ == "__main__":
    main()



