import React from 'react';
import { Table, Button, Select } from 'antd';

const { Option } = Select;

const StandardsComparator = ({ standards, onCompare }) => {
  // Placeholder columns - adjust based on actual data structure
  const columns = [
    { title: 'Standard Name', dataIndex: 'name', key: 'name' },
    { title: 'Version', dataIndex: 'version', key: 'version' },
    { title: 'Details', dataIndex: 'details', key: 'details' },
  ];

  return (
    <div>
      {/* Add Select components for choosing standards to compare if needed */}
      <Button onClick={onCompare} type="primary" style={{ marginBottom: 16 }}>
        Compare Selected Standards
      </Button>
      <Table dataSource={standards} columns={columns} rowKey="id" />
    </div>
  );
};

export default StandardsComparator;
