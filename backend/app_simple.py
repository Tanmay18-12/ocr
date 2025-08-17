#!/usr/bin/env python3
"""
Simplified Flask Backend for Testing
Bypasses user management system to isolate storage issues
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3

# Add the parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import extractors
try:
    from aadhaar_extractor_simple import SimpleAadhaarExtractionTool
    from pan_extractor_with_sql import PANExtractionTool
    print("✅ Successfully imported extractors")
except Exception as e:
    print(f"❌ Error importing extractors: {e}")
    SimpleAadhaarExtractionTool = None
    PANExtractionTool = None

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extractors
aadhaar_extractor = None
pan_extractor = None

try:
    if SimpleAadhaarExtractionTool:
        aadhaar_extractor = SimpleAadhaarExtractionTool()
        print("✅ Aadhaar extractor initialized")
    
    if PANExtractionTool:
        pan_extractor = PANExtractionTool()
        print("✅ PAN extractor initialized")
except Exception as e:
    print(f"❌ Error initializing extractors: {e}")

def format_response(success=True, message="", data=None, error=None):
    """Format API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error is not None:
        response["error"] = error
    
    return response

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(format_response(
        success=True,
        message="Backend is running",
        data={
            'aadhaar_extractor': aadhaar_extractor is not None,
            'pan_extractor': pan_extractor is not None,
            'timestamp': datetime.now().isoformat()
        }
    ))

@app.route('/api/upload', methods=['POST'])
def upload_document():
    """Upload and process document"""
    try:
        if 'file' not in request.files:
            return jsonify(format_response(
                success=False,
                message="No file provided",
                error="NO_FILE"
            )), 400
        
        file = request.files['file']
        document_type = request.form.get('documentType', 'AADHAAR').upper()
        
        if file.filename == '':
            return jsonify(format_response(
                success=False,
                message="No file selected",
                error="NO_FILE_SELECTED"
            )), 400
        
        if file:
            # Save file temporarily
            filename = file.filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            file.save(filepath)
            
            # Check if extractors are available
            if document_type == 'AADHAAR' and aadhaar_extractor is None:
                return jsonify(format_response(
                    success=False,
                    message="Aadhaar extractor not available",
                    error="EXTRACTOR_NOT_AVAILABLE"
                )), 503
            
            if document_type == 'PAN' and pan_extractor is None:
                return jsonify(format_response(
                    success=False,
                    message="PAN extractor not available",
                    error="EXTRACTOR_NOT_AVAILABLE"
                )), 503
            
            # Process document
            print(f"🔄 Processing {document_type} document: {filepath}")
            
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
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except:
                pass
            
            # Format response
            if result.get('overall_status') == 'success':
                extracted_data = result.get('extraction', {}).get('extracted_data', {})
                
                return jsonify(format_response(
                    success=True,
                    message="Document processed successfully",
                    data={
                        'documentType': document_type,
                        'extractedFields': extracted_data,
                        'confidence': result.get('extraction', {}).get('extraction_confidence', 0),
                        'processingTime': result.get('extraction', {}).get('extraction_timestamp')
                    }
                ))
            
            elif result.get('overall_status') == 'duplicate_rejected':
                return jsonify(format_response(
                    success=False,
                    message="Duplicate document detected",
                    error="DUPLICATE_DOCUMENT",
                    data={
                        'documentType': document_type,
                        'extractedFields': result.get('extraction', {}).get('extracted_data', {}),
                        'confidence': result.get('extraction', {}).get('extraction_confidence', 0)
                    }
                )), 409
            
            else:
                # Check if extraction was successful but storage failed
                extraction_status = result.get('extraction', {}).get('status', 'unknown')
                if extraction_status == 'success':
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
                    error_message = result.get('extraction', {}).get('error_message', 'Document extraction failed')
                    return jsonify(format_response(
                        success=False,
                        message=error_message,
                        error="EXTRACTION_FAILED"
                    )), 500
    
    except Exception as e:
        print(f"❌ Error in upload_document: {e}")
        return jsonify(format_response(
            success=False,
            message=f"Server error: {str(e)}",
            error="SERVER_ERROR"
        )), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    return jsonify(format_response(
        success=True,
        message="Statistics retrieved successfully",
        data={
            'aadhaar_extractor': aadhaar_extractor is not None,
            'pan_extractor': pan_extractor is not None,
            'timestamp': datetime.now().isoformat()
        }
    ))

if __name__ == '__main__':
    print("🚀 Starting Simplified Flask Backend Server...")
    print("🌐 Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
