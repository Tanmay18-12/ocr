#!/usr/bin/env python3
"""
Debug script to test backend processing without Flask
This will help identify the exact issue with document processing
"""

import sys
import os
import tempfile
import shutil

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_extractor_with_sample_file():
    """Test the extractor with a sample file"""
    print("🔍 Testing extractor with sample file...")
    
    # Check if sample file exists
    sample_files = [
        "sample_documents/aadhar_sample 1.pdf",
        "sample_documents/aadhar_sample.pdf",
        "sample_documents/aadhaar_sample.pdf"
    ]
    
    sample_file = None
    for file_path in sample_files:
        if os.path.exists(file_path):
            sample_file = file_path
            break
    
    if not sample_file:
        print("❌ No sample file found. Please ensure you have a sample document.")
        return False
    
    print(f"📄 Using sample file: {sample_file}")
    
    try:
        # Import the extractor
        from aadhaar_extractor_with_sql import AadhaarExtractionTool
        
        # Initialize extractor
        print("🔧 Initializing extractor...")
        extractor = AadhaarExtractionTool()
        print("✅ Extractor initialized successfully")
        
        # Test extraction
        print("🔄 Testing extraction...")
        result = extractor.extract_and_store(sample_file)
        
        print("📊 Extraction result:")
        print(f"  Overall Status: {result.get('overall_status', 'unknown')}")
        print(f"  Extraction Status: {result.get('extraction', {}).get('status', 'unknown')}")
        print(f"  Storage Status: {result.get('storage', {}).get('status', 'unknown')}")
        
        if result.get('extraction'):
            extraction = result['extraction']
            print(f"  Extraction Details:")
            print(f"    Document Type: {extraction.get('document_type', 'unknown')}")
            print(f"    Confidence: {extraction.get('extraction_confidence', 0)}")
            print(f"    Extracted Data: {list(extraction.get('extracted_data', {}).keys())}")
        
        if result.get('storage'):
            storage = result['storage']
            print(f"  Storage Details:")
            print(f"    Status: {storage.get('status', 'unknown')}")
            if 'error_message' in storage:
                print(f"    Error: {storage['error_message']}")
        
        # Both 'success' and 'duplicate_rejected' are valid outcomes
        status = result.get('overall_status')
        is_valid = status in ['success', 'duplicate_rejected']
        
        if status == 'duplicate_rejected':
            print("✅ Duplicate detection working correctly!")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extractor_with_temp_file():
    """Test the extractor with a temporary file (simulating upload)"""
    print("\n🔍 Testing extractor with temporary file (simulating upload)...")
    
    # Check if sample file exists
    sample_file = "sample_documents/aadhar_sample 1.pdf"
    if not os.path.exists(sample_file):
        print("❌ Sample file not found for temp test")
        return False
    
    try:
        # Create temporary file (simulating upload)
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "uploaded_document.pdf")
        
        # Copy sample to temp location
        shutil.copy2(sample_file, temp_file)
        print(f"📁 Created temporary file: {temp_file}")
        
        # Import and initialize extractor
        from aadhaar_extractor_with_sql import AadhaarExtractionTool
        extractor = AadhaarExtractionTool()
        
        # Test extraction with temp file
        print("🔄 Testing extraction with temp file...")
        result = extractor.extract_and_store(temp_file)
        
        print("📊 Temp file extraction result:")
        print(f"  Overall Status: {result.get('overall_status', 'unknown')}")
        
        # Clean up
        try:
            os.remove(temp_file)
            os.rmdir(temp_dir)
            print("🗑️ Cleaned up temporary files")
        except:
            pass
        
        return result.get('overall_status') == 'success'
        
    except Exception as e:
        print(f"❌ Temp file extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_initialization():
    """Test if backend components can be initialized like in Flask app"""
    print("\n🔍 Testing backend initialization (like Flask app)...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from aadhaar_extractor_with_sql import AadhaarExtractionTool
        from pan_extractor_with_sql import PANExtractionTool
        from user_management_demo import UserManagementSystem
        print("✅ All imports successful")
        
        # Test initialization
        print("🔧 Testing initialization...")
        aadhaar_extractor = AadhaarExtractionTool()
        print("✅ Aadhaar extractor initialized")
        
        pan_extractor = PANExtractionTool()
        print("✅ PAN extractor initialized")
        
        user_system = UserManagementSystem()
        print("✅ User management system initialized")
        
        return True, (aadhaar_extractor, pan_extractor, user_system)
        
    except Exception as e:
        print(f"❌ Backend initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Run all debug tests"""
    print("🚀 Backend Processing Debug")
    print("=" * 50)
    
    # Test 1: Backend initialization
    init_success, components = test_backend_initialization()
    if not init_success:
        print("\n❌ Backend initialization failed. Cannot proceed with other tests.")
        return False
    
    # Test 2: Sample file extraction
    sample_success = test_extractor_with_sample_file()
    
    # Test 3: Temp file extraction (simulating upload)
    temp_success = test_extractor_with_temp_file()
    
    print("\n" + "=" * 50)
    print("📊 DEBUG RESULTS SUMMARY:")
    print(f"  Backend Initialization: {'✅ PASS' if init_success else '❌ FAIL'}")
    print(f"  Sample File Extraction: {'✅ PASS' if sample_success else '❌ FAIL'}")
    print(f"  Temp File Extraction: {'✅ PASS' if temp_success else '❌ FAIL'}")
    
    if init_success and sample_success and temp_success:
        print("\n✅ All tests passed! Backend processing should work.")
        print("💡 The issue might be in Flask request handling or file upload process.")
    else:
        print("\n❌ Some tests failed. This explains the 500 error in the backend.")
        print("💡 Fix the failing components before testing the frontend again.")
    
    return init_success and sample_success and temp_success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)