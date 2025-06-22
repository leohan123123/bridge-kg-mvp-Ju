import React from 'react';
import { Result, Button } from 'antd';
import { Link } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  return (
    <Result
      status="404"
      title="404 - 页面未找到"
      subTitle="抱歉，您访问的页面不存在。"
      extra={
        <Link to="/">
          <Button type="primary">返回首页</Button>
        </Link>
      }
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%' // 确保在父容器中垂直居中
      }}
    />
  );
};

export default NotFoundPage;
