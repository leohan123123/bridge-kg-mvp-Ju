import React, { useState, useEffect } from 'react';
import { Upload, message, Button, List, Typography, Progress, Space, Alert, Modal, Tag, Divider } from 'antd';
import { InboxOutlined, FileTextOutlined, UploadOutlined, CheckCircleOutlined, CloseCircleOutlined, LoadingOutlined, ExperimentOutlined } from '@ant-design/icons';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Dragger } = Upload;
const { Text, Link, Paragraph, Title } = Typography; // Added Paragraph and Title

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_FILE_TYPES = ['.dxf', '.pdf', '.ifc'];
const UPLOAD_URL = '/v1/files/upload'; // Backend endpoint
const PDF_EXTRACT_URL = '/v1/pdf/extract'; // PDF Text Extraction endpoint
const ENTITY_EXTRACT_URL = '/v1/entities/extract'; // Entity Extraction endpoint
const BUILD_GRAPH_URL = '/api/v1/rag/build_graph'; // RAG Knowledge Graph Build endpoint
const GRAPH_STATS_URL = '/api/v1/rag/graph_stats'; // RAG Graph Stats endpoint

// Define colors for entity types
const ENTITY_TYPE_COLORS = {
  "桥梁类型": "magenta",
  "材料": "blue",
  "结构": "green",
  "规范": "purple",
  // Add more colors if new types are introduced
};

const FileUpload = () => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [overallProgress, setOverallProgress] = useState(0); // For overall progress of a batch
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFilesInfo, setUploadedFilesInfo] = useState([]);

  // State for PDF text extraction modal
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalContent, setModalContent] = useState(''); // Holds PDF text or error messages
  const [modalTitle, setModalTitle] = useState('');
  const [isExtractingText, setIsExtractingText] = useState(false); // For PDF text extraction
  const [isRecognizingEntities, setIsRecognizingEntities] = useState(false); // For entity recognition
  const [extractedEntities, setExtractedEntities] = useState(null); // Holds recognized entities
  const [currentFilenameForModal, setCurrentFilenameForModal] = useState('');

  // State for Knowledge Graph Building
  const [isBuildingGraph, setIsBuildingGraph] = useState(false);
  const [graphBuildProgress, setGraphBuildProgress] = useState({ step: '', percent: 0 });
  const [graphBuildStats, setGraphBuildStats] = useState(null); // { nodes: 0, edges: 0, density: 0.0 }
  const [graphBuildError, setGraphBuildError] = useState(null);
  const [currentTextForGraphBuild, setCurrentTextForGraphBuild] = useState(''); // Text used for the current graph build
  const [currentEntitiesForGraphBuild, setCurrentEntitiesForGraphBuild] = useState(null); // Entities used for the current graph build


  const handleExtractText = async (fileInfo) => {
    if (!fileInfo.filename.toLowerCase().endsWith('.pdf')) {
      message.error('Only PDF files can have text extracted.');
      return;
    }
    setIsExtractingText(true);
    setExtractedEntities(null); // Clear previous entities
    setCurrentFilenameForModal(fileInfo.filename);
    setModalTitle(`Extracting text from ${fileInfo.filename}...`);
    setModalContent('');
    setIsModalVisible(true);

    try {
      const relativePath = fileInfo.filename;
      const response = await axios.post(PDF_EXTRACT_URL, { file_path: relativePath });
      setModalTitle(`Text from ${fileInfo.filename}`);
      if (response.data && response.data.text) {
        setModalContent(response.data.text);
      } else {
        setModalContent('No text found or an error occurred during extraction.');
      }
    } catch (error) {
      console.error('Error extracting PDF text:', error);
      let errorText = 'Failed to extract text.';
      if (error.response && error.response.data && error.response.data.detail) {
        errorText = error.response.data.detail;
      } else if (error.message) {
        errorText = error.message;
      }
      setModalContent(errorText);
      setModalTitle(`Error extracting text from ${fileInfo.filename}`);
      message.error(errorText);
    } finally {
      setIsExtractingText(false);
    }
  };

  // const handleRecognizeEntities = async () => { // This is the original one, to be replaced or merged
  //   if (!modalContent || typeof modalContent !== 'string' || modalContent.startsWith('Failed to extract text') || modalContent.startsWith('No text found')) {
  //     message.error('Cannot recognize entities: No valid text available or text extraction failed.');
  //     return;
  //   }
  //   setIsRecognizingEntities(true);
  //   setExtractedEntities(null); // Clear previous entities

  //   try {
  //     const response = await axios.post(ENTITY_EXTRACT_URL, { text: modalContent });
  //     if (response.data && response.data.entities) {
  //       setExtractedEntities(response.data.entities);
  //       if (response.data.total_count === 0) {
  //         message.info('No entities found in the current text.');
  //       } else {
  //         message.success(`Found ${response.data.total_count} entities.`);
  //       }
  //     } else {
  //       setExtractedEntities({}); // Set to empty object to indicate no entities found
  //       message.warning('No entities found or an error occurred during recognition.');
  //     }
  //   } catch (error) {
  //     console.error('Error recognizing entities:', error);
  //     let errorMsg = 'Failed to recognize entities.';
  //     if (error.response && error.response.data && error.response.data.detail) {
  //       errorMsg = error.response.data.detail;
  //     }
  //     message.error(errorMsg);
  //     setExtractedEntities(null); // Set to null on error
  //   } finally {
  //     setIsRecognizingEntities(false);
  //   }
  // };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setModalContent('');
    setModalTitle('');
    setExtractedEntities(null); // Clear entities when modal closes
    setCurrentFilenameForModal('');
    setIsExtractingText(false); // Reset states
    setIsRecognizingEntities(false);
    // Reset graph building states as well
    setIsBuildingGraph(false);
    setGraphBuildProgress({ step: '', percent: 0 });
    setGraphBuildStats(null);
    setGraphBuildError(null);
    setCurrentTextForGraphBuild('');
    setCurrentEntitiesForGraphBuild(null);
  };

  const handleRecognizeEntities = async () => {
    if (!modalContent || typeof modalContent !== 'string' || modalContent.startsWith('Failed to extract text') || modalContent.startsWith('No text found')) {
      message.error('Cannot recognize entities: No valid text available or text extraction failed.');
      return;
    }
    setIsRecognizingEntities(true);
    setExtractedEntities(null); // Clear previous entities
    setGraphBuildStats(null); // Clear previous graph stats
    setGraphBuildError(null); // Clear previous graph errors
    setCurrentTextForGraphBuild(modalContent); // Store text for potential graph build

    try {
      const response = await axios.post(ENTITY_EXTRACT_URL, { text: modalContent });
      if (response.data && response.data.entities) {
        setExtractedEntities(response.data.entities);
        setCurrentEntitiesForGraphBuild(response.data.entities); // Store entities for potential graph build
        if (response.data.total_count === 0) {
          message.info('No entities found in the current text.');
        } else {
          message.success(`Found ${response.data.total_count} entities.`);
        }
      } else {
        setExtractedEntities({});
        setCurrentEntitiesForGraphBuild({});
        message.warning('No entities found or an error occurred during recognition.');
      }
    } catch (error) {
      console.error('Error recognizing entities:', error);
      let errorMsg = 'Failed to recognize entities.';
      if (error.response && error.response.data && error.response.data.detail) {
        errorMsg = error.response.data.detail;
      }
      message.error(errorMsg);
      setExtractedEntities(null);
      setCurrentEntitiesForGraphBuild(null);
    } finally {
      setIsRecognizingEntities(false);
    }
  };

  const handleBuildGraph = async () => {
    if (!currentTextForGraphBuild || !currentEntitiesForGraphBuild || Object.keys(currentEntitiesForGraphBuild).length === 0) {
      message.error('Cannot build graph: No valid text or entities available. Please recognize entities first.');
      return;
    }
    setIsBuildingGraph(true);
    setGraphBuildProgress({ step: 'Initializing graph build...', percent: 0 });
    setGraphBuildStats(null);
    setGraphBuildError(null);

    try {
      // Simulate progress
      setGraphBuildProgress({ step: 'Sending data to build graph...', percent: 10 });
      await new Promise(resolve => setTimeout(resolve, 300)); // Short delay

      const payload = {
        text_content: currentTextForGraphBuild,
        entities: currentEntitiesForGraphBuild,
      };

      setGraphBuildProgress({ step: 'Extracting relations and building triples...', percent: 30 });
      const response = await axios.post(BUILD_GRAPH_URL, payload);
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate work

      setGraphBuildProgress({ step: 'Storing graph and finalizing...', percent: 70 });

      if (response.data && response.data.message) {
        message.success(response.data.message);
        // Fetch full graph stats after building
        try {
          setGraphBuildProgress({ step: 'Fetching graph statistics...', percent: 90 });
          const statsResponse = await axios.get(GRAPH_STATS_URL);
          if (statsResponse.data) {
            setGraphBuildStats(statsResponse.data);
            message.success('Graph statistics loaded.');
          }
        } catch (statsError) {
          console.error('Error fetching graph stats:', statsError);
          setGraphBuildError('Graph built, but failed to fetch statistics.');
          // Use summary from build response if available
          if (response.data.graph_summary) {
            const summary = response.data.graph_summary;
            setGraphBuildStats({
              node_count: summary.nodes?.length || 0,
              edge_count: summary.edges?.length || 0,
              graph_density: summary.nodes?.length > 1 ? (summary.edges?.length || 0) / (summary.nodes.length * (summary.nodes.length -1)) : 0
            });
          }
        }
      } else {
        throw new Error('Unexpected response from build graph endpoint.');
      }
      setGraphBuildProgress({ step: 'Graph build complete.', percent: 100 });

    } catch (error) {
      console.error('Error building knowledge graph:', error);
      let errorMsg = 'Failed to build knowledge graph.';
      if (error.response && error.response.data && error.response.data.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      message.error(errorMsg);
      setGraphBuildError(errorMsg);
      setGraphBuildProgress({ step: 'Error occurred.', percent: 100 }); // Mark as complete even on error
    } finally {
      setIsBuildingGraph(false);
      // Keep progress at 100 or error state, don't reset immediately
    }
  };

  const handleFileChange = (info) => {
    let newFileList = [...info.fileList];
    setFileList(newFileList);

    const { status, response, name: fileName } = info.file;

    if (status === 'uploading') {
      setUploading(true);
      setUploadError(null); // Clear previous error on new upload attempt
      // Individual file progress is handled by AntD's Upload component if customRequest is not used,
      // or via onProgress in customRequest.
    } else if (status === 'done') {
      message.success(`${fileName} file uploaded successfully.`);
      // Response from customRequest's onSuccess or default AntD upload
      // Expecting response to be an array of FileUploadResponse from our backend
      if (response && Array.isArray(response)) {
        setUploadedFilesInfo(prev => {
          const currentFileNames = new Set(prev.map(f => f.filename));
          const newUniqueFiles = response.filter(uploadedFile => !currentFileNames.has(uploadedFile.filename));
          return [...prev, ...newUniqueFiles];
        });
      } else if (response && response.filename) { // If backend returns single object for single file upload
        setUploadedFilesInfo(prev => {
          if (!prev.some(f => f.filename === response.filename)) {
            return [...prev, response];
          }
          return prev;
        });
      }
      setUploading(false);
    } else if (status === 'error') {
      const errorMsg = info.file.error?.message || `${fileName} file upload failed.`;
      message.error(errorMsg);
      setUploadError(errorMsg);
      setUploading(false);
    }
  };

  const draggerProps = {
    name: 'files', // Key for FormData, backend expects 'files' for List[UploadFile]
    multiple: true,
    accept: ALLOWED_FILE_TYPES.join(','),
    fileList: fileList,
    beforeUpload: (file, FileList) => {
      setUploadError(null); // Clear previous errors at the start of a new batch
      const isAllowedType = ALLOWED_FILE_TYPES.some(type => file.name.toLowerCase().endsWith(type));
      if (!isAllowedType) {
        const errorMsg = `${file.name}: File type not allowed. Only ${ALLOWED_FILE_TYPES.join(', ')} are accepted.`;
        message.error(errorMsg);
        setUploadError(errorMsg); // Show in global error alert
        return Upload.LIST_IGNORE;
      }
      const isLt50M = file.size <= MAX_FILE_SIZE;
      if (!isLt50M) {
        const errorMsg = `${file.name}: File exceeds 50MB limit.`;
        message.error(errorMsg);
        setUploadError(errorMsg); // Show in global error alert
        return Upload.LIST_IGNORE;
      }
      return true; // Proceed with upload if all checks pass
    },
    customRequest: async ({ file, onSuccess, onError, onProgress }) => {
      // This customRequest will be called for each file individually by AntD
      // We still want to send them as a batch if possible, or handle one by one
      // For simplicity, this example sends one file per request.
      // To send as a batch, you'd collect files in `beforeUpload` or `onChange`
      // and trigger a single FormData request manually.
      // However, the problem implies `List[UploadFile]` on backend, suggesting it can handle multiple files in one request.
      // AntD's default behavior with `multiple: true` and a compatible backend might do this automatically.
      // If not, customRequest needs to manage the batching.
      // For now, let's assume `name: 'files'` and `multiple: true` with `axios` will work.
      // The backend endpoint is `/api/v1/files/upload` and expects `List[UploadFile] = File(...)`
      // This means FastAPI expects a list of files under the key 'files'.

      const formData = new FormData();
      formData.append('files', file); // Even for single file, backend expects a list.

      try {
        setUploading(true); // Ensure uploading state is true
        const response = await axios.post(UPLOAD_URL, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (event) => {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress({ percent }, file); // Update AntD's individual file progress
            setOverallProgress(percent); // Update overall progress (for the current file in this setup)
          },
        });
        // `response.data` is expected to be List[FileUploadResponse]
        // For a single file upload via customRequest, backend might return just the one item in the list.
        onSuccess(response.data, file); // Pass backend response to AntD
      } catch (err) {
        console.error("Upload error in customRequest:", err);
        let errorMessage = "Upload failed.";
        if (err.response) {
            errorMessage = err.response.data?.detail || `Server error: ${err.response.status}`;
        } else if (err.request) {
            errorMessage = "No response from server.";
        } else {
            errorMessage = err.message;
        }
        onError(new Error(errorMessage), err.response?.data); // Pass error to AntD
      } finally {
        // setUploading(false); // This will be handled by onChange status 'done' or 'error'
        // setOverallProgress(0); // Reset progress after this file (or batch)
      }
    },
    onChange: handleFileChange, // Use the consolidated handler
    onRemove: (file) => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
      setUploadedFilesInfo(prev => prev.filter(item => item.filename !== file.name));
      if (fileList.length === 1) { // If last file is removed
        setUploadError(null); // Clear errors
      }
      return true;
    },
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: 'auto', fontFamily: "'Roboto', sans-serif" }}>
      <Typography.Title level={2} style={{ textAlign: 'center', marginBottom: '30px', color: '#1890ff' }}>
        Bridge Project File Upload
      </Typography.Title>

      <Dragger {...draggerProps} style={{ marginBottom: '20px', padding: '30px', border: '2px dashed #1890ff' }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined style={{ fontSize: '60px', color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text" style={{ fontSize: '18px', color: '#555' }}>Click or drag files to this area to upload</p>
        <p className="ant-upload-hint" style={{ fontSize: '14px', color: '#888' }}>
          Supports DXF, PDF, and IFC files. Maximum file size: 50MB.
          You can upload multiple files at once.
        </p>
      </Dragger>

      {uploading && fileList.some(f => f.status === 'uploading') && (
        <Progress percent={overallProgress} status="active" style={{ marginBottom: '20px' }} />
      )}

      {uploadError && !uploading && ( // Show error only if not actively uploading
          <Alert message={uploadError} type="error" showIcon closable onClose={() => setUploadError(null)} style={{ marginBottom: '20px' }} />
      )}

      {uploadedFilesInfo.length > 0 && (
        <>
          <Typography.Title level={4} style={{ marginTop: '40px', marginBottom: '20px', color: '#1890ff' }}>
            Successfully Uploaded Files
          </Typography.Title>
          <List
            itemLayout="horizontal"
            bordered
            dataSource={uploadedFilesInfo}
            renderItem={(item) => {
              const actions = [<CheckCircleOutlined style={{ color: 'green', fontSize: '24px' }} />];
              if (item.filename.toLowerCase().endsWith('.pdf')) {
                actions.unshift( // Add to the beginning of actions array
                  <Button
                    type="link"
                    icon={isExtractingText && currentFilenameForModal === item.filename ? <LoadingOutlined /> : <FileTextOutlined />}
                    onClick={() => handleExtractText(item)}
                    disabled={isExtractingText && currentFilenameForModal === item.filename}
                  >
                    {isExtractingText && currentFilenameForModal === item.filename ? 'Extracting...' : 'Extract Text'}
                  </Button>
                );
              }
              return (
                <List.Item actions={actions}>
                  <List.Item.Meta
                    avatar={<FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />}
                    title={<Text strong>{item.filename}</Text>}
                  description={
                    <Space direction="vertical" size={2}>
                      <Text type="secondary">Size: {(item.size / 1024 / 1024).toFixed(2)} MB</Text>
                      <Text type="secondary">Type: {item.content_type}</Text>
                      {/* <Text type="secondary">Saved At: {item.saved_path}</Text> */}
                      <Text type="secondary">Uploaded: {new Date(item.uploaded_at).toLocaleString()}</Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
            style={{ background: '#fff' }}
          />
        </>
      )}

      <Modal
        title={modalTitle}
        visible={isModalVisible}
        onOk={handleModalClose}
        onCancel={handleModalClose}
        width="80%"
        style={{ top: 20 }}
        footer={[
          <Button key="recognize"
            onClick={handleRecognizeEntities}
            loading={isRecognizingEntities}
            icon={<ExperimentOutlined />}
            disabled={isExtractingText || isBuildingGraph || !modalContent || modalContent.startsWith('Failed to extract text') || modalContent.startsWith('No text found')}
          >
            Recognize Entities
          </Button>,
          <Button key="buildGraph"
            type="primary"
            onClick={handleBuildGraph}
            loading={isBuildingGraph}
            icon={<ExperimentOutlined />} // Consider a different icon, e.g., ApartmentOutlined or ShareAltOutlined
            disabled={isExtractingText || isRecognizingEntities || isBuildingGraph || !extractedEntities || Object.keys(extractedEntities).length === 0 || Object.values(extractedEntities).every(arr => arr.length === 0)}
          >
            {isBuildingGraph ? 'Building Graph...' : 'Build Knowledge Graph'}
          </Button>,
          <Button key="back" onClick={handleModalClose} disabled={isBuildingGraph}>
            Close
          </Button>,
        ]}
      >
        {isExtractingText && modalContent === '' ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <LoadingOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
            <Paragraph style={{ marginTop: '10px' }}>Extracting text...</Paragraph>
          </div>
        ) : (
          <>
            <Paragraph style={{ whiteSpace: 'pre-wrap', maxHeight: '50vh', overflowY: 'auto', marginBottom: '20px', border: '1px solid #f0f0f0', padding: '10px', borderRadius: '4px' }}>
              {modalContent}
            </Paragraph>
            {extractedEntities && (
              <div>
                <Divider>Recognized Entities ({Object.values(extractedEntities).flat().length})</Divider>
                {Object.entries(extractedEntities).map(([type, entities]) => (
                  entities.length > 0 && (
                    <div key={type} style={{ marginBottom: '10px' }}>
                      <Title level={5} style={{ marginBottom: '5px' }}>{type}:</Title>
                      {entities.map((entity, index) => (
                        <Tag key={index} color={ENTITY_TYPE_COLORS[type] || 'default'} style={{ margin: '2px' }}>
                          {entity}
                        </Tag>
                      ))}
                    </div>
                  )
                ))}
                {Object.values(extractedEntities).every(arr => arr.length === 0) && !isRecognizingEntities && (
                     <Paragraph type="secondary" style={{textAlign: 'center'}}>No entities were found in the text.</Paragraph>
                )}
+                {/* Graph Building Progress and Stats Display */}
+                {(isBuildingGraph || graphBuildProgress.percent > 0 || graphBuildStats || graphBuildError) && <Divider>Knowledge Graph Construction</Divider>}
+
+                {isBuildingGraph && (
+                  <div style={{ margin: '20px 0' }}>
+                    <Progress percent={graphBuildProgress.percent} status="active" />
+                    <Paragraph style={{ textAlign: 'center', marginTop: '10px' }}>{graphBuildProgress.step}</Paragraph>
+                  </div>
+                )}
+
+                {!isBuildingGraph && graphBuildProgress.percent === 100 && !graphBuildError && graphBuildStats && (
+                  <div style={{ margin: '20px 0' }}>
+                    <Alert message="Graph built successfully!" type="success" showIcon style={{ marginBottom: '15px' }} />
+                    <Title level={5}>Graph Statistics:</Title>
+                    <List size="small">
+                      <List.Item>Nodes: <Text strong>{graphBuildStats.node_count}</Text></List.Item>
+                      <List.Item>Relationships: <Text strong>{graphBuildStats.edge_count}</Text></List.Item>
+                      <List.Item>Density: <Text strong>{graphBuildStats.graph_density?.toFixed(4) || 'N/A'}</Text></List.Item>
+                    </List>
+                  </div>
+                )}
+                 {!isBuildingGraph && graphBuildError && (
+                  <Alert message={graphBuildError} type="error" showIcon style={{ marginTop: '15px' }} />
+                )}
+              </div>
+            )}
+            {isRecognizingEntities && (
+                <div style={{ textAlign: 'center', padding: '20px' }}>
+                    <LoadingOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
+                    <Paragraph style={{ marginTop: '8px' }}>Recognizing entities...</Paragraph>
+                </div>
+            )}
+          </>
+        )}
+      </Modal>
    </div>
  );
};

export default FileUpload;
