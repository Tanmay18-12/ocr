# Document Processing System - Setup Guide

## 🚀 Quick Start

This guide will help you set up and run the Document Processing System with proper frontend-backend connectivity and duplicate handling.

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Tesseract OCR installed on your system

## 🏗️ Project Structure

```
newocr3/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── backend_env/        # Python virtual environment
│   └── uploads/            # Temporary file uploads
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── App.js          # Main React app
│   └── package.json        # Frontend dependencies
└── test_connection.py      # Connection test script
```

## 🔧 Backend Setup

### 1. Activate Virtual Environment
```bash
cd backend
backend_env\Scripts\Activate.ps1  # Windows PowerShell
# OR
source backend_env/bin/activate   # Linux/Mac
```

### 2. Install Dependencies (if needed)
```bash
pip install flask flask-cors pytesseract pdf2image pillow
```

### 3. Start Backend Server
```bash
python app.py
```

The backend will start on `http://localhost:5000`

## 🎨 Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Frontend Server
```bash
npm start
```

The frontend will start on `http://localhost:3000`

## 🔗 Connection Configuration

### Frontend-Backend Connection
- **Proxy Configuration**: Frontend uses proxy in `package.json` to forward API calls to backend
- **Direct API**: Fallback direct connection via `api-direct.js`
- **CORS**: Backend has CORS enabled for cross-origin requests

### API Endpoints
- `GET /api/health` - Health check
- `POST /api/upload` - Document upload and processing
- `POST /api/check-duplicate` - Duplicate document checking
- `GET /api/stats` - System statistics

## 🚫 Duplicate Handling

### How It Works
1. **Detection**: System checks for existing Aadhaar/PAN numbers before processing
2. **Response**: Returns `409` status with detailed duplicate information
3. **UI Display**: Frontend shows warning toast and detailed duplicate information
4. **No Errors**: Duplicates are handled gracefully without throwing errors

### Duplicate Response Format
```json
{
  "success": false,
  "message": "Duplicate document detected - this Aadhaar/PAN already exists in the system",
  "error": "DUPLICATE_DOCUMENT",
  "data": {
    "documentType": "AADHAAR",
    "duplicateInfo": {...},
    "existingRecord": {...},
    "extractedFields": {...},
    "confidence": 0.95
  }
}
```

## 🧪 Testing

### Run Connection Test
```bash
python test_connection.py
```

This will test:
- ✅ Backend health
- ✅ API endpoints
- ✅ CORS configuration
- ✅ Frontend proxy
- ✅ Duplicate checking

### Manual Testing
1. Start both servers
2. Open `http://localhost:3000`
3. Upload a document
4. Try uploading the same document again to test duplicate handling

## 🔍 Troubleshooting

### Backend Issues
- **Import Errors**: Ensure virtual environment is activated
- **Port Conflicts**: Check if port 5000 is available
- **Database Errors**: Check file permissions for database files

### Frontend Issues
- **Connection Errors**: Ensure backend is running on port 5000
- **CORS Errors**: Check CORS configuration in backend
- **Proxy Issues**: Verify proxy setting in `package.json`

### Common Solutions
1. **Restart both servers** if connection issues persist
2. **Clear browser cache** if UI issues occur
3. **Check console logs** for detailed error messages
4. **Verify file paths** for uploaded documents

## 📊 Features

### ✅ Working Features
- Document upload (PDF, PNG, JPG, JPEG)
- Aadhaar and PAN card processing
- Automatic field extraction
- Duplicate detection and handling
- User management system
- Real-time statistics
- Responsive UI

### 🎯 Key Benefits
- **No Errors on Duplicates**: System handles duplicates gracefully
- **Detailed Feedback**: Shows extracted information even for duplicates
- **Robust Connection**: Multiple fallback mechanisms
- **User-Friendly**: Clear error messages and status indicators

## 🚀 Production Deployment

### Backend
- Use production WSGI server (Gunicorn, uWSGI)
- Set up proper environment variables
- Configure database for production use
- Enable HTTPS

### Frontend
- Build production version: `npm run build`
- Serve static files from web server
- Configure proper API endpoints
- Enable HTTPS

## 📞 Support

If you encounter issues:
1. Check the console logs for both frontend and backend
2. Run the connection test script
3. Verify all prerequisites are installed
4. Ensure both servers are running on correct ports

---

**Status**: ✅ **FULLY FUNCTIONAL** - Frontend-backend connection working, duplicate handling implemented, no errors thrown for duplicates.

