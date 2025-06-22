import React from 'react';
import { Breadcrumb } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import routeConfig from '../routes'; // 路由配置
import { HomeOutlined } from '@ant-design/icons';

const BreadcrumbNav = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter(i => i);

  // 找到首页的配置，通常是 path: '/'
  const homeRoute = routeConfig.find(route => route.path === '/');

  const breadcrumbItems = [
    <Breadcrumb.Item key="home">
      {homeRoute ? (
        <Link to={homeRoute.path}>
          <HomeOutlined style={{ marginRight: '4px' }} />
          {homeRoute.name}
        </Link>
      ) : (
        <Link to="/">
          <HomeOutlined style={{ marginRight: '4px' }} />
          首页
        </Link>
      )}
    </Breadcrumb.Item>
  ];

  let currentPath = '';
  pathSnippets.forEach((snippet, index) => {
    currentPath += `/${snippet}`;
    const route = routeConfig.find(r => r.path === currentPath);

    if (route && route.path !== '/') { // 确保不是重复添加首页，并且路由存在
      const isLast = index === pathSnippets.length - 1;
      breadcrumbItems.push(
        <Breadcrumb.Item key={currentPath}>
          {isLast || !route.isNavItem ? ( // 如果是最后一项，或者该路由项本身不应该作为可导航项(例如只是路径片段)
            <span>{route.name}</span>
          ) : (
            <Link to={route.path}>{route.name}</Link>
          )}
        </Breadcrumb.Item>
      );
    } else if (!route && index === pathSnippets.length - 1) {
      // 如果路径片段在路由配置中找不到，但它是最后一个片段 (可能是动态参数或未配置的页面)
      // 尝试从整个路径中找到最接近的路由名称作为当前页面的标题
      const matchedRouteForTitle = routeConfig.find(r => location.pathname.startsWith(r.path) && r.path !== '/');
      if (matchedRouteForTitle) {
         breadcrumbItems.push(
            <Breadcrumb.Item key={location.pathname}>
              <span>{matchedRouteForTitle.name}</span>
            </Breadcrumb.Item>
          );
      } else {
        // 如果完全找不到，显示路径片段本身（首字母大写）
        const fallbackName = snippet.charAt(0).toUpperCase() + snippet.slice(1);
        breadcrumbItems.push(
          <Breadcrumb.Item key={location.pathname}>
            <span>{fallbackName}</span>
          </Breadcrumb.Item>
        );
      }
    }
  });

  // 如果只有一个首页项（即当前就在首页），有些UI设计会选择不显示面包屑或者只显示标题
  // 但通常的面包屑至少会显示首页。如果路径是'/'，breadcrumbItems 长度为1。
  // 如果当前就在首页，并且breadcrumbItems只有一个元素，可以考虑不渲染Breadcrumb组件或返回null
  if (location.pathname === '/' && homeRoute && breadcrumbItems.length === 1) {
     // 可以选择返回 null，或者只显示一个简单的标题/面包屑
     // return null;
     // 或者，如果希望首页也显示面包屑（仅含首页），则保持现状
  }


  return (
    <Breadcrumb style={{ marginBottom: 16 }}>
      {/* marginBottom 为面包屑和下方内容之间留出间距 */}
      {breadcrumbItems}
    </Breadcrumb>
  );
};

export default BreadcrumbNav;
