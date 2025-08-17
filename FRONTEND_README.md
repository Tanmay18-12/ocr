# Document Processing Frontend

A React-based web application for uploading and processing Aadhaar and PAN card documents with real-time field extraction and duplicate prevention.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ installed
- Python 3.8+ installed
- Backend system set up and running

### Setup Instructions

1. **Setup Backend** (First time only):
   ```bash
   # Run the setup script
   setup_backend.bat
   ```

2. **Setup Frontend** (First time only):
   ```bash
   # Run the setup script
   setup_frontend.bat
   ```

3. **Start Application**:
   ```bash
   # Start both backend and frontend
   start_application.bat
   ```

4. **Access Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## 🎯 Features

### Document Upload
- **Drag & Drop Interface**: Easy file upload with visual feedback
- **File Validation**: Supports PDF, PNG, JPG, JPEG (max 16MB)
- **Document Type Selection**: Choose between Aadhaar and PAN cards
- **Real-time Processing**: Live upload progress and status

### Field Extraction Display
- **Structured Results**: Clean display of extracted fields
- **Confidence Scoring**: Shows extraction confidence percentage
- **User ID Tracking**: Displays assigned unique user ID
- **Timestamp Information**: Processing time and date

### Duplicate Detection
- **Real-time Validation**: Prevents duplicate document processing
- **Existing Record Info**: Shows details of existing records
- **Clear Error Messages**: User-friendly duplicate notifications
- **Audit Trail**: Complete history of duplicate attempts

### System Monitoring
- **Live Statistics**: Real-time system health metrics
- **Data Quality Metrics**: Duplicate percentages and data integrity
- **User Analytics**: Total users and document counts
- **Performance Monitoring**: Processing success rates

## 🏗️ Architecture

### Frontend Stack
- **React 18**: Modern React with hooks and functional components
- **Axios**: HTTP client for API communication
- **React Dropzone**: File upload with drag & drop
- **React Toastify**: User notifications and alerts
- **Lucide React**: Modern icon library
- **CSS Grid/Flexbox**: Responsive layout design

### Backend Integration
- **REST API**: Clean API endpoints for all operations
- **File Upload**: Multipart form data handling
- **Error Handling**: Structured error responses
- **CORS Support**: Cross-origin resource sharing enabled

## 📱 User Interface

### Main Components

#### 1. Document Uploader
```jsx
<DocumentUploader 
  onUpload={handleDocumentUpload}
  loading={loading}
/>
```
- File drag & drop zone
- Document type selector
- Upload progress indicator
- File validation feedback

#### 2. Results Display
```jsx
<ResultsDisplay 
  results={results}
  onClear={clearResults}
/>
```
- Success results with extracted fields
- Duplicate detection alerts
- Error messages with details
- Clear all functionality

#### 3. System Statistics
```jsx
<SystemStats stats={stats} />
```
- Real-time metrics dashboard
- Data quality indicators
- User and document counts
- Visual stat cards

### Responsive Design
- **Desktop**: Two-column layout with full features
- **Tablet**: Stacked layout with optimized spacing
- **Mobile**: Single-column responsive design
- **Touch-friendly**: Large buttons and touch targets

## 🔧 Configuration

### Environment Variables
Create `.env` file in frontend directory:
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_MAX_FILE_SIZE=16777216
REACT_APP_SUPPORTED_FORMATS=pdf,png,jpg,jpeg
```

### API Endpoints
```javascript
// Document processing
POST /api/upload
POST /api/check-duplicate

// System information
GET /api/health
GET /api/stats
GET /api/user/{userId}/documents
```

## 🎨 Styling

### CSS Architecture
- **Global Styles**: Base typography and layout
- **Component Styles**: Scoped component styling
- **Responsive Design**: Mobile-first approach
- **Color Scheme**: Professional blue gradient theme

### Key Style Features
- **Gradient Backgrounds**: Modern visual appeal
- **Card-based Layout**: Clean content organization
- **Hover Effects**: Interactive feedback
- **Loading States**: Visual processing indicators
- **Error States**: Clear error visualization

## 🔍 Error Handling

### Client-Side Validation
```javascript
// File validation
const validateFile = (file) => {
  if (file.size > MAX_FILE_SIZE) {
    return 'File too large';
  }
  if (!ALLOWED_TYPES.includes(file.type)) {
    return 'Invalid file type';
  }
  return null;
};
```

### API Error Handling
```javascript
// Structured error responses
{
  "success": false,
  "error": "DUPLICATE_DOCUMENT",
  "message": "Document already exists",
  "data": {
    "existingRecord": {...}
  }
}
```

### User Feedback
- **Toast Notifications**: Success, warning, and error messages
- **Visual Indicators**: Loading spinners and progress bars
- **Error Cards**: Detailed error information display
- **Retry Mechanisms**: Clear retry instructions

## 📊 Performance

### Optimization Features
- **File Size Limits**: 16MB maximum upload size
- **Request Timeouts**: 30-second timeout for uploads
- **Loading States**: Prevent multiple simultaneous uploads
- **Error Recovery**: Automatic retry suggestions

### Metrics
- **Upload Speed**: Optimized for typical document sizes
- **Response Time**: <2 seconds for most operations
- **Memory Usage**: Efficient file handling
- **Network Efficiency**: Compressed API responses

## 🧪 Testing

### Manual Testing Checklist
- [ ] Upload valid Aadhaar PDF
- [ ] Upload valid PAN PDF
- [ ] Test duplicate detection
- [ ] Verify error handling
- [ ] Check responsive design
- [ ] Test file validation
- [ ] Verify statistics display

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🚨 Troubleshooting

### Common Issues

**Backend Connection Failed**
```
Error: Network Error
Solution: Ensure backend is running on port 5000
Command: cd backend && python app.py
```

**File Upload Fails**
```
Error: File too large / Invalid type
Solution: Check file size (<16MB) and format (PDF/PNG/JPG)
```

**Duplicate Detection Not Working**
```
Error: Duplicate not detected
Solution: Verify backend user management system is set up
Command: python user_management_demo.py --setup
```

**Frontend Won't Start**
```
Error: npm start fails
Solution: Install dependencies and check Node.js version
Commands: 
  npm install
  node --version (should be 16+)
```

### Debug Mode
```bash
# Enable debug logging
set REACT_APP_DEBUG=true
npm start
```

## 🔄 Development Workflow

### Local Development
1. Start backend: `cd backend && python app.py`
2. Start frontend: `cd frontend && npm start`
3. Open browser: http://localhost:3000
4. Make changes and see live reload

### Building for Production
```bash
cd frontend
npm run build
# Serve build folder with web server
```

### API Testing
```bash
# Test backend health
curl http://localhost:5000/api/health

# Test file upload
curl -X POST -F "file=@test.pdf" -F "documentType=AADHAAR" \
  http://localhost:5000/api/upload
```

## 📈 Future Enhancements

### Planned Features
- **Batch Upload**: Multiple file processing
- **Progress Tracking**: Real-time processing progress
- **Document Preview**: PDF/image preview before upload
- **Export Results**: Download extracted data as CSV/JSON
- **User Authentication**: Secure user sessions
- **Document History**: View previously processed documents

### Technical Improvements
- **WebSocket Integration**: Real-time updates
- **Offline Support**: Service worker implementation
- **PWA Features**: Install as mobile app
- **Advanced Validation**: Client-side OCR preview
- **Caching Strategy**: Improved performance

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify backend is running and accessible
3. Check browser console for JavaScript errors
4. Ensure all dependencies are installed correctly

**System Requirements:**
- Node.js 16+
- Modern web browser
- Backend system running on port 5000
- Stable internet connection for API calls