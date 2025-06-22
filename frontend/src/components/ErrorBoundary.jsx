// frontend/src/components/ErrorBoundary.jsx
import React from 'react';
import { Result, Button } from 'antd';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // 更新 state 使下一次渲染能够显示降级后的 UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // 你同样可以将错误日志上报给服务器
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({ errorInfo });
    // logErrorToMyService(error, errorInfo); // 示例：发送到日志服务
  }

  handleGoHome = () => {
    // 尝试跳转到首页或刷新
    window.location.href = '/';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // 你可以自定义降级后的 UI 并渲染
      return (
        <Result
          status="error"
          title="页面加载出错"
          subTitle={this.props.errorMessage || "抱歉，此部分内容加载失败，请稍后重试或联系技术支持。"}
          extra={[
            <Button type="primary" key="console" onClick={this.handleGoHome}>
              返回首页
            </Button>,
            <Button key="buy" onClick={this.handleReload}>再试一次</Button>,
          ]}
        >
          {/* 可以选择性显示错误信息给开发者 */}
          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <div style={{ textAlign: 'left', whiteSpace: 'pre-wrap', background: '#fff0f0', padding: '15px', marginTop: '15px' }}>
              <p><strong>错误详情 (开发模式):</strong></p>
              {this.state.error && this.state.error.toString()}
              <br />
              {this.state.errorInfo.componentStack}
            </div>
          )}
        </Result>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
