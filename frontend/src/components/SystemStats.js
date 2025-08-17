import React from 'react';
import { Users, FileText, AlertTriangle, TrendingUp } from 'lucide-react';

const SystemStats = ({ stats }) => {
    const userStats = stats.user_statistics || {};
    const qualityMetrics = stats.data_quality_metrics || {};
    const aadhaarMetrics = qualityMetrics.aadhaar_metrics || {};
    const panMetrics = qualityMetrics.pan_metrics || {};

    const statCards = [
        {
            icon: <Users size={24} />,
            label: 'Total Users',
            value: userStats.total_users || 0,
            color: '#667eea'
        },
        {
            icon: <FileText size={24} />,
            label: 'Aadhaar Records',
            value: aadhaarMetrics.total_records || 0,
            color: '#28a745'
        },
        {
            icon: <FileText size={24} />,
            label: 'PAN Records',
            value: panMetrics.total_records || 0,
            color: '#17a2b8'
        },
        {
            icon: <AlertTriangle size={24} />,
            label: 'Aadhaar Duplicates',
            value: aadhaarMetrics.duplicate_records || 0,
            color: '#ffc107'
        },
        {
            icon: <AlertTriangle size={24} />,
            label: 'PAN Duplicates',
            value: panMetrics.duplicate_records || 0,
            color: '#fd7e14'
        },
        {
            icon: <TrendingUp size={24} />,
            label: 'Data Quality',
            value: `${(100 - (aadhaarMetrics.duplicate_percentage || 0)).toFixed(1)}%`,
            color: '#6f42c1'
        }
    ];

    return (
        <div className="card stats-section">
            <h2>System Statistics</h2>
            <div className="stats-grid">
                {statCards.map((stat, index) => (
                    <div key={index} className="stat-card" style={{ background: stat.color }}>
                        <div style={{ marginBottom: '10px' }}>
                            {stat.icon}
                        </div>
                        <div className="stat-number">{stat.value}</div>
                        <div className="stat-label">{stat.label}</div>
                    </div>
                ))}
            </div>

            {qualityMetrics.timestamp && (
                <div style={{ marginTop: '20px', fontSize: '12px', color: '#666', textAlign: 'center' }}>
                    Last updated: {new Date(qualityMetrics.timestamp).toLocaleString()}
                </div>
            )}
        </div>
    );
};

export default SystemStats;