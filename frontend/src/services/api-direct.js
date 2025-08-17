import axios from 'axios';

// Direct connection API service (bypasses proxy issues)
const api = axios.create({
    baseURL: 'http://localhost:5000/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add CORS headers to all requests
api.defaults.headers.common['Access-Control-Allow-Origin'] = '*';
api.defaults.headers.common['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
api.defaults.headers.common['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization';

// Enhanced request interceptor with detailed logging
api.interceptors.request.use(
    (config) => {
        console.log('🚀 DIRECT API Request:');
        console.log('  Method:', config.method?.toUpperCase());
        console.log('  Full URL:', config.baseURL + config.url);
        console.log('  Headers:', config.headers);
        console.log('  Timeout:', config.timeout);
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
        console.log('✅ DIRECT API Response Success:');
        console.log('  Status:', response.status);
        console.log('  Headers:', response.headers);
        console.log('  Data:', response.data);
        return response;
    },
    (error) => {
        console.error('❌ DIRECT API Response Error:');
        console.error('  Error Code:', error.code);
        console.error('  Error Message:', error.message);
        console.error('  Request URL:', error.config?.url);
        console.error('  Request Method:', error.config?.method);
        console.error('  Response Status:', error.response?.status);
        console.error('  Response Headers:', error.response?.headers);
        console.error('  Response Data:', error.response?.data);
        console.error('  Full Error Object:', error);

        // Detailed error analysis
        if (error.code === 'ERR_NETWORK') {
            console.error('🌐 Network Error - This usually means:');
            console.error('   1. Backend server is not running');
            console.error('   2. CORS is blocking the request');
            console.error('   3. Firewall is blocking the connection');
        } else if (error.code === 'ECONNABORTED') {
            console.error('🕐 Request timed out after 30 seconds');
        } else if (error.code === 'ECONNREFUSED') {
            console.error('🚫 Connection refused - Backend server not running on port 5000');
        } else if (!error.response) {
            console.error('📡 No response received - Backend server might be down');
        }

        return Promise.reject(error);
    }
);

// Test connection with multiple approaches
export const testBackendConnection = async () => {
    console.log('🔍 Testing DIRECT backend connection...');

    try {
        // Test 1: Direct fetch to health endpoint
        console.log('Test 1: Direct fetch to health endpoint');
        const directResponse = await fetch('http://localhost:5000/api/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (directResponse.ok) {
            const data = await directResponse.json();
            console.log('✅ Direct fetch successful:', data);
        } else {
            console.error('❌ Direct fetch failed:', directResponse.status, directResponse.statusText);
        }

        // Test 2: Axios request
        console.log('Test 2: Axios health check');
        const healthResponse = await api.get('/health');
        console.log('✅ Axios health check passed:', healthResponse.data);

        // Test 3: Stats endpoint
        console.log('Test 3: Stats endpoint');
        const statsResponse = await api.get('/stats');
        console.log('✅ Stats endpoint passed:', statsResponse.data);

        return { success: true, message: 'Backend connection successful' };

    } catch (error) {
        console.error('❌ Backend connection test failed:', error);

        // Try alternative connection test
        try {
            console.log('🔄 Trying alternative connection test...');
            const response = await fetch('http://localhost:5000/api/health');
            const data = await response.json();
            console.log('✅ Alternative test successful:', data);
            return { success: true, message: 'Backend connection successful (via alternative method)' };
        } catch (altError) {
            console.error('❌ Alternative test also failed:', altError);
        }

        return {
            success: false,
            message: error.message,
            code: error.code,
            details: error
        };
    }
};

// Enhanced upload function with multiple retry attempts
export const uploadDocument = async (file, documentType) => {
    console.log('📤 Starting DIRECT document upload...');
    console.log('  File:', file.name, file.size, 'bytes', file.type);
    console.log('  Document Type:', documentType);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('documentType', documentType);

    console.log('📋 FormData created successfully');

    try {
        // Method 1: Try with axios
        console.log('🔄 Attempting upload with axios...');
        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                console.log(`📊 Upload progress: ${percentCompleted}%`);
            }
        });

        console.log('✅ Axios upload successful:', response.data);
        return response;

    } catch (axiosError) {
        console.error('❌ Axios upload failed:', axiosError);

        // Method 2: Try with fetch as fallback
        try {
            console.log('🔄 Attempting upload with fetch as fallback...');
            const fetchResponse = await fetch('http://localhost:5000/api/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await fetchResponse.json();

            if (fetchResponse.ok) {
                console.log('✅ Fetch upload successful:', data);
                return { data };
            } else {
                console.error('❌ Fetch upload failed:', fetchResponse.status, data);
                throw new Error(data.message || 'Upload failed');
            }

        } catch (fetchError) {
            console.error('❌ Fetch upload also failed:', fetchError);
            throw axiosError; // Throw the original axios error
        }
    }
};

export const getSystemStats = async () => {
    try {
        return await api.get('/stats');
    } catch (error) {
        console.error('❌ Stats request failed, trying fetch fallback...');
        const response = await fetch('http://localhost:5000/api/stats');
        const data = await response.json();
        return { data };
    }
};

export const healthCheck = async () => {
    try {
        return await api.get('/health');
    } catch (error) {
        console.error('❌ Health check failed, trying fetch fallback...');
        const response = await fetch('http://localhost:5000/api/health');
        const data = await response.json();
        return { data };
    }
};

export default api;