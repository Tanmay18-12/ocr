#!/usr/bin/env python3
"""
Test: 11-Digit Aadhaar Number (Invalid Case)
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.validator_agent import FieldValidator

def test_11_digit_aadhaar():
    """Test an 11-digit Aadhaar number (invalid case)"""
    
    # Test an 11-digit Aadhaar number
    invalid_aadhaar = "12345678901"  # 11 digits instead of 12
    
    print("="*60)
    print("11-DIGIT AADHAAR NUMBER (INVALID CASE)")
    print("="*60)
    
    print(f"Input Aadhaar: {invalid_aadhaar}")
    print(f"Length: {len(invalid_aadhaar)} digits")
    print(f"Problem: Aadhaar number must be exactly 12 digits")
    
    # Validate the number
    result = FieldValidator.validate_aadhaar_number(invalid_aadhaar)
    
    print(f"\nValidation Result:")
    print(f"  Valid: {result['valid']}")
    print(f"  Type: {result['type']}")
    print(f"  Reason: {result['reason']}")
    
    print(f"\nDetailed Analysis:")
    print(f"  Length: {len(invalid_aadhaar)} digits ❌ (should be 12)")
    print(f"  All digits: {invalid_aadhaar.isdigit()} ✓")
    print(f"  Expected length: 12 digits")
    print(f"  Actual length: {len(invalid_aadhaar)} digits")
    
    print(f"\nConclusion: ❌ INVALID - {result['reason']}")
    print("="*60)

if __name__ == "__main__":
    test_11_digit_aadhaar() 