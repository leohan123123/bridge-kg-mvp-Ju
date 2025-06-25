import React, { useState, useEffect, useRef } from 'react';
import { Layout, Typography, Row, Col, Card, Tabs, Spin, Alert, Empty, List, Button } from 'antd';
import ProfessionalSearch from '../components/professional/ProfessionalSearch';
import KnowledgeTree from '../components/professional/KnowledgeTree';
import StandardsComparator from '../components/professional/StandardsComparator';
import ParameterCalculator from '../components/professional/ParameterCalculator';
import { Network } from 'vis-network/standalone/esm/vis-network'; // For graph visualization
import apiClient, {
    getDesignTheoryCategories,
    getFormulas,
    getDesignNorms,
    getMaterialParams,
    getDesignCases,
    searchDesignKnowledge,
    getDesignKnowledgeGraph
} from '../utils/api'; // Import the apiClient and specific functions

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

// Example calculator params, could also be fetched or defined based on context
const mockCalculatorParams = [
    { name: 'load', label: 'Load (kN)', defaultValue: 100 },
    { name: 'span', label: 'Span (m)', defaultValue: 10 },
];

const BridgeDesignKB = () => {
  const [designTheoryCategories, setDesignTheoryCategories] = useState({ data: [], loading: true, error: null });
  const [formulas, setFormulas] = useState({ data: [], loading: false, error: null });
  const [selectedCategoryFormulas, setSelectedCategoryFormulas] = useState(null);
  const [designNorms, setDesignNorms] = useState({ data: [], loading: true, error: null });
  const [materialParams, setMaterialParams] = useState({ data: [], loading: true, error: null });
  const [designCases, setDesignCases] = useState({ data: [], loading: true, error: null });
  const [knowledgeGraphData, setKnowledgeGraphData] = useState({ data: null, loading: true, error: null });
  const [searchResults, setSearchResults] = useState({ data: [], loading: false, error: null });

  const [selectedNormsForComparison, setSelectedNormsForComparison] = useState([]); // IDs of norms
  const graphRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setDesignTheoryCategories(prev => ({ ...prev, loading: true }));
        const categories = await getDesignTheoryCategories();
        // Assuming API returns data in a format suitable for antd Tree: { title, key, children: [] }
        // If not, transform data here. e.g. categories.map(c => ({ title: c.name, key: c.id, ... }))
        setDesignTheoryCategories({ data: categories || [], loading: false, error: null });
      } catch (error) {
        setDesignTheoryCategories({ data: [], loading: false, error: error.message || 'Failed to fetch categories' });
      }

      try {
        setDesignNorms(prev => ({ ...prev, loading: true }));
        const norms = await getDesignNorms();
        // Assuming API returns: { id, name, version, details }
        setDesignNorms({ data: norms || [], loading: false, error: null });
      } catch (error) {
        setDesignNorms({ data: [], loading: false, error: error.message || 'Failed to fetch norms' });
      }

      try {
        setMaterialParams(prev => ({ ...prev, loading: true }));
        const materials = await getMaterialParams();
         // Assuming API returns: { id, name, params }
        setMaterialParams({ data: materials || [], loading: false, error: null });
      } catch (error) {
        setMaterialParams({ data: [], loading: false, error: error.message || 'Failed to fetch materials' });
      }

      try {
        setDesignCases(prev => ({ ...prev, loading: true }));
        const cases = await getDesignCases();
        // Assuming API returns: { id, name, template }
        setDesignCases({ data: cases || [], loading: false, error: null });
      } catch (error) {
        setDesignCases({ data: [], loading: false, error: error.message || 'Failed to fetch design cases' });
      }

      try {
        setKnowledgeGraphData(prev => ({ ...prev, loading: true }));
        const graphData = await getDesignKnowledgeGraph(); // Expects { nodes: [], edges: [] }
        setKnowledgeGraphData({ data: graphData, loading: false, error: null });
      } catch (error) {
        setKnowledgeGraphData({ data: null, loading: false, error: error.message || 'Failed to fetch graph data' });
      }
    };
    fetchData();
  }, []);

  // Fetch formulas when a category is selected
  const handleCategorySelect = async (selectedKeys, info) => {
    if (selectedKeys.length > 0) {
      const categoryId = selectedKeys[0];
      setSelectedCategoryFormulas(categoryId); // Keep track of selected category for formulas
      setFormulas(prev => ({ ...prev, loading: true, error: null }));
      try {
        const fetchedFormulas = await getFormulas(categoryId);
        // Assuming API returns: { id, name, details }
        setFormulas({ data: fetchedFormulas || [], loading: false, error: null });
      } catch (error) {
        setFormulas({ data: [], loading: false, error: error.message || `Failed to fetch formulas for category ${info.node.title}`});
      }
    }
  };

  const handleSearch = async (value) => {
    if (!value) {
        setSearchResults({data: [], loading: false, error: null});
        return;
    }
    setSearchResults(prev => ({ ...prev, loading: true, error: null }));
    try {
      const results = await searchDesignKnowledge(value);
      // Assuming API returns: { id, title, description }
      setSearchResults({ data: results || [], loading: false, error: null });
    } catch (error) {
      setSearchResults({ data: [], loading: false, error: error.message || 'Search failed' });
    }
  };

  const handleCompareNorms = () => {
    console.log('Comparing selected norms:', selectedNormsForComparison);
    // Implement comparison logic or display component here
    // This might involve fetching detailed data for selected norms if not already available
    alert(`Comparing norms: ${selectedNormsForComparison.join(', ')}. (Further implementation needed)`);
  };

  const handleCalculate = (data) => {
    console.log('Calculating with data:', data);
    // Example: POST to a calculation endpoint
    // apiClient.post('/bridge-design/calculate/bending-moment', data)
    //   .then(response => alert(`Calculated result: ${response.result}`))
    //   .catch(err => alert(`Calculation failed: ${err.message}`));
    alert(`Mock Calculation: Moment = ${data.load * data.span / 8} kNm (API call not implemented)`);
  };

  useEffect(() => {
    if (graphRef.current && knowledgeGraphData.data && !knowledgeGraphData.loading && !knowledgeGraphData.error) {
      try {
        const network = new Network(graphRef.current, knowledgeGraphData.data, {
            nodes: { shape: 'dot', size: 16 },
            edges: { arrows: 'to' }
        });
         // Handle click events on nodes, etc.
        network.on("click", function (params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = knowledgeGraphData.data.nodes.find(n => n.id === nodeId);
                console.log('Clicked node:', node);
                // Potentially display more info about the node
            }
        });
      } catch(e){
        console.error("Failed to initialize graph", e);
        setKnowledgeGraphData(prev => ({...prev, error: "Failed to render graph."}))
      }
    }
  }, [knowledgeGraphData.data, knowledgeGraphData.loading, knowledgeGraphData.error]);

  const renderLoading = (isLoading, error, data, itemName, renderItem) => {
    if (isLoading) return <Spin tip={`Loading ${itemName}...`} />;
    if (error) return <Alert message={`Error loading ${itemName}`} description={error} type="error" showIcon />;
    if (!data || data.length === 0) return <Empty description={`No ${itemName} found.`} />;
    return renderItem(data);
  };

  return (
    <Layout style={{ padding: '24px' }}>
      <Content>
        <Title level={2}>Bridge Design Knowledge Base</Title>
        <ProfessionalSearch onSearch={handleSearch} />

        {searchResults.loading && <Spin tip="Searching..." style={{display: 'block', marginTop: 16}}/>}
        {searchResults.error && <Alert message="Search Error" description={searchResults.error} type="error" showIcon style={{marginTop: 16}}/>}
        {searchResults.data.length > 0 && (
          <Card title="Search Results" style={{marginTop: 24}}>
            <List
              itemLayout="horizontal"
              dataSource={searchResults.data}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    title={<a href={`#item-${item.id}`}>{item.title}</a>} // Link to actual content if possible
                    description={item.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24} md={6}>
            <Card title="Design Theory Categories">
              {renderLoading(designTheoryCategories.loading, designTheoryCategories.error, designTheoryCategories.data, 'categories', (data) => (
                <KnowledgeTree
                    treeData={data}
                    onSelect={handleCategorySelect}
                />
              ))}
            </Card>
          </Col>
          <Col xs={24} md={18}>
            <Tabs defaultActiveKey="1">
              <TabPane tab="Formulas & Methods" key="1">
                <Card title={`Formulas for ${selectedCategoryFormulas ? designTheoryCategories.data.find(c=>c.key===selectedCategoryFormulas)?.title || 'Selected Category' : 'All Categories (Select One)'}`}>
                  {renderLoading(formulas.loading, formulas.error, formulas.data, 'formulas', (data) => (
                     <List
                        dataSource={data}
                        renderItem={item => <List.Item><Text strong>{item.name}:</Text> {item.details}</List.Item>}
                     />
                  ))}
                   {!selectedCategoryFormulas && !formulas.loading && <Paragraph>Select a category from the tree to view specific formulas.</Paragraph>}
                </Card>
              </TabPane>
              <TabPane tab="Design Norms" key="2">
                {renderLoading(designNorms.loading, designNorms.error, designNorms.data, 'design norms', (data) => (
                  <StandardsComparator
                    standards={data}
                    onCompare={handleCompareNorms}
                    // TODO: Add a mechanism in StandardsComparator to select norms for comparison
                    // and update selectedNormsForComparison state.
                  />
                ))}
              </TabPane>
              <TabPane tab="Material Parameters" key="3">
                <Card title="Material Design Parameters">
                  {renderLoading(materialParams.loading, materialParams.error, materialParams.data, 'material parameters', (data) => (
                     <List
                        dataSource={data}
                        renderItem={item => <List.Item><Text strong>{item.name}:</Text> {item.params}</List.Item>}
                     />
                  ))}
                </Card>
              </TabPane>
              <TabPane tab="Design Cases & Templates" key="4">
                <Card title="Structure Design Cases and Templates">
                  {renderLoading(designCases.loading, designCases.error, designCases.data, 'design cases', (data) => (
                     <List
                        dataSource={data}
                        renderItem={item => (
                            <List.Item>
                                <Text strong>{item.name}:</Text> {item.template}
                                {item.url && <Button type="link" href={item.url} target="_blank">View Template</Button>}
                            </List.Item>
                        )}
                     />
                  ))}
                </Card>
              </TabPane>
              <TabPane tab="Knowledge Graph" key="5">
                <Card title="Design Knowledge Association Graph">
                  {renderLoading(knowledgeGraphData.loading, knowledgeGraphData.error, knowledgeGraphData.data, 'knowledge graph', () => (
                     <div ref={graphRef} style={{ height: '500px', border: '1px solid #eee', background: '#f9f9f9' }} />
                  ))}
                  {knowledgeGraphData.error && <Alert message="Graph Error" description={knowledgeGraphData.error} type="error" showIcon />}
                </Card>
              </TabPane>
              <TabPane tab="Parameter Calculator" key="6">
                 <ParameterCalculator parameters={mockCalculatorParams} onSubmit={handleCalculate} />
              </TabPane>
            </Tabs>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default BridgeDesignKB;
