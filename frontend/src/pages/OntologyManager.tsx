import React, { useState, useEffect, useCallback } from 'react';
import {
    Layout,
    Typography,
    Row,
    Col,
    Card,
    Collapse,
    List,
    Spin,
    Alert,
    Button,
    Modal,
    Form,
    Input,
    message, // for snackbar-like messages
    Space,
    Tag,
    Tooltip
} from 'antd';
import {
    ApartmentOutlined, // For ontology structure
    PlusOutlined,      // For adding
    SaveOutlined,      // For saving snapshot
    CloudUploadOutlined, // For suggest updates
    HistoryOutlined,   // For versions
    EditOutlined,      // For editing (placeholder)
    DeleteOutlined,    // For deleting (placeholder)
    SyncOutlined,      // For refresh/loading
} from '@ant-design/icons';

import * as api from '../services/systemApi'; // API functions
import ErrorBoundary from '../components/ErrorBoundary'; // Import ErrorBoundary

const { Title, Text, Paragraph } = Typography;
const { Content } = Layout;
const { Panel } = Collapse;

// Define interfaces based on systemApi.ts and requirements
interface OntologyStructure {
    entity_types: Record<string, { properties: string[]; description?: string }>;
    relationship_types: Record<string, { from: string[]; to: string[]; description?: string }>;
}

interface OntologyVersion {
    name: string;
    timestamp: string;
    description?: string;
}

// TODO: Define more specific types for form data if needed
interface NewEntityTypeForm {
    name: string;
    properties: string; // comma-separated
    description: string;
}

interface NewRelationshipTypeForm {
    name: string;
    fromTypes: string; // comma-separated
    toTypes: string;   // comma-separated
    description: string;
}

interface NewSnapshotForm {
    versionName: string;
    description: string;
}

interface PageProps {
  // No specific props for this page component
}

interface PageState {
    ontologyStructure: OntologyStructure | null;
    versions: OntologyVersion[];
    // updateSuggestions: any | null; // Define type for suggestions

    loadingStructure: boolean;
    loadingVersions: boolean;
    // loadingSuggestions: boolean;

    error: string | null;

    // Modal visibility
    isEntityTypeModalVisible: boolean;
    isRelationshipTypeModalVisible: boolean;
    isSnapshotModalVisible: boolean;
}


const OntologyManager: React.FC<PageProps> = () => {
    const [ontologyStructure, setOntologyStructure] = useState<PageState['ontologyStructure']>(null);
    const [versions, setVersions] = useState<PageState['versions']>([]);
    // const [updateSuggestions, setUpdateSuggestions] = useState<PageState['updateSuggestions']>(null);

    const [loadingStructure, setLoadingStructure] = useState<PageState['loadingStructure']>(false);
    const [loadingVersions, setLoadingVersions] = useState<PageState['loadingVersions']>(false);
    // const [loadingSuggestions, setLoadingSuggestions] = useState<PageState['loadingSuggestions']>(false);

    const [error, setError] = useState<PageState['error']>(null);

    const [isEntityTypeModalVisible, setIsEntityTypeModalVisible] = useState<PageState['isEntityTypeModalVisible']>(false);
    const [isRelationshipTypeModalVisible, setIsRelationshipTypeModalVisible] = useState<PageState['isRelationshipTypeModalVisible']>(false);
    const [isSnapshotModalVisible, setIsSnapshotModalVisible] = useState<PageState['isSnapshotModalVisible']>(false);

    const [entityTypeForm] = Form.useForm<NewEntityTypeForm>();
    const [relationshipTypeForm] = Form.useForm<NewRelationshipTypeForm>();
    const [snapshotForm] = Form.useForm<NewSnapshotForm>();

    const fetchOntologyStructure = useCallback(async () => {
        setLoadingStructure(true);
        setError(null);
        try {
            const data = await api.getOntologyStructure();
            setOntologyStructure(data);
        } catch (err: any) {
            const errorMessage = err.message || (err.response && err.response.data && err.response.data.detail) || 'Failed to fetch ontology structure.';
            setError(errorMessage);
            message.error(errorMessage);
        } finally {
            setLoadingStructure(false);
        }
    }, []);

    const fetchVersions = useCallback(async () => {
        setLoadingVersions(true);
        setError(null);
        try {
            const data = await api.getOntologyVersions();
            setVersions(data);
        } catch (err: any) {
            const errorMessage = err.message || (err.response && err.response.data && err.response.data.detail) || 'Failed to fetch ontology versions.';
            setError(errorMessage);
            message.error(errorMessage);
        } finally {
            setLoadingVersions(false);
        }
    }, []);

    useEffect(() => {
        fetchOntologyStructure();
        fetchVersions();
    }, [fetchOntologyStructure, fetchVersions]);

    const handleAddEntityType = async (values: NewEntityTypeForm) => {
        try {
            message.loading({ content: 'Adding entity type...', key: 'addEntityType' });
            const payload = {
                entity_type: values.name,
                properties: values.properties.split(',').map(p => p.trim()).filter(p => p),
                description: values.description,
            };
            await api.addEntityType(payload);
            message.success({ content: `Entity type '${values.name}' added successfully.`, key: 'addEntityType' });
            setIsEntityTypeModalVisible(false);
            entityTypeForm.resetFields();
            fetchOntologyStructure(); // Refresh structure
        } catch (err: any) {
            const errorMessage = err.message || (err.response && err.response.data && err.response.data.detail) || 'Failed to add entity type.';
            message.error({ content: errorMessage, key: 'addEntityType' });
        }
    };

    const handleAddRelationshipType = async (values: NewRelationshipTypeForm) => {
        try {
            message.loading({ content: 'Adding relationship type...', key: 'addRelationshipType' });
            const payload = {
                // rel_type: values.name, // systemApi expects addEntityType to have entity_type, assuming similar for rels if backend differs
                name: values.name, // Assuming 'name' is the field for systemApi.ts function if it's generic
                from_types: values.fromTypes.split(',').map(p => p.trim()).filter(p => p),
                to_types: values.toTypes.split(',').map(p => p.trim()).filter(p => p),
                description: values.description,
            };
            // TODO: Verify api.addRelationshipType exists and matches payload
            // await api.addRelationshipType(payload);
            message.info({ content: 'Add Relationship Type functionality to be fully connected.', key: 'addRelationshipType' });
            // For now, let's assume it's not implemented in systemApi.ts yet or payload needs adjustment
            console.log("Payload for add relationship type:", payload);
            // setIsRelationshipTypeModalVisible(false);
            // relationshipTypeForm.resetFields();
            // fetchOntologyStructure(); // Refresh structure
        } catch (err: any)
 {
            const errorMessage = err.message || (err.response && err.response.data && err.response.data.detail) || 'Failed to add relationship type.';
            message.error({ content: errorMessage, key: 'addRelationshipType' });
        }
    };

    const handleCreateSnapshot = async (values: NewSnapshotForm) => {
        try {
            message.loading({ content: 'Creating snapshot...', key: 'createSnapshot' });
            await api.createOntologySnapshot(values);
            message.success({ content: `Snapshot '${values.versionName}' created successfully.`, key: 'createSnapshot' });
            setIsSnapshotModalVisible(false);
            snapshotForm.resetFields();
            fetchVersions(); // Refresh versions list
        } catch (err: any) {
            const errorMessage = err.message || (err.response && err.response.data && err.response.data.detail) || 'Failed to create snapshot.';
            message.error({ content: errorMessage, key: 'createSnapshot' });
        }
    };

    // Render Functions for list items to add more detail or actions
    const renderEntityTypeItem = (type: string, details: { properties: string[]; description?: string }) => (
        <List.Item
            actions={[
                <Tooltip title="Edit (Not Implemented)"><Button type="text" icon={<EditOutlined />} disabled /></Tooltip>,
                <Tooltip title="Delete (Not Implemented)"><Button type="text" danger icon={<DeleteOutlined />} disabled /></Tooltip>
            ]}
        >
            <List.Item.Meta
                avatar={<ApartmentOutlined />}
                title={<Text strong>{type}</Text>}
                description={
                    <>
                        <Paragraph ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}>
                            {details.description || 'No description.'}
                        </Paragraph>
                        <Text type="secondary">Properties: </Text>
                        {details.properties && details.properties.length > 0
                            ? details.properties.map(prop => <Tag key={prop}>{prop}</Tag>)
                            : <Text type="secondary">None</Text>}
                    </>
                }
            />
        </List.Item>
    );

    const renderRelationshipTypeItem = (type: string, details: { from: string[]; to: string[]; description?: string }) => (
         <List.Item
            actions={[
                <Tooltip title="Edit (Not Implemented)"><Button type="text" icon={<EditOutlined />} disabled /></Tooltip>,
                <Tooltip title="Delete (Not Implemented)"><Button type="text" danger icon={<DeleteOutlined />} disabled /></Tooltip>
            ]}
        >
            <List.Item.Meta
                avatar={<ApartmentOutlined style={{ transform: 'rotate(90deg)'}}/>}
                title={<Text strong>{type}</Text>}
                description={
                     <>
                        <Paragraph ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}>
                            {details.description || 'No description.'}
                        </Paragraph>
                        <Text type="secondary">From: </Text>
                        {details.from && details.from.length > 0 ? details.from.map(f => <Tag key={f} color="blue">{f}</Tag>) : <Tag>Any</Tag>}
                        <Text type="secondary" style={{marginLeft: 5}}> To: </Text>
                        {details.to && details.to.length > 0 ? details.to.map(t => <Tag key={t} color="green">{t}</Tag>) : <Tag>Any</Tag>}
                    </>
                }
            />
        </List.Item>
    );


    return (
        <Layout style={{ padding: '24px' }}>
            <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 'calc(100vh - 48px)' }}>
                <ErrorBoundary> {/* Wrap content with ErrorBoundary */}
                    <Title level={2} style={{ marginBottom: '24px' }}>本体管理 (Ontology Management)</Title>

                    {error && <Alert message="Error" description={error} type="error" closable showIcon style={{ marginBottom: 16 }} />}

                    <Row gutter={[16, 16]}>
                        {/* Column 1: Ontology Structure & Actions */}
                        <Col xs={24} lg={12}>
                            <Card
                                title="Ontology Structure & Actions"
                                bordered={false}
                                extra={<Button icon={<SyncOutlined spin={loadingStructure}/>} onClick={fetchOntologyStructure} disabled={loadingStructure}>Refresh</Button>}
                                style={{ marginBottom: 16 }}
                            >
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsEntityTypeModalVisible(true)} block>
                                        Add Entity Type
                                    </Button>
                                    <Button icon={<PlusOutlined />} onClick={() => setIsRelationshipTypeModalVisible(true)} block disabled> {/* TODO: Implement Add Relationship Type */}
                                        Add Relationship Type (Not fully implemented)
                                    </Button>
                                </Space>
                                <Collapse defaultActiveKey={['1']} style={{ marginTop: 16 }}>
                                    <Panel header={<Text strong>Entity Types ({ontologyStructure ? Object.keys(ontologyStructure.entity_types || {}).length : 0})</Text>} key="1">
                                        {loadingStructure && !ontologyStructure ? <Spin /> :
                                            <List
                                                itemLayout="horizontal"
                                                dataSource={ontologyStructure ? Object.entries(ontologyStructure.entity_types || {}) : []}
                                                renderItem={([type, details]) => renderEntityTypeItem(type, details)}
                                                locale={{ emptyText: 'No entity types found.'}}
                                            />
                                        }
                                    </Panel>
                                    <Panel header={<Text strong>Relationship Types ({ontologyStructure ? Object.keys(ontologyStructure.relationship_types || {}).length : 0})</Text>} key="2">
                                        {loadingStructure && !ontologyStructure ? <Spin /> :
                                            <List
                                                itemLayout="horizontal"
                                                dataSource={ontologyStructure ? Object.entries(ontologyStructure.relationship_types || {}) : []}
                                                renderItem={([type, details]) => renderRelationshipTypeItem(type, details)}
                                                locale={{ emptyText: 'No relationship types found.'}}
                                            />
                                        }
                                    </Panel>
                                </Collapse>
                            </Card>

                            <Card title="Ontology Update Suggestions (Placeholder)" bordered={false}>
                                 <Paragraph>
                                    This section will allow users to input text or upload documents to get automatic suggestions for ontology updates (new entity types, properties, relationships) based on the content.
                                </Paragraph>
                                <Input.TextArea rows={4} placeholder="Paste text for suggestions..." disabled style={{marginBottom: 8}}/>
                                <Button icon={<CloudUploadOutlined />} disabled>Get Suggestions</Button>
                                {/* TODO: Display suggestions list */}
                            </Card>
                        </Col>

                        {/* Column 2: Version Management */}
                        <Col xs={24} lg={12}>
                            <Card
                                title="Version Management"
                                bordered={false}
                                extra={<Button icon={<SyncOutlined spin={loadingVersions}/>} onClick={fetchVersions} disabled={loadingVersions}>Refresh Versions</Button>}
                            >
                                <Button type="primary" icon={<SaveOutlined />} onClick={() => setIsSnapshotModalVisible(true)} block style={{ marginBottom: 16 }}>
                                    Create New Snapshot
                                </Button>
                                {loadingVersions && versions.length === 0 ? <Spin /> :
                                    <List
                                        header={<Text strong>Existing Versions ({versions.length})</Text>}
                                        bordered
                                        dataSource={versions}
                                        renderItem={version => (
                                            <List.Item actions={[<Button type="link" disabled>Compare</Button>, <Button type="link" danger disabled>Rollback</Button>]}>
                                                <List.Item.Meta
                                                    avatar={<HistoryOutlined />}
                                                    title={version.name}
                                                    description={`Created: ${new Date(version.timestamp).toLocaleString()} - ${version.description || 'No description'}`}
                                                />
                                            </List.Item>
                                        )}
                                        locale={{ emptyText: 'No versions found.'}}
                                    />
                                }
                            </Card>
                        </Col>
                    </Row>
                </ErrorBoundary>
            </Content>

            {/* Modals */}
            <Modal
                title="Add New Entity Type"
                visible={isEntityTypeModalVisible}
                onCancel={() => setIsEntityTypeModalVisible(false)}
                footer={null} // Custom footer in Form
            >
                <Form form={entityTypeForm} layout="vertical" onFinish={handleAddEntityType}>
                    <Form.Item name="name" label="Entity Type Name" rules={[{ required: true, message: 'Please input the entity type name!' }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="properties" label="Properties (comma-separated)" rules={[{ required: true, message: 'Please input properties!' }]}>
                        <Input placeholder="e.g., color, size, weight"/>
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea rows={3} />
                    </Form.Item>
                    <Form.Item style={{ textAlign: 'right' }}>
                        <Button onClick={() => setIsEntityTypeModalVisible(false)} style={{ marginRight: 8 }}>Cancel</Button>
                        <Button type="primary" htmlType="submit">Add Entity Type</Button>
                    </Form.Item>
                </Form>
            </Modal>

            {/* TODO: Relationship Type Modal - currently disabled button */}
             <Modal
                title="Add New Relationship Type"
                visible={isRelationshipTypeModalVisible}
                onCancel={() => setIsRelationshipTypeModalVisible(false)}
                footer={null}
            >
                <Form form={relationshipTypeForm} layout="vertical" onFinish={handleAddRelationshipType}>
                    <Form.Item name="name" label="Relationship Type Name" rules={[{ required: true }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="fromTypes" label="From Entity Types (comma-separated)" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Person, Organization"/>
                    </Form.Item>
                     <Form.Item name="toTypes" label="To Entity Types (comma-separated)" rules={[{ required: true }]}>
                        <Input placeholder="e.g., Project, Location"/>
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea rows={3} />
                    </Form.Item>
                     <Form.Item style={{ textAlign: 'right' }}>
                        <Button onClick={() => setIsRelationshipTypeModalVisible(false)} style={{ marginRight: 8 }}>Cancel</Button>
                        <Button type="primary" htmlType="submit">Add Relationship Type</Button>
                    </Form.Item>
                </Form>
            </Modal>


            <Modal
                title="Create New Snapshot"
                visible={isSnapshotModalVisible}
                onCancel={() => setIsSnapshotModalVisible(false)}
                footer={null}
            >
                <Form form={snapshotForm} layout="vertical" onFinish={handleCreateSnapshot}>
                    <Form.Item name="versionName" label="Version Name (e.g., v1.0.1)" rules={[{ required: true, message: 'Please input the version name!' }]}>
                        <Input />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea rows={3} />
                    </Form.Item>
                    <Form.Item style={{ textAlign: 'right' }}>
                        <Button onClick={() => setIsSnapshotModalVisible(false)} style={{ marginRight: 8 }}>Cancel</Button>
                        <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>Create Snapshot</Button>
                    </Form.Item>
                </Form>
            </Modal>

        </Layout>
    );
};

export default OntologyManager;
