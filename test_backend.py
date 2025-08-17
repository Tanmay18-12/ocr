#!/usr/bin/env python3
"""
Test script to verify backend functionality
Run this to test if the extractors work before starting the Flask server
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from aadhaar_extractor_with_sql import AadhaarExtractionTool
        print("✅ AadhaarExtractionTool imported successfully")
        
        from pan_extractor_with_sql import PANExtractionTool
        print("✅ PANExtractionTool imported successfully")
        
        from user_management_demo import UserManagementSystem
        print("✅ UserManagementSystem imported successfully")
        
        return True, (AadhaarExtractionTool, PANExtractionTool, UserManagementSystem)
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False, None

def test_extractor_initialization():
    """Test if extractors can be initialized"""
    print("\n🔧 Testing extractor initialization...")
    
    success, modules = test_imports()
    if not success:
        return False
    
    AadhaarExtractionTool, PANExtractionTool, UserManagementSystem = modules
    
    try:
        # Test Aadhaar extractor
        aadhaar_extractor = AadhaarExtractionTool()
        print("✅ Aadhaar extractor initialized")
        
        # Test PAN extractor
        pan_extractor = PANExtractionTool()
        print("✅ PAN extractor initialized")
        
        # Test user management system
        user_system = UserManagementSystem()
        print("✅ User management system initialized")
        
        return True, (aadhaar_extractor, pan_extractor, user_system)
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False, None

def test_basic_functionality():
    """Test basic functionality without file processing"""
    print("\n🧪 Testing basic functionality...")
    
    success, extractors = test_extractor_initialization()
    if not success:
        return False
    
    aadhaar_extractor, pan_extractor, user_system = extractors
    
    try:
        # Test user statistics
        stats = user_system.get_system_statistics()
        print(f"✅ System statistics retrieved: {stats.get('user_statistics', {}).get('total_users', 0)} users")
        
        # Test duplicate checking
        aadhaar_check = aadhaar_extractor.check_aadhaar_exists("123456789012")
        print(f"✅ Aadhaar duplicate check works: {aadhaar_check.get('exists', False)}")
        
        pan_check = pan_extractor.check_pan_exists("ABCDE1234F")
        print(f"✅ PAN duplicate check works: {pan_check.get('exists', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_sample_document():
    """Test with a sample document if available"""
    print("\n📄 Testing sample document processing...")
    
    # Check if sample documents exist
    sample_files = [
        "sample_documents/aadhar_sample 1.pdf",
        "sample_documents/aadhar_sample.pdf",
        "sample_documents/pan_sample.pdf"
    ]
    
    available_samples = []
    for sample in sample_files:
        if os.path.exists(sample):
            available_samples.append(sample)
    
    if not available_samples:
        print("⚠️ No sample documents found. Skipping document processing test.")
        return True
    
    success, extractors = test_extractor_initialization()
    if not success:
        return False
    
    aadhaar_extractor, pan_extractor, user_system = extractors
    
    # Test with first available sample
    sample_file = available_samples[0]
    print(f"📄 Testing with: {sample_file}")
    
    try:
        if 'aadhar' in sample_file.lower() or 'aadhaar' in sample_file.lower():
            result = aadhaar_extractor.extract_and_store(sample_file)
        else:
            result = pan_extractor.extract_and_store(sample_file)
        
        print(f"✅ Document processing result: {result.get('overall_status', 'unknown')}")
        
        if result.get('overall_status') == 'success':
            extracted_data = result.get('extraction', {}).get('extracted_data', {})
            print(f"📋 Extracted fields: {list(extracted_data.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Backend Functionality Test")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports()[0]:
        print("\n❌ Import test failed. Cannot proceed.")
        return False
    
    # Test 2: Initialization
    if not test_extractor_initialization()[0]:
        print("\n❌ Initialization test failed. Cannot proceed.")
        return False
    
    # Test 3: Basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality test failed.")
        return False
    
    # Test 4: Sample document (optional)
    test_sample_document()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    print("🚀 Backend should work properly with Flask server.")
    print("\nTo start the backend server:")
    print("  cd backend")
    print("  backend_env\\Scripts\\activate")
    print("  python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Tests failed. Please fix the issues before starting the backend server.")
        sys.exit(1)