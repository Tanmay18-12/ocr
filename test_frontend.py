#!/usr/bin/env python3
"""
Test script to verify frontend setup
"""

import os
import subprocess
import sys
import json

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js installed: {version}")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False

def check_npm_installed():
    """Check if npm is installed"""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ npm installed: {version}")
            return True
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not installed")
        return False

def check_frontend_directory():
    """Check if frontend directory exists with required files"""
    frontend_dir = "frontend"
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found")
        return False
    
    print("✅ Frontend directory exists")
    
    # Check package.json
    package_json_path = os.path.join(frontend_dir, "package.json")
    if not os.path.exists(package_json_path):
        print("❌ package.json not found")
        return False
    
    print("✅ package.json exists")
    
    # Check if dependencies are installed
    node_modules_path = os.path.join(frontend_dir, "node_modules")
    if not os.path.exists(node_modules_path):
        print("⚠️ node_modules not found - dependencies need to be installed")
        return False
    
    print("✅ node_modules exists")
    return True

def install_dependencies():
    """Install npm dependencies"""
    print("📦 Installing npm dependencies...")
    
    try:
        result = subprocess.run(["npm", "install"], 
                              cwd="frontend", 
                              capture_output=True, 
                              text=True,
                              timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Installation timed out")
        return False
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def test_backend_connection():
    """Test if backend is running"""
    print("🔗 Testing backend connection...")
    
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
            return True
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️ requests library not available for testing")
        return True  # Skip this test
    except Exception as e:
        print(f"⚠️ Backend not accessible: {e}")
        print("💡 Make sure to start the backend first")
        return False

def main():
    """Run all frontend tests"""
    print("🎯 Frontend Setup Test")
    print("=" * 40)
    
    # Test 1: Node.js
    if not check_node_installed():
        print("\n❌ Please install Node.js from https://nodejs.org/")
        return False
    
    # Test 2: npm
    if not check_npm_installed():
        print("\n❌ npm should come with Node.js installation")
        return False
    
    # Test 3: Frontend directory
    if not check_frontend_directory():
        print("\n❌ Frontend setup incomplete")
        
        # Try to install dependencies
        if os.path.exists("frontend/package.json"):
            print("🔧 Attempting to install dependencies...")
            if install_dependencies():
                print("✅ Dependencies installed")
            else:
                return False
        else:
            return False
    
    # Test 4: Backend connection (optional)
    test_backend_connection()
    
    print("\n" + "=" * 40)
    print("✅ Frontend tests completed!")
    print("\nTo start the frontend:")
    print("  cd frontend")
    print("  npm start")
    print("\nThe frontend will be available at http://localhost:3000")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Frontend tests failed. Please fix the issues.")
        sys.exit(1)