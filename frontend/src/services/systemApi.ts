// 添加重试机制和超时处理
const apiClient = {
  async request(url: string, options: RequestInit = {}, retries = 3, delay = 1000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        if (retries > 0 && response.status >= 500) { // Retry on server errors
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.request(url, options, retries - 1, delay * 2); // Exponential backoff
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response;
    } catch (error: any) {
      clearTimeout(timeoutId);
      if (error.name === 'AbortError' && retries > 0) { // Retry on timeout if retries are left
        // This specific AbortError is from our timeout
        console.warn(`Request timed out. Retrying... (${retries} retries left)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request(url, options, retries - 1, delay * 2);
      }
      if (retries > 0) { // Retry on other network errors
        console.warn(`Request failed. Retrying... (${retries} retries left): ${error.message}`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.request(url, options, retries - 1, delay * 2);
      }
       // Before throwing, call the centralized handler
       handleApiError(error, `apiClient.request ${url}`); // Original error is re-thrown by handleApiError
       // The line below is now unreachable if handleApiError always throws, which it does.
       // throw error;
    }
  }
};

// Unified error handler
export const handleApiError = (error: any, context?: string): never => { // Mark as 'never' as it always throws
  console.error(`API Error${context ? ` in ${context}` : ''}:`, error);

  let errorMessage = "An unexpected error occurred.";
  let errorDetails = null;

  if (error.response) { // Axios-like error structure
    errorMessage = `Server Error: ${error.response.status} - ${error.response.statusText || ''}`;
    errorDetails = error.response.data;
    if (error.response.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'string' ? error.response.data.detail : JSON.stringify(error.response.data.detail);
    } else if (typeof error.response.data === 'string' && error.response.data.length < 200) { // Simple string error
        errorMessage = error.response.data;
    }

    if (error.response.status === 401) {
      // Handle unauthorized access, e.g., redirect to login
      // This might involve calling a function from a UI context or an event emitter
      console.warn("Unauthorized access (401). Consider redirecting to login.");
      // window.location.href = '/login'; // Example, but services should not directly manipulate window.location
    } else if (error.response.status === 403) {
      console.warn("Forbidden access (403). User does not have permission.");
    } else if (error.response.status >= 500) {
      console.error("Server error (5xx). Please try again later or contact support.");
    }
  } else if (error.request) { // Request was made but no response received (e.g. network error)
    errorMessage = "Network error or no response from server. Please check your connection.";
  } else if (error.name === 'AbortError') { // For fetch AbortController
    errorMessage = "The request was aborted (e.g., timeout).";
  }
  else { // Something else happened in setting up the request
    errorMessage = error.message || "An unknown error occurred during the API request.";
  }

  // For UI display, one might throw a new error or return a structured error object
  // For now, this function primarily logs and identifies common patterns.
  // Depending on usage, you might want to:
  // 1. `throw new Error(errorMessage);` to propagate a simplified error message.
  // 2. Return a structured object: `return { message: errorMessage, status: error.response?.status, details: errorDetails };`
  // For this implementation, let's re-throw a generic error to be caught by the caller,
  // assuming the console logs are for developer insight.
  // Or, if this handler is the *final* point, it shouldn't re-throw but perhaps trigger a global notification.
  // Given it's a utility, re-throwing a simplified/consistent error is often useful.

  // Re-throwing the original error to allow specific handling by the caller if needed,
  // after logging and identifying the type of error.
  // If a more generic error message is preferred, one could: throw new Error(errorMessage);
  throw error;
};


export default apiClient;

// Example usage (optional, can be removed or kept for reference)
/*
apiClient.request('/api/data')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Failed to fetch data:', error));

apiClient.request('/api/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ foo: 'bar' }),
})
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
*/
