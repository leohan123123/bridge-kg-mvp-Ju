import React, { useState, useEffect } from 'react';
import { Select, Table, Spin, message, Typography, Input, Button, Alert, Divider } from 'antd';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Title, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const NODE_TYPES = ['Bridge', 'Component', 'Material'];

const KnowledgeQuery = () => {
  // State for Knowledge Graph Query
  const [selectedNodeType, setSelectedNodeType] = useState(NODE_TYPES[0]);
  const [tableData, setTableData] = useState([]);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [columns, setColumns] = useState([]);

  // State for Simple RAG QA
  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState('');
  const [loadingQA, setLoadingQA] = useState(false);
  const [qaError, setQaError] = useState('');

  useEffect(() => {
    if (selectedNodeType) {
      fetchData(selectedNodeType);
    }
  }, [selectedNodeType]);

  const fetchData = async (nodeType) => {
    setLoadingGraph(true);
    setTableData([]); // Clear previous data
    try {
      const response = await axios.get(`/knowledge/nodes/${nodeType}`);
      if (response.data && response.data.length > 0) {
        const firstItemKeys = Object.keys(response.data[0]);
        const generatedColumns = firstItemKeys.map(key => ({
          title: key.charAt(0).toUpperCase() + key.slice(1),
          dataIndex: key,
          key: key,
        }));
        setColumns(generatedColumns);
        setTableData(response.data.map(item => ({ ...item, key: item.id || Math.random().toString() })));
      } else {
        setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]);
        setTableData([]);
        if (response.data && response.data.length === 0) {
          message.info(`No data found for node type: ${nodeType}`);
        }
      }
    } catch (error) {
      console.error('Failed to fetch knowledge data:', error);
      message.error(`Failed to fetch data for ${nodeType}. ${error.response?.data?.detail || error.message}`);
      setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]);
    } finally {
      setLoadingGraph(false);
    }
  };

  const handleNodeTypeChange = (value) => {
    setSelectedNodeType(value);
  };

  const handleQAQuestionChange = (e) => {
    setQaQuestion(e.target.value);
  };

  const handleAskQuestion = async () => {
    if (!qaQuestion.trim()) {
      message.warning('Please enter a question.');
      return;
    }
    setLoadingQA(true);
    setQaAnswer('');
    setQaError('');
    try {
      const response = await axios.post('/v1/qa/ask', { question: qaQuestion });
      if (response.data && response.data.message && response.data.message.content) {
        setQaAnswer(response.data.message.content);
      } else {
        // Handle cases where the response structure might be different or indicate an error
        setQaError('Received an unexpected response format from the server.');
        console.error('Unexpected QA response format:', response.data);
      }
    } catch (error) {
      console.error('Failed to ask question:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to get an answer.';
      setQaError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoadingQA(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2}>Knowledge Graph Query</Title>
      <Select
        defaultValue={selectedNodeType}
        style={{ width: 200, marginBottom: '20px' }}
        onChange={handleNodeTypeChange}
        loading={loadingGraph}
      >
        {NODE_TYPES.map(type => (
          <Option key={type} value={type}>{type}</Option>
        ))}
      </Select>
      <Spin spinning={loadingGraph}>
        <Table
          columns={columns}
          dataSource={tableData}
          bordered
          size="small"
          rowKey={record => record.id || Math.random().toString()}
        />
      </Spin>

      <Divider />

      <Title level={2} style={{ marginTop: '30px' }}>Simple Question Answering</Title>
      <TextArea
        rows={3}
        placeholder="Ask a question about bridge engineering..."
        value={qaQuestion}
        onChange={handleQAQuestionChange}
        style={{ marginBottom: '10px' }}
      />
      <Button
        type="primary"
        onClick={handleAskQuestion}
        loading={loadingQA}
        style={{ marginBottom: '20px' }}
      >
        Ask Question
      </Button>

      {loadingQA && <Spin tip="Getting your answer..." />}

      {qaError && !loadingQA && (
        <Alert message="Error" description={qaError} type="error" showIcon style={{ marginBottom: '20px' }}/>
      )}

      {qaAnswer && !loadingQA && !qaError && (
        <Alert
          message="Answer"
          description={<Paragraph copyable>{qaAnswer}</Paragraph>}
          type="info"
          showIcon
          style={{ whiteSpace: 'pre-wrap' }} // Preserve whitespace and newlines in answer
        />
      )}
    </div>
  );
};

export default KnowledgeQuery;
