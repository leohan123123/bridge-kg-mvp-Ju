import React, { useEffect, useState } from 'react';
import { Typography, Card, Row, Col, Statistic, Button, message } from 'antd';
import apiClient from '../utils/axios'; // 引入封装的axios实例

const { Title, Paragraph } = Typography;

interface HealthStatus {
  status: string;
}

interface PageProps {
  // 根据实际需要定义
}

interface PageState {
  loading: boolean;
  backendStatus: string;
  error: string | null; // For general page errors, though not used in current logic
}

const HomePage: React.FC<PageProps> = () => {
  const [backendStatus, setBackendStatus] = useState<PageState['backendStatus']>('检查中...');
  const [loading, setLoading] = useState<PageState['loading']>(false);
  // const [error, setError] = useState<PageState['error']>(null); // Example if needed

  const checkBackendHealth = async () => {
    setLoading(true);
    try {
      // 注意：apiClient 默认返回 response.data，所以类型直接是 HealthStatus
      const response = await apiClient.get<HealthStatus>('/health/health');
      if (response && response.status === 'ok') {
        setBackendStatus('后端服务正常');
        message.success('成功连接到后端服务！');
      } else {
        setBackendStatus('后端服务异常');
        message.error('后端服务状态未知或异常。');
      }
    } catch (error: any) {
      console.error("检查后端健康状态失败:", error);
      setBackendStatus('无法连接到后端');
      let errorMsg = '无法连接到后端服务。';
      if (error.response) {
        errorMsg += ` 状态码: ${error.response.status}.`;
      } else if (error.request) {
        errorMsg += ' 未收到响应。';
      } else {
        errorMsg += ` 错误: ${error.message}.`;
      }
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkBackendHealth(); // 组件加载时自动检查一次
  }, []);

  return (
    <div>
      <Title level={2}>欢迎使用知识图谱管理平台</Title>
      <Paragraph>
        这是一个基于 React, Ant Design, Vite, FastAPI 和 Neo4j 构建的全栈Web应用MVP。
        您可以在这里管理和可视化您的知识图谱数据。
      </Paragraph>

      <Row gutter={16} style={{ marginTop: '24px' }}>
        <Col span={12}>
          <Card title="项目概览">
            <Paragraph>前端技术: React, Vite, Ant Design, TypeScript</Paragraph>
            <Paragraph>后端技术: FastAPI, Python</Paragraph>
            <Paragraph>数据库: Neo4j</Paragraph>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="服务状态">
            <Statistic title="后端服务连接状态" value={backendStatus} />
            <Button type="primary" onClick={checkBackendHealth} loading={loading} style={{ marginTop: 16 }}>
              重新检查后端状态
            </Button>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="快速开始">
            <Paragraph>
              - 左侧菜单栏可以导航到不同功能模块 (当前为示例)。
            </Paragraph>
            <Paragraph>
              - 后续将添加节点管理、关系管理、图谱可视化等功能。
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HomePage;
