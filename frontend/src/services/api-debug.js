import axios from 'axios';

// Debug version of API service with detailed logging
const api = axios.create({
    baseURL: '/api',  // Use relative URL to leverage proxy from package.json
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Enhanced request interceptor with detailed logging
api.interceptors.request.use(
    (config) => {
        console.log('🚀 API Request Details:');
        console.log('  Method:', config.method?.toUpperCase());
        console.log('  URL:', config.baseURL + config.url);
        console.log('  Headers:', config.headers);
        console.log('  Data:', config.data);
        return config;
    },
    (error) => {
        console.error('❌ Request Setup Error:', error);
        return Promise.reject(error);
    }
);

// Enhanced response interceptor with detailed logging
api.interceptors.response.use(
    (response) => {
        console.log('✅ API Response Success:');
        console.log('  Status:', response.status);
        console.log('  Data:', response.data);
        return response;
    },
    (error) => {
        console.error('❌ API Response Error:');
        console.error('  Error Code:', error.code);
        console.error('  Error Message:', error.message);
        console.error('  Response Status:', error.response?.status);
        console.error('  Response Data:', error.response?.data);
        console.error('  Full Error:', error);

        // Specific error handling
        if (error.code === 'ECONNABORTED') {
            console.error('🕐 Request timed out after 30 seconds');
        } else if (error.code === 'ECONNREFUSED') {
            console.error('🚫 Connection refused - Backend server not running?');
        } else if (error.code === 'NETWORK_ERROR') {
            console.error('🌐 Network error - Check internet connection');
        } else if (!error.response) {
            console.error('📡 No response received - Backend server might be down');
        }

        return Promise.reject(error);
    }
);

// Test connection function
export const testBackendConnection = async () => {
    console.log('🔍 Testing backend connection...');

    try {
        // Test 1: Basic health check
        console.log('Test 1: Health check');
        const healthResponse = await api.get('/health');
        console.log('✅ Health check passed:', healthResponse.data);

        // Test 2: Stats endpoint
        console.log('Test 2: Stats endpoint');
        const statsResponse = await api.get('/stats');
        console.log('✅ Stats endpoint passed:', statsResponse.data);

        return { success: true, message: 'Backend connection successful' };

    } catch (error) {
        console.error('❌ Backend connection test failed:', error);
        return {
            success: false,
            message: error.message,
            code: error.code,
            details: error
        };
    }
};

// Enhanced upload function with detailed logging
export const uploadDocument = async (file, documentType) => {
    console.log('📤 Starting document upload...');
    console.log('  File:', file.name, file.size, 'bytes');
    console.log('  Document Type:', documentType);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    console.log('📋 FormData contents:');
    for (let [key, value] of formData.entries()) {
        console.log(`  ${key}:`, value);
    }

    try {
        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                console.log(`📊 Upload progress: ${percentCompleted}%`);
            }
        });

        console.log('✅ Upload successful:', response.data);
        return response;

    } catch (error) {
        console.error('❌ Upload failed:', error);
        throw error;
    }
};

export const getSystemStats = async () => {
    return api.get('/stats');
};

export const healthCheck = async () => {
    return api.get('/health');
};

export default api;