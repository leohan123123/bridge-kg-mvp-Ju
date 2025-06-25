import React from 'react';
import { Table, Typography } from 'antd';
import type { TableProps } from 'antd';

const { Title, Paragraph } = Typography;

// This is a very basic placeholder.
// Ant Design's Table is already very powerful. A dedicated DataTable component
// would typically be created if there's a very specific set of features,
// configurations, or data transformations commonly needed across multiple tables
// that can't be easily achieved by configuring Antd's Table directly on pages.

interface CustomDataTableProps<T extends object = any> extends TableProps<T> {
    title?: string;
    // Add custom props for batch actions, export, print if needed
    // For example: onBatchDelete?: (selectedRowKeys: React.Key[]) => void;
}

const DataTable = <T extends object = any>({ title, dataSource, columns, ...rest }: CustomDataTableProps<T>) => {
    return (
        <div>
            {title && <Title level={4}>{title}</Title>}
            <Paragraph type="secondary">
                This is a placeholder for a dedicated DataTable component.
                Ant Design's Table is used below. Specific features like advanced filtering,
                custom batch actions, or integrated print/export buttons would be added here.
            </Paragraph>
            <Table<T>
                dataSource={dataSource}
                columns={columns}
                rowKey={(record: any) => record.id || record.key || JSON.stringify(record)} // Default rowKey
                {...rest} // Pass through other Antd Table props
            />
        </div>
    );
};

export default DataTable;
