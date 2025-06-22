import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import 'antd/dist/reset.css'; // Ant Design 核心重置样式
import './styles/global.css';   // 全局自定义样式
import './styles/antd-custom.less'; // Ant Design 自定义主题 (确保Vite配置了Less)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
