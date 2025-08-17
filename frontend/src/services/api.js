import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || '/api',  // Use proxy configuration
    timeout: 30000, // 30 second timeout for file uploads
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a test endpoint to check backend connectivity
export const testConnection = async () => {
    try {
        const response = await axios.get('http://localhost:5000/');
        return response;
    } catch (error) {
        console.error('Backend connection test failed:', error);
        throw error;
    }
};

// Request interceptor for logging
api.interceptors.request.use(
    (config) => {
        console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        console.error('Response error:', error);

        if (error.code === 'ECONNABORTED') {
            console.error('Request timeout');
        } else if (error.response?.status === 413) {
            console.error('File too large');
        } else if (error.response?.status >= 500) {
            console.error('Server error');
        }

        return Promise.reject(error);
    }
);

// API endpoints
export const uploadDocument = async (file, documentType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    return api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
};

export const checkDuplicate = async (documentNumber, documentType) => {
    return api.post('/check-duplicate', {
        documentNumber,
        documentType,
    });
};

export const getSystemStats = async () => {
    return api.get('/stats');
};

export const getUserDocuments = async (userId) => {
    return api.get(`/user/${userId}/documents`);
};

export const healthCheck = async () => {
    return api.get('/health');
};

export default api;