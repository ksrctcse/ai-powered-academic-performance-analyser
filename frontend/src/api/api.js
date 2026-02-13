
import axios from 'axios';

const api = axios.create({ 
  baseURL: 'http://localhost:8000',
  timeout: 60000  // Increased to 60 seconds for file uploads
});

// Request interceptor
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Don't override Content-Type for FormData
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    
    // Log request
    console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, {
      timestamp: new Date().toISOString(),
      data: config.data instanceof FormData ? '[FormData]' : config.data
    });
    
    return config;
  },
  error => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  response => {
    console.log(`[API Response] ${response.status} ${response.config.url}`, {
      timestamp: new Date().toISOString(),
      data: response.data
    });
    return response;
  },
  error => {
    console.error('[API Response Error]', {
      timestamp: new Date().toISOString(),
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Clear auth data if unauthorized
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    
    return Promise.reject(error);
  }
);

export default api;
