#!/usr/bin/env python3
"""
Simple Validator to Database Integration Demo
Shows validator JSON output structure and database integration
(No OpenAI API key required)
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import FieldValidator

def demonstrate_validator_json_output():
    """Demonstrate the JSON output structure from validator agent"""
    
    print("="*80)
    print("VALIDATOR AGENT JSON OUTPUT STRUCTURE")
    print("="*80)
    
    print("\n1. 📋 SAMPLE EXTRACTION DATA")
    print("-" * 60)
    
    # Sample extraction data (what PDFExtractorTool would return)
    sample_extraction_data = {
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
    
    print("Sample Extraction Data:")
    print(json.dumps(sample_extraction_data, indent=2))
    
    print("\n2. 🔍 FIELD VALIDATION RESULTS")
    print("-" * 60)
    
    # Validate individual fields using FieldValidator
    validation_details = {}
    
    # Validate Aadhaar Number
    aadhaar = sample_extraction_data["extracted_data"]["Aadhaar Number"]
    aadhaar_validation = FieldValidator.validate_aadhaar_number(aadhaar)
    validation_details["Aadhaar Number"] = aadhaar_validation
    
    # Validate Name
    name = sample_extraction_data["extracted_data"]["Name"]
    name_validation = FieldValidator.validate_name(name)
    validation_details["Name"] = name_validation
    
    # Validate DOB
    dob = sample_extraction_data["extracted_data"]["DOB"]
    dob_validation = FieldValidator.validate_date(dob)
    validation_details["DOB"] = dob_validation
    
    # Validate Gender
    gender = sample_extraction_data["extracted_data"]["Gender"]
    gender_validation = FieldValidator.validate_gender(gender)
    validation_details["Gender"] = gender_validation
    
    # Validate Address
    address = sample_extraction_data["extracted_data"]["Address"]
    address_validation = FieldValidator.validate_address(address)
    validation_details["Address"] = address_validation
    
    print("Field Validation Results:")
    for field_name, field_result in validation_details.items():
        status = "✅ VALID" if field_result.get('valid', False) else "❌ INVALID"
        reason = field_result.get('reason', 'N/A')
        print(f"  {field_name}: {status} ({reason})")
    
    print("\n3. 📊 COMPLETE VALIDATOR JSON OUTPUT")
    print("-" * 60)
    
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
    
    # Create complete validation result (what ValidatorAgent would return)
    validation_result = {
        "validation_status": "passed" if len(errors) == 0 else "failed",
        "document_type": "AADHAAR",
        "validation_details": validation_details,
        "errors": errors,
        "warnings": warnings,
        "overall_score": overall_score,
        "extracted_data": sample_extraction_data["extracted_data"],
        "is_valid": len(errors) == 0
    }
    
    print("Complete Validator Agent JSON Output:")
    print(json.dumps(validation_result, indent=2))
    
    print("\n4. 🗄️ DATABASE INTEGRATION EXPLANATION")
    print("-" * 60)
    
    print("How Database Agent Uses Validator JSON:")
    print("1. Receives validation_result JSON from ValidatorAgent")
    print("2. Extracts 'validation_details' keys as table column names")
    print("3. Creates dynamic table with columns based on field names")
    print("4. Stores validation results in the dynamic table")
    print("5. Only creates new table when structure changes")
    
    print("\nValidator JSON Structure Analysis:")
    validation_details = validation_result['validation_details']
    print("Field names from validator JSON (become table columns):")
    for field_name in validation_details.keys():
        print(f"  - {field_name}")
    
    print("\n5. 🔄 COMPLETE WORKFLOW")
    print("-" * 60)
    
    print("1. PDFExtractorTool extracts data → JSON output")
    print("2. ValidatorAgent validates data → JSON output with validation_details")
    print("3. DatabaseAgent receives validator JSON → Creates dynamic table")
    print("4. DatabaseAgent stores validation results → Success/error response")
    
    print("\n6. 🎯 KEY JSON FIELDS FOR DATABASE")
    print("-" * 60)
    
    print("✅ validation_status: 'passed' or 'failed'")
    print("✅ is_valid: boolean flag for quick validation check")
    print("✅ validation_details: field-level validation results (becomes table columns)")
    print("✅ errors: list of validation errors")
    print("✅ warnings: list of validation warnings")
    print("✅ overall_score: confidence score (0.0 to 1.0)")
    print("✅ extracted_data: original extracted data")
    print("✅ document_type: type of document processed")

def show_invalid_case_example():
    """Show an invalid case example"""
    
    print("\n" + "="*80)
    print("INVALID CASE EXAMPLE")
    print("="*80)
    
    # Invalid extraction data
    invalid_extraction_data = {
        "status": "success",
        "document_type": "AADHAAR",
        "extraction_confidence": 0.85,
        "extracted_data": {
            "Aadhaar Number": "12345678901",  # 11 digits (invalid)
            "Name": "John123",  # Contains numbers (invalid)
            "DOB": "32/13/1990",  # Invalid date
            "Gender": "X",  # Invalid gender
            "Address": "Short"  # Too short (invalid)
        },
        "warnings": []
    }
    
    print("Invalid Extraction Data:")
    print(json.dumps(invalid_extraction_data, indent=2))
    
    # Validate fields
    validation_details = {}
    
    aadhaar_validation = FieldValidator.validate_aadhaar_number(invalid_extraction_data["extracted_data"]["Aadhaar Number"])
    validation_details["Aadhaar Number"] = aadhaar_validation
    
    name_validation = FieldValidator.validate_name(invalid_extraction_data["extracted_data"]["Name"])
    validation_details["Name"] = name_validation
    
    dob_validation = FieldValidator.validate_date(invalid_extraction_data["extracted_data"]["DOB"])
    validation_details["DOB"] = dob_validation
    
    gender_validation = FieldValidator.validate_gender(invalid_extraction_data["extracted_data"]["Gender"])
    validation_details["Gender"] = gender_validation
    
    address_validation = FieldValidator.validate_address(invalid_extraction_data["extracted_data"]["Address"])
    validation_details["Address"] = address_validation
    
    # Calculate scores
    valid_fields = sum(1 for result in validation_details.values() if result.get('valid', False))
    total_fields = len(validation_details)
    overall_score = valid_fields / total_fields if total_fields > 0 else 0.0
    
    # Collect errors
    errors = []
    warnings = []
    for field_name, field_result in validation_details.items():
        if not field_result.get('valid', False):
            errors.append(f"{field_name}: {field_result.get('reason', 'invalid')}")
    
    # Create validation result
    invalid_validation_result = {
        "validation_status": "failed",
        "document_type": "AADHAAR",
        "validation_details": validation_details,
        "errors": errors,
        "warnings": warnings,
        "overall_score": overall_score,
        "extracted_data": invalid_extraction_data["extracted_data"],
        "is_valid": False
    }
    
    print("\nInvalid Validation Result:")
    print(json.dumps(invalid_validation_result, indent=2))
    
    print("\nField Validation Results:")
    for field_name, field_result in validation_details.items():
        status = "✅ VALID" if field_result.get('valid', False) else "❌ INVALID"
        reason = field_result.get('reason', 'N/A')
        print(f"  {field_name}: {status} ({reason})")

if __name__ == "__main__":
    demonstrate_validator_json_output()
    show_invalid_case_example() 