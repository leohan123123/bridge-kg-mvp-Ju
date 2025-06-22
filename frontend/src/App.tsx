import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Spin, Typography, theme } from 'antd'; // Spin 用于加载指示
import './App.css'; // App特定样式

const { Header, Content, Footer, Sider } = Layout;
const { Title } = Typography;

// 页面组件 - 使用 React.lazy 进行代码分割和懒加载
const HomePage = lazy(() => import('./pages/HomePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage')); // 404页面

const App: React.FC = () => {
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 导航菜单项
  const menuItems = [
    { key: '1', label: <Link to="/">首页</Link> },
    { key: '2', label: <Link to="/about">关于</Link> },
    // 添加更多导航项
  ];

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider
          breakpoint="lg"
          collapsedWidth="0"
          // onBreakpoint={(broken) => { console.log(broken); }}
          // onCollapse={(collapsed, type) => { console.log(collapsed, type); }}
        >
          <div style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.2)', textAlign:'center', lineHeight:'32px', color:'white', borderRadius:'5px' }}>
            BridgeKG
          </div>
          <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']} items={menuItems} />
        </Sider>
        <Layout>
          <Header style={{ padding: '0 16px', background: colorBgContainer, display: 'flex', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>知识图谱应用</Title>
          </Header>
          <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
            <div
              style={{
                padding: 24,
                textAlign: 'center',
                background: colorBgContainer,
                borderRadius: borderRadiusLG,
                minHeight: 'calc(100vh - 180px)' // 估算高度，可调整
              }}
            >
              <Suspense fallback={<Spin size="large" tip="页面加载中..." style={{marginTop: '50px'}} />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/about" element={<AboutPage />} />
                  {/* 404 Not Found 路由应该放在最后 */}
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </Suspense>
            </div>
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            Bridge KG MVP ©{new Date().getFullYear()} Created by AI Agent
          </Footer>
        </Layout>
      </Layout>
    </Router>
  );
};

export default App;
