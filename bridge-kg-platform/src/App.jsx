import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider, theme as antdTheme } from 'antd';
import zhCN from './locales/zh_CN'; // 从本地导入中文语言包
import MainLayout from './layouts/MainLayout';
import routeConfig from './routes';

const App = () => {
  const [currentTheme, setCurrentTheme] = useState(() => {
    const savedTheme = localStorage.getItem('appTheme');
    return savedTheme || 'light'; // 默认为亮色主题
  });

  useEffect(() => {
    // 在 body 上添加 class，方便 CSS 根据主题进行样式调整
    document.body.className = currentTheme;
    localStorage.setItem('appTheme', currentTheme);
  }, [currentTheme]);

  const toggleTheme = () => {
    setCurrentTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  const { defaultAlgorithm, darkAlgorithm } = antdTheme;

  // 主题配置，大部分颜色定义将通过 antd-custom.less 实现
  // ConfigProvider 的 token 主要用于动态切换算法和覆盖少量无法通过 Less 方便修改的 token
  const themeConfig = {
    algorithm: currentTheme === 'light' ? defaultAlgorithm : darkAlgorithm,
    token: {
      // primaryColor 将由 antd-custom.less 定义
      // 如果 antd-custom.less 中 @primary-color 被设置，这里就不需要再显式设置
      // colorPrimary: '#264E70', // 示例：可以保留以确保JS端也能访问，但CSS优先
    },
    components: {
      Layout: {
        // 这些背景色也可以通过 Less 变量覆盖，例如 @layout-body-background
        // 在JS中配置的好处是可以动态响应 currentTheme 变化，而Less编译时固定
        // 如果 antd-custom.less 中针对暗黑模式有自己的布局背景色定义，这里的可能会覆盖或被覆盖，取决于优先级
        bodyBackground: currentTheme === 'dark' ? '#001529' : '#f0f2f5',
        headerBackground: currentTheme === 'dark' ? '#001529' : '#ffffff',
      },
      // Menu 在暗色主题下，Sider 和 Menu 的 theme="dark" 已有良好表现
      // 如需更细致调整，可在这里或 antd-custom.less 中进行
    },
  };

  return (
    <ConfigProvider locale={zhCN} theme={themeConfig}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <MainLayout
                toggleTheme={toggleTheme}
                currentTheme={currentTheme}
              />
            }
          >
            {routeConfig.map(route =>
              route.path === '/' ? (
                <Route key="index" index element={route.element} />
              ) : (
                <Route
                  key={route.path}
                  path={route.path.substring(1)} // 移除开头的 '/'
                  element={route.element}
                />
              )
            )}
            {/* Example of a 404 page: */}
            {/* <Route path="*" element={<NotFoundPage />} /> */}
          </Route>
          {/* <Route path="/login" element={<LoginPage />} /> */}
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;
