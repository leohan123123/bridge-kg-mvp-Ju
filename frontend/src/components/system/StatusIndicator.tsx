import React from 'react';
import { Tag, Tooltip } from 'antd';
import {
    CheckCircleOutlined,
    CloseCircleOutlined,
    SyncOutlined,
    ClockCircleOutlined,
    WarningOutlined,
} from '@ant-design/icons';

export type StatusType = 'success' | 'error' | 'processing' | 'pending' | 'warning';

interface StatusIndicatorProps {
    status: StatusType;
    text?: string; // Optional text to display next to the icon/tag
    tooltip?: string; // Optional tooltip for more details
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, text, tooltip }) => {
    let icon;
    let color;

    switch (status) {
        case 'success':
            icon = <CheckCircleOutlined />;
            color = 'success';
            break;
        case 'error':
            icon = <CloseCircleOutlined />;
            color = 'error';
            break;
        case 'processing':
            icon = <SyncOutlined spin />;
            color = 'processing';
            break;
        case 'pending':
            icon = <ClockCircleOutlined />;
            color = 'default';
            break;
        case 'warning':
            icon = <WarningOutlined />;
            color = 'warning';
            break;
        default:
            icon = null;
            color = 'default';
    }

    const content = (
        <Tag icon={icon} color={color}>
            {text || status.charAt(0).toUpperCase() + status.slice(1)}
        </Tag>
    );

    if (tooltip) {
        return <Tooltip title={tooltip}>{content}</Tooltip>;
    }

    return content;
};

export default StatusIndicator;
