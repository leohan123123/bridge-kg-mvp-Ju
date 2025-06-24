import React, { useState, useEffect } from 'react';
import { Select, Table, Spin, message, Typography } from 'antd';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Title } = Typography;
const { Option } = Select;

const NODE_TYPES = ['Bridge', 'Component', 'Material'];

const KnowledgeQuery = () => {
  const [selectedNodeType, setSelectedNodeType] = useState(NODE_TYPES[0]);
  const [tableData, setTableData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    if (selectedNodeType) {
      fetchData(selectedNodeType);
    }
  }, [selectedNodeType]);

  const fetchData = async (nodeType) => {
    setLoading(true);
    setTableData([]); // Clear previous data
    try {
      const response = await axios.get(`/knowledge/nodes/${nodeType}`);
      if (response.data && response.data.length > 0) {
        // Dynamically create columns based on the keys of the first object
        const firstItemKeys = Object.keys(response.data[0]);
        const generatedColumns = firstItemKeys.map(key => ({
          title: key.charAt(0).toUpperCase() + key.slice(1), // Capitalize first letter
          dataIndex: key,
          key: key,
        }));
        setColumns(generatedColumns);
        setTableData(response.data.map(item => ({ ...item, key: item.id }))); // Add key for Table
      } else {
        setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]); // Default columns
        setTableData([]);
        if (response.data && response.data.length === 0) {
          message.info(`No data found for node type: ${nodeType}`);
        }
      }
    } catch (error) {
      console.error('Failed to fetch knowledge data:', error);
      message.error(`Failed to fetch data for ${nodeType}. ${error.message}`);
      setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]); // Default columns on error
    } finally {
      setLoading(false);
    }
  };

  const handleNodeTypeChange = (value) => {
    setSelectedNodeType(value);
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2}>Knowledge Graph Query</Title>
      <Select
        defaultValue={selectedNodeType}
        style={{ width: 200, marginBottom: '20px' }}
        onChange={handleNodeTypeChange}
        loading={loading}
      >
        {NODE_TYPES.map(type => (
          <Option key={type} value={type}>{type}</Option>
        ))}
      </Select>
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={tableData}
          bordered
          size="small"
        />
      </Spin>
    </div>
  );
};

export default KnowledgeQuery;
