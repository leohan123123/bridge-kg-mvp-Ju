const storage = {
  setItem: (key: string, value: any) => {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn('Storage not available', e);
    }
  },
  getItem: (key: string) => {
    try {
      const item = sessionStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      console.warn('Error reading from storage', e);
      return null;
    }
  },
  removeItem: (key: string) => {
    try {
      sessionStorage.removeItem(key);
    } catch (e) {
      console.warn('Error removing from storage', e);
    }
  }
};

export default storage;
