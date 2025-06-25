import React, { useState, useEffect, useRef } from 'react';
import { Layout, Typography, Row, Col, Card, Tabs } from 'antd';
import ProfessionalSearch from '../components/professional/ProfessionalSearch';
import ProcessFlow from '../components/professional/ProcessFlow';
import QualityChecklist from '../components/professional/QualityChecklist';
// import { Network } from 'vis-network/standalone/esm/vis-network'; // For graph visualization

const { Content } = Layout;
const { Title, Paragraph } = Typography;
const { TabPane } = Tabs;

// Mock Data - Replace with API calls
const mockConstructionTimeline = [
  { label: '2024-01-01', content: 'Site Preparation' },
  { label: '2024-02-15', content: 'Foundation Work' },
  { label: '2024-04-01', content: 'Pier Construction' },
  { label: '2024-06-10', content: 'Superstructure Assembly' },
];

const mockProcessStandards = [
  { id: 'ps1', name: 'Concrete Pouring Standard XYZ', details: 'Details about temperature, slump, etc.' },
  { id: 'ps2', name: 'Welding Procedure ABC', details: 'Preheat requirements, electrode types...' },
];

const mockQCChecklistItems = [
  { id: 'qc1', label: 'Verify rebar placement' },
  { id: 'qc2', label: 'Check concrete slump test' },
  { id: 'qc3', label: 'Inspect weld quality' },
];

const mockSafetyRegs = [
  { id: 'sr1', name: 'Working at Height', content: 'Fall arrest systems required...' },
  { id: 'sr2', name: 'Confined Space Entry', content: 'Atmospheric testing, rescue plan...' },
];

const mockEquipment = [
  { id: 'eq1', name: 'Tower Crane TC-500', specs: 'Max lift: 10T, Jib length: 50m' },
  { id: 'eq2', name: 'Concrete Pump CP-120', specs: 'Output: 120 m³/hr' },
];

const ConstructionKB = () => {
  const [searchResults, setSearchResults] = useState([]);
  // const graphRef = useRef(null); // For vis-network dependency graph

  const handleSearch = (value) => {
    console.log('Searching construction KB for:', value);
    setSearchResults([{ id: 'csr1', title: `Construction result for ${value}`, description: 'Details...' }]);
  };

  const handleGenerateChecklist = () => {
    console.log("Generating new checklist based on criteria (not implemented yet)");
    // Potentially update mockQCChecklistItems or fetch new ones
  };

  // useEffect(() => { // For vis-network dependency graph
  //   if (graphRef.current) {
  //     const nodes = [
  //       { id: 1, label: 'Foundation' },
  //       { id: 2, label: 'Piers' },
  //       { id: 3, label: 'Deck' },
  //     ];
  //     const edges = [
  //       { from: 1, to: 2, label: 'supports' },
  //       { from: 2, to: 3, label: 'supports' },
  //     ];
  //     const data = { nodes, edges };
  //     const options = {
  //        edges: {
  //           arrows: 'to'
  //        }
  //     };
  //     new Network(graphRef.current, data, options);
  //   }
  // }, []);

  return (
    <Layout style={{ padding: '24px' }}>
      <Content>
        <Title level={2}>Construction Process Knowledge Base</Title>
        <ProfessionalSearch onSearch={handleSearch} />
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col xs={24}>
            <Tabs defaultActiveKey="1">
              <TabPane tab="Process Timeline" key="1">
                <Card title="Construction Process Visual Timeline">
                  <ProcessFlow steps={mockConstructionTimeline} />
                </Card>
              </TabPane>
              <TabPane tab="Standards & Procedures" key="2">
                <Card title="Process Standards and Operating Procedures">
                  {mockProcessStandards.map(ps => <Paragraph key={ps.id}><b>{ps.name}:</b> {ps.details}</Paragraph>)}
                </Card>
              </TabPane>
              <TabPane tab="Quality Control" key="3">
                <QualityChecklist
                    items={mockQCChecklistItems}
                    title="Quality Control Checklist"
                    onGenerate={handleGenerateChecklist}
                />
              </TabPane>
              <TabPane tab="Safety Regulations" key="4">
                <Card title="Safety Regulations and Emergency Plans">
                  {mockSafetyRegs.map(sr => <Paragraph key={sr.id}><b>{sr.name}:</b> {sr.content}</Paragraph>)}
                </Card>
              </TabPane>
              <TabPane tab="Equipment & Materials" key="5">
                <Card title="Construction Equipment and Material Specs">
                  {mockEquipment.map(eq => <Paragraph key={eq.id}><b>{eq.name}:</b> {eq.specs}</Paragraph>)}
                </Card>
              </TabPane>
              <TabPane tab="Dependency Graph" key="6">
                <Card title="Process Flow Dependency Graph">
                  {/* <div ref={graphRef} style={{ height: '400px', border: '1px solid #eee' }} /> */}
                  <Paragraph>Graph visualization for dependencies will be here.</Paragraph>
                </Card>
              </TabPane>
              <TabPane tab="Monitoring Panel" key="7">
                <Card title="Construction Progress and Quality Monitoring Panel">
                  <Paragraph>Monitoring dashboard (e.g. using ECharts) will be here.</Paragraph>
                  {/* Placeholder for ECharts dashboard */}
                </Card>
              </TabPane>
            </Tabs>
          </Col>
        </Row>
        {searchResults.length > 0 && (
          <Card title="Search Results" style={{marginTop: 24}}>
            {searchResults.map(r => <Paragraph key={r.id}><b>{r.title}:</b> {r.description}</Paragraph>)}
          </Card>
        )}
      </Content>
    </Layout>
  );
};

export default ConstructionKB;
