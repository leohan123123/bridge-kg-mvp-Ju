import React from 'react';
import { Layout, Button, Typography, Space, Avatar, Dropdown, theme as antdThemeHook } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SunOutlined,
  MoonOutlined,
  UserOutlined, // 用户头像占位
  DownOutlined
} from '@ant-design/icons';

const { Header } = Layout;
const { Title, Text } = Typography;
const { useToken } = antdThemeHook;


const AppHeader = ({
  collapsed,
  toggleCollapsed,
  toggleTheme,
  currentTheme,
  currentRouteName,
  isMobile
}) => {
  const { token } = useToken(); // 获取 antd theme token

  const userMenuItems = [
    { key: 'profile', label: '个人中心' },
    { key: 'logout', label: '退出登录' },
  ];

  const headerStyle = {
    padding: '0 16px', // 左右内边距
    background: token.colorBgContainer, // 使用 AntD token 的背景色
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: `1px solid ${token.colorBorderSecondary}`, // 添加底部边框线
  };

  return (
    <Header style={headerStyle}>
      <Space align="center">
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleCollapsed}
          style={{
            fontSize: '16px',
            width: 64,
            height: 64,
            marginLeft: -16, // 抵消padding，让按钮更靠左
          }}
        />
        {!isMobile && currentRouteName && ( // 在非移动端且有路由名称时显示
          <Title level={4} style={{ margin: 0, fontWeight: 'normal' }}>
            {currentRouteName}
          </Title>
        )}
      </Space>

      <Space align="center" size="middle">
        <Button
          shape="circle"
          icon={currentTheme === 'light' ? <MoonOutlined /> : <SunOutlined />}
          onClick={toggleTheme}
          title={currentTheme === 'light' ? '切换到暗色主题' : '切换到亮色主题'}
        />

        {/* 简单用户头像和下拉菜单占位 */}
        <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
          <a onClick={(e) => e.preventDefault()} style={{ display: 'inline-flex', alignItems: 'center' }}>
            <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: 8 }} />
            <Text style={{color: token.colorTextBase}}>工程师 <DownOutlined /></Text>
          </a>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default AppHeader;
