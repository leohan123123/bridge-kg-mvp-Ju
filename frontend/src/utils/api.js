import axios from 'axios';

// Define a base URL for your API
// const API_BASE_URL = 'http://localhost:8000/api'; // Example: Replace with your actual backend URL
// For now, let's assume the backend is on the same host or proxied, so relative paths might work.
const API_BASE_URL = '/api';


const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Add any other common headers like Authorization tokens if needed
    // 'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
});

// Optional: Add interceptors for request or response handling
// Request interceptor
apiClient.interceptors.request.use(
  config => {
    // Modify config before request is sent (e.g., add auth token)
    // const token = localStorage.getItem('userToken');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  error => {
    // Handle request error
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  response => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response.data; // Return only data part of the response
  },
  error => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // Handle errors globally if needed
    console.error('API call error:', error.response || error.message);
    // Example: if (error.response && error.response.status === 401) { logoutUser(); }
    return Promise.reject(error.response ? error.response.data : error); // Return error payload or error object
  }
);

export default apiClient;

// Example usage of specific API functions (can be organized into separate files per resource)

// Bridge Design KB
export const getDesignTheoryCategories = () => apiClient.get('/bridge-design/categories');
export const getFormulas = (categoryId) => apiClient.get(`/bridge-design/formulas`, { params: { categoryId } });
export const getDesignNorms = () => apiClient.get('/bridge-design/norms');
export const getMaterialParams = () => apiClient.get('/bridge-design/materials');
export const getDesignCases = () => apiClient.get('/bridge-design/cases');
export const searchDesignKnowledge = (query) => apiClient.get('/bridge-design/search', { params: { q: query } });
export const getDesignKnowledgeGraph = () => apiClient.get('/bridge-design/graph');
// Add more specific API functions as needed for other KBs
// e.g. getConstructionTimeline, getSafetyRegulations etc.
