#!/usr/bin/env python3
"""
Test: Validator Agent Pattern Validation
Demonstrates the enhanced validator agent with comprehensive pattern validation
"""

import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import ValidatorAgent, FieldValidator

def test_aadhaar_validation():
    """Test Aadhaar number validation patterns"""
    print("\n" + "="*60)
    print("TESTING AADHAAR VALIDATION PATTERNS")
    print("="*60)
    
    test_cases = [
        # Valid cases
        ("123456789012", "Valid unmasked Aadhaar"),
        ("1234XXXX5678", "Valid masked Aadhaar"),
        ("1234****5678", "Valid masked Aadhaar with asterisks"),
        
        # Invalid cases
        ("12345678901", "Too short"),
        ("1234567890123", "Too long"),
        ("12345678901A", "Contains letters"),
        ("000000000000", "All zeros"),
        ("123456789012", "Sequential numbers"),
        ("111111111111", "Repeated pattern"),
        ("", "Empty string"),
        ("1234XXX5678", "Invalid mask pattern"),
    ]
    
    for aadhaar, description in test_cases:
        result = FieldValidator.validate_aadhaar_number(aadhaar)
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {description}: {aadhaar}")
        print(f"   Result: {result}")
        print()

def test_pan_validation():
    """Test PAN number validation patterns"""
    print("\n" + "="*60)
    print("TESTING PAN VALIDATION PATTERNS")
    print("="*60)
    
    test_cases = [
        # Valid cases
        ("ABCDE1234F", "Valid PAN"),
        ("ABCDE1234F", "Valid PAN (uppercase)"),
        
        # Invalid cases
        ("ABCD1234F", "Too short"),
        ("ABCDE12345F", "Too long"),
        ("ABCDE1234", "Missing last letter"),
        ("ABCDE1234G", "Invalid pattern"),
        ("12345ABCDE", "Wrong format"),
        ("ABCDE1234F", "Sequential pattern"),
        ("AAAAA1111A", "Repeated pattern"),
        ("", "Empty string"),
    ]
    
    for pan, description in test_cases:
        result = FieldValidator.validate_pan_number(pan)
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {description}: {pan}")
        print(f"   Result: {result}")
        print()

def test_name_validation():
    """Test name validation patterns"""
    print("\n" + "="*60)
    print("TESTING NAME VALIDATION PATTERNS")
    print("="*60)
    
    test_cases = [
        # Valid cases
        ("John Doe", "Valid name"),
        ("Mary Jane", "Valid name with space"),
        ("O'Connor", "Valid name with apostrophe"),
        ("Dr. Smith", "Valid name with title"),
        
        # Invalid cases
        ("A", "Too short"),
        ("This is a very long name that exceeds the maximum allowed length", "Too long"),
        ("John123", "Contains numbers"),
        ("John@Doe", "Contains special characters"),
        ("TEST", "Suspicious pattern"),
        ("ABCD", "Suspicious pattern"),
        ("", "Empty string"),
    ]
    
    for name, description in test_cases:
        result = FieldValidator.validate_name(name)
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {description}: {name}")
        print(f"   Result: {result}")
        print()

def test_date_validation():
    """Test date validation patterns"""
    print("\n" + "="*60)
    print("TESTING DATE VALIDATION PATTERNS")
    print("="*60)
    
    test_cases = [
        # Valid cases
        ("15/03/1990", "Valid DD/MM/YYYY"),
        ("15-03-1990", "Valid DD-MM-YYYY"),
        ("1990-03-15", "Valid YYYY-MM-DD"),
        ("15/03/90", "Valid DD/MM/YY"),
        
        # Invalid cases
        ("32/13/1990", "Invalid date"),
        ("15/03/2025", "Future date"),
        ("15/03/1800", "Too old"),
        ("15.03.1990", "Invalid format"),
        ("1990/03/15", "Invalid format"),
        ("", "Empty string"),
    ]
    
    for date, description in test_cases:
        result = FieldValidator.validate_date(date)
        status = "✅" if result["valid"] else "❌"
        print(f"{status} {description}: {date}")
        print(f"   Result: {result}")
        print()

def test_complete_validation():
    """Test complete validation with sample data"""
    print("\n" + "="*60)
    print("TESTING COMPLETE VALIDATION")
    print("="*60)
    
    validator = ValidatorAgent()
    
    # Sample Aadhaar data
    aadhaar_data = {
        "document_type": "AADHAAR",
        "Aadhaar Number": "123456789012",
        "Name": "John Doe",
        "DOB": "15/03/1990",
        "Gender": "Male",
        "Address": "123 Main Street, City, State 123456"
    }
    
    # Sample PAN data
    pan_data = {
        "document_type": "PAN",
        "PAN Number": "ABCDE1234F",
        "Name": "Jane Smith",
        "Father's Name": "Robert Smith",
        "DOB": "20/05/1985"
    }
    
    # Test Aadhaar validation
    print("Testing Aadhaar validation:")
    aadhaar_result = validator.validate({
        "status": "success",
        "extracted_data": aadhaar_data
    })
    
    print(f"Validation Status: {aadhaar_result['validation_status']}")
    print(f"Is Valid: {aadhaar_result['is_valid']}")
    print(f"Overall Score: {aadhaar_result['overall_score']:.1%}")
    print(f"Errors: {aadhaar_result['errors']}")
    print(f"Warnings: {aadhaar_result['warnings']}")
    
    print("\n" + "-"*40)
    
    # Test PAN validation
    print("Testing PAN validation:")
    pan_result = validator.validate({
        "status": "success",
        "extracted_data": pan_data
    })
    
    print(f"Validation Status: {pan_result['validation_status']}")
    print(f"Is Valid: {pan_result['is_valid']}")
    print(f"Overall Score: {pan_result['overall_score']:.1%}")
    print(f"Errors: {pan_result['errors']}")
    print(f"Warnings: {pan_result['warnings']}")

def main():
    """Run all validation tests"""
    print("VALIDATOR AGENT PATTERN VALIDATION TESTS")
    print("="*60)
    
    # Test individual field validations
    test_aadhaar_validation()
    test_pan_validation()
    test_name_validation()
    test_date_validation()
    
    # Test complete validation
    test_complete_validation()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main() 