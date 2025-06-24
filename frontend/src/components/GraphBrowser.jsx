import React, { useState, useEffect } from 'react';
import { List, Input, Select, Typography, Card, Tag, Spin, Alert, Empty, Row, Col, Button, Modal } from 'antd';
import axios from '../utils/axios'; // Assuming axios is configured

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

// API Endpoints for graph browsing (assuming they exist as per backend plan)
const SEARCH_ENTITIES_URL = '/api/v1/rag/search'; // GET /api/v1/rag/search?keywords=...&entity_types=...
const GET_ENTITY_NEIGHBORHOOD_URL = (entityId) => `/api/v1/rag/entity/${entityId}/neighborhood`; // GET /api/v1/rag/entity/{entity_id}/neighborhood?radius=...

// Available entity types for filtering (could be fetched or defined based on ontology)
// These should ideally match the keys in BRIDGE_RAG_ONTOLOGY
const ENTITY_TYPES = ["Bridge", "Material", "Component", "Standard", "Technique"];

const GraphBrowser = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntityTypes, setSelectedEntityTypes] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [isNeighborhoodModalVisible, setIsNeighborhoodModalVisible] = useState(false);
  const [selectedEntityForNeighborhood, setSelectedEntityForNeighborhood] = useState(null);
  const [neighborhoodData, setNeighborhoodData] = useState(null);
  const [isNeighborhoodLoading, setIsNeighborhoodLoading] = useState(false);
  const [neighborhoodError, setNeighborhoodError] = useState(null);
  const [neighborhoodRadius, setNeighborhoodRadius] = useState(1);


  // Debounced search effect could be added here if desired
  useEffect(() => {
    if (searchTerm.trim() === '' && selectedEntityTypes.length === 0) {
      setSearchResults([]); // Clear results if search is empty and no types selected
      // Or fetch all entities of a default type, or a general overview
      return;
    }
    fetchEntities();
  }, [searchTerm, selectedEntityTypes]);

  const fetchEntities = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (searchTerm.trim()) {
        params.append('keywords', searchTerm.trim());
      }
      if (selectedEntityTypes.length > 0) {
        params.append('entity_types', selectedEntityTypes.join(','));
      }

      // If both are empty, the backend might return all or an error.
      // For this stub, we expect at least one to be present, or backend handles it.
      if (!params.toString()) {
         setSearchResults([]);
         setIsLoading(false);
         return;
      }

      const response = await axios.get(`${SEARCH_ENTITIES_URL}?${params.toString()}`);
      setSearchResults(response.data || []);
      if (response.data.length === 0) {
        // message.info('No entities found matching your criteria.');
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
  };

  const fetchEntityNeighborhood = async (entity, radius = 1) => {
    if (!entity || !entity.id) return;

    setSelectedEntityForNeighborhood(entity);
    setIsNeighborhoodLoading(true);
    setNeighborhoodError(null);
    setNeighborhoodData(null);
    setIsNeighborhoodModalVisible(true);
    setNeighborhoodRadius(radius);

    try {
      const response = await axios.get(GET_ENTITY_NEIGHBORHOOD_URL(entity.id), { params: { radius } });
      setNeighborhoodData(response.data);
    } catch (err) {
      console.error('Error fetching entity neighborhood:', err);
      setNeighborhoodError(err.response?.data?.detail || 'Failed to fetch neighborhood data.');
    } finally {
      setIsNeighborhoodLoading(false);
    }
  };

  const handleRadiusChange = (newRadius) => {
    if (selectedEntityForNeighborhood) {
      fetchEntityNeighborhood(selectedEntityForNeighborhood, newRadius);
    }
  };


  const renderEntityItem = (item) => (
    <List.Item
      actions={[
        <Button type="link" onClick={() => fetchEntityNeighborhood(item, 1)}>View Neighborhood</Button>
      ]}
    >
      <List.Item.Meta
        title={<Text strong>{item.properties?.name || item.id}</Text>}
        description={
          <>
            <Tag color="blue">{item.type || 'Unknown Type'}</Tag>
            {item.properties && Object.entries(item.properties).map(([key, value]) => {
              if (key !== 'name' && typeof value === 'string' || typeof value === 'number') { // Display simple properties
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
    if (!neighborhoodData || !neighborhoodData.center_node) {
      return <Empty description="No neighborhood data available." />;
    }

    const { center_node, nodes, relationships } = neighborhoodData;

    return (
      <div>
        <Title level={5}>Center Node: {center_node.properties?.name || center_node.id} (<Tag>{center_node.type}</Tag>)</Title>
        <Paragraph>
            Radius: <Select value={neighborhoodRadius} onChange={handleRadiusChange} style={{ width: 80 }} size="small">
                        {[0,1,2,3].map(r => <Option key={r} value={r}>{r}</Option>)}
                    </Select> hops
        </Paragraph>
        {nodes && nodes.length > 0 && (
          <>
            <Text strong>Connected Nodes ({nodes.length}):</Text>
            <List
              size="small"
              dataSource={nodes}
              renderItem={node => (
                <List.Item>
                  <Text>{node.properties?.name || node.id} (<Tag>{node.type}</Tag>)</Text>
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
              renderItem={rel => (
                <List.Item>
                  <Text>
                    ({rel.source_name || rel.source?.substring(0,10) + '...'})
                    - <Tag color="geekblue">{rel.type || rel.label}</Tag> ->
                    ({rel.target_name || rel.target?.substring(0,10) + '...'})
                    {rel.properties && Object.keys(rel.properties).length > 0 &&
                        <Text type="secondary" style={{fontSize: '0.8em', marginLeft: '5px'}}>({JSON.stringify(rel.properties)})</Text>}
                  </Text>
                </List.Item>
              )}
              style={{maxHeight: '200px', overflowY: 'auto'}}
            />
          </>
        )}
        {(!nodes || nodes.length === 0) && (!relationships || relationships.length === 0) && (
            <Paragraph type="secondary">No connected nodes or relationships found within this radius.</Paragraph>
        )}
      </div>
    );
  };


  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: 'auto' }}>
      <Title level={3} style={{ textAlign: 'center', marginBottom: '20px' }}>Knowledge Graph Browser</Title>

      <Card style={{ marginBottom: '20px' }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Search
              placeholder="Search entities by keywords (e.g., bridge, steel)"
              onSearch={handleSearch}
              onChange={(e) => { if(e.target.value === '') setSearchTerm('');}} // Handle clear button
              enterButton
              loading={isLoading}
              style={{ width: '100%' }}
            />
          </Col>
          <Col>
            <Select
              mode="multiple"
              allowClear
              style={{ width: '250px' }}
              placeholder="Filter by entity type"
              onChange={handleEntityTypeChange}
              value={selectedEntityTypes}
              options={ENTITY_TYPES.map(type => ({ label: type, value: type }))}
            />
          </Col>
        </Row>
      </Card>

      {isLoading && !error && <div style={{ textAlign: 'center', padding: '30px' }}><Spin size="large" tip="Searching..." /></div>}
      {error && <Alert message={error} type="error" showIcon style={{ marginBottom: '20px' }} />}

      {!isLoading && !error && searchResults.length === 0 && (searchTerm || selectedEntityTypes.length > 0) && (
        <Empty description="No entities found matching your criteria. Try different keywords or types." />
      )}

      {!isLoading && !error && searchResults.length > 0 && (
        <List
          header={<Title level={5}>Search Results ({searchResults.length})</Title>}
          bordered
          dataSource={searchResults}
          renderItem={renderEntityItem}
          pagination={{
            pageSize: 5, // Adjust as needed
            responsive: true,
          }}
        />
      )}

      {selectedEntityForNeighborhood && (
        <Modal
          title={`Neighborhood of: ${selectedEntityForNeighborhood.properties?.name || selectedEntityForNeighborhood.id}`}
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
