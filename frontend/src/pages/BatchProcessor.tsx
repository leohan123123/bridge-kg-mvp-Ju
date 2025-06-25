import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Layout,
    Typography,
    Row,
    Col,
    Card,
    Upload,
    Button,
    Input,
    Progress,
    Table,
    Alert,
    message,
    Spin,
    Tag,
    Space,
    Modal, // For job config if needed in modal, or for other messages
} from 'antd';
import {
    InboxOutlined,      // For Upload Dragger
    PlayCircleOutlined, // For Start Processing
    FileTextOutlined,   // For Report
    LoadingOutlined,    // For loading state in status
    CheckCircleOutlined,
    CloseCircleOutlined,
    SyncOutlined,
    WarningOutlined,
    StopOutlined, // For Cancel
    DownloadOutlined // For download report
} from '@ant-design/icons';

import * as api from '../services/systemApi'; // API functions
import ErrorBoundary from '../components/ErrorBoundary'; // Import ErrorBoundary
import { UploadFile, UploadChangeParam } from 'antd/lib/upload/interface';

const { Title, Text, Paragraph } = Typography;
const { Content } = Layout;
const { TextArea } = Input;

// Interfaces based on systemApi.ts and page needs
interface UploadedFileOnServer {
    original_name: string;
    server_path: string;
    uid: string; // To link back to Antd UploadFile
}

interface BatchJobStatus extends api.BatchJobStatus {} // Use from API
interface BatchJobReport extends api.BatchJobReport {} // Use from API

const BatchProcessor: React.FC = () => {
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const [uploadedFilesOnServer, setUploadedFilesOnServer] = useState<UploadedFileOnServer[]>([]);
    const [jobConfig, setJobConfig] = useState<string>('{}');
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);
    const [jobStatus, setJobStatus] = useState<BatchJobStatus | null>(null);
    const [jobReport, setJobReport] = useState<BatchJobReport | null>(null);

    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [isProcessing, setIsProcessing] = useState<boolean>(false); // For when job is submitted
    const [isFetchingStatus, setIsFetchingStatus] = useState<boolean>(false);
    const [isFetchingReport, setIsFetchingReport] = useState<boolean>(false);

    const [error, setError] = useState<string | null>(null);

    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

    const clearJobState = () => {
        setCurrentJobId(null);
        setJobStatus(null);
        setJobReport(null);
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    };

    const handleFileChange = (info: UploadChangeParam) => {
        setFileList(info.fileList);
        if (info.file.status === 'done') {
            message.success(`${info.file.name} file uploaded successfully`);
            // Assuming backend returns path in response.data for customRequest
            // For now, we'll use a mock server path based on file name
            // In a real scenario, this would come from the upload success response
            setUploadedFilesOnServer(prev => [...prev, {
                original_name: info.file.name,
                server_path: `/tmp/uploads/${info.file.uid}_${info.file.name}`, // Mock path
                uid: info.file.uid
            }]);
        } else if (info.file.status === 'error') {
            message.error(`${info.file.name} file upload failed.`);
        } else if (info.file.status === 'removed') {
            setUploadedFilesOnServer(prev => prev.filter(f => f.uid !== info.file.uid));
        }
        clearJobState(); // Clear previous job state if files change
    };

    // Custom request for Antd Upload to simulate backend upload for now
    // In a real app, this would make an API call to an upload endpoint.
    // The task description implies BatchProcessor handles multi-file upload,
    // then sends paths to /batch/process. So, an upload step is needed.
    const handleCustomUpload = async (options: any) => {
        const { onSuccess, onError, file, onProgress } = options;
        setIsUploading(true);
        // Simulate upload progress
        let percent = 0;
        const timer = setInterval(() => {
            percent += 10;
            if (percent >= 100) {
                clearInterval(timer);
                onProgress({ percent: 100 });
                onSuccess("Ok"); // Mock success
                // In real scenario, response from server would be passed to onSuccess
            } else {
                onProgress({ percent });
            }
        }, 100);
        // Simulate API call for upload
        // For now, we just mark as success.
        // Replace with actual API call to an upload endpoint.
        // e.g. const fmData = new FormData(); fmData.append("file", file); await axios.post("/api/v1/batch/uploadfile", fmData);
        // The response should contain the server_path
        setIsUploading(false);
    };


    const fetchJobStatusCallback = useCallback(async (jobIdToFetch: string) => {
        if (!jobIdToFetch) return;
        setIsFetchingStatus(true);
        try {
            const status = await api.getBatchJobStatus(jobIdToFetch);
            setJobStatus(status);
            if (['COMPLETED', 'FAILED', 'CANCELLED', 'PARTIAL_SUCCESS'].includes(status.status)) {
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
                if (status.status !== 'CANCELLED') { // Don't fetch report if cancelled explicitly by user action here
                    fetchJobReportCallback(jobIdToFetch);
                }
            }
        } catch (err: any) {
            const msg = err.message || (err.response?.data?.detail) || 'Error fetching job status.';
            message.error(msg);
            setError(msg);
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        } finally {
            setIsFetchingStatus(false);
        }
    }, []);

    const fetchJobReportCallback = useCallback(async (jobIdToFetch: string) => {
        if (!jobIdToFetch) return;
        setIsFetchingReport(true);
        try {
            const report = await api.getBatchJobReport(jobIdToFetch);
            setJobReport(report);
        } catch (err: any) {
            const msg = err.message || (err.response?.data?.detail) || 'Error fetching job report.';
            message.error(msg);
            setError(msg);
        } finally {
            setIsFetchingReport(false);
        }
    }, []);


    const handleStartProcessing = async () => {
        if (uploadedFilesOnServer.length === 0) {
            message.warning('Please upload files first.');
            return;
        }
        setIsProcessing(true);
        setError(null);
        clearJobState(); // Clear any previous job info before starting a new one

        const formData = new FormData();
        uploadedFilesOnServer.forEach(f => formData.append('file_paths', f.server_path));
        formData.append('job_config_str', jobConfig);

        try {
            message.loading({ content: 'Starting batch processing...', key: 'startProcessing' });
            const response = await api.createBatchJob(formData);
            setCurrentJobId(response.job_id);
            message.success({ content: `Batch job started with ID: ${response.job_id}`, key: 'startProcessing', duration: 5 });

            fetchJobStatusCallback(response.job_id); // Initial fetch
            if (!pollingIntervalRef.current) {
                 pollingIntervalRef.current = setInterval(() => fetchJobStatusCallback(response.job_id), 5000); // Poll every 5s
            }
        } catch (err: any) {
            const msg = err.message || (err.response?.data?.detail) || 'Failed to start batch processing.';
            message.error({ content: msg, key: 'startProcessing' });
            setError(msg);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleCancelJob = async () => {
        if (!currentJobId) {
            message.warning('No active job to cancel.');
            return;
        }

        Modal.confirm({
            title: 'Confirm Cancel Job',
            content: `Are you sure you want to cancel job ID: ${currentJobId}? This action cannot be undone.`,
            okText: 'Yes, Cancel Job',
            okType: 'danger',
            cancelText: 'No, Keep Job',
            onOk: async () => {
                try {
                    message.loading({ content: `Cancelling job ${currentJobId}...`, key: 'cancelJob' });
                    await api.cancelBatchJob(currentJobId);
                    message.success({ content: `Job ${currentJobId} cancellation requested.`, key: 'cancelJob' });
                    if (pollingIntervalRef.current) {
                        clearInterval(pollingIntervalRef.current);
                        pollingIntervalRef.current = null;
                    }
                    setJobStatus(prev => prev ? {...prev, status: 'CANCELLED'} : {job_id: currentJobId, status: 'CANCELLED'}); // Optimistic update
                } catch (err: any) {
                    const msg = err.message || (err.response?.data?.detail) || 'Failed to cancel job.';
                    message.error({ content: msg, key: 'cancelJob' });
                }
            },
            onCancel: () => {
                message.info('Job cancellation aborted.');
            }
        });
    };

    useEffect(() => {
        // Cleanup polling on component unmount
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, []);

    const downloadReport = () => {
        if (!jobReport) return;
        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
            JSON.stringify(jobReport, null, 2)
        )}`;
        const link = document.createElement("a");
        link.href = jsonString;
        link.download = `batch_report_${currentJobId}.json`;
        link.click();
        message.success("Report download started.");
    };

    const jobStatusColumns = [
        { title: 'Property', dataIndex: 'property', key: 'property', width: '30%' },
        { title: 'Value', dataIndex: 'value', key: 'value', width: '70%' },
    ];

    const jobStatusData = jobStatus ? [
        { key: '1', property: 'Job ID', value: jobStatus.job_id },
        { key: '2', property: 'Status', value: <Tag color={
            jobStatus.status === 'COMPLETED' ? 'success' :
            jobStatus.status === 'RUNNING' ? 'processing' :
            jobStatus.status === 'FAILED' ? 'error' :
            jobStatus.status === 'CANCELLED' ? 'warning' :
            jobStatus.status === 'PARTIAL_SUCCESS' ? 'warning' :
            'default'}>{jobStatus.status}</Tag>
        },
        { key: '3', property: 'Total Files', value: jobStatus.total_files ?? 'N/A' },
        { key: '4', property: 'Processed', value: jobStatus.processed_files_count ?? 'N/A' },
        { key: '5', property: 'Successful', value: jobStatus.successful_files_count ?? 'N/A' },
        { key: '6', property: 'Failed', value: jobStatus.failed_files_count ?? 'N/A' },
        { key: '7', property: 'Est. Remaining Time', value: `${jobStatus.estimated_remaining_time_seconds ?? 'N/A'} sec` },
    ] : [];

    const reportFilesColumns = [
        { title: 'File Path', dataIndex: 'file_path', key: 'file_path' },
        { title: 'Status', dataIndex: 'status', key: 'status', render: (status: string) => <Tag color={status === 'SUCCESS' ? 'success' : 'error'}>{status}</Tag> },
        { title: 'Details', dataIndex: 'details', key: 'details' },
        { title: 'Output Path', dataIndex: 'output_path', key: 'output_path'},
    ];

    const errorSummaryColumns = [
        { title: 'File Path', dataIndex: 'file_path', key: 'file_path'},
        { title: 'Reason', dataIndex: 'reason', key: 'reason'}
    ];

    return (
        <Layout style={{ padding: '24px' }}>
            <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 'calc(100vh - 48px)' }}>
                <ErrorBoundary> {/* Wrap content with ErrorBoundary */}
                    <Title level={2} style={{ marginBottom: '24px' }}>批量处理 (Batch Processor)</Title>

                    {error && <Alert message="Error" description={error} type="error" closable showIcon style={{ marginBottom: 16 }} onClose={() => setError(null)} />}

                    <Row gutter={[24, 24]}>
                        {/* Column 1: Upload and Configuration */}
                        <Col xs={24} lg={10}>
                            <Card title="1. Upload Files & Configure" bordered={false} style={{ marginBottom: 24 }}>
                                <Upload.Dragger
                                    name="files"
                                    multiple={true}
                                    fileList={fileList}
                                    onChange={handleFileChange}
                                    customRequest={handleCustomUpload} // Using custom request for more control / to mock
                                    // beforeUpload={() => !isUploading} // Prevent new uploads while one is in progress if desired
                                    onRemove={(file) => {
                                        // Also remove from uploadedFilesOnServer if it was successfully "uploaded"
                                        setUploadedFilesOnServer(prev => prev.filter(f => f.uid !== file.uid));
                                        return true;
                                    }}
                                >
                                    <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                                    <p className="ant-upload-text">Click or drag files to this area to upload</p>
                                    <p className="ant-upload-hint">Support for single or bulk upload. Strictly prohibit from uploading company data or other band files</p>
                                </Upload.Dragger>

                                <Title level={5} style={{marginTop: 20, marginBottom: 8}}>Job Configuration (JSON)</Title>
                                <TextArea
                                    rows={4}
                                    value={jobConfig}
                                    onChange={e => setJobConfig(e.target.value)}
                                    placeholder='e.g., {"mode": "full_analysis", "priority": "high"}'
                                    disabled={isProcessing || (jobStatus && jobStatus.status === 'RUNNING')}
                                />
                                <Button
                                    type="primary"
                                    icon={<PlayCircleOutlined />}
                                    onClick={handleStartProcessing}
                                    disabled={isUploading || uploadedFilesOnServer.length === 0 || isProcessing || (jobStatus && jobStatus.status === 'RUNNING')}
                                    loading={isProcessing}
                                    style={{ marginTop: 16, width: '100%' }}
                                >
                                    Start Processing Uploaded Batch
                                </Button>
                            </Card>
                        </Col>

                        {/* Column 2: Job Status and Report */}
                        <Col xs={24} lg={14}>
                            {currentJobId && (
                                <Card title="2. Job Status & Progress" bordered={false} style={{ marginBottom: 24 }}
                                    extra={ jobStatus && jobStatus.status === 'RUNNING' &&
                                        <Button icon={<SyncOutlined spin={isFetchingStatus}/>} onClick={() => fetchJobStatusCallback(currentJobId)} disabled={isFetchingStatus}>Refresh Status</Button>
                                    }
                                >
                                    {isFetchingStatus && !jobStatus && <Spin tip="Fetching status..."><div style={{height: 50}} /></Spin>}
                                    {jobStatus && (
                                        <>
                                            <Table
                                                columns={jobStatusColumns}
                                                dataSource={jobStatusData}
                                                pagination={false}
                                                showHeader={false}
                                                size="small"
                                                style={{ marginBottom: 16 }}
                                            />
                                            {jobStatus.status === 'RUNNING' && jobStatus.total_files && jobStatus.processed_files_count !== undefined && (
                                                <Progress
                                                    percent={Math.round((jobStatus.processed_files_count / jobStatus.total_files) * 100)}
                                                    status="active"
                                                />
                                            )}
                                            {jobStatus.status === 'RUNNING' && (
                                                <Button
                                                    danger
                                                    icon={<StopOutlined />}
                                                    onClick={handleCancelJob}
                                                    style={{marginTop: 16, width: '100%'}}
                                                >
                                                    Cancel Job
                                                </Button>
                                            )}
                                        </>
                                    )}
                                    {!jobStatus && !isFetchingStatus && <Text type="secondary">No job active or status not yet available.</Text>}
                                </Card>
                            )}

                            {jobReport && (
                                <Card title="3. Batch Processing Report" bordered={false}
                                    extra={<Button icon={<DownloadOutlined />} onClick={downloadReport}>Download Report (JSON)</Button>}
                                >
                                    {isFetchingReport && <Spin tip="Fetching report..."><div style={{height:50}} /></Spin>}
                                    <Paragraph><strong>Overall Status:</strong> <Tag color={jobReport.status === 'COMPLETED' ? 'success' : 'warning'}>{jobReport.status}</Tag></Paragraph>
                                    <Paragraph><strong>Summary:</strong> {jobReport.summary || "N/A"}</Paragraph>

                                    {jobReport.results && jobReport.results.length > 0 &&
                                        <>
                                            <Title level={5} style={{marginTop: 16}}>Processed Files Details</Title>
                                            <Table
                                                columns={reportFilesColumns}
                                                dataSource={jobReport.results}
                                                rowKey="file_path"
                                                size="small"
                                                scroll={{ x: 800 }}
                                            />
                                        </>
                                    }
                                    {jobReport.error_summary && jobReport.error_summary.length > 0 &&
                                        <>
                                            <Title level={5} style={{marginTop: 16}}>Error Summary</Title>
                                            <Table
                                                columns={errorSummaryColumns}
                                                dataSource={jobReport.error_summary}
                                                rowKey={(record, index) => `${record.file_path}-${index}`}
                                                size="small"
                                            />
                                             {/* TODO: Add "Retry Failed Files" button - requires backend support */}
                                        </>
                                    }
                                </Card>
                            )}
                        </Col>
                    </Row>
                </ErrorBoundary>
            </Content>
        </Layout>
    );
};

export default BatchProcessor;

[end of frontend/src/pages/BatchProcessor.tsx]
