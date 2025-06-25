import React, { useState, useEffect } from 'react';
import { Layout, Row, Col, Card, Typography, Spin, Alert, Statistic, DatePicker, Button, Space } from 'antd';
import { PieChart, LineChart, BarChart } from '../components/visualization/ChartComponents'; // Using specific chart stubs
import { MetricCard } from '../components/visualization/PerformanceMetrics'; // Re-using MetricCard for stats
import { getDashboardMetrics, getKnowledgeAnalytics, getUsageStatistics } from '../services/advancedApi'; // API calls

const { Content } = Layout;
const { Title, Paragraph } = Typography;
const { RangePicker } = DatePicker;

/**
 * ProfessionalDashboard Page
 *
 * Provides a comprehensive overview of system statistics, knowledge analytics,
 * document processing, and user behavior through various charts and metrics.
 */
const ProfessionalDashboard: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // State for data - can be refined based on actual API responses
  const [systemOverviewData, setSystemOverviewData] = useState<any>(null);
  const [knowledgeAnalyticsData, setKnowledgeAnalyticsData] = useState<any>(null);
  // Add states for other modules as they are developed

  useEffect(() => {
    const fetchAllDashboardData = async () => {
      try {
        setLoading(true);
        // Parallel fetch for initial data
        const [overview, knowledgeStats] = await Promise.all([
          getDashboardMetrics(), // Fetches { metrics: [...] }
          getKnowledgeAnalytics()  // Fetches { analytics: {...} }
        ]);

        // Mock data structure for system overview if API returns minimal
        setSystemOverviewData(overview?.metrics?.length > 0 ? overview.metrics : {
          totalEntities: 12500,
          totalRelations: 75000,
          processedDocs: 580,
          activeUsers: 25,
        });

        // Mock data for knowledge analytics charts
        setKnowledgeAnalyticsData(knowledgeStats?.analytics ? knowledgeStats.analytics : {
          domainDistribution: [
            { value: 300, name: 'Bridge Design' },
            { value: 250, name: 'Construction Tech' },
            { value: 180, name: 'Inspection & Maint.' },
            { value: 220, name: 'Quality Control' },
            { value: 150, name: 'Other' }
          ],
          growthTrend: {
            dates: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            values: [100, 120, 150, 180, 220, 270]
          },
          // Placeholder for other analytics data (keyword cloud, quality radar)
        });

        setError(null);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data. Displaying sample data.");
        // Fallback to more extensive mock data on error
        setSystemOverviewData({ totalEntities: 12500, totalRelations: 75000, processedDocs: 580, activeUsers: 25 });
        setKnowledgeAnalyticsData({
          domainDistribution: [{ value: 300, name: 'Bridge Design' }, { value: 250, name: 'Construction Tech' }],
          growthTrend: { dates: ['Jan', 'Feb', 'Mar'], values: [100, 120, 150] }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchAllDashboardData();
  }, []);

  if (loading) {
    return <Spin tip="Loading dashboard..." size="large" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }} />;
  }

  if (error && !systemOverviewData) { // Show error only if no fallback data could be set
    return <Alert message="Error" description={error} type="error" showIcon />;
  }

  // Basic data for PieChart and LineChart stubs
  const knowledgeDistributionPieData = {
      options: { title: { text: "Knowledge Distribution" } },
      data: knowledgeAnalyticsData?.domainDistribution || []
  };
  const knowledgeGrowthLineData = {
      options: { title: { text: "Knowledge Growth Trend" } },
      data: {
          xAxis: { type: 'category', data: knowledgeAnalyticsData?.growthTrend?.dates || [] },
          yAxis: { type: 'value'},
          series: [{ data: knowledgeAnalyticsData?.growthTrend?.values || [], type: 'line' }]
      }
  };


  return (
    <Layout style={{ padding: '20px' }}>
      <Content>
        <Title level={2} style={{ marginBottom: '20px' }}>Professional Dashboard</Title>

        <Space direction="vertical" size="large" style={{width: '100%'}}>
            {/* 1. System Overview Module */}
            <Card title="System Overview">
                <Row gutter={16}>
                    <Col xs={24} sm={12} md={6}>
                        <MetricCard title="Total Entities" value={systemOverviewData?.totalEntities || 0} />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricCard title="Total Relations" value={systemOverviewData?.totalRelations || 0} />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricCard title="Processed Documents" value={systemOverviewData?.processedDocs || 0} />
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <MetricCard title="Active Users (Today)" value={systemOverviewData?.activeUsers || 0} />
                    </Col>
                    {/* TODO: Add System Usage概览, User Activity Heatmap placeholders */}
                </Row>
                 <Paragraph style={{marginTop: '10px', textAlign: 'center'}}>User Activity Heatmap (Placeholder)</Paragraph>
            </Card>

            {/* 2. Professional Knowledge Analysis Module */}
            <Card title="Professional Knowledge Analysis">
                <Row gutter={16}>
                    <Col xs={24} md={12} lg={8}>
                        <PieChart {...knowledgeDistributionPieData} />
                    </Col>
                    <Col xs={24} md={12} lg={16}>
                        <LineChart {...knowledgeGrowthLineData} />
                    </Col>
                </Row>
                <Row gutter={16} style={{marginTop: '20px'}}>
                    <Col xs={24} md={12}><Card size="small" title="Hot Search Keywords (TBD)"><Paragraph>Keyword cloud will appear here.</Paragraph></Card></Col>
                    <Col xs={24} md={12}><Card size="small" title="Knowledge Quality Score (TBD)"><Paragraph>Radar chart for quality scores will appear here.</Paragraph></Card></Col>
                </Row>
            </Card>

            {/* 3. Document Processing Analysis Module (Placeholder) */}
            <Card title="Document Processing Analysis (TBD)">
                <Paragraph>
                    Charts for document type statistics, success rates, error types, and processing times will be displayed here.
                </Paragraph>
            </Card>

            {/* 4. User Behavior Analysis Module (Placeholder) */}
            <Card title="User Behavior Analysis (TBD)">
                <Paragraph>
                    Statistics on feature usage, access times, search behavior, and data exports will be shown here.
                </Paragraph>
            </Card>

            {/* 5. Custom Dashboard & Report Generation (Placeholders) */}
            <Row gutter={16}>
                <Col xs={24} md={12}>
                    <Card title="Custom Dashboard Configuration (TBD)">
                        <Paragraph>Drag-and-drop layout, chart configuration, save/load dashboard settings.</Paragraph>
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card title="Report Generation (TBD)">
                        <Paragraph>Automated reports, custom templates, export (PDF, Excel), email functionality.</Paragraph>
                        <Button type="primary" style={{marginTop: '10px'}}>Generate Sample Report</Button>
                    </Card>
                </Col>
            </Row>
        </Space>
      </Content>
    </Layout>
  );
};

export default ProfessionalDashboard;
