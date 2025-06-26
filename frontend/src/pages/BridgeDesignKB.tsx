import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Layout, Typography, Row, Col, Card, Tabs, Spin, Alert, Empty, List, Button, Input } from 'antd';
import { debounce } from 'lodash'; // Or your preferred debounce implementation
import ProfessionalSearch from '../components/professional/ProfessionalSearch';
import KnowledgeTree from '../components/professional/KnowledgeTree';
import StandardsComparator from '../components/professional/StandardsComparator';
import ParameterCalculator from '../components/professional/ParameterCalculator';
import { Network } from 'vis-network/standalone/esm/vis-network'; // For graph visualization
import apiClient, { // apiClient might need its own type definitions
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

// Define basic types for data, these should be refined based on actual API responses
interface DesignCategory {
  key: string;
  title: string;
  children?: DesignCategory[];
  // Add other properties from API
}
interface Formula {
  id: string;
  name: string;
  details: string;
  // Add other properties from API
}
interface DesignNorm {
  id: string;
  name: string;
  version: string;
  details: string;
  // Add other properties from API
}
interface MaterialParam {
  id: string;
  name: string;
  params: string; // Or a more structured object
  // Add other properties from API
}
interface DesignCase {
  id: string;
  name: string;
  template: string;
  url?: string;
  // Add other properties from API
}
interface KnowledgeGraphNode {
  id: string;
  label: string;
  // Add other vis.js node properties
}
interface KnowledgeGraphEdge {
  from: string;
  to: string;
  label?: string;
  // Add other vis.js edge properties
}
interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}
interface SearchResult {
  id: string;
  title: string;
  description: string;
  // Add other properties from API
}

interface DataState<T> {
  data: T;
  loading: boolean;
  error: string | null;
}

interface PageProps {
  // No props expected for this page component
}

interface PageState {
  designTheoryCategories: DataState<DesignCategory[]>;
  formulas: DataState<Formula[]>;
  selectedCategoryFormulas: string | null; // Assuming categoryId is a string
  designNorms: DataState<DesignNorm[]>;
  materialParams: DataState<MaterialParam[]>;
  designCases: DataState<DesignCase[]>;
  knowledgeGraphData: DataState<KnowledgeGraph | null>;
  searchResults: DataState<SearchResult[]>;
  selectedNormsForComparison: string[]; // IDs of norms
}

// Example calculator params, could also be fetched or defined based on context
// TODO: Type this properly
const mockCalculatorParams: Array<{name: string, label: string, defaultValue: number}> = [
    { name: 'load', label: 'Load (kN)', defaultValue: 100 },
    { name: 'span', label: 'Span (m)', defaultValue: 10 },
];

const BridgeDesignKB: React.FC<PageProps> = () => {
  const [designTheoryCategories, setDesignTheoryCategories] = useState<PageState['designTheoryCategories']>({ data: [], loading: true, error: null });
  const [formulas, setFormulas] = useState<PageState['formulas']>({ data: [], loading: false, error: null });
  const [selectedCategoryFormulas, setSelectedCategoryFormulas] = useState<PageState['selectedCategoryFormulas']>(null);
  const [designNorms, setDesignNorms] = useState<PageState['designNorms']>({ data: [], loading: true, error: null });
  const [materialParams, setMaterialParams] = useState<PageState['materialParams']>({ data: [], loading: true, error: null });
  const [designCases, setDesignCases] = useState<PageState['designCases']>({ data: [], loading: true, error: null });
  const [knowledgeGraphData, setKnowledgeGraphData] = useState<PageState['knowledgeGraphData']>({ data: null, loading: true, error: null });
  const [searchResults, setSearchResults] = useState<PageState['searchResults']>({ data: [], loading: false, error: null });

  const [selectedNormsForComparison, setSelectedNormsForComparison] = useState<PageState['selectedNormsForComparison']>([]);
  const graphRef = useRef<HTMLDivElement>(null); // Typed graphRef for the div element

  // Performance Optimization Presets
  const paginationConfig = useMemo(() => ({
    defaultPageSize: 10, // Adjusted for potentially dense list items
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number) => `共 ${total} 项`,
    size: 'small', // For denser layout
  }), []);

  // Debounced search function (replaces the immediate handleSearch if ProfessionalSearch uses an Input)
  // If ProfessionalSearch calls onSearch directly on button click, this debounced version is for a separate Input if added.
  const performDebouncedSearch = useCallback(async (value: string) => {
    if (!value) {
        setSearchResults({data: [], loading: false, error: null });
        return;
    }
    setSearchResults(prev => ({ ...prev, loading: true, error: null }));
    try {
      const results: SearchResult[] = await searchDesignKnowledge(value);
      setSearchResults({ data: results || [], loading: false, error: null });
    } catch (error: any) {
      setSearchResults({ data: [], loading: false, error: error.message || 'Search failed' });
    }
  }, []); // Dependencies: searchDesignKnowledge (if it's not stable, e.g. from props)

  const debouncedSearchHandler = useMemo(
    () => debounce(performDebouncedSearch, 300),
    [performDebouncedSearch]
  );

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setDesignTheoryCategories(prev => ({ ...prev, loading: true }));
        const categories = await getDesignTheoryCategories();
        setDesignTheoryCategories({ data: categories || [], loading: false, error: null });
      } catch (error: any) {
        setDesignTheoryCategories({ data: [], loading: false, error: error.message || 'Failed to fetch categories' });
      }

      try {
        setDesignNorms(prev => ({ ...prev, loading: true }));
        const norms = await getDesignNorms();
        setDesignNorms({ data: norms || [], loading: false, error: null });
      } catch (error: any) {
        setDesignNorms({ data: [], loading: false, error: error.message || 'Failed to fetch norms' });
      }

      try {
        setMaterialParams(prev => ({ ...prev, loading: true }));
        const materials = await getMaterialParams();
        setMaterialParams({ data: materials || [], loading: false, error: null });
      } catch (error: any) {
        setMaterialParams({ data: [], loading: false, error: error.message || 'Failed to fetch materials' });
      }

      try {
        setDesignCases(prev => ({ ...prev, loading: true }));
        const cases = await getDesignCases();
        setDesignCases({ data: cases || [], loading: false, error: null });
      } catch (error: any) {
        setDesignCases({ data: [], loading: false, error: error.message || 'Failed to fetch design cases' });
      }

      try {
        setKnowledgeGraphData(prev => ({ ...prev, loading: true }));
        const graphData = await getDesignKnowledgeGraph();
        setKnowledgeGraphData({ data: graphData, loading: false, error: null });
      } catch (error: any) {
        setKnowledgeGraphData({ data: null, loading: false, error: error.message || 'Failed to fetch graph data' });
      }
    };
    fetchData();
  }, []);

  // Fetch formulas when a category is selected
  const handleCategorySelect = async (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const categoryId = selectedKeys[0] as string;
      setSelectedCategoryFormulas(categoryId);
      setFormulas(prev => ({ ...prev, loading: true, error: null }));
      try {
        const fetchedFormulas: Formula[] = await getFormulas(categoryId);
        setFormulas({ data: fetchedFormulas || [], loading: false, error: null });
      } catch (error: any) {
        setFormulas({ data: [], loading: false, error: error.message || `Failed to fetch formulas for category ${info.node.title}`});
      }
    }
  };

  // Note: handleSearch is already defined above for ProfessionalSearch component.
  // If debouncedSearchHandler is used with a new Input, ensure no naming conflict or merge logic.

  // const handleSearch = async (value: string) => { // This is the duplicate to be removed
  // if (!value) {
  // setSearchResults({data: [], loading: false, error: null });
        return;
    }
    setSearchResults(prev => ({ ...prev, loading: true, error: null }));
    try {
      // TODO: Ensure searchDesignKnowledge returns Promise<SearchResult[]>
      const results: SearchResult[] = await searchDesignKnowledge(value);
      setSearchResults({ data: results || [], loading: false, error: null });
    } catch (error: any) {
      setSearchResults({ data: [], loading: false, error: error.message || 'Search failed' });
    }
  };

  const handleCompareNorms = (): void => {
    console.log('Comparing selected norms:', selectedNormsForComparison);
    // Implement comparison logic or display component here
    // This might involve fetching detailed data for selected norms if not already available
    alert(`Comparing norms: ${selectedNormsForComparison.join(', ')}. (Further implementation needed)`);
  };

  // TODO: Define a type for 'data' based on mockCalculatorParams or actual calculator input structure
  const handleCalculate = (data: Record<string, number>): void => {
    console.log('Calculating with data:', data);
    // Example: POST to a calculation endpoint
    // apiClient.post('/bridge-design/calculate/bending-moment', data)
    //   .then(response => alert(`Calculated result: ${response.result}`)) // Type response
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

  const renderLoading = <T,>(
    isLoading: boolean,
    error: string | null,
    data: T[] | T | null, // Allow single object or array for data
    itemName: string,
    renderItem: (data: T[] | T) => React.ReactNode
  ): React.ReactNode => {
    if (isLoading) return <Spin tip={`Loading ${itemName}...`} />;
    if (error) return <Alert message={`Error loading ${itemName}`} description={error} type="error" showIcon />;
    // Check for array length if data is an array, otherwise check if data itself is null/undefined
    if (!data || (Array.isArray(data) && data.length === 0)) return <Empty description={`No ${itemName} found.`} />;
    return renderItem(data);
  };

  return (
    <Layout style={{ padding: '24px' }}>
      <Content>
        <Title level={2}>Bridge Design Knowledge Base</Title>
        {/* ProfessionalSearch is likely a button-triggered search.
            If a live input search is also desired on this page:
        <Input
          placeholder="Live search design knowledge..."
          onChange={(e) => debouncedSearchHandler(e.target.value)}
          style={{margin: '0 0 16px', width: '300px'}}
          allowClear
        />
        */}
        <ProfessionalSearch onSearch={handleSearch} />

        {searchResults.loading && <Spin tip="Searching..." style={{display: 'block', marginTop: 16}}/>}
        {searchResults.error && <Alert message="Search Error" description={searchResults.error} type="error" showIcon style={{marginTop: 16}}/>}
        {searchResults.data.length > 0 && (
          <Card title="Search Results" style={{marginTop: 24}}>
            <List
              itemLayout="horizontal"
              dataSource={searchResults.data}
              pagination={searchResults.data.length > (paginationConfig.defaultPageSize || 10) ? paginationConfig : false}
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
                  {renderLoading(formulas.loading, formulas.error, formulas.data, 'formulas', (data: Formula[]) => ( // Explicitly type data here
                     <List
                        dataSource={data}
                        pagination={data.length > (paginationConfig.defaultPageSize || 10) ? paginationConfig : false}
                        renderItem={(item: Formula) => <List.Item><Text strong>{item.name}:</Text> {item.details}</List.Item>}
                     />
                  ))}
                   {!selectedCategoryFormulas && !formulas.loading && <Paragraph>Select a category from the tree to view specific formulas.</Paragraph>}
                </Card>
              </TabPane>
              <TabPane tab="Design Norms" key="2">
                {/* StandardsComparator might have its own pagination/search or this data is usually not excessively long */}
                {renderLoading(designNorms.loading, designNorms.error, designNorms.data, 'design norms', (data: DesignNorm[]) => (
                  <StandardsComparator
                    standards={data} // Pass typed data
                    onCompare={handleCompareNorms}
                    // TODO: Add a mechanism in StandardsComparator to select norms for comparison
                    // and update selectedNormsForComparison state.
                  />
                ))}
              </TabPane>
              <TabPane tab="Material Parameters" key="3">
                <Card title="Material Design Parameters">
                  {renderLoading(materialParams.loading, materialParams.error, materialParams.data, 'material parameters', (data: MaterialParam[]) => (
                     <List
                        dataSource={data}
                        pagination={data.length > (paginationConfig.defaultPageSize || 10) ? paginationConfig : false}
                        renderItem={(item: MaterialParam) => <List.Item><Text strong>{item.name}:</Text> {item.params}</List.Item>}
                     />
                  ))}
                </Card>
              </TabPane>
              <TabPane tab="Design Cases & Templates" key="4">
                <Card title="Structure Design Cases and Templates">
                  {renderLoading(designCases.loading, designCases.error, designCases.data, 'design cases', (data: DesignCase[]) => (
                     <List
                        dataSource={data}
                        pagination={data.length > (paginationConfig.defaultPageSize || 10) ? paginationConfig : false}
                        renderItem={(item: DesignCase) => (
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
