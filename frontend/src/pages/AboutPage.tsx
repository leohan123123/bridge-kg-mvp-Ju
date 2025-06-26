import React from 'react';
import { Typography, Card, Avatar, Descriptions } from 'antd';
import { GithubOutlined, UserOutlined } from '@ant-design/icons'; // 引入图标

const { Title, Paragraph, Link } = Typography;

interface PageProps {
  // 根据实际需要定义
}

interface PageState {
  loading: boolean;
  data: any[];
  error: string | null;
}

const AboutPage: React.FC<PageProps> = () => {
  // 组件实现
  return (
    <div>
      <Title level={2}>关于本项目</Title>
      <Paragraph>
        本项目 (Bridge KG MVP) 是一个旨在演示如何构建一个基于知识图谱的全栈Web应用的最小可行产品。
        它整合了现代前后端技术栈，并提供了一个基础的框架，可供后续扩展。
      </Paragraph>

      <Card title="技术栈详情" style={{ marginTop: '24px' }}>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="前端">
            React, Vite, Ant Design, TypeScript, Axios, React Router
          </Descriptions.Item>
          <Descriptions.Item label="后端">
            FastAPI, Python 3.9+, Uvicorn, Pydantic
          </Descriptions.Item>
          <Descriptions.Item label="数据库">
            Neo4j (图数据库)
          </Descriptions.Item>
          <Descriptions.Item label="容器化">
            Docker, Docker Compose
          </Descriptions.Item>
          <Descriptions.Item label="核心功能理念">
            构建、管理和可视化知识图谱数据。
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="开发者信息" style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar size={64} icon={<UserOutlined />} style={{ marginRight: '16px' }}/>
          <div>
            <Title level={4} style={{ margin: 0 }}>AI Agent (Jules)</Title>
            <Paragraph style={{ margin: '4px 0 0' }}>
              由一个AI软件工程师自动生成的项目结构和基础代码。
            </Paragraph>
            <Link href="https://github.com/your-repo-link-here" target="_blank"> {/* 替换为你的仓库链接 */}
              <GithubOutlined /> GitHub仓库 (待补充)
            </Link>
          </div>
        </div>
      </Card>

      <Paragraph style={{ marginTop: '32px', textAlign: 'center' }}>
        感谢您的关注！如果您有任何建议或问题，欢迎通过GitHub Issue进行反馈。
      </Paragraph>
    </div>
  );
};

export default AboutPage;
