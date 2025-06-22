import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// 从环境变量获取API基础URL (Vite中通过 import.meta.env)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // 'Authorization': `Bearer ${yourAuthToken}` // 如果需要认证，可以在这里或请求拦截器中添加
  },
  timeout: 10000, // 请求超时时间 (毫秒)
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 在发送请求之前做些什么
    // 例如，添加认证token
    // const token = localStorage.getItem('authToken');
    // if (token && config.headers) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    console.log('发起请求:', config.method?.toUpperCase(), config.url, config.data || config.params || '');
    return config;
  },
  (error: AxiosError) => {
    // 对请求错误做些什么
    console.error('请求配置错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据做点什么
    // 例如，只返回 response.data
    console.log('收到响应:', response.status, response.config.url, response.data);
    return response.data; // 通常直接返回data部分
  },
  (error: AxiosError) => {
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    console.error('响应错误:', error.response?.status, error.config?.url, error.response?.data);

    if (error.response) {
      // 服务器返回了错误状态码
      const { status, data } = error.response;
      // 你可以在这里处理常见的错误状态码，例如 401 (未授权), 403 (禁止访问), 500 (服务器错误)
      // 例如:
      // if (status === 401) {
      //   // 跳转到登录页或刷新token
      //   console.error('未授权，请登录');
      //   // window.location.href = '/login';
      // } else if (status === 403) {
      //   console.error('禁止访问');
      // } else if (status === 500) {
      //   console.error('服务器内部错误');
      // }
      // 为了简单起见，我们直接抛出错误，让调用方处理
      // 或者你可以返回一个包含错误信息的特定格式对象
      // return Promise.reject(new Error( (data as any)?.message || `请求失败，状态码：${status}`));
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      console.error('无响应:', error.request);
      // return Promise.reject(new Error('网络错误，请检查您的连接'));
    } else {
      // 发送请求时出了点问题
      console.error('请求设置错误:', error.message);
    }
    // 为了让调用处的 .catch() 能捕获到，需要 Promise.reject
    return Promise.reject(error);
  }
);

export default apiClient;
