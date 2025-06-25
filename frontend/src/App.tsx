import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Spin, Typography, theme, Breadcrumb } from 'antd'; // Spin 用于加载指示, Breadcrumb for navigation
import { HomeOutlined, ReadOutlined, ExperimentOutlined, ToolOutlined, SafetyCertificateOutlined, ControlOutlined, BulbOutlined, FileAddOutlined, SettingOutlined, InfoCircleOutlined } from '@ant-design/icons'; // Icons
import './App.css'; // App特定样式

// 引入 AI 聊天组件
import AIChatInterface from './components/AIChatInterface'; // 直接导入，非懒加载

const { Header, Content, Footer, Sider } = Layout;
const { Title } = Typography;

// 页面组件 - 使用 React.lazy 进行代码分割和懒加载
const HomePage = lazy(() => import('./pages/HomePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const KnowledgeQueryPage = lazy(() => import('./pages/KnowledgeQuery'));
const FileUploadPage = lazy(() => import('./pages/FileUpload'));
const OntologyManagerPage = lazy(() => import('./pages/OntologyManagerPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

// Professional Knowledge Base Pages
const BridgeDesignKBPage = lazy(() => import('./pages/BridgeDesignKB'));
const ConstructionKBPage = lazy(() => import('./pages/ConstructionKB'));
const InspectionMaintenanceKBPage = lazy(() => import('./pages/InspectionMaintenanceKB'));
const QualityControlKBPage = lazy(() => import('./pages/QualityControlKB'));


// Breadcrumb mapping
const breadcrumbNameMap: Record<string, string> = {
  '/': '首页',
  '/knowledge-query': '知识查询',
  '/ai-assistant': 'AI 助手',
  '/file-upload': '文件上传',
  '/ontology-management': '本体管理',
  '/about': '关于',
  '/professional-kb': '专业知识库',
  '/professional-kb/design': '设计知识库',
  '/professional-kb/construction': '施工工艺知识库',
  '/professional-kb/inspection-maintenance': '检测维护知识库',
  '/professional-kb/quality-control': '质量控制标准库',
};

const AppContent: React.FC = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter(i => i);
  const extraBreadcrumbItems = pathSnippets.map((_, index) => {
    const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
    return (
      <Breadcrumb.Item key={url}>
        <Link to={url}>{breadcrumbNameMap[url] || url.substring(url.lastIndexOf('/') + 1)}</Link>
      </Breadcrumb.Item>
    );
  });

  const breadcrumbItems = [
    <Breadcrumb.Item key="home">
      <Link to="/"><HomeOutlined /></Link>
    </Breadcrumb.Item>,
  ].concat(extraBreadcrumbItems);

  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  return (
    <Layout>
      <Header style={{ padding: '0 16px', background: colorBgContainer, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Title level={3} style={{ margin: 0 }}>知识图谱应用</Title>
        {/* Quick search could be placed here if needed globally */}
      </Header>
      <Content style={{ margin: '0 16px' }}>
        <Breadcrumb style={{ margin: '16px 0' }}>
          {breadcrumbItems}
        </Breadcrumb>
        <div
          style={{
            // padding: 24, // Keep outer padding for content div if needed, but individual pages handle their own via Layout
            textAlign: 'center', // May not be needed if pages define their own alignment
            background: colorBgContainer, // This applies background to the content shell
            borderRadius: borderRadiusLG, // Rounded corners for the content shell
            minHeight: 'calc(100vh - 220px)', // Adjusted height
            // display: 'flex', // These might conflict with page layouts; pages should control their own display
            // flexDirection: 'column'
          }}
        >
          <Suspense fallback={<Spin size="large" tip="页面加载中..." style={{marginTop: '50px'}} />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/knowledge-query" element={<KnowledgeQueryPage />} />
              <Route path="/ai-assistant" element={<AIChatInterface />} />
              <Route path="/file-upload" element={<FileUploadPage />} />
              <Route path="/ontology-management" element={<OntologyManagerPage />} />

              {/* Professional Knowledge Base Routes */}
              <Route path="/professional-kb/design" element={<BridgeDesignKBPage />} />
              <Route path="/professional-kb/construction" element={<ConstructionKBPage />} />
              <Route path="/professional-kb/inspection-maintenance" element={<InspectionMaintenanceKBPage />} />
              <Route path="/professional-kb/quality-control" element={<QualityControlKBPage />} />

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        Bridge KG MVP ©{new Date().getFullYear()} Created by AI Agent
      </Footer>
    </Layout>
  );
};


const App: React.FC = () => {
  const location = useLocation(); // Import useLocation here if App is wrapped by Router

  const getCurrentKeys = () => {
    const path = location.pathname;
    let selectedKey = '';
    let openKey = '';

    if (path === '/') selectedKey = 'home';
    else if (path.startsWith('/knowledge-query')) selectedKey = 'knowledge-query';
    else if (path.startsWith('/professional-kb')) {
      openKey = 'professional-kb';
      if (path.includes('/design')) selectedKey = 'kb-design';
      else if (path.includes('/construction')) selectedKey = 'kb-construction';
      else if (path.includes('/inspection-maintenance')) selectedKey = 'kb-inspection';
      else if (path.includes('/quality-control')) selectedKey = 'kb-quality';
      else selectedKey = 'professional-kb'; // Fallback if just /professional-kb
    }
    else if (path.startsWith('/ai-assistant')) selectedKey = 'ai-assistant';
    else if (path.startsWith('/file-upload')) selectedKey = 'file-upload';
    else if (path.startsWith('/ontology-management')) selectedKey = 'ontology-management';
    else if (path.startsWith('/about')) selectedKey = 'about';

    return { selectedKey, openKey };
  };

  const { selectedKey, openKey } = getCurrentKeys();

  // Navigation menu items
  const menuItems = [
    { key: 'home', icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
    { key: 'knowledge-query', icon: <ReadOutlined />, label: <Link to="/knowledge-query">知识查询</Link> },
    {
      key: 'professional-kb',
      icon: <BulbOutlined />,
      label: '专业知识库',
      children: [
        { key: 'kb-design', icon: <ExperimentOutlined />, label: <Link to="/professional-kb/design">设计知识库</Link> },
        { key: 'kb-construction', icon: <ToolOutlined />, label: <Link to="/professional-kb/construction">施工工艺</Link> },
        { key: 'kb-inspection', icon: <SafetyCertificateOutlined />, label: <Link to="/professional-kb/inspection-maintenance">检测维护</Link> },
        { key: 'kb-quality', icon: <ControlOutlined />, label: <Link to="/professional-kb/quality-control">质量控制</Link> },
      ]
    },
    { key: 'ai-assistant', icon: <BulbOutlined />, label: <Link to="/ai-assistant">AI 助手</Link> },
    { key: 'file-upload', icon: <FileAddOutlined />, label: <Link to="/file-upload">文件上传</Link> },
    { key: 'ontology-management', icon: <SettingOutlined />, label: <Link to="/ontology-management">本体管理</Link> },
    { key: 'about', icon: <InfoCircleOutlined />, label: <Link to="/about">关于</Link> },
  ];

  return (
    // Router is already wrapping this component if App is the root for routes.
    // If App itself is not wrapped by Router, then useLocation won't work here.
    // Assuming Router is at a higher level or App is wrapped like: <Router><App /></Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="0"
        >
          <div style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.2)', textAlign:'center', lineHeight:'32px', color:'white', borderRadius:'5px' }}>
            BridgeKG
          </div>
          <Menu
            theme="dark"
            mode="inline"
            items={menuItems}
            selectedKeys={[selectedKey]}
            defaultOpenKeys={openKey ? [openKey] : []} // Use defaultOpenKeys or manage openKeys dynamically if needed
          />
        </Sider>
        <AppContent /> {/* Main content and header are now in AppContent */}
      </Layout>
  );
};


// To use useLocation directly in App, App itself must be a child of Router.
// So, the export should be something like this:
// export default () => <Router><App /></Router>;
// Or ensure that in your main index.tsx/jsx, <Router> wraps <App />.
// For this exercise, I'll assume Router is already wrapping App.

const AppWrapper: React.FC = () => (
  <Router>
    <App />
  </Router>
);

export default AppWrapper;
