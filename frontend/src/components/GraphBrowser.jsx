import React, { useState, useEffect } from 'react';
import { List, Input, Select, Typography, Card, Tag, Spin, Alert, Empty, Row, Col, Button, Modal, Statistic, Descriptions } from 'antd';
import axios from '../utils/axios'; // Assuming axios is configured

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

// API Endpoints
const SEARCH_ENTITIES_URL = '/api/v1/rag/search'; // GET /api/v1/rag/search?query=...
const GET_ENTITY_NEIGHBORHOOD_URL = (entityId) => `/api/v1/rag/entity/${entityId}/neighborhood`; // GET /api/v1/rag/entity/{entity_id}/neighborhood?max_depth=...
const GET_GRAPH_STATS_URL = '/api/v1/rag/graph_stats'; // GET /api/v1/rag/graph_stats

// Available entity types for filtering (could be fetched or defined based on ontology)
// These should ideally match the keys in BRIDGE_RAG_ONTOLOGY.
// Note: The current backend search API takes a general 'query' string, not specific entity_types for filtering.
const ENTITY_TYPES = ["结构类型", "材料类型", "技术规范", "施工工艺"]; // Updated to match ontology examples

const GraphBrowser = () => {
  const [searchTerm, setSearchTerm] = useState('');
  // selectedEntityTypes is kept for potential future use or if search logic is enhanced
  const [selectedEntityTypes, setSelectedEntityTypes] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [isNeighborhoodModalVisible, setIsNeighborhoodModalVisible] = useState(false);
  const [selectedEntityForNeighborhood, setSelectedEntityForNeighborhood] = useState(null);
  const [neighborhoodData, setNeighborhoodData] = useState(null);
  const [isNeighborhoodLoading, setIsNeighborhoodLoading] = useState(false);
  const [neighborhoodError, setNeighborhoodError] = useState(null);
  const [neighborhoodMaxDepth, setNeighborhoodMaxDepth] = useState(1); // Changed from radius

  // State for Graph Statistics
  const [graphStats, setGraphStats] = useState(null);
  const [isStatsLoading, setIsStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState(null);

  // Fetch graph statistics on component mount
  useEffect(() => {
    fetchGraphStats();
  }, []);

  const fetchGraphStats = async () => {
    setIsStatsLoading(true);
    setStatsError(null);
    try {
      const response = await axios.get(GET_GRAPH_STATS_URL);
      setGraphStats(response.data);
    } catch (err) {
      console.error('Error fetching graph stats:', err);
      setStatsError(err.response?.data?.detail || 'Failed to fetch graph statistics.');
    } finally {
      setIsStatsLoading(false);
    }
  };


  // Debounced search effect
  useEffect(() => {
    // The new search API takes a 'query' string.
    // If searchTerm is empty, we might not want to search, or search for "everything" (if supported)
    if (searchTerm.trim() === '') {
      setSearchResults([]);
      // Optionally, clear error if search term is cleared
      // setError(null);
      return;
    }
    // No explicit selectedEntityTypes in the new search query structure for backend
    fetchEntities();
  }, [searchTerm]); // Removed selectedEntityTypes from dependency array as it's not used in query

  const fetchEntities = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (searchTerm.trim()) {
        params.append('query', searchTerm.trim()); // Changed 'keywords' to 'query'
      }
      // selectedEntityTypes is not part of the new API query structure for search_knowledge_graph_api
      // if (selectedEntityTypes.length > 0) {
      //   params.append('entity_types', selectedEntityTypes.join(','));
      // }

      if (!params.toString()) {
         setSearchResults([]);
         setIsLoading(false);
         return;
      }

      const response = await axios.get(`${SEARCH_ENTITIES_URL}?${params.toString()}`);
      // Assuming response.data is the list of entities or an object with an error message
      if (response.data && Array.isArray(response.data)) {
        setSearchResults(response.data);
        if (response.data.length === 0) {
            // Optional: message.info('No entities found matching your criteria.');
        }
      } else if (response.data && response.data.message) { // Handle "no matches" message from backend
        setSearchResults([]);
        // setError(response.data.message); // Or display as info
      } else {
        setSearchResults([]);
      }
    } catch (err) {
      console.error('Error fetching entities:', err);
      setError(err.response?.data?.detail || 'Failed to fetch entities.');
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
  };

  const handleEntityTypeChange = (values) => {
    setSelectedEntityTypes(values);
    // Note: This won't trigger a new search automatically unless fetchEntities is called or searchTerm changes.
    // And current backend search doesn't filter by types via query param.
  };

  const fetchEntityNeighborhood = async (entity, depth = 1) => { // Renamed radius to depth
    if (!entity || !entity.id) return; // entity.id should be Neo4j element ID

    setSelectedEntityForNeighborhood(entity);
    setIsNeighborhoodLoading(true);
    setNeighborhoodError(null);
    setNeighborhoodData(null);
    setIsNeighborhoodModalVisible(true);
    setNeighborhoodMaxDepth(depth); // Use max_depth

    try {
      // Backend expects entity_id as path param and max_depth as query param
      const response = await axios.get(GET_ENTITY_NEIGHBORHOOD_URL(entity.id), { params: { max_depth: depth } });
      setNeighborhoodData(response.data); // data should be {nodes: [], relationships: []}
    } catch (err) {
      console.error('Error fetching entity neighborhood:', err);
      setNeighborhoodError(err.response?.data?.detail || 'Failed to fetch neighborhood data.');
    } finally {
      setIsNeighborhoodLoading(false);
    }
  };

  const handleMaxDepthChange = (newDepth) => { // Renamed from handleRadiusChange
    if (selectedEntityForNeighborhood) {
      fetchEntityNeighborhood(selectedEntityForNeighborhood, newDepth);
    }
  };

  const renderEntityItem = (item) => ( // item is an entity from search results
    <List.Item
      actions={[
        // Pass item (which includes item.id as the elementId)
        <Button type="link" onClick={() => fetchEntityNeighborhood(item, 1)}>View Neighborhood</Button>
      ]}
    >
      <List.Item.Meta
        title={<Text strong>{item.name || item.id}</Text>} // 'name' from KnowledgeGraphEngine.query_graph_knowledge
        description={
          <>
            {item.labels && item.labels.map(label => <Tag color="blue" key={label}>{label}</Tag>)}
            {item.properties && Object.entries(item.properties).map(([key, value]) => {
              if (typeof value === 'string' || typeof value === 'number') {
                return <Text key={key} style={{ display: 'block' }}><Text strong>{key}:</Text> {String(value).substring(0,100)}{String(value).length > 100 ? '...' : ''}</Text>;
              }
              return null;
            })}
          </>
        }
      />
    </List.Item>
  );

  const renderNeighborhoodContent = () => {
    if (isNeighborhoodLoading) {
      return <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" tip="Loading neighborhood..." /></div>;
    }
    if (neighborhoodError) {
      return <Alert message={neighborhoodError} type="error" showIcon />;
    }
    // neighborhoodData structure from backend: { nodes: [...], relationships: [...] }
    // Each node: { id: elementId, labels: [], properties: {...} }
    // Each rel: { id: elementId, type: "REL_TYPE", start_node_id: "", end_node_id: "", properties: {...} }
    if (!neighborhoodData || (!neighborhoodData.nodes && !neighborhoodData.relationships)) {
      return <Empty description="No neighborhood data available or entity not found." />;
    }

    const { nodes, relationships } = neighborhoodData;
    const centerNode = selectedEntityForNeighborhood ? nodes?.find(n => n.id === selectedEntityForNeighborhood.id) : null;

    return (
      <div>
        {selectedEntityForNeighborhood && (
             <Title level={5}>
                Neighborhood of: {selectedEntityForNeighborhood.name || selectedEntityForNeighborhood.id}
                {centerNode && centerNode.labels && centerNode.labels.map(l => <Tag key={l} style={{marginLeft: '5px'}}>{l}</Tag>)}
            </Title>
        )}
        <Paragraph>
            Max Depth: <Select value={neighborhoodMaxDepth} onChange={handleMaxDepthChange} style={{ width: 80 }} size="small">
                        {[1, 2, 3, 4, 5].map(d => <Option key={d} value={d}>{d}</Option>)}
                    </Select> hops
        </Paragraph>
        {nodes && nodes.length > 0 && (
          <>
            <Text strong>Nodes in Neighborhood ({nodes.length}):</Text>
            <List
              size="small"
              dataSource={nodes}
              renderItem={node => (
                <List.Item>
                  <Text>{node.name || node.properties?.name || node.id} </Text>
                  {node.labels && node.labels.map(l => <Tag key={l}>{l}</Tag>)}
                </List.Item>
              )}
              style={{maxHeight: '200px', overflowY: 'auto', marginBottom: '10px'}}
            />
          </>
        )}
        {relationships && relationships.length > 0 && (
          <>
            <Text strong>Relationships ({relationships.length}):</Text>
            <List
              size="small"
              dataSource={relationships}
              renderItem={rel => {
                const startNode = nodes.find(n => n.id === rel.start_node_id);
                const endNode = nodes.find(n => n.id === rel.end_node_id);
                return (
                    <List.Item>
                    <Text>
                        ({startNode?.properties?.name || startNode?.name || rel.start_node_id.substring(0,8)})
                        - <Tag color="geekblue">{rel.type}</Tag> ->
                        ({endNode?.properties?.name || endNode?.name || rel.end_node_id.substring(0,8)})
                        {rel.properties && Object.keys(rel.properties).length > 0 &&
                            <Text type="secondary" style={{fontSize: '0.8em', marginLeft: '5px'}}>({JSON.stringify(rel.properties)})</Text>}
                    </Text>
                    </List.Item>
                );
              }}
              style={{maxHeight: '200px', overflowY: 'auto'}}
            />
          </>
        )}
        {(!nodes || nodes.length === 0) && (!relationships || relationships.length === 0) && (
            <Paragraph type="secondary">No connected nodes or relationships found within this depth for the selected entity.</Paragraph>
        )}
      </div>
    );
  };

  const renderGraphStatistics = () => {
    if (isStatsLoading) {
      return <div style={{ textAlign: 'center', padding: '20px' }}><Spin tip="Loading graph statistics..." /></div>;
    }
    if (statsError) {
      return <Alert message={statsError} type="error" showIcon style={{ marginBottom: '20px' }} />;
    }
    if (!graphStats) {
      return <Empty description="Graph statistics are not available." style={{ marginBottom: '20px' }} />;
    }

    return (
      <Card title="Graph Statistics" style={{ marginBottom: '20px' }}>
        <Row gutter={16}>
          <Col span={8}><Statistic title="Total Nodes" value={graphStats.total_nodes} /></Col>
          <Col span={8}><Statistic title="Total Relationships" value={graphStats.total_relationships} /></Col>
          <Col span={8}><Statistic title="Graph Density" value={graphStats.graph_density?.toFixed(4) || 'N/A'} /></Col>
        </Row>
        <Row gutter={16} style={{marginTop: '20px'}}>
            <Col span={24}>
                <Text strong>Connectivity:</Text> <Text>{graphStats.connected_components_count || 'N/A'}</Text>
            </Col>
        </Row>
        {graphStats.node_type_distribution && Object.keys(graphStats.node_type_distribution).length > 0 && (
          <Descriptions title="Node Type Distribution" bordered column={1} size="small" style={{ marginTop: '20px' }}>
            {Object.entries(graphStats.node_type_distribution).map(([type, count]) => (
              <Descriptions.Item label={type} key={type}>{count}</Descriptions.Item>
            ))}
          </Descriptions>
        )}
        {graphStats.relationship_type_distribution && Object.keys(graphStats.relationship_type_distribution).length > 0 && (
          <Descriptions title="Relationship Type Distribution" bordered column={1} size="small" style={{ marginTop: '20px' }}>
            {Object.entries(graphStats.relationship_type_distribution).map(([type, count]) => (
              <Descriptions.Item label={type} key={type}>{count}</Descriptions.Item>
            ))}
          </Descriptions>
        )}
      </Card>
    );
  };

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: 'auto' }}>
      <Title level={3} style={{ textAlign: 'center', marginBottom: '20px' }}>Knowledge Graph Browser & Statistics</Title>

      {renderGraphStatistics()}

      <Card title="Entity Search & Exploration" style={{ marginBottom: '20px' }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Search
              placeholder="Search entities by keywords (e.g., bridge, steel)"
              onSearch={handleSearch} // Triggers search by setting searchTerm
              onChange={(e) => { if(e.target.value === '') setSearchTerm('');}} // Handle clear button
              enterButton
              loading={isLoading}
              style={{ width: '100%' }}
            />
          </Col>
          <Col>
            {/* Select for entity types is currently not used by backend search but kept for UI consistency or future */}
            <Select
              mode="multiple"
              allowClear
              style={{ width: '250px' }}
              placeholder="Filter by entity type (visual only)"
              onChange={handleEntityTypeChange}
              value={selectedEntityTypes}
              options={ENTITY_TYPES.map(type => ({ label: type, value: type }))}
            />
          </Col>
        </Row>
      </Card>

      {isLoading && !error && <div style={{ textAlign: 'center', padding: '30px' }}><Spin size="large" tip="Searching..." /></div>}
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: '20px' }} />}

      {!isLoading && !error && searchResults.length === 0 && searchTerm && ( // Show empty only if a search was made
        <Empty description="No entities found matching your criteria. Try different keywords or types." />
      )}

      {!isLoading && !error && searchResults.length > 0 && (
        <List
          header={<Title level={5}>Search Results ({searchResults.length})</Title>}
          bordered
          dataSource={searchResults}
          renderItem={renderEntityItem}
          pagination={{
            pageSize: 5,
            responsive: true,
          }}
        />
      )}

      {selectedEntityForNeighborhood && (
        <Modal
          title={`Neighborhood of: ${selectedEntityForNeighborhood.name || selectedEntityForNeighborhood.id}`}
          visible={isNeighborhoodModalVisible}
          onOk={() => setIsNeighborhoodModalVisible(false)}
          onCancel={() => setIsNeighborhoodModalVisible(false)}
          width="70%"
          footer={[<Button key="close" onClick={() => setIsNeighborhoodModalVisible(false)}>Close</Button>]}
        >
          {renderNeighborhoodContent()}
        </Modal>
      )}
    </div>
  );
};

export default GraphBrowser;
