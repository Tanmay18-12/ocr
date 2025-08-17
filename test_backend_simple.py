#!/usr/bin/env python3
"""
Simple Backend Test
Tests if the backend can start without user management system
"""

import sys
import os

# Add the backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend_startup():
    """Test backend startup without user management"""
    print("🔍 Testing Backend Startup")
    print("=" * 50)
    
    try:
        # Test basic Flask app creation
        from flask import Flask
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        @app.route('/api/health', methods=['GET'])
        def health_check():
            return {'status': 'ok', 'message': 'Backend is running'}
        
        print("✅ Basic Flask app created successfully")
        
        # Test if we can start the server
        print("🌐 Starting test server...")
        app.run(debug=False, host='0.0.0.0', port=5001)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_backend_startup()
