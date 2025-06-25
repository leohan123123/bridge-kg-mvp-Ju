import React from 'react';
import { Progress, Typography, Button, Space, Popover, Card } from 'antd';
import { PauseCircleOutlined, PlayCircleOutlined, StopOutlined, InfoCircleOutlined } from '@ant-design/icons';
import StatusIndicator, { StatusType as StatusIndicatorStatusType } from './StatusIndicator'; // Assuming StatusIndicator is in the same folder

const { Text } = Typography;

export interface TaskDetails {
    id: string;
    name: string;
    submittedAt?: Date;
    startedAt?: Date;
    finishedAt?: Date;
    // Add other relevant details
    [key: string]: any;
}

interface TaskProgressMonitorProps {
    taskId: string;
    taskName?: string;
    progressPercent: number; // 0-100
    status: StatusIndicatorStatusType; // 'success' | 'error' | 'processing' | 'pending' | 'warning'
    statusText?: string;
    details?: TaskDetails | null; // Optional task details for popover

    onPause?: (taskId: string) => void;
    onResume?: (taskId: string) => void; // Assuming pause implies a possible resume
    onCancel?: (taskId: string) => void;
    onRetry?: (taskId: string) => void; // If applicable for failed tasks

    isPausable?: boolean;
    isResumable?: boolean; // e.g. if currently paused
    isCancellable?: boolean;
    isRetryable?: boolean; // e.g. if task failed
}

const TaskProgressMonitor: React.FC<TaskProgressMonitorProps> = ({
    taskId,
    taskName = "Task",
    progressPercent,
    status,
    statusText,
    details,
    onPause,
    onResume,
    onCancel,
    onRetry,
    isPausable = false,
    isResumable = false,
    isCancellable = false,
    isRetryable = false,
}) => {

    const antdProgressStatus = (s: StatusIndicatorStatusType): "success" | "exception" | "normal" | "active" => {
        switch(s) {
            case 'success': return 'success';
            case 'error': return 'exception';
            case 'processing': return 'active';
            case 'pending': return 'normal'; // Or handle as 0% active
            case 'warning': return 'exception'; // Or normal with warning color
            default: return 'normal';
        }
    }

    const detailsContent = details ? (
        <Card size="small" title="Task Details">
            <Text strong>ID:</Text> <Text copyable>{details.id}</Text><br/>
            <Text strong>Name:</Text> {details.name || taskName}<br/>
            {details.submittedAt && <><Text strong>Submitted:</Text> {details.submittedAt.toLocaleString()}<br/></>}
            {/* Add more details as needed */}
        </Card>
    ) : <Text>No additional details available.</Text>;

    return (
        <Card
            size="small"
            title={taskName}
            style={{ marginBottom: 16 }}
            extra={details && (
                <Popover content={detailsContent} title="Task Information" trigger="click">
                    <Button type="text" icon={<InfoCircleOutlined />} />
                </Popover>
            )}
        >
            <Space direction="vertical" style={{ width: '100%' }}>
                <Progress percent={progressPercent} status={antdProgressStatus(status)} />
                <Space direction="horizontal" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <StatusIndicator status={status} text={statusText || status} />
                    <Space>
                        {isPausable && onPause && <Button size="small" icon={<PauseCircleOutlined />} onClick={() => onPause(taskId)}>Pause</Button>}
                        {isResumable && onResume && <Button size="small" icon={<PlayCircleOutlined />} onClick={() => onResume(taskId)}>Resume</Button>}
                        {isRetryable && onRetry && <Button size="small" onClick={() => onRetry(taskId)}>Retry</Button>}
                        {isCancellable && onCancel && <Button size="small" danger icon={<StopOutlined />} onClick={() => onCancel(taskId)}>Cancel</Button>}
                    </Space>
                </Space>
            </Space>
        </Card>
    );
};

export default TaskProgressMonitor;
