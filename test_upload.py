#!/usr/bin/env python3
"""
Test Document Upload Script
Tests the document upload functionality to verify storage is working
"""

import requests
import os
import json
from datetime import datetime

def test_document_upload():
    """Test document upload functionality"""
    print("🚀 Testing Document Upload Functionality")
    print("=" * 50)
    
    # Check if we have a sample document
    sample_docs = [
        "sample_documents/aadhar_sample_2.pdf",
        "backend/uploads/20250817_160358_aadhar_sample_2.pdf"
    ]
    
    test_file = None
    for doc in sample_docs:
        if os.path.exists(doc):
            test_file = doc
            break
    
    if not test_file:
        print("❌ No sample document found for testing")
        print("Please place a sample Aadhaar PDF in sample_documents/ or backend/uploads/")
        return False
    
    print(f"📄 Using test file: {test_file}")
    
    # Test upload
    try:
        url = "http://localhost:5000/api/upload"
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {'documentType': 'AADHAAR'}
            
            print("🔄 Uploading document...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"📋 Result: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"📋 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during upload test: {e}")
        return False

def test_duplicate_upload():
    """Test duplicate document upload"""
    print("\n🔄 Testing Duplicate Upload...")
    print("=" * 30)
    
    # Check if we have a sample document
    sample_docs = [
        "sample_documents/aadhar_sample_2.pdf",
        "backend/uploads/20250817_160358_aadhar_sample_2.pdf"
    ]
    
    test_file = None
    for doc in sample_docs:
        if os.path.exists(doc):
            test_file = doc
            break
    
    if not test_file:
        print("❌ No sample document found for duplicate testing")
        return False
    
    try:
        url = "http://localhost:5000/api/upload"
        
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {'documentType': 'AADHAAR'}
            
            print("🔄 Uploading duplicate document...")
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 409:
                result = response.json()
                print("✅ Duplicate detection working!")
                print(f"📋 Result: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"⚠️ Expected 409 (duplicate) but got {response.status_code}")
                print(f"📋 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during duplicate test: {e}")
        return False

def main():
    """Run all tests"""
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test basic upload
    upload_success = test_document_upload()
    
    # Test duplicate upload
    duplicate_success = test_duplicate_upload()
    
    print("\n" + "=" * 50)
    print("📊 UPLOAD TEST SUMMARY")
    print("=" * 50)
    
    if upload_success:
        print("✅ Document upload: SUCCESS")
    else:
        print("❌ Document upload: FAILED")
    
    if duplicate_success:
        print("✅ Duplicate detection: SUCCESS")
    else:
        print("❌ Duplicate detection: FAILED")
    
    if upload_success and duplicate_success:
        print("\n🎉 All upload tests passed!")
        print("✅ Storage issue has been resolved!")
    else:
        print("\n⚠️ Some upload tests failed.")
        print("Please check the errors above.")

if __name__ == "__main__":
    main()
