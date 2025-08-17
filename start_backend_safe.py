#!/usr/bin/env python3
"""
Safe backend startup script
Tests functionality first, then starts the Flask server
"""

import sys
import os
import subprocess
import time

def run_tests():
    """Run the test script first"""
    print("🧪 Running backend tests first...")
    
    try:
        result = subprocess.run([sys.executable, "test_backend.py"], 
                              capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting Flask backend server...")
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return False
    
    # Check if virtual environment exists
    venv_path = os.path.join(backend_dir, "backend_env", "Scripts", "python.exe")
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found. Please run setup first.")
        return False
    
    # Start the Flask server
    app_path = os.path.join(backend_dir, "app.py")
    
    try:
        print("🌐 Backend server starting on http://localhost:5000")
        print("📝 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Run the Flask app
        subprocess.run([venv_path, app_path], cwd=backend_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Safe Backend Startup")
    print("=" * 40)
    
    # Step 1: Run tests
    if not run_tests():
        print("\n❌ Tests failed. Please fix the issues before starting the server.")
        print("\nCommon issues:")
        print("1. Missing dependencies - run: pip install -r backend/requirements.txt")
        print("2. Missing database files - run: python user_management_demo.py --setup")
        print("3. Import path issues - ensure all Python files are in the correct location")
        return False
    
    print("\n✅ All tests passed!")
    print("🚀 Starting backend server...")
    time.sleep(2)
    
    # Step 2: Start backend
    start_backend()

if __name__ == "__main__":
    main()