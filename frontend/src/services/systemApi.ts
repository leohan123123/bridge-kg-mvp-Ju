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
      throw error;
    }
  }
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
