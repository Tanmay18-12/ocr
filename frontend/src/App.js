import React, { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import DocumentUploader from './components/DocumentUploader';
import ResultsDisplay from './components/ResultsDisplay';
import SystemStats from './components/SystemStats';
import { uploadDocument, getSystemStats, testBackendConnection } from './services/api-direct';

function App() {
    const [results, setResults] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);
    const [backendConnected, setBackendConnected] = useState(false);

    // Test backend connection and load stats on component mount
    useEffect(() => {
        testBackendConnectionFunc();
    }, []);

    const testBackendConnectionFunc = async () => {
        console.log('🔍 Testing backend connection from React app...');

        try {
            const result = await testBackendConnection();

            if (result.success) {
                setBackendConnected(true);
                toast.success('Connected to backend successfully!');
                console.log('✅ Backend connection successful');
                loadStats();
            } else {
                setBackendConnected(false);
                toast.error(`Backend connection failed: ${result.message}`);
                console.error('❌ Backend connection failed:', result);
            }
        } catch (error) {
            setBackendConnected(false);
            toast.error('Cannot connect to backend. Please ensure the backend server is running on port 5000.');
            console.error('❌ Backend connection error:', error);
        }
    };

    const loadStats = async () => {
        try {
            const response = await getSystemStats();
            if (response.data.success) {
                setStats(response.data.data);
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    };

    const handleDocumentUpload = async (file, documentType) => {
        setLoading(true);

        try {
            const response = await uploadDocument(file, documentType);

            if (response.data.success) {
                // Success - add to results
                const newResult = {
                    id: Date.now(),
                    type: 'success',
                    documentType: response.data.data.documentType,
                    extractedFields: response.data.data.extractedFields,
                    userId: response.data.data.userId,
                    confidence: response.data.data.confidence,
                    timestamp: new Date().toLocaleString()
                };

                setResults(prev => [newResult, ...prev]);
                toast.success('Document processed successfully!');

                // Reload stats
                loadStats();
            } else {
                // Handle different error types
                const errorType = response.data.error;
                let errorResult;

                if (errorType === 'DUPLICATE_DOCUMENT') {
                    errorResult = {
                        id: Date.now(),
                        type: 'duplicate',
                        documentType: documentType,
                        message: response.data.message,
                        duplicateInfo: response.data.data?.duplicateInfo,
                        existingRecord: response.data.data?.existingRecord,
                        extractedFields: response.data.data?.extractedFields,
                        confidence: response.data.data?.confidence,
                        timestamp: new Date().toLocaleString()
                    };
                    toast.warning('Duplicate document detected - this document already exists in the system');
                } else {
                    errorResult = {
                        id: Date.now(),
                        type: 'error',
                        documentType: documentType,
                        message: response.data.message,
                        error: errorType,
                        timestamp: new Date().toLocaleString()
                    };
                    toast.error(`Processing failed: ${response.data.message}`);
                }

                setResults(prev => [errorResult, ...prev]);
            }
        } catch (error) {
            console.error('Upload error:', error);

            const errorResult = {
                id: Date.now(),
                type: 'error',
                documentType: documentType,
                message: error.response?.data?.message || 'Network error occurred',
                error: 'NETWORK_ERROR',
                timestamp: new Date().toLocaleString()
            };

            setResults(prev => [errorResult, ...prev]);
            toast.error('Upload failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const clearResults = () => {
        setResults([]);
        toast.info('Results cleared');
    };

    return (
        <div className="container">
            <header className="header">
                <h1>Document Processing System</h1>
                <p>Upload Aadhaar and PAN cards for automated field extraction</p>
                <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px', justifyContent: 'center' }}>
                    <div style={{
                        padding: '8px 16px',
                        borderRadius: '20px',
                        background: backendConnected ? '#28a745' : '#dc3545',
                        color: 'white',
                        fontSize: '14px'
                    }}>
                        {backendConnected ? '🟢 Backend Connected' : '🔴 Backend Disconnected'}
                    </div>
                    <button
                        onClick={testBackendConnectionFunc}
                        style={{
                            padding: '8px 16px',
                            borderRadius: '20px',
                            border: 'none',
                            background: '#007bff',
                            color: 'white',
                            fontSize: '14px',
                            cursor: 'pointer'
                        }}
                    >
                        🔄 Test Connection
                    </button>
                </div>
            </header>

            <main className="main-content">
                <DocumentUploader
                    onUpload={handleDocumentUpload}
                    loading={loading}
                />

                <ResultsDisplay
                    results={results}
                    onClear={clearResults}
                />

                {stats && (
                    <SystemStats stats={stats} />
                )}
            </main>

            <ToastContainer
                position="top-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="light"
            />
        </div>
    );
}

export default App;