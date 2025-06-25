/**
 * Checks if the current browser supports modern JavaScript features
 * like fetch and Promise.
 * @returns {boolean} True if the browser is considered modern, false otherwise.
 */
const isModernBrowser = (): boolean => {
  return 'fetch' in window && 'Promise' in window;
};

/**
 * Performs a comprehensive browser compatibility check.
 * You can expand this function to check for other features as needed.
 */
export const checkBrowserCompatibility = () => {
  if (!isModernBrowser()) {
    console.warn(
      'Your browser might not support all features of this application. ' +
      'For the best experience, please use a modern browser.'
    );
    // Optionally, display a more prominent message to the user here
    // For example, by updating a state in a React component that renders a banner.
  }
  // Add more checks here if necessary
  // e.g., localStorage, sessionStorage, specific CSS features, etc.
};

// Example: Call this function when the application loads, perhaps in main.tsx or App.tsx
// checkBrowserCompatibility();

export default isModernBrowser;
