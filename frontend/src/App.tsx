import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Spin, Typography, theme, Breadcrumb } from 'antd'; // Spin 用于加载指示, Breadcrumb for navigation
import { HomeOutlined, ReadOutlined, ExperimentOutlined, ToolOutlined, SafetyCertificateOutlined, ControlOutlined, BulbOutlined, FileAddOutlined, SettingOutlined, InfoCircleOutlined, DatabaseOutlined, ApartmentOutlined, CloudUploadOutlined, ExportOutlined, MonitorOutlined, ShareAltOutlined, DashboardOutlined, FundViewOutlined } from '@ant-design/icons'; // Added new Icons for Advanced Features
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
const OntologyManagerPage = lazy(() => import('./pages/OntologyManager'));
const BatchProcessorPage = lazy(() => import('./pages/BatchProcessor'));
const TrainingDataExporterPage = lazy(() => import('./pages/TrainingDataExporter'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

// Professional Knowledge Base Pages
const BridgeDesignKBPage = lazy(() => import('./pages/BridgeDesignKB'));
const ConstructionKBPage = lazy(() => import('./pages/ConstructionKB'));
const InspectionMaintenanceKBPage = lazy(() => import('./pages/InspectionMaintenanceKB'));
const QualityControlKBPage = lazy(() => import('./pages/QualityControlKB'));

// Advanced Feature Pages
const AdvancedGraphVisualizationPage = lazy(() => import('./pages/AdvancedGraphVisualization'));
const ProfessionalDashboardPage = lazy(() => import('./pages/ProfessionalDashboard'));
const SystemMonitoringPage = lazy(() => import('./pages/SystemMonitoring'));
const DataAnalyticsPlaceholderPage: React.FC = () => ( // Placeholder for Data Analytics
  <div style={{ padding: 50, textAlign: 'center' }}>
    <Title level={3}>数据分析 (Data Analytics)</Title>
    <p>此功能正在规划中，敬请期待。</p>
    <FundViewOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
  </div>
);

// Placeholder for System Monitoring (will be replaced by actual SystemMonitoringPage)
// const SystemMonitoringPlaceholder: React.FC = () => (
//   <div style={{ padding: 50, textAlign: 'center' }}>
//     <Title level={3}>系统监控 (System Monitoring)</Title>
//     <p>此功能正在开发中，敬请期待。</p>
//     <MonitorOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
//   </div>
// );

// Breadcrumb mapping
const breadcrumbNameMap: Record<string, string> = {
  '/': '首页',
  '/knowledge-query': '知识查询',
  '/ai-assistant': 'AI 助手',
  '/file-upload': '文件上传',
  '/about': '关于',
  '/professional-kb': '专业知识库',
  '/professional-kb/design': '设计知识库',
  '/professional-kb/construction': '施工工艺知识库',
  '/professional-kb/inspection-maintenance': '检测维护知识库',
  '/professional-kb/quality-control': '质量控制标准库',
  // System Management Paths
  '/system': '系统管理',
  '/system/ontology-manager': '本体管理',
  '/system/batch-processor': '批量处理',
  '/system/training-data-exporter': '训练数据导出',
  // '/system/system-monitoring': '系统监控', // This was part of System Management, will be handled by new Advanced menu
  // Advanced Features Paths
  '/advanced-graph': '图谱可视化',
  '/professional-dashboard': '专业仪表板',
  '/system-monitoring': '系统监控', // Note: This path is now top-level as per task spec for advanced features
  // '/data-analytics': '数据分析', // For future use - placeholder
};

const AppContent: React.FC = () => {
  const location = useLocation();
  const pathSnippets = location.pathname.split('/').filter(i => i);

  const breadcrumbItemsFromSnippets = pathSnippets.map((snippet, index) => {
    const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
    // Handle cases where a part of the path might not be in breadcrumbNameMap directly
    // e.g. /system/ontology-manager, "system" might not be a linkable breadcrumb on its own
    // if breadcrumbNameMap has /system, and /system/ontology-manager
    const name = breadcrumbNameMap[url] || snippet;
    if (breadcrumbNameMap[url]) { // Only create a link if it's a defined breadcrumb path
      return (
        <Breadcrumb.Item key={url}>
          <Link to={url}>{name}</Link>
        </Breadcrumb.Item>
      );
    }
    // If intermediate path like '/system' is not meant to be clickable or doesn't have a name,
    // just display its name or skip. For a cleaner approach, ensure all path segments that
    // should appear in breadcrumbs are in breadcrumbNameMap.
    // For this example, we'll display the name if it exists, otherwise the snippet.
    return (
      <Breadcrumb.Item key={url}>
        {name}
      </Breadcrumb.Item>
    );
  });


  const breadcrumbItems = [
    <Breadcrumb.Item key="home">
      <Link to="/"><HomeOutlined /></Link>
    </Breadcrumb.Item>,
  ].concat(breadcrumbItemsFromSnippets);

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
            // textAlign: 'center', // May not be needed if pages define their own alignment
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

              {/* System Management Routes */}
              <Route path="/system/ontology-manager" element={<OntologyManagerPage />} />
              <Route path="/system/batch-processor" element={<BatchProcessorPage />} />
              <Route path="/system/training-data-exporter" element={<TrainingDataExporterPage />} />
              {/* <Route path="/system/system-monitoring" element={<SystemMonitoringPlaceholder />} /> */} {/* This specific route under /system is removed or handled by the new top-level /system-monitoring */}

              {/* Advanced Feature Routes */}
              <Route path="/advanced-graph" element={<AdvancedGraphVisualizationPage />} />
              <Route path="/professional-dashboard" element={<ProfessionalDashboardPage />} />
              <Route path="/system-monitoring" element={<SystemMonitoringPage />} />
              <Route path="/data-analytics" element={<DataAnalyticsPlaceholderPage />} /> {/* Placeholder route */}

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
  const location = useLocation();

  const getCurrentKeys = () => {
    const path = location.pathname;
    let selectedKey = path; // Default selected key to current path for specific matches
    let openKey = '';

    if (path === '/') selectedKey = 'home';
    else if (path.startsWith('/knowledge-query')) selectedKey = 'knowledge-query';
    else if (path.startsWith('/professional-kb')) {
      openKey = 'professional-kb';
      // Specific child selected
      if (path === '/professional-kb/design') selectedKey = 'kb-design';
      else if (path === '/professional-kb/construction') selectedKey = 'kb-construction';
      else if (path === '/professional-kb/inspection-maintenance') selectedKey = 'kb-inspection';
      else if (path === '/professional-kb/quality-control') selectedKey = 'kb-quality';
      else selectedKey = 'professional-kb'; // Fallback for parent
    }
    else if (path.startsWith('/ai-assistant')) selectedKey = 'ai-assistant';
    else if (path.startsWith('/file-upload')) selectedKey = 'file-upload';
    else if (path.startsWith('/system')) {
      openKey = 'system-management'; // Parent key for the group
      if (path === '/system/ontology-manager') selectedKey = 'ontology-manager';
      else if (path === '/system/batch-processor') selectedKey = 'batch-processor';
      else if (path === '/system/training-data-exporter') selectedKey = 'training-data-exporter';
      // else if (path === '/system/system-monitoring') selectedKey = 'system-monitoring'; // Removed as it's moving to advanced features
      else selectedKey = 'system-management'; // Fallback for parent
    }
    // Add selection logic for new advanced features
    else if (path.startsWith('/advanced-graph')) {
      selectedKey = 'advanced-graph';
      openKey = 'advanced-features';
    } else if (path.startsWith('/professional-dashboard')) {
      selectedKey = 'professional-dashboard';
      openKey = 'advanced-features';
    } else if (path.startsWith('/system-monitoring')) {
      selectedKey = 'system-monitoring'; // This key is now a child of 'advanced-features'
      openKey = 'advanced-features';
    } else if (path.startsWith('/data-analytics')) { // For future placeholder
      selectedKey = 'data-analytics';
      openKey = 'advanced-features';
    }
    else if (path.startsWith('/about')) selectedKey = 'about';

    return { selectedKey, openKey };
  };

  const { selectedKey, openKey } = getCurrentKeys();

  // Navigation menu items
  const menuItems: MenuProps['items'] = [ // Added MenuProps type for items
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
    {
      key: 'system-management', // Parent key for the group
      icon: <SettingOutlined />,
      label: '系统管理',
      children: [
        { key: 'ontology-manager', icon: <ApartmentOutlined />, label: <Link to="/system/ontology-manager">本体管理</Link> },
        { key: 'batch-processor', icon: <CloudUploadOutlined />, label: <Link to="/system/batch-processor">批量处理</Link> },
        { key: 'training-data-exporter', icon: <ExportOutlined />, label: <Link to="/system/training-data-exporter">训练数据导出</Link> },
        // { key: 'system-monitoring', icon: <MonitorOutlined />, label: <Link to="/system/system-monitoring">系统监控</Link> }, // Removed, will be in Advanced Features
      ]
    },
    {
      key: 'advanced-features', // Parent key for the new group
      icon: <ExperimentOutlined />, // Using ExperimentOutlined as a general icon for "Advanced Features"
      label: '高级功能',
      children: [
        { key: 'advanced-graph', icon: <ShareAltOutlined />, label: <Link to="/advanced-graph">图谱可视化</Link> },
        { key: 'professional-dashboard', icon: <DashboardOutlined />, label: <Link to="/professional-dashboard">专业仪表板</Link> },
        { key: 'system-monitoring', icon: <MonitorOutlined />, label: <Link to="/system-monitoring">系统监控</Link> },
        { key: 'data-analytics', icon: <FundViewOutlined />, label: <Link to="/data-analytics">数据分析 (预留)</Link> }, // Placeholder
      ]
    },
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
