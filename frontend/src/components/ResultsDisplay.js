import React from 'react';
import { CheckCircle, XCircle, AlertTriangle, User, Calendar, MapPin, CreditCard, Trash2 } from 'lucide-react';

const ResultsDisplay = ({ results, onClear }) => {
    const renderSuccessResult = (result) => (
        <div key={result.id} className="result-card">
            <div className="result-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <CheckCircle size={20} color="#28a745" />
                    <span className="result-type">{result.documentType}</span>
                </div>
                <div className="result-confidence">
                    Confidence: {(result.confidence * 100).toFixed(1)}%
                </div>
            </div>

            <div className="extracted-fields">
                {Object.entries(result.extractedFields).map(([key, value]) => {
                    if (!value) return null;

                    const getIcon = (fieldName) => {
                        switch (fieldName.toLowerCase()) {
                            case 'name':
                            case 'father\'s name':
                                return <User size={16} />;
                            case 'dob':
                                return <Calendar size={16} />;
                            case 'address':
                                return <MapPin size={16} />;
                            case 'aadhaar number':
                            case 'pan number':
                                return <CreditCard size={16} />;
                            default:
                                return null;
                        }
                    };

                    return (
                        <div key={key} className="field-item">
                            <div className="field-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                {getIcon(key)}
                                {key}:
                            </div>
                            <div className="field-value">{value}</div>
                        </div>
                    );
                })}

                {result.userId && (
                    <div className="field-item">
                        <div className="field-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <User size={16} />
                            User ID:
                        </div>
                        <div className="field-value" style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                            {result.userId}
                        </div>
                    </div>
                )}
            </div>

            <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
                Processed at: {result.timestamp}
            </div>
        </div>
    );

    const renderDuplicateResult = (result) => (
        <div key={result.id} className="result-card" style={{ borderLeftColor: '#ffc107' }}>
            <div className="result-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <AlertTriangle size={20} color="#ffc107" />
                    <span className="result-type" style={{ background: '#ffc107' }}>
                        DUPLICATE DETECTED
                    </span>
                </div>
                {result.confidence && (
                    <div className="result-confidence">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                    </div>
                )}
            </div>

            <div className="error-message" style={{ marginBottom: '15px' }}>
                {result.message}
            </div>

            {result.existingRecord && (
                <div className="duplicate-info">
                    <h4>Existing Record Information:</h4>
                    <p><strong>Document ID:</strong> {result.existingRecord.document_id}</p>
                    <p><strong>Name:</strong> {result.existingRecord.name}</p>
                    <p><strong>File:</strong> {result.existingRecord.file_path}</p>
                    <p><strong>Created:</strong> {new Date(result.existingRecord.created_at).toLocaleString()}</p>
                </div>
            )}

            {result.extractedFields && Object.keys(result.extractedFields).length > 0 && (
                <div className="extracted-fields" style={{ marginTop: '15px' }}>
                    <h4>Extracted Information (Duplicate):</h4>
                    {Object.entries(result.extractedFields).map(([key, value]) => {
                        if (!value) return null;

                        const getIcon = (fieldName) => {
                            switch (fieldName.toLowerCase()) {
                                case 'name':
                                case 'father\'s name':
                                    return <User size={16} />;
                                case 'dob':
                                    return <Calendar size={16} />;
                                case 'address':
                                    return <MapPin size={16} />;
                                case 'aadhaar number':
                                case 'pan number':
                                    return <CreditCard size={16} />;
                                default:
                                    return null;
                            }
                        };

                        return (
                            <div key={key} className="field-item">
                                <div className="field-label" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {getIcon(key)}
                                    {key}:
                                </div>
                                <div className="field-value">{value}</div>
                            </div>
                        );
                    })}
                </div>
            )}

            <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
                Attempted at: {result.timestamp}
            </div>
        </div>
    );

    const renderErrorResult = (result) => (
        <div key={result.id} className="error-card">
            <div className="error-title">
                <XCircle size={16} />
                Processing Failed ({result.documentType})
            </div>
            <div className="error-message">{result.message}</div>
            {result.error && (
                <div style={{ marginTop: '10px', fontSize: '12px', color: '#999' }}>
                    Error Code: {result.error}
                </div>
            )}
            <div style={{ marginTop: '15px', fontSize: '12px', color: '#666' }}>
                Failed at: {result.timestamp}
            </div>
        </div>
    );

    const renderResult = (result) => {
        switch (result.type) {
            case 'success':
                return renderSuccessResult(result);
            case 'duplicate':
                return renderDuplicateResult(result);
            case 'error':
                return renderErrorResult(result);
            default:
                return null;
        }
    };

    return (
        <div className="card results-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2>Processing Results</h2>
                {results.length > 0 && (
                    <button className="clear-button" onClick={onClear}>
                        <Trash2 size={14} style={{ marginRight: '5px' }} />
                        Clear All
                    </button>
                )}
            </div>

            {results.length === 0 ? (
                <div className="no-results">
                    No documents processed yet. Upload a document to see results here.
                </div>
            ) : (
                <div>
                    {results.map(renderResult)}
                </div>
            )}
        </div>
    );
};

export default ResultsDisplay;