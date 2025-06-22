import React, { useState, useEffect } from 'react';
import { Layout, Grid, theme as antdThemeHook } from 'antd';
import { Outlet, useLocation } from 'react-router-dom';
import AppHeader from '../components/Header';
import AppSider from '../components/Sider';   // 稍后创建
import BreadcrumbNav from '../components/BreadcrumbNav'; // 稍后创建
import routeConfig from '../routes'; // 路由配置，用于面包屑和Sider菜单

const { Content } = Layout;
const { useBreakpoint } = Grid;
const { useToken } = antdThemeHook;

const MainLayout = ({ toggleTheme, currentTheme }) => {
  const [collapsed, setCollapsed] = useState(false);
  const screens = useBreakpoint(); // 用于响应式设计
  const location = useLocation();
  const { token } = useToken(); // 获取 antd theme token

  // 根据屏幕宽度自动折叠Sider
  useEffect(() => {
    if (screens.md === false && screens.lg === true) { // 平板
        setCollapsed(true);
    } else if (screens.lg === false) { // 手机
        setCollapsed(true);
    } else { // 桌面
        setCollapsed(false);
    }
  }, [screens]);

  // 移动端Sider的特殊处理：点击菜单项后自动关闭Sider
  const handleMenuClick = () => {
    if (!screens.lg) { // 如果是移动设备 (小于 lg 断点)
      setCollapsed(true);
    }
  };

  // 找到当前路由对应的名称，用于Header显示
  const getCurrentRouteName = () => {
    // 优先匹配完整路径
    let currentRoute = routeConfig.find(route => route.path === location.pathname);
    if (currentRoute) return currentRoute.name;

    // 如果没有完整路径匹配（比如是子路由），尝试匹配父路径
    // 注意：这里的路由匹配逻辑比较简单，复杂嵌套路由可能需要更完善的匹配策略
    const pathSegments = location.pathname.split('/').filter(Boolean);
    if (pathSegments.length > 1) {
        const parentPath = `/${pathSegments[0]}`;
        currentRoute = routeConfig.find(route => route.path === parentPath);
        if (currentRoute) {
            // 可以进一步查找子路由的name，但当前routeConfig结构不支持直接查找
            // 暂时返回父级name，或根据具体需求调整
            const fullPathRoute = routeConfig.find(route => location.pathname.startsWith(route.path) && route.path !== '/');
            if (fullPathRoute) return fullPathRoute.name;
            return currentRoute.name; // 默认返回父级
        }
    }
    const homeRoute = routeConfig.find(route => route.path === '/');
    return homeRoute ? homeRoute.name : '桥梁工程知识图谱';
  };

  const currentRouteName = getCurrentRouteName();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppSider
        collapsed={collapsed}
        onMenuClick={handleMenuClick}
        currentPath={location.pathname}
      />
      <Layout className="site-layout">
        <AppHeader
          collapsed={collapsed}
          toggleCollapsed={() => setCollapsed(!collapsed)}
          toggleTheme={toggleTheme}
          currentTheme={currentTheme}
          currentRouteName={currentRouteName} // 将当前路由名称传递给Header
          isMobile={!screens.lg} // 判断是否为移动端视图
        />
        <Content style={{ margin: '0 16px', paddingTop: '24px' /* 为面包屑留出空间 */ }}>
          <BreadcrumbNav />
          <div
            className="site-layout-background"
            style={{
              padding: 24,
              minHeight: 360,
              background: token.colorBgContainer, // 使用 AntD token 的背景色
            }}
          >
            <Outlet /> {/* 子页面将在这里渲染 */}
          </div>
        </Content>
        {/* 可以添加 Footer */}
        {/* <Footer style={{ textAlign: 'center' }}>桥梁工程知识图谱平台 ©2023 Created by AI</Footer> */}
      </Layout>
    </Layout>
  );
};

export default MainLayout;
