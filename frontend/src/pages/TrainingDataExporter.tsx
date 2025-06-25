import React, { useState, useEffect, useCallback } from 'react';
import {
    Layout,
    Typography,
    Row,
    Col,
    Card,
    Form,
    Select,
    InputNumber,
    Button,
    Table,
    Tag,
    Space,
    message,
    Spin,
    Input,
    Divider,
    Progress, // For export task progress
    // Tooltip,
    // Modal
} from 'antd';
import {
    ExperimentOutlined, // For Generate
    DownloadOutlined,   // For Export
    HistoryOutlined,    // For History
    SettingOutlined,    // For Config
    FileTextOutlined,   // For Preview/Report
    SyncOutlined,
} from '@ant-design/icons';

import * as api from '../services/systemApi'; // API functions
import ErrorBoundary from '../components/ErrorBoundary'; // Import ErrorBoundary

const { Title, Text, Paragraph } = Typography;
const { Content } = Layout;
const { Option } = Select;

// Interfaces based on systemApi.ts and page needs
interface TrainingDataGeneratePayload extends api.TrainingDataGeneratePayload {}
interface TrainingDataExportPayload extends api.TrainingDataExportPayload {}
interface ExportHistoryItem extends api.ExportHistoryItem {}
// interface DataQualityReport extends api.DataQualityReport {} // For later

interface GenerationFormValues {
    type: 'qa' | 'triples' | 'description';
    data_amount: number;
    entity_type_filters?: string; // Comma-separated
    relation_type_filters?: string; // Comma-separated
    // Add other quality params as form fields if needed
}

interface ExportFormValues {
    task_id?: string; // Optional, if exporting from a generated task
    format: 'JSONL' | 'CSV' | 'RDF' | 'JSON-LD';
    // Potentially include generation params here if not from task_id
    file_naming_rules?: string;
}


const TrainingDataExporter: React.FC = () => {
    const [generationForm] = Form.useForm<GenerationFormValues>();
    const [exportForm] = Form.useForm<ExportFormValues>();

    const [isGenerating, setIsGenerating] = useState<boolean>(false);
    const [generatedDataTaskId, setGeneratedDataTaskId] = useState<string | null>(null);
    // const [generatedDataPreview, setGeneratedDataPreview] = useState<any[] | null>(null); // For data preview table
    const [generationTaskStatus, setGenerationTaskStatus] = useState<api.TaskStatus | null>(null);
    const generationPollingRef = React.useRef<NodeJS.Timeout | null>(null);

    const [isExporting, setIsExporting] = useState<boolean>(false);
    const [currentExportId, setCurrentExportId] = useState<string | null>(null);
    const [exportTaskStatus, setExportTaskStatus] = useState<api.TaskStatus | null>(null);
    const exportPollingRef = React.useRef<NodeJS.Timeout | null>(null);

    const [exportHistory, setExportHistory] = useState<ExportHistoryItem[]>([]);
    const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

    // const [qualityReport, setQualityReport] = useState<DataQualityReport | null>(null); // For later
    // const [loadingQualityReport, setLoadingQualityReport] = useState<boolean>(false);


    const stopPolling = (ref: React.MutableRefObject<NodeJS.Timeout | null>) => {
        if (ref.current) {
            clearInterval(ref.current);
            ref.current = null;
        }
    };

    const fetchExportHistory = useCallback(async () => {
        setLoadingHistory(true);
        try {
            const history = await api.getExportHistory();
            setExportHistory(history);
        } catch (err: any) {
            message.error(err.message || 'Failed to fetch export history.');
        } finally {
            setLoadingHistory(false);
        }
    }, []);

    useEffect(() => {
        fetchExportHistory();
        // Cleanup polling on unmount
        return () => {
            stopPolling(generationPollingRef);
            stopPolling(exportPollingRef);
        };
    }, [fetchExportHistory]);

    const pollGenerationStatus = useCallback(async (taskId: string) => {
        try {
            const status = await api.getGenerationTaskStatus(taskId);
            setGenerationTaskStatus(status);
            if (status.status === 'COMPLETED' || status.status === 'FAILED') {
                stopPolling(generationPollingRef);
                if(status.status === 'COMPLETED') message.success(`Generation task ${taskId} completed.`);
                else message.error(`Generation task ${taskId} failed: ${status.message}`);
            }
        } catch (error) {
            message.error(`Error polling generation status for ${taskId}.`);
            stopPolling(generationPollingRef);
        }
    }, []);

    const handleGenerateData = async (values: GenerationFormValues) => {
        setIsGenerating(true);
        setGeneratedDataTaskId(null);
        setGenerationTaskStatus(null);
        stopPolling(generationPollingRef);
        message.loading({ content: 'Generating training data...', key: 'generateData' });

        const payload: TrainingDataGeneratePayload = {
            type: values.type,
            data_amount: values.data_amount,
            filters: {
                entity_types: values.entity_type_filters?.split(',').map(s => s.trim()).filter(s => s) || [],
                relation_types: values.relation_type_filters?.split(',').map(s => s.trim()).filter(s => s) || [],
            },
        };

        try {
            const response = await api.generateTrainingData(payload);
            message.success({ content: `Data generation task started: ${response.task_id}`, key: 'generateData', duration: 5 });
            setGeneratedDataTaskId(response.task_id);
            setGenerationTaskStatus({task_id: response.task_id, status: 'PENDING', progress: 0});
            generationPollingRef.current = setInterval(() => pollGenerationStatus(response.task_id), 2000); // Poll every 2s
        } catch (err: any) {
            message.error({ content: err.message || 'Failed to start data generation.', key: 'generateData' });
            setIsGenerating(false);
        }
        // setIsGenerating(false) will be handled by poller completion or error
    };

    const pollExportStatus = useCallback(async (exportId: string) => {
        try {
            const status = await api.getExportTaskStatus(exportId); // Assuming exportId is the taskId for status check
            setExportTaskStatus(status);
            if (status.status === 'COMPLETED' || status.status === 'FAILED') {
                stopPolling(exportPollingRef);
                fetchExportHistory(); // Refresh history when export is done
                if(status.status === 'COMPLETED') message.success(`Export task ${exportId} completed. File: ${status.result_url}`);
                else message.error(`Export task ${exportId} failed: ${status.message}`);
            }
        } catch (error) {
            message.error(`Error polling export status for ${exportId}.`);
            stopPolling(exportPollingRef);
        }
    }, [fetchExportHistory]);

    const handleExportData = async (values: ExportFormValues) => {
        setIsExporting(true);
        setCurrentExportId(null);
        setExportTaskStatus(null);
        stopPolling(exportPollingRef);
        message.loading({ content: 'Preparing data for export...', key: 'exportData' });

        const payload: TrainingDataExportPayload = {
            task_id: generatedDataTaskId || values.task_id,
            format: values.format,
        };

        if (!payload.task_id && !generationForm.getFieldValue('type')) { // Check if generation form has data for ad-hoc
             message.error({ content: 'No generation task ID. Please generate data first or provide parameters for ad-hoc export.', key: 'exportData'});
             setIsExporting(false);
             return;
        }
        // If no task_id but generationForm has values, construct generation_config for ad-hoc export
        if (!payload.task_id) {
            const genValues = generationForm.getFieldsValue();
            payload.generation_config = {
                 type: genValues.type,
                 data_amount: genValues.data_amount,
                 filters: {
                    entity_types: genValues.entity_type_filters?.split(',').map(s => s.trim()).filter(s => s) || [],
                    relation_types: genValues.relation_type_filters?.split(',').map(s => s.trim()).filter(s => s) || [],
                 }
            };
            message.info({content: "No specific task ID, attempting ad-hoc export with current generation parameters.", key: "exportData", duration: 5});
        }

        try {
            const response = await api.exportTrainingData(payload);
            // message.success({ content: `Export task started: ${response.export_id}. File will be available at: ${response.file_url || 'pending'}.`, key: 'exportData', duration: 8 });
            setCurrentExportId(response.export_id);
            setExportTaskStatus({task_id: response.export_id, status: 'PENDING', progress: 0});
            exportPollingRef.current = setInterval(() => pollExportStatus(response.export_id), 2500); // Poll every 2.5s
            // fetchExportHistory(); // Refresh history - will be refreshed by poller on completion
        } catch (err: any) {
            message.error({ content: err.message || 'Failed to start data export.', key: 'exportData' });
            setIsExporting(false);
        }
        // setIsExporting(false) will be handled by poller completion or error
    };

    const historyColumns = [
        { title: 'Export ID', dataIndex: 'export_id', key: 'export_id', width: 150, ellipsis: true },
        { title: 'Timestamp', dataIndex: 'timestamp', key: 'timestamp', render: (ts: string) => new Date(ts).toLocaleString(), width: 180 },
        { title: 'Format', dataIndex: 'format', key: 'format', width: 80, render: (format:string) => <Tag>{format}</Tag> },
        { title: 'Status', dataIndex: 'status', key: 'status', width: 120, render: (status:string) => <Tag color={status === 'COMPLETED' ? 'success' : (status === 'FAILED' ? 'error' : 'processing')}>{status}</Tag>},
        { title: 'Config Summary', dataIndex: 'config_summary', key: 'config_summary', ellipsis: true, render: (cfg: Record<string,any>) => <Tooltip title={<pre style={{maxWidth: 400, whiteSpace: 'pre-wrap', wordBreak: 'break-all'}}>{JSON.stringify(cfg, null, 2)}</pre>}><Text style={{cursor: 'pointer'}}>View Config</Text></Tooltip>},
        { title: 'Actions', key: 'actions', width: 100, fixed: 'right' as 'right', render: (_: any, record: ExportHistoryItem) => (
            <Tooltip title="Download file">
                {record.file_url && record.status === 'COMPLETED' ?
                    <Button type="primary" shape="circle" icon={<DownloadOutlined />} href={record.file_url} target="_blank" />
                    : <Button type="primary" shape="circle" icon={<DownloadOutlined />} disabled />
                }
            </Tooltip>
        )},
    ];

    return (
        <Layout style={{ padding: '24px' }}>
            <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 'calc(100vh - 48px)' }}>
                <ErrorBoundary> {/* Wrap content with ErrorBoundary */}
                    <Title level={2} style={{ marginBottom: '24px' }}>训练数据导出 (Training Data Exporter)</Title>

                    <Row gutter={[24, 24]}>
                        {/* Column 1: Configuration & Generation */}
                        <Col xs={24} lg={10}>
                            <Card title="1. Data Generation Configuration" bordered={false} style={{ marginBottom: 24 }}>
                                <Form form={generationForm} layout="vertical" onFinish={handleGenerateData} initialValues={{type: 'qa', data_amount: 100}}>
                                    <Form.Item name="type" label="Data Type" rules={[{ required: true }]}>
                                        <Select placeholder="Select data type">
                                            <Option value="qa">Question-Answer Pairs</Option>
                                            <Option value="triples">Triples (Subject-Predicate-Object)</Option>
                                            <Option value="description">Entity Descriptions</Option>
                                        </Select>
                                    </Form.Item>
                                    <Form.Item name="data_amount" label="Data Amount / Number of Samples" rules={[{ required: true }]}>
                                        <InputNumber min={1} style={{ width: '100%' }} />
                                    </Form.Item>
                                    <Form.Item name="entity_type_filters" label="Entity Type Filters (comma-separated, optional)">
                                        <Input placeholder="e.g., Person,Location" />
                                    </Form.Item>
                                    <Form.Item name="relation_type_filters" label="Relation Type Filters (comma-separated, optional)">
                                        <Input placeholder="e.g., WORKS_AT,LOCATED_IN" />
                                    </Form.Item>
                                    <Form.Item>
                                        <Button type="primary" htmlType="submit" icon={<ExperimentOutlined />} loading={isGenerating || generationTaskStatus?.status === 'PROCESSING'} block>
                                            {generationTaskStatus?.status === 'PROCESSING' ? 'Generating...' : 'Generate Data'}
                                        </Button>
                                    </Form.Item>
                                </Form>
                            </Card>

                            {generationTaskStatus && (
                                <Card title="Current Generation Task Status" bordered={false} style={{ marginBottom: 24 }}>
                                    <Paragraph>Task ID: <Text strong copyable>{generationTaskStatus.task_id}</Text></Paragraph>
                                    <Progress percent={generationTaskStatus.progress || 0} status={
                                        generationTaskStatus.status === 'FAILED' ? 'exception' :
                                        generationTaskStatus.status === 'COMPLETED' ? 'success' :
                                        'active'
                                    } />
                                    <Text type="secondary">{generationTaskStatus.message}</Text>
                                </Card>
                            )}

                            <Card title="2. Export Configuration" bordered={false}>
                                 <Form form={exportForm} layout="vertical" onFinish={handleExportData} initialValues={{format: 'JSONL'}}>
                                    <Form.Item name="task_id" label="Source Task ID (from generation)">
                                         <Input placeholder="Defaults to recently generated task ID" defaultValue={generatedDataTaskId || undefined} readOnly={!!generatedDataTaskId} key={generatedDataTaskId} />
                                    </Form.Item>
                                    <Form.Item name="format" label="Export Format" rules={[{ required: true }]}>
                                        <Select placeholder="Select export format">
                                            <Option value="JSONL">JSONL</Option>
                                            <Option value="CSV">CSV</Option>
                                            <Option value="RDF">RDF (N-Triples/Turtle - TBD)</Option>
                                            <Option value="JSON-LD">JSON-LD</Option>
                                        </Select>
                                    </Form.Item>
                                    <Form.Item>
                                        <Button type="primary" htmlType="submit" icon={<DownloadOutlined />} loading={isExporting || exportTaskStatus?.status === 'PROCESSING'} block>
                                            {exportTaskStatus?.status === 'PROCESSING' ? 'Exporting...' : 'Export Data'}
                                        </Button>
                                    </Form.Item>
                                </Form>
                            </Card>
                            {exportTaskStatus && (
                                 <Card title="Current Export Task Status" bordered={false} style={{marginTop: 24}}>
                                    <Paragraph>Export ID: <Text strong copyable>{exportTaskStatus.task_id}</Text></Paragraph>
                                    <Progress percent={exportTaskStatus.progress || 0} status={
                                        exportTaskStatus.status === 'FAILED' ? 'exception' :
                                        exportTaskStatus.status === 'COMPLETED' ? 'success' :
                                        'active'
                                    } />
                                    <Text type="secondary">{exportTaskStatus.message}</Text>
                                    {exportTaskStatus.status === 'COMPLETED' && exportTaskStatus.result_url &&
                                        <Paragraph style={{marginTop: 8}}><Button type="link" href={exportTaskStatus.result_url} target="_blank" icon={<DownloadOutlined />}>Download Exported File</Button></Paragraph>
                                    }
                                </Card>
                            )}
                        </Col>

                        {/* Column 2: Export History & Quality (Preview placeholder) */}
                        <Col xs={24} lg={14}>
                            <Card
                                title="3. Export History"
                                bordered={false}
                                style={{ marginBottom: 24 }}
                                extra={<Button icon={<SyncOutlined spin={loadingHistory}/>} onClick={fetchExportHistory} loading={loadingHistory}>Refresh History</Button>}
                            >
                                <Table
                                    columns={historyColumns}
                                    dataSource={exportHistory}
                                    rowKey="export_id"
                                    size="small"
                                    scroll={{ x: 800, y: 400 }}
                                    loading={loadingHistory}
                                    locale={{emptyText: "No export history found."}}
                                />
                            </Card>

                            <Card title="4. Data Quality & Preview (Placeholder)" bordered={false}>
                                <Paragraph type="secondary">
                                    This section will display a preview of the generated data, quality scores, and any identified issues before final export.
                                    It will also allow for viewing quality reports of past exports.
                                </Paragraph>
                            </Card>
                        </Col>
                    </Row>
                </ErrorBoundary>
            </Content>
        </Layout>
    );
};

// Need to import Tooltip for history table
import { Tooltip } from 'antd';

export default TrainingDataExporter;

[end of frontend/src/pages/TrainingDataExporter.tsx]
