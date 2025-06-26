import React, { useState, useEffect, ChangeEvent, useMemo, useCallback } from 'react';
import { Select, Table, Spin, message, Typography, Input, Button, Alert, Divider } from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import { debounce } from 'lodash';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Title, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const NODE_TYPES: string[] = ['Bridge', 'Component', 'Material']; // Explicitly type

// Define a generic type for node data, as properties can vary
interface NodeData {
  id: string | number; // Assuming an ID property exists for keys
  key?: React.Key; // For Ant Design Table
  [key: string]: any; // Allow any other properties
}

// Type for QA API response
interface QAResponse {
  message: {
    content: string;
    // Potentially other fields like 'role', 'tool_calls' if they exist
  };
  // Any other top-level fields from the QA response
}


interface PageProps {}

interface PageState {
  selectedNodeType: string;
  tableData: NodeData[];
  loadingGraph: boolean;
  columns: ColumnsType<NodeData>; // Ant Design's ColumnsType
  qaQuestion: string;
  qaAnswer: string;
  loadingQA: boolean;
  qaError: string | null;
}

const KnowledgeQuery: React.FC<PageProps> = () => {
  const [selectedNodeType, setSelectedNodeType] = useState<PageState['selectedNodeType']>(NODE_TYPES[0]);
  const [tableData, setTableData] = useState<PageState['tableData']>([]);
  const [loadingGraph, setLoadingGraph] = useState<PageState['loadingGraph']>(false);
  const [columns, setColumns] = useState<PageState['columns']>([]);

  const [qaQuestion, setQaQuestion] = useState<PageState['qaQuestion']>('');
  const [qaAnswer, setQaAnswer] = useState<PageState['qaAnswer']>('');
  const [loadingQA, setLoadingQA] = useState<PageState['loadingQA']>(false);
  const [qaError, setQaError] = useState<PageState['qaError']>(null);

  // For table search/filter, if needed
  const [filterValue, setFilterValue] = useState<string>('');

  // Performance Optimization Presets
  const paginationConfig = useMemo((): TablePaginationConfig => ({ // Type for AntD Table
    defaultPageSize: 20,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => `${range[0]}-${range[1]} of ${total} items`,
    pageSizeOptions: ['10', '20', '50', '100'],
  }), []);

  const performNodeSearch = useCallback(async (nodeType: string, searchTerm: string) => {
    setLoadingGraph(true);
    setTableData([]);
    try {
      // Assuming an API endpoint for searching nodes like /knowledge/nodes/search?type=nodeType&term=searchTerm
      // This is a hypothetical endpoint. Adjust to your actual API.
      // If no search endpoint, filtering would be client-side on all fetched data (less ideal for large sets).
      const response = await axios.get<NodeData[]>(`/knowledge/nodes/search`, { params: { type: nodeType, term: searchTerm } });
      if (response.data && response.data.length > 0) {
        const firstItemKeys = Object.keys(response.data[0]);
        const generatedColumns: ColumnsType<NodeData> = firstItemKeys.map(key => ({
          title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
          dataIndex: key,
          key: key,
        }));
        setColumns(generatedColumns);
        setTableData(response.data.map(item => ({ ...item, key: item.id || Math.random().toString() })));
      } else {
        setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]);
        setTableData([]);
        message.info(`No data found for '${searchTerm}' in ${nodeType}`);
      }
    } catch (error: any) {
      console.error('Failed to search knowledge data:', error);
      message.error(`Failed to search data for ${nodeType}. ${error.response?.data?.detail || error.message}`);
      setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]);
      setTableData([]);
    } finally {
      setLoadingGraph(false);
    }
  }, []);


  const debouncedNodeSearch = useMemo(
    () => debounce(performNodeSearch, 500), // 500ms debounce
    [performNodeSearch]
  );


  useEffect(() => {
    if (selectedNodeType) {
      // If there's a filter value, trigger debounced search, else fetch all for type
      if (filterValue.trim()) {
        debouncedNodeSearch(selectedNodeType, filterValue.trim());
      } else {
        fetchData(selectedNodeType);
      }
    }
  }, [selectedNodeType, filterValue, debouncedNodeSearch]); // Add debouncedNodeSearch to dependencies

  const fetchData = async (nodeType: string) => {
    setLoadingGraph(true);
    setTableData([]);
    try {
      const response = await axios.get<NodeData[]>(`/knowledge/nodes/${nodeType}`);
      if (response.data && response.data.length > 0) {
        const firstItemKeys = Object.keys(response.data[0]);
        const generatedColumns: ColumnsType<NodeData> = firstItemKeys.map(key => ({
          title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '), // Format title
          dataIndex: key,
          key: key,
          // Add sorter or filter examples if applicable
          // sorter: (a, b) => typeof a[key] === 'number' && typeof b[key] === 'number' ? a[key] - b[key] : String(a[key]).localeCompare(String(b[key])),
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
    } catch (error: any) {
      console.error('Failed to fetch knowledge data:', error);
      message.error(`Failed to fetch data for ${nodeType}. ${error.response?.data?.detail || error.message}`);
      setColumns([{ title: 'ID', dataIndex: 'id', key: 'id' }, { title: 'Name', dataIndex: 'name', key: 'name' }]);
      setTableData([]); // Ensure tableData is empty on error
    } finally {
      setLoadingGraph(false);
    }
  };

  const handleNodeTypeChange = (value: string) => {
    setSelectedNodeType(value);
    // Optionally clear filter when node type changes, or let useEffect handle refetch
    // setFilterValue('');
  };

  const handleNodeFilterChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFilterValue(e.target.value);
  };

  const handleQAQuestionChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setQaQuestion(e.target.value);
  };

  const handleAskQuestion = async () => {
    if (!qaQuestion.trim()) {
      message.warning('Please enter a question.');
      return;
    }
    setLoadingQA(true);
    setQaAnswer('');
    setQaError(null);
    try {
      const response = await axios.post<QAResponse>('/v1/qa/ask', { question: qaQuestion });
      if (response.data?.message?.content) {
        setQaAnswer(response.data.message.content);
      } else {
        setQaError('Received an unexpected response format from the server.');
        console.error('Unexpected QA response format:', response.data);
      }
    } catch (error: any) {
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
      <Input
        placeholder={`Filter ${selectedNodeType} nodes...`}
        value={filterValue}
        onChange={handleNodeFilterChange}
        style={{ width: 240, marginBottom: '20px', marginLeft: '10px' }}
        allowClear
      />
      <Spin spinning={loadingGraph}>
        <Table
          columns={columns}
          dataSource={tableData}
          bordered
          size="small"
          rowKey={record => record.id || Math.random().toString()}
          pagination={paginationConfig}
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
