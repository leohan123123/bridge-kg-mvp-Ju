import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css' // 全局样式 (如果需要)

// Ant Design 配置
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN'; // 引入中文语言包

// 如果需要自定义 Ant Design 主题，可以在这里引入或配置
// import 'antd/dist/reset.css'; // Antd v5+ 使用此方式重置基本样式

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
