#!/usr/bin/env python3
"""
Test PAN Number Validation Patterns
Tests various PAN number formats and validation rules
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import ValidatorAgent, FieldValidator
from agents.pan_extractor_agent import PANExtractorAgent
import json

def test_pan_validation_patterns():
    """Test PAN number validation with various patterns"""
    print("🔍 Testing PAN Number Validation Patterns")
    print("=" * 60)
    
    # Initialize validator
    validator = ValidatorAgent()
    
    # Test invalid patterns
    print("\n📋 Testing Invalid PAN Patterns:")
    invalid_patterns = [
        ("ABCD1234E", "9 characters - too short"),
        ("ABCDE12345F", "11 characters - too long"),
        ("ABCD1234EF", "Wrong format - 4 letters, 4 digits, 2 letters"),
        ("12345ABCDE", "Wrong format - 5 digits, 5 letters"),
        ("ABCDE1234", "Missing last letter"),
        ("AAAAA0000A", "All A's and 0's - common invalid pattern"),
        ("ZZZZZ9999Z", "All Z's and 9's - common invalid pattern"),
        ("ABCDE1234F", "Sequential pattern - common invalid pattern"),
        ("AAAAA1111A", "All same letters"),
        ("", "Empty string"),
        ("ABCD 1234 E", "With spaces"),
        ("ABCD-1234-E", "With dashes"),
        ("ABCDE1234a", "Last character lowercase"),
        ("abcde1234F", "First 5 characters lowercase"),
        ("ABCDE1234", "Missing last character"),
    ]
    
    for pan, description in invalid_patterns:
        result = FieldValidator.validate_pan_number(pan)
        status = "❌ INVALID" if not result["valid"] else "✅ VALID"
        print(f"{status} | {pan:15} | {description}")
        if not result["valid"]:
            print(f"    Reason: {result.get('reason', 'unknown')}")
    
    print("\n📋 Testing Valid PAN Patterns:")
    valid_patterns = [
        ("ABCDE1234F", "Standard valid PAN"),
        ("PANCD1234E", "Valid PAN with different letters"),
        ("XYZAB5678C", "Valid PAN with different digits"),
        ("MNOPS9012Q", "Valid PAN with different structure"),
    ]
    
    for pan, description in valid_patterns:
        result = FieldValidator.validate_pan_number(pan)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{status} | {pan:15} | {description}")
        if result["valid"]:
            structure = result.get("structure", {})
            print(f"    Structure: {structure.get('letters_part')}-{structure.get('digits_part')}-{structure.get('last_letter')}")

def test_pan_extractor_agent():
    """Test PAN extractor agent with sample text"""
    print("\n🔍 Testing PAN Extractor Agent")
    print("=" * 60)
    
    # Initialize PAN extractor
    pan_extractor = PANExtractorAgent()
    
    # Sample PAN card text
    sample_text = """
    PERMANENT ACCOUNT NUMBER CARD
    
    Name: John Doe
    Father's Name: Robert Doe
    Date of Birth: 15/03/1985
    PAN: ABCDE1234F
    
    Government of India
    Income Tax Department
    """
    
    print("📄 Sample PAN Card Text:")
    print(sample_text)
    
    # Extract fields
    print("\n🔍 Extracting Fields...")
    result = pan_extractor.extract_pan_fields(sample_text)
    
    print("\n📊 Extraction Results:")
    print(json.dumps(result, indent=2))
    
    # Validate extracted PAN
    if result.get("status") == "success":
        extracted_data = result.get("extracted_data", {})
        pan_number = extracted_data.get("PAN Number")
        
        if pan_number:
            print(f"\n🔍 Validating Extracted PAN: {pan_number}")
            validation_result = pan_extractor.validate_pan_number(pan_number)
            print(f"Validation Result: {json.dumps(validation_result, indent=2)}")

def test_comprehensive_validation():
    """Test comprehensive validation patterns"""
    print("\n🔍 Testing Comprehensive Validation")
    print("=" * 60)
    
    validator = ValidatorAgent()
    
    # Test all invalid patterns
    print("\n📋 Running Comprehensive Pattern Tests...")
    test_results = validator.test_invalid_patterns()
    
    print("\n📊 Test Summary:")
    summary = test_results.get("summary", {})
    print(f"Aadhaar Tests: {summary.get('total_aadhaar_tests', 0)} total, {summary.get('invalid_aadhaar_count', 0)} invalid")
    print(f"PAN Tests: {summary.get('total_pan_tests', 0)} total, {summary.get('invalid_pan_count', 0)} invalid")
    
    print("\n📋 PAN Test Details:")
    pan_tests = test_results.get("pan_tests", {})
    for description, test_data in pan_tests.items():
        input_pan = test_data["input"]
        is_invalid = test_data["is_invalid"]
        reason = test_data["validation_result"].get("reason", "unknown")
        status = "❌ INVALID" if is_invalid else "✅ VALID"
        print(f"{status} | {input_pan:15} | {description} | Reason: {reason}")

def test_edge_cases():
    """Test edge cases for PAN validation"""
    print("\n🔍 Testing Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        ("ABCDE1234F", "Perfect valid PAN"),
        ("ABCDE1234f", "Last character lowercase"),
        ("abcde1234F", "First 5 characters lowercase"),
        ("ABCDE1234F ", "Trailing space"),
        (" ABCDE1234F", "Leading space"),
        ("ABCDE 1234F", "Space in middle"),
        ("ABCDE-1234F", "Dash in middle"),
        ("ABCDE1234F.", "Trailing period"),
        ("ABCDE1234F,", "Trailing comma"),
        ("ABCDE1234F;", "Trailing semicolon"),
        ("ABCDE1234F!", "Trailing exclamation"),
        ("ABCDE1234F?", "Trailing question mark"),
        ("ABCDE1234F\n", "Trailing newline"),
        ("ABCDE1234F\t", "Trailing tab"),
    ]
    
    for pan, description in edge_cases:
        result = FieldValidator.validate_pan_number(pan)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{status} | {pan:15} | {description}")
        if not result["valid"]:
            print(f"    Reason: {result.get('reason', 'unknown')}")

def main():
    """Run all PAN validation tests"""
    print("🎯 PAN Card Validation Test Suite")
    print("=" * 60)
    
    try:
        # Test basic validation patterns
        test_pan_validation_patterns()
        
        # Test PAN extractor agent
        test_pan_extractor_agent()
        
        # Test comprehensive validation
        test_comprehensive_validation()
        
        # Test edge cases
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("🎉 All PAN validation tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()



