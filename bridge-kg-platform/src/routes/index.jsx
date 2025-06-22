import React from 'react';
import {
  DashboardOutlined,
  UploadOutlined,
  ApartmentOutlined, // 用于知识图谱
  SketchOutlined,    // 用于3D查看器 (或 CrownOutlined, BlockOutlined)
  MessageOutlined,   // 用于AI问答
  SettingOutlined,
  HomeOutlined,      // 用于首页 (如果Dashboard是首页，则可复用)
} from '@ant-design/icons';

// 引入页面组件
import Dashboard from '../pages/Dashboard';
import FileUpload from '../pages/FileUpload';
import KnowledgeGraph from '../pages/KnowledgeGraph';
import Viewer3D from '../pages/Viewer3D';
import AIChat from '../pages/AIChat';
import Settings from '../pages/Settings';

const routeConfig = [
  {
    path: '/',
    name: '项目概览', // Dashboard
    icon: <DashboardOutlined />,
    element: <Dashboard />,
    isNavItem: true, // 是否在侧边栏导航中显示
  },
  {
    path: '/upload',
    name: '文件上传',
    icon: <UploadOutlined />,
    element: <FileUpload />,
    isNavItem: true,
  },
  {
    path: '/knowledge-graph',
    name: '知识图谱',
    icon: <ApartmentOutlined />,
    element: <KnowledgeGraph />,
    isNavItem: true,
  },
  {
    path: '/viewer-3d',
    name: '3D查看器',
    icon: <SketchOutlined />,
    element: <Viewer3D />,
    isNavItem: true,
  },
  {
    path: '/ai-chat',
    name: 'AI智能问答',
    icon: <MessageOutlined />,
    element: <AIChat />,
    isNavItem: true,
  },
  {
    path: '/settings',
    name: '系统设置',
    icon: <SettingOutlined />,
    element: <Settings />,
    isNavItem: true,
  },
  // 可以添加一些不在导航栏显示但需要路由的页面，例如详情页
  // {
  //   path: '/details/:id',
  //   name: '详情页面', // 这个name主要用于面包屑或标题
  //   element: <DetailPage />,
  //   isNavItem: false, // 不在侧边栏显示
  // },
];

export default routeConfig;

// 辅助函数，用于根据路径查找路由配置 (面包屑导航可能会用到)
export const findRouteByPath = (path) => {
  // 完全匹配
  let route = routeConfig.find(r => r.path === path);
  if (route) return route;
  // 匹配动态路由或子路由 (当前配置中没有，但可以扩展)
  // 例如: /entity/123, 匹配 /entity/:id
  // 此处简化处理，实际应用中可能需要更复杂的匹配逻辑
  route = routeConfig.find(r => path.startsWith(r.path + '/') && r.path !== '/');
  return route;
};
