# 🚀 How to Run the Document Processing Project

## Step-by-Step Instructions

### 📋 Prerequisites
- Python 3.8+ installed
- Node.js 16+ installed
- All project files in the correct directory

### 🔧 Step 1: Test Backend Functionality

**Before starting the Flask server, test if everything works:**

```bash
# Run the backend test script
python test_backend.py
```

This will:
- ✅ Test if all modules can be imported
- ✅ Test if extractors can be initialized  
- ✅ Test basic functionality
- ✅ Test with sample documents (if available)

**If tests fail, fix the issues before proceeding.**

### 🌐 Step 2: Start Backend Server

**Option A: Safe startup (recommended)**
```bash
# This will test first, then start the server
python start_backend_safe.py
```

**Option B: Manual startup**
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
backend_env\Scripts\activate

# Start Flask server
python app.py
```

**Backend will be available at: http://localhost:5000**

### 🎨 Step 3: Test Frontend Setup

**In a new terminal/command prompt:**

```bash
# Test frontend setup
python test_frontend.py
```

This will:
- ✅ Check if Node.js is installed
- ✅ Check if npm is installed
- ✅ Verify frontend directory structure
- ✅ Install dependencies if needed
- ✅ Test backend connection

### 🖥️ Step 4: Start Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not done automatically)
npm install

# Start React development server
npm start
```

**Frontend will be available at: http://localhost:3000**

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "Processing Failed - Network Error"

**Cause:** Frontend can't connect to backend

**Solutions:**
1. Make sure backend is running on port 5000
2. Check if backend shows any errors in console
3. Test backend directly: http://localhost:5000/api/health

```bash
# Test backend health
curl http://localhost:5000/api/health
```

### Issue 2: "Import Error" in Backend

**Cause:** Python modules not found

**Solutions:**
1. Make sure you're in the correct directory
2. Check if all Python files are present
3. Run the test script first

```bash
# Check current directory
pwd
ls -la *.py

# Run test script
python test_backend.py
```

### Issue 3: "Module not found" for user_management

**Cause:** User management system not set up

**Solution:**
```bash
# Set up user management system
python user_management_demo.py --setup
```

### Issue 4: Backend starts but creates infinite loop

**Cause:** Flask development server runs continuously

**This is normal behavior!** The Flask server runs continuously to handle requests.

**To stop the server:** Press `Ctrl+C`

### Issue 5: Frontend won't start

**Cause:** Node.js dependencies not installed

**Solutions:**
```bash
cd frontend
npm install
npm start
```

### Issue 6: "Database locked" errors

**Cause:** Multiple processes accessing database

**Solutions:**
1. Stop all running Python processes
2. Restart the backend server
3. Check if any database files are corrupted

---

## 📊 Testing the Complete System

### 1. Upload Test Document

1. Open http://localhost:3000
2. Select document type (Aadhaar or PAN)
3. Drag & drop a PDF file or click to select
4. Click "Upload" button
5. Check results in the right panel

### 2. Test Duplicate Detection

1. Upload the same document twice
2. Second upload should show "Duplicate Detected" error
3. Check system statistics for duplicate counts

### 3. Verify System Statistics

- Check the statistics panel at the bottom
- Should show user counts, document counts, etc.
- Statistics update in real-time

---

## 🔍 Debug Mode

### Enable Backend Debug Logging

```bash
# In backend/app.py, Flask runs with debug=True
# Check console output for detailed logs
```

### Enable Frontend Debug Logging

```bash
# In frontend directory
set REACT_APP_DEBUG=true
npm start
```

### Check API Responses

**Open browser developer tools (F12) and check:**
- Network tab for API requests
- Console tab for JavaScript errors
- Response data from backend

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── backend_env/        # Virtual environment
├── frontend/
│   ├── src/                # React source code
│   ├── package.json        # Node.js dependencies
│   └── node_modules/       # Installed packages
├── user_management/        # User management system
├── aadhaar_extractor_with_sql.py  # Aadhaar processor
├── pan_extractor_with_sql.py      # PAN processor
├── test_backend.py         # Backend test script
├── test_frontend.py        # Frontend test script
└── start_backend_safe.py   # Safe backend startup
```

---

## 🎯 Quick Commands Summary

```bash
# Test everything first
python test_backend.py
python test_frontend.py

# Start backend (in one terminal)
python start_backend_safe.py

# Start frontend (in another terminal)
cd frontend
npm start

# Access application
# Frontend: http://localhost:3000
# Backend:  http://localhost:5000
```

---

## 🆘 Still Having Issues?

1. **Check all prerequisites are installed**
2. **Run test scripts first**
3. **Check console output for specific errors**
4. **Ensure all files are in correct locations**
5. **Try restarting both servers**

**Remember:** The backend server runs continuously - this is normal! Use Ctrl+C to stop it when needed.