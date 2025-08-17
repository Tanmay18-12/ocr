#!/usr/bin/env python3
"""
Test: Invalid Aadhaar Number Validation
Demonstrates how the system detects various invalid Aadhaar patterns
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import FieldValidator

def test_invalid_aadhaar_patterns():
    """Test various invalid Aadhaar number patterns"""
    print("="*80)
    print("INVALID AADHAAR NUMBER VALIDATION DEMONSTRATION")
    print("="*80)
    
    # Test cases with different types of invalid patterns
    test_cases = [
        # Sequential numbers (common OCR error)
        ("123456789012", "Sequential Numbers", "Detects consecutive digits"),
        ("987654321098", "Reverse Sequential", "Detects reverse consecutive digits"),
        
        # Repeated patterns
        ("111111111111", "All Ones", "Detects repeated single digit"),
        ("222222222222", "All Twos", "Detects repeated single digit"),
        ("123123123123", "Repeated Pattern", "Detects repeated 3-digit pattern"),
        
        # Invalid lengths
        ("12345678901", "Too Short (11 digits)", "Must be exactly 12 digits"),
        ("1234567890123", "Too Long (13 digits)", "Must be exactly 12 digits"),
        ("123456789", "Very Short (9 digits)", "Must be exactly 12 digits"),
        
        # Invalid characters
        ("12345678901A", "Contains Letter", "Must contain only digits"),
        ("12345678901@", "Contains Symbol", "Must contain only digits"),
        ("12345678901 ", "Contains Space", "Must contain only digits"),
        
        # All zeros (suspicious)
        ("000000000000", "All Zeros", "Detects suspicious all-zero pattern"),
        
        # Invalid masked patterns
        ("1234XXX5678", "Invalid Mask (3 X)", "Must have exactly 4 X or * characters"),
        ("1234*****678", "Invalid Mask (5 *)", "Must have exactly 4 X or * characters"),
        ("1234ABC5678", "Invalid Mask (Letters)", "Mask must use X or * only"),
        
        # Mixed patterns
        ("121212121212", "Alternating Pattern", "Detects repeated pattern"),
        
        # Empty and null cases
        ("", "Empty String", "Handles empty input"),
    ]
    
    print(f"{'Pattern':<25} {'Type':<20} {'Result':<15} {'Reason'}")
    print("-" * 80)
    
    for aadhaar, pattern_type, description in test_cases:
        try:
            result = FieldValidator.validate_aadhaar_number(aadhaar)
            status = "❌ INVALID" if not result["valid"] else "✅ VALID"
            reason = result.get("reason", "N/A")
            
            # Handle None values safely
            aadhaar_display = str(aadhaar) if aadhaar is not None else "None"
            
            print(f"{aadhaar_display:<25} {pattern_type:<20} {status:<15} {reason}")
            
        except Exception as e:
            aadhaar_display = str(aadhaar) if aadhaar is not None else "None"
            print(f"{aadhaar_display:<25} {pattern_type:<20} {'❌ ERROR':<15} {str(e)}")
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    # Test a few valid cases for comparison
    valid_cases = [
        ("987654321098", "Valid Unmasked"),
        ("1234XXXX5678", "Valid Masked (X)"),
        ("1234****5678", "Valid Masked (*)"),
    ]
    
    print("\nVALID AADHAAR EXAMPLES:")
    print("-" * 40)
    for aadhaar, description in valid_cases:
        result = FieldValidator.validate_aadhaar_number(aadhaar)
        status = "✅ VALID" if result["valid"] else "❌ INVALID"
        print(f"{aadhaar:<20} {description:<20} {status}")

def demonstrate_validation_logic():
    """Demonstrate the validation logic step by step"""
    print("\n" + "="*80)
    print("VALIDATION LOGIC DEMONSTRATION")
    print("="*80)
    
    # Test a specific invalid case with detailed analysis
    invalid_aadhaar = "123456789012"
    print(f"\nAnalyzing invalid Aadhaar: {invalid_aadhaar}")
    print("-" * 50)
    
    result = FieldValidator.validate_aadhaar_number(invalid_aadhaar)
    
    print(f"Input: {invalid_aadhaar}")
    print(f"Length: {len(invalid_aadhaar)} digits")
    print(f"Contains only digits: {invalid_aadhaar.isdigit()}")
    print(f"Is sequential: {FieldValidator._is_sequential(invalid_aadhaar)}")
    print(f"Has repeated pattern: {FieldValidator._has_repeated_pattern(invalid_aadhaar)}")
    print(f"All zeros: {invalid_aadhaar == '000000000000'}")
    print(f"Final Result: {result}")

def show_validation_categories():
    """Show different categories of validation failures"""
    print("\n" + "="*80)
    print("VALIDATION FAILURE CATEGORIES")
    print("="*80)
    
    categories = {
        "Format Errors": [
            ("12345678901", "Too short"),
            ("1234567890123", "Too long"),
            ("12345678901A", "Contains letters"),
        ],
        "Pattern Detection": [
            ("123456789012", "Sequential numbers"),
            ("111111111111", "Repeated digits"),
            ("121212121212", "Alternating pattern"),
        ],
        "Suspicious Patterns": [
            ("000000000000", "All zeros"),
            ("999999999999", "All nines"),
        ],
        "Mask Errors": [
            ("1234XXX5678", "Wrong number of X"),
            ("1234ABC5678", "Wrong mask characters"),
        ]
    }
    
    for category, cases in categories.items():
        print(f"\n{category}:")
        print("-" * 30)
        for aadhaar, reason in cases:
            result = FieldValidator.validate_aadhaar_number(aadhaar)
            print(f"  {aadhaar} -> {result.get('reason', 'Unknown')}")

if __name__ == "__main__":
    test_invalid_aadhaar_patterns()
    demonstrate_validation_logic()
    show_validation_categories()
    
    print("\n" + "="*80)
    print("TEST COMPLETED - Invalid Aadhaar Detection Working!")
    print("="*80) 