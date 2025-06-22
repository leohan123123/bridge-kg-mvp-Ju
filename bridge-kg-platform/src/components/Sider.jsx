import React from 'react';
import { Layout, Menu, Typography, Grid } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import routeConfig from '../routes'; // 路由配置
import logo from '../assets/logo.svg'; // 引入Logo (稍后添加)

const { Sider } = Layout;
const { Title } = Typography;
const { useBreakpoint } = Grid;

const AppSider = ({ collapsed, onMenuClick, currentPath }) => {
  const screens = useBreakpoint();

  // 从路由配置生成菜单项
  const menuItems = routeConfig
    .filter(route => route.isNavItem) // 只选择需要在导航中显示的项
    .map(route => ({
      key: route.path,
      icon: route.icon,
      label: <Link to={route.path}>{route.name}</Link>,
      onClick: onMenuClick, // 用于移动端点击后关闭Sider
    }));

  // 获取当前选中的菜单项的key
  // 需要处理 / 开头的路径，以及可能的子路径高亮 (当前配置下，直接匹配path即可)
  const selectedKeys = [currentPath];

  // 移动端 Drawer 模式下的 Sider 样式
  const siderStyle = !screens.lg ? {
    position: 'fixed',
    top: 0,
    left: 0,
    height: '100vh',
    zIndex: 1000, // 确保在最上层
    boxShadow: '2px 0 6px rgba(0,21,41,.35)',
  } : {};

  return (
    <Sider
      trigger={null} // 自定义触发器在Header中
      collapsible
      collapsed={collapsed}
      breakpoint="lg" // Ant Design 内置的响应式断点
      collapsedWidth={screens.lg ? "80" : "0"} // 移动端折叠后宽度为0 (隐藏)
      onBreakpoint={broken => {
        // console.log('Sider onBreakpoint:', broken);
        // 这个回调可以用来处理断点变化时的逻辑，但大部分已通过collapsed state 和 useEffect 在 MainLayout 处理
      }}
      // onCollapse={(collapsed, type) => {
      //   console.log('Sider onCollapse:', collapsed, type);
      //   // 这个回调可以用来更新collapsed状态，但我们从props传入
      // }}
      theme="dark" // 可以根据整体主题调整 (light/dark)
      style={siderStyle}
      className={!screens.lg && collapsed ? 'sider-collapsed-mobile' : ''} // 用于自定义移动端隐藏样式
    >
      <div className="logo" style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}>
        <img src={logo} alt="Logo" style={{ height: 32, marginRight: collapsed ? 0 : 8 }} />
        {!collapsed && (
          <Title level={5} style={{ color: 'white', margin: 0, whiteSpace: 'nowrap' }}>
            桥梁知识图谱
          </Title>
        )}
      </div>
      <Menu
        theme="dark" // 与Sider主题一致
        mode="inline"
        selectedKeys={selectedKeys}
        items={menuItems}
      />
    </Sider>
  );
};

export default AppSider;

// 添加一个简单的CSS来处理移动端Sider完全隐藏的情况 (如果 collapsedWidth="0" 不够)
// 这部分可以放到 global.css 或 AppSider.css
// 确保在 global.css 中添加:
// .sider-collapsed-mobile { display: none !important; }
// 但通常 antd 的 collapsedWidth="0" 应该能处理好，除非有其他样式覆盖
// 对于 position: fixed 的 Sider，当 collapsed (通过 state 控制，而非 antd 内部的 collapsed) 时，
// 应该不渲染或者 visibility: hidden。
// AntD Sider 在 breakpoint 触发时，如果 collapsedWidth 为 0，它会添加 .ant-layout-sider-collapsed 类，并设置 width: 0。
// 如果是自定义的 collapsed 状态，需要确保 Sider 组件的 `collapsed` prop 正确传递。
// 在 MainLayout 中，我们已经通过 setCollapsed(true) 来控制移动端折叠，
// Sider 的 collapsed={collapsed} 和 collapsedWidth="0" 应该可以使其隐藏。
// 如果在移动端，当 collapsed 为 true 时，它应该消失。
// AppSider 组件的 collapsed prop 由 MainLayout 控制，当屏幕变小，MainLayout 会 setCollapsed(true)。
// 如果 collapsed 为 true 且 collapsedWidth 为 '0'，Sider 应该不显示。
// 如果是 Drawer 效果，则需要更复杂的实现，例如使用 antd Drawer 组件包裹 Sider。
// 当前实现是Sider在移动端折叠后宽度为0，如果需要更平滑的动画或覆盖效果，可考虑Drawer。
// 目前的方案是，非 lg 屏幕下，Sider position:fixed，如果 collapsed 为 true，则其宽度为 0，从而隐藏。
// 如果要实现点击遮罩关闭等，需要用 Drawer。目前仅是折叠。
// className={!screens.lg && collapsed ? 'sider-collapsed-mobile' : ''} 这行其实可能不需要了，
// 因为 antd 的 collapsedWidth="0" 应该会处理。
// 如果要实现点击外部关闭，则 MainLayout 需要处理遮罩层和点击事件。
// 为了简化，当前版本不实现遮罩关闭，仅通过Header按钮控制。
