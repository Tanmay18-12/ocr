import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle } from 'lucide-react';

const DocumentUploader = ({ onUpload, loading }) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [documentType, setDocumentType] = useState('AADHAAR');
    const [dragError, setDragError] = useState('');

    const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
        setDragError('');

        if (rejectedFiles.length > 0) {
            const rejection = rejectedFiles[0];
            if (rejection.errors.some(e => e.code === 'file-too-large')) {
                setDragError('File is too large. Maximum size is 16MB.');
            } else if (rejection.errors.some(e => e.code === 'file-invalid-type')) {
                setDragError('Invalid file type. Please upload PDF, PNG, JPG, or JPEG files.');
            } else {
                setDragError('File rejected. Please try another file.');
            }
            return;
        }

        if (acceptedFiles.length > 0) {
            setSelectedFile(acceptedFiles[0]);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'image/png': ['.png'],
            'image/jpeg': ['.jpg', '.jpeg'],
        },
        maxSize: 16 * 1024 * 1024, // 16MB
        multiple: false,
    });

    const handleUpload = async () => {
        if (!selectedFile) return;

        await onUpload(selectedFile, documentType);
        setSelectedFile(null); // Clear file after upload
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="card upload-section">
            <h2>Upload Document</h2>

            <div className="document-type-selector">
                <label htmlFor="documentType">Document Type:</label>
                <select
                    id="documentType"
                    value={documentType}
                    onChange={(e) => setDocumentType(e.target.value)}
                    disabled={loading}
                >
                    <option value="AADHAAR">Aadhaar Card</option>
                    <option value="PAN">PAN Card</option>
                </select>
            </div>

            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'active' : ''} ${isDragReject ? 'rejected' : ''}`}
            >
                <input {...getInputProps()} />
                <div className="dropzone-content">
                    <Upload size={48} className="dropzone-icon" />
                    {isDragActive ? (
                        <p className="dropzone-text">Drop the file here...</p>
                    ) : (
                        <>
                            <p className="dropzone-text">
                                Drag & drop a document here, or click to select
                            </p>
                            <p className="dropzone-hint">
                                Supports PDF, PNG, JPG, JPEG (max 16MB)
                            </p>
                        </>
                    )}
                </div>
            </div>

            {dragError && (
                <div className="error-card">
                    <div className="error-title">
                        <AlertCircle size={16} style={{ marginRight: '8px' }} />
                        Upload Error
                    </div>
                    <div className="error-message">{dragError}</div>
                </div>
            )}

            {selectedFile && (
                <div className="file-info">
                    <h4>
                        <FileText size={16} style={{ marginRight: '8px' }} />
                        Selected File
                    </h4>
                    <p><strong>Name:</strong> {selectedFile.name}</p>
                    <p><strong>Size:</strong> {formatFileSize(selectedFile.size)}</p>
                    <p><strong>Type:</strong> {selectedFile.type}</p>
                </div>
            )}

            <button
                className="upload-button"
                onClick={handleUpload}
                disabled={!selectedFile || loading}
            >
                {loading ? (
                    <div className="loading">
                        <div className="spinner"></div>
                        Processing...
                    </div>
                ) : (
                    `Upload ${documentType} Document`
                )}
            </button>
        </div>
    );
};

export default DocumentUploader;