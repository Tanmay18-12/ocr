#!/usr/bin/env python3
"""
Flask Backend API for Document Processing
Provides REST API endpoints for the React frontend
"""

import os
import sys
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime

# Add parent directory to path to import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

print(f"Looking for modules in: {parent_dir}")

try:
    from aadhaar_extractor_with_sql import AadhaarExtractionTool
    print("✅ Successfully imported AadhaarExtractionTool")
    from pan_extractor_with_sql import PANExtractionTool
    print("✅ Successfully imported PANExtractionTool")
    from user_management_demo import UserManagementSystem
    print("✅ Successfully imported UserManagementSystem")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print("Available files in parent directory:")
    try:
        for file in os.listdir(parent_dir):
            if file.endswith('.py'):
                print(f"  - {file}")
    except:
        pass
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extractors
try:
    print("🔧 Initializing extractors...")
    aadhaar_extractor = AadhaarExtractionTool()
    print("✅ Aadhaar extractor initialized")
    
    pan_extractor = PANExtractionTool()
    print("✅ PAN extractor initialized")
    
    user_system = UserManagementSystem()
    print("✅ User management system initialized")
    
except Exception as e:
    print(f"❌ Failed to initialize extractors: {e}")
    print("This might be due to missing dependencies or database issues")
    # Continue anyway for basic API functionality
    aadhaar_extractor = None
    pan_extractor = None
    user_system = None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_response(success=True, message="", data=None, error=None):
    """Format standardized API response"""
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    if error is not None:
        response['error'] = error
    
    return response

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify(format_response(
        success=True,
        message="Document Processing API is running",
        data={'status': 'healthy', 'version': '1.0.0', 'endpoints': [
            '/api/health',
            '/api/upload',
            '/api/check-duplicate',
            '/api/stats'
        ]}
    ))

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(format_response(
        success=True,
        message="API is running",
        data={'status': 'healthy', 'version': '1.0.0'}
    ))

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process document"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify(format_response(
                success=False,
                message="No file provided",
                error="FILE_MISSING"
            )), 400
        
        file = request.files['file']
        document_type = request.form.get('documentType', 'AADHAAR').upper()
        
        # Check if file is selected
        if file.filename == '':
            return jsonify(format_response(
                success=False,
                message="No file selected",
                error="FILE_NOT_SELECTED"
            )), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify(format_response(
                success=False,
                message="Invalid file type. Only PDF, PNG, JPG, JPEG allowed",
                error="INVALID_FILE_TYPE"
            )), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        # Check if extractors are available
        if document_type == 'AADHAAR' and aadhaar_extractor is None:
            return jsonify(format_response(
                success=False,
                message="Aadhaar extractor not available. Please check server setup.",
                error="EXTRACTOR_NOT_AVAILABLE"
            )), 503
        
        if document_type == 'PAN' and pan_extractor is None:
            return jsonify(format_response(
                success=False,
                message="PAN extractor not available. Please check server setup.",
                error="EXTRACTOR_NOT_AVAILABLE"
            )), 503
        
        # Process document based on type
        print(f"🔄 Processing {document_type} document: {filepath}")
        print(f"📁 File size: {os.path.getsize(filepath)} bytes")
        
        if document_type == 'AADHAAR':
            result = aadhaar_extractor.extract_and_store(filepath)
        elif document_type == 'PAN':
            result = pan_extractor.extract_and_store(filepath)
        else:
            return jsonify(format_response(
                success=False,
                message="Invalid document type. Use AADHAAR or PAN",
                error="INVALID_DOCUMENT_TYPE"
            )), 400
        
        print(f"📊 Processing result: {result.get('overall_status', 'unknown')}")
        print(f"📊 Full result keys: {list(result.keys())}")
        
        # Log detailed result for debugging
        if result.get('extraction'):
            extraction = result['extraction']
            print(f"📊 Extraction status: {extraction.get('status', 'unknown')}")
            print(f"📊 Extraction confidence: {extraction.get('extraction_confidence', 0)}")
            print(f"📊 Extracted fields: {list(extraction.get('extracted_data', {}).keys())}")
        
        if result.get('storage'):
            storage = result['storage']
            print(f"📊 Storage status: {storage.get('status', 'unknown')}")
            if 'error' in storage:
                print(f"📊 Storage error: {storage.get('error', {})}")
            if 'error_message' in storage:
                print(f"📊 Storage error message: {storage.get('error_message', '')}")
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass  # Ignore cleanup errors
        
        # Format response based on processing result
        if result.get('overall_status') == 'success':
            extracted_data = result.get('extraction', {}).get('extracted_data', {})
            
            return jsonify(format_response(
                success=True,
                message="Document processed successfully",
                data={
                    'documentType': document_type,
                    'extractedFields': extracted_data,
                    'userId': result.get('user_id'),
                    'confidence': result.get('extraction', {}).get('extraction_confidence', 0),
                    'processingTime': result.get('extraction', {}).get('extraction_timestamp')
                }
            ))
        
        elif result.get('overall_status') == 'duplicate_rejected':
            # Handle duplicate as a special case, not an error
            return jsonify(format_response(
                success=False,
                message="Duplicate document detected - this Aadhaar/PAN already exists in the system",
                error="DUPLICATE_DOCUMENT",
                data={
                    'documentType': document_type,
                    'duplicateInfo': result.get('duplicate_info'),
                    'existingRecord': result.get('storage', {}).get('details', {}),
                    'extractedFields': result.get('extraction', {}).get('extracted_data', {}),
                    'confidence': result.get('extraction', {}).get('extraction_confidence', 0)
                }
            )), 409
        
        else:
            # Check if extraction was successful but storage failed
            extraction_status = result.get('extraction', {}).get('status', 'unknown')
            if extraction_status == 'success':
                # Extraction worked, but storage had issues
                extracted_data = result.get('extraction', {}).get('extracted_data', {})
                storage_error = result.get('storage', {}).get('error_message', 'Storage failed')
                
                return jsonify(format_response(
                    success=False,
                    message=f"Document extracted successfully but storage failed: {storage_error}",
                    error="STORAGE_FAILED",
                    data={
                        'documentType': document_type,
                        'extractedFields': extracted_data,
                        'confidence': result.get('extraction', {}).get('extraction_confidence', 0),
                        'storageError': storage_error
                    }
                )), 500
            else:
                # Extraction itself failed
                error_message = result.get('extraction', {}).get('error_message', 'Document extraction failed')
                return jsonify(format_response(
                    success=False,
                    message=error_message,
                    error="EXTRACTION_FAILED"
                )), 500
    
    except Exception as e:
        return jsonify(format_response(
            success=False,
            message=f"Server error: {str(e)}",
            error="SERVER_ERROR"
        )), 500

@app.route('/api/check-duplicate', methods=['POST'])
def check_duplicate():
    """Check if document number already exists"""
    try:
        data = request.get_json()
        document_number = data.get('documentNumber')
        document_type = data.get('documentType', 'AADHAAR').upper()
        
        if not document_number:
            return jsonify(format_response(
                success=False,
                message="Document number is required",
                error="MISSING_DOCUMENT_NUMBER"
            )), 400
        
        # Check for existing document
        if document_type == 'AADHAAR':
            result = aadhaar_extractor.check_aadhaar_exists(document_number)
        elif document_type == 'PAN':
            result = pan_extractor.check_pan_exists(document_number)
        else:
            return jsonify(format_response(
                success=False,
                message="Invalid document type",
                error="INVALID_DOCUMENT_TYPE"
            )), 400
        
        return jsonify(format_response(
            success=True,
            message="Duplicate check completed",
            data={
                'exists': result.get('exists', False),
                'documentNumber': document_number,
                'documentType': document_type,
                'existingRecord': result.get('existing_record') if result.get('exists') else None
            }
        ))
    
    except Exception as e:
        return jsonify(format_response(
            success=False,
            message=f"Server error: {str(e)}",
            error="SERVER_ERROR"
        )), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = user_system.get_system_statistics()
        
        return jsonify(format_response(
            success=True,
            message="Statistics retrieved successfully",
            data=stats
        ))
    
    except Exception as e:
        return jsonify(format_response(
            success=False,
            message=f"Failed to get statistics: {str(e)}",
            error="STATS_ERROR"
        )), 500

@app.route('/api/user/<user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    """Get all documents for a specific user"""
    try:
        documents = user_system.get_user_documents(user_id)
        
        return jsonify(format_response(
            success=True,
            message="User documents retrieved successfully",
            data=documents
        ))
    
    except Exception as e:
        return jsonify(format_response(
            success=False,
            message=f"Failed to get user documents: {str(e)}",
            error="USER_DOCS_ERROR"
        )), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify(format_response(
        success=False,
        message="File too large. Maximum size is 16MB",
        error="FILE_TOO_LARGE"
    )), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify(format_response(
        success=False,
        message="Endpoint not found",
        error="NOT_FOUND"
    )), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify(format_response(
        success=False,
        message="Internal server error",
        error="INTERNAL_ERROR"
    )), 500

if __name__ == '__main__':
    print("🚀 Starting Flask Backend Server...")
    
    # Initialize system on startup if available
    if user_system is not None:
        print("🔧 Initializing User Management System...")
        try:
            setup_result = user_system.setup_system()
            
            if setup_result['system_ready']:
                print("✅ User Management System ready!")
            else:
                print("⚠️ User Management System setup had issues:")
                for error in setup_result.get('errors', []):
                    print(f"  - {error}")
                print("🔄 Continuing with basic functionality...")
        except Exception as e:
            print(f"⚠️ User Management System initialization failed: {e}")
            print("🔄 Continuing with basic functionality...")
    else:
        print("⚠️ User Management System not available")
        print("🔄 Starting server with basic functionality...")
    
    print("🌐 Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)