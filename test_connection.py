#!/usr/bin/env python3
"""
Comprehensive Connection Test Script
Tests frontend-backend connectivity, API endpoints, and duplicate handling
"""

import requests
import json
import time
import os
from datetime import datetime

def test_backend_health():
    """Test backend health endpoint"""
    print("🔍 Testing Backend Health...")
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Backend Health Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health Error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("🔍 Testing Root Endpoint...")
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root Endpoint: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Root Endpoint Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root Endpoint Error: {e}")
        return False

def test_stats_endpoint():
    """Test stats endpoint"""
    print("🔍 Testing Stats Endpoint...")
    try:
        response = requests.get('http://localhost:5000/api/stats', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats Endpoint: {data.get('message', 'OK')}")
            return True
        else:
            print(f"❌ Stats Endpoint Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats Endpoint Error: {e}")
        return False

def test_duplicate_check():
    """Test duplicate checking functionality"""
    print("🔍 Testing Duplicate Check...")
    try:
        # Test with a sample Aadhaar number
        test_data = {
            "documentNumber": "123456789012",
            "documentType": "AADHAAR"
        }
        
        response = requests.post(
            'http://localhost:5000/api/check-duplicate',
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            exists = data.get('data', {}).get('exists', False)
            print(f"✅ Duplicate Check: Aadhaar {test_data['documentNumber']} exists: {exists}")
            return True
        else:
            print(f"❌ Duplicate Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Duplicate Check Error: {e}")
        return False

def test_cors_headers():
    """Test CORS headers"""
    print("🔍 Testing CORS Headers...")
    try:
        response = requests.options('http://localhost:5000/api/health', timeout=10)
        cors_headers = response.headers.get('Access-Control-Allow-Origin')
        if cors_headers:
            print(f"✅ CORS Headers: {cors_headers}")
            return True
        else:
            print("❌ CORS Headers Missing")
            return False
    except Exception as e:
        print(f"❌ CORS Test Error: {e}")
        return False

def test_frontend_proxy():
    """Test if frontend proxy is working"""
    print("🔍 Testing Frontend Proxy...")
    try:
        # Test if React dev server is running
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Server: Running on port 3000")
            return True
        else:
            print(f"❌ Frontend Server: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend Server: Not running or error - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Connection Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Root Endpoint", test_root_endpoint),
        ("Stats Endpoint", test_stats_endpoint),
        ("Duplicate Check", test_duplicate_check),
        ("CORS Headers", test_cors_headers),
        ("Frontend Proxy", test_frontend_proxy),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} Exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Frontend-backend connection is working perfectly.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("❌ Multiple tests failed. Please check your setup.")
    
    print("\n💡 Recommendations:")
    if not any(name == "Backend Health" and success for name, success in results):
        print("  - Start the backend server: cd backend && python app.py")
    if not any(name == "Frontend Proxy" and success for name, success in results):
        print("  - Start the frontend server: cd frontend && npm start")
    if not any(name == "CORS Headers" and success for name, success in results):
        print("  - Check CORS configuration in backend/app.py")

if __name__ == "__main__":
    main()

