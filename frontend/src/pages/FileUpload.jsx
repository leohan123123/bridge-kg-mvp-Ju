import React, { useState, useEffect } from 'react';
import { Upload, message, Button, List, Typography, Progress, Space, Alert, Modal, Tag, Divider, Descriptions } from 'antd';
import { InboxOutlined, FileTextOutlined, CheckCircleOutlined, LoadingOutlined, ExperimentOutlined, ApartmentOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Dragger } = Upload;
const { Text, Link, Paragraph, Title } = Typography;

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_FILE_TYPES = ['.dxf', '.pdf', '.ifc', '.txt', '.md']; // Added .txt, .md for easier testing
const UPLOAD_URL = '/api/v1/files/upload'; // Updated to match provided structure if different (original: /v1/files/upload)
const PDF_EXTRACT_URL = '/api/v1/pdf/extract-text'; // Updated (original: /v1/pdf/extract)
// const ENTITY_EXTRACT_URL = '/api/v1/entities/extract'; // This is now part of the graph build process on backend
const BUILD_GRAPH_URL = '/api/v1/rag/build_graph';

// Define colors for entity types (can be expanded)
const ENTITY_TYPE_COLORS = {
  "结构类型": "magenta",
  "材料类型": "blue",
  "技术规范": "green",
  "施工工艺": "purple",
  // Add more colors if new types are introduced
};

const FileUpload = () => {
  const navigate = useNavigate();
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [overallProgress, setOverallProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFilesInfo, setUploadedFilesInfo] = useState([]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalContent, setModalContent] = useState(''); // Holds PDF text
  const [modalTitle, setModalTitle] = useState('');
  const [isExtractingText, setIsExtractingText] = useState(false);
  const [currentFilenameForModal, setCurrentFilenameForModal] = useState('');
  const [currentFileContentForModal, setCurrentFileContentForModal] = useState('');


  // State for Knowledge Graph Building
  const [isBuildingGraph, setIsBuildingGraph] = useState(false);
  const [graphBuildProgress, setGraphBuildProgress] = useState({ step: '', percent: 0, message: '' });
  const [graphBuildResult, setGraphBuildResult] = useState(null); // Stores the full response from build_graph
  const [graphBuildError, setGraphBuildError] = useState(null);


  const handleExtractText = async (fileInfo) => {
    // If not PDF, maybe just read as text for .txt, .md
    if (!fileInfo.filename.toLowerCase().endsWith('.pdf')) {
        // For non-PDFs, attempt to read as plain text directly if it's a text-based format
        if (fileInfo.originFileObj && (fileInfo.filename.toLowerCase().endsWith('.txt') || fileInfo.filename.toLowerCase().endsWith('.md'))) {
            const reader = new FileReader();
            reader.onload = (e) => {
                setModalContent(e.target.result);
                setCurrentFileContentForModal(e.target.result);
                setModalTitle(`Content of ${fileInfo.filename}`);
                setIsModalVisible(true);
                setCurrentFilenameForModal(fileInfo.filename);
            };
            reader.onerror = () => {
                message.error(`Failed to read content from ${fileInfo.filename}`);
                setModalContent(`Failed to read content from ${fileInfo.filename}`);
                setIsModalVisible(true);
            }
            reader.readAsText(fileInfo.originFileObj);
            return;
        }
      message.info('Text extraction is primarily for PDF files. For other types, content will be used as is if possible.');
      // For other non-PDFs, we might not have a preview, or allow building graph directly.
      // For now, only enable modal for PDF and text files.
      // If it's a DXF/IFC, graph building might happen differently (not covered by this text-based flow).
      setModalContent(`Text extraction/preview not available for ${fileInfo.filename}. You can try to build graph directly if applicable.`);
      setCurrentFileContentForModal(''); // No text content for non-PDFs/non-text
      setModalTitle(`File: ${fileInfo.filename}`);
      setIsModalVisible(true);
      setCurrentFilenameForModal(fileInfo.filename);
      return;
    }

    setIsExtractingText(true);
    setGraphBuildResult(null); // Clear previous graph build results
    setGraphBuildError(null);
    setCurrentFilenameForModal(fileInfo.filename);
    setModalTitle(`Extracting text from ${fileInfo.filename}...`);
    setModalContent('');
    setIsModalVisible(true);

    try {
      const relativePath = fileInfo.filename; // Assuming filename is the key backend uses
      const response = await axios.post(PDF_EXTRACT_URL, { file_path: relativePath });
      setModalTitle(`Text from ${fileInfo.filename}`);
      if (response.data && response.data.text_content) {
        setModalContent(response.data.text_content);
        setCurrentFileContentForModal(response.data.text_content); // Store for graph build
      } else {
        setModalContent('No text found or an error occurred during extraction.');
        setCurrentFileContentForModal('');
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
      setCurrentFileContentForModal('');
      setModalTitle(`Error extracting text from ${fileInfo.filename}`);
      message.error(errorText);
    } finally {
      setIsExtractingText(false);
    }
  };

  const handleModalClose = () => {
    setIsModalVisible(false);
    setModalContent('');
    setModalTitle('');
    setCurrentFilenameForModal('');
    setCurrentFileContentForModal('');
    setIsExtractingText(false);
    setIsBuildingGraph(false);
    setGraphBuildProgress({ step: '', percent: 0, message: '' });
    setGraphBuildResult(null);
    setGraphBuildError(null);
  };

  const handleBuildGraph = async () => {
    if (!currentFileContentForModal && !currentFilenameForModal.toLowerCase().endsWith('.dxf') && !currentFilenameForModal.toLowerCase().endsWith('.ifc')) {
        // If it's not a text-based flow and not a known direct-to-graph format
      message.error('No text content available to build graph. Please extract text from a PDF or use a text file.');
      return;
    }
    if (!currentFilenameForModal) {
        message.error('File context is missing. Please re-open the file action modal.');
        return;
    }

    setIsBuildingGraph(true);
    setGraphBuildProgress({ step: 'Initializing...', percent: 0, message: 'Preparing to build knowledge graph.' });
    setGraphBuildResult(null);
    setGraphBuildError(null);

    try {
      // Simulate frontend progress for stages
      setGraphBuildProgress({ step: 'Step 1/3', percent: 30, message: 'Sending document to backend for processing...' });

      // Backend's /api/v1/rag/build_graph expects: text_content, document_name
      const payload = {
        text_content: currentFileContentForModal, // This will be empty for non-text files, backend should handle
        document_name: currentFilenameForModal,
      };

      const response = await axios.post(BUILD_GRAPH_URL, payload);

      setGraphBuildProgress({ step: 'Step 2/3', percent: 70, message: 'Backend processing entities and relationships...' });
      // Simulate delay for backend processing visibility
      await new Promise(resolve => setTimeout(resolve, 1000));

      if (response.data && response.data.status) {
        if (response.data.status.includes("complete") || response.data.status.includes("success")) {
          setGraphBuildResult(response.data);
          message.success(`Graph built for ${response.data.document_name}: ${response.data.status}`);
          setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: 'Graph construction finished!' });
        } else if (response.data.status.includes("No entities found")) {
            setGraphBuildResult(response.data); // Store partial success/info
            message.warning(`Graph construction for ${response.data.document_name}: ${response.data.status}`);
            setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: response.data.status });
        } else { // Other non-error statuses from backend
            setGraphBuildResult(response.data);
            message.info(`Graph construction for ${response.data.document_name}: ${response.data.status}`);
            setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: response.data.status });
        }
      } else if (response.data && response.data.error) {
        throw new Error(response.data.error);
      }
      else {
        throw new Error('Unexpected response from build graph endpoint.');
      }

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
      setGraphBuildProgress({ step: 'Error', percent: 100, message: 'An error occurred during graph construction.' });
    } finally {
      setIsBuildingGraph(false);
      // Progress remains at 100 or error state. Result is stored in graphBuildResult or graphBuildError.
    }
  };


  const handleFileChange = (info) => {
    let newFileList = [...info.fileList];
    setFileList(newFileList); // Update file list for display

    const { status, response, name: fileName, originFileObj } = info.file;

    if (status === 'uploading') {
        setUploading(true);
        setUploadError(null);
    } else if (status === 'done') {
        message.success(`${fileName} file uploaded successfully.`);
        // Assuming backend returns a list of FileUploadResponse, even for a single file.
        // And customRequest's onSuccess correctly passes the first item if only one.
        const uploadedFileResponse = Array.isArray(response) ? response[0] : response;

        if (uploadedFileResponse && uploadedFileResponse.filename) {
            setUploadedFilesInfo(prev => {
                // Add file metadata along with the AntD file object for later use (like reading content)
                const existingFile = prev.find(f => f.filename === uploadedFileResponse.filename);
                if (!existingFile) {
                    return [...prev, { ...uploadedFileResponse, originFileObj }];
                }
                // If exists, update it (though less likely for new uploads)
                return prev.map(f => f.filename === uploadedFileResponse.filename ? { ...uploadedFileResponse, originFileObj } : f);
            });
        }
        // If it's the last file in the current batch being uploaded
        if (newFileList.every(f => f.status === 'done' || f.status === 'error')) {
            setUploading(false);
        }
    } else if (status === 'error') {
        const errorMsg = info.file.error?.message || `${fileName} file upload failed.`;
        message.error(errorMsg);
        setUploadError(errorMsg); // Display a general error for the batch
        if (newFileList.every(f => f.status === 'done' || f.status === 'error')) {
            setUploading(false);
        }
    }
};


  const draggerProps = {
    name: 'files',
    multiple: true,
    accept: ALLOWED_FILE_TYPES.join(','),
    fileList: fileList,
    beforeUpload: (file) => {
      setUploadError(null);
      const isAllowedType = ALLOWED_FILE_TYPES.some(type => file.name.toLowerCase().endsWith(type));
      if (!isAllowedType) {
        const errorMsg = `${file.name}: File type not allowed. Only ${ALLOWED_FILE_TYPES.join(', ')} are accepted.`;
        message.error(errorMsg);
        setUploadError(errorMsg);
        return Upload.LIST_IGNORE;
      }
      const isLt50M = file.size <= MAX_FILE_SIZE;
      if (!isLt50M) {
        const errorMsg = `${file.name}: File exceeds 50MB limit.`;
        message.error(errorMsg);
        setUploadError(errorMsg);
        return Upload.LIST_IGNORE;
      }
      return true;
    },
    customRequest: async ({ file, onSuccess, onError, onProgress }) => {
      const formData = new FormData();
      // Backend API /api/v1/files/upload expects 'files: List[UploadFile]'
      // When sending one by one via customRequest, it's still a list with one item.
      formData.append('files', file);

      try {
        const response = await axios.post(UPLOAD_URL, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (event) => {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress({ percent }, file);
            setOverallProgress(percent);
          },
        });
        // response.data is List[FileUploadResponse], customRequest handles one file, so take first.
        onSuccess(response.data[0] || response.data, file);
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
        onError(new Error(errorMessage), err.response?.data);
      }
    },
    onChange: handleFileChange,
    onRemove: (file) => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
      setUploadedFilesInfo(prev => prev.filter(item => item.filename !== file.name)); // Use filename for matching backend info
      if (fileList.length === 1) {
        setUploadError(null);
      }
      return true;
    },
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: 'auto', fontFamily: "'Roboto', sans-serif" }}>
      <Typography.Title level={2} style={{ textAlign: 'center', marginBottom: '30px', color: '#1890ff' }}>
        Bridge Project File Upload & Processing
      </Typography.Title>

      <Dragger {...draggerProps} style={{ marginBottom: '20px', padding: '30px', border: '2px dashed #1890ff' }}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined style={{ fontSize: '60px', color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text" style={{ fontSize: '18px', color: '#555' }}>Click or drag files to this area to upload</p>
        <p className="ant-upload-hint" style={{ fontSize: '14px', color: '#888' }}>
          Supports DXF, PDF, IFC, TXT, MD files. Maximum file size: 50MB.
        </p>
      </Dragger>

      {uploading && fileList.some(f => f.status === 'uploading') && (
        <Progress percent={overallProgress} status="active" style={{ marginBottom: '20px' }} />
      )}

      {uploadError && !uploading && (
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
            dataSource={uploadedFilesInfo} // Use the state that stores backend response
            renderItem={(item) => { // item is FileUploadResponse from backend
              const fileCanBeProcessed = item.filename.toLowerCase().endsWith('.pdf') ||
                                         item.filename.toLowerCase().endsWith('.txt') ||
                                         item.filename.toLowerCase().endsWith('.md');
              const actions = [];
              if (fileCanBeProcessed) {
                actions.push(
                  <Button
                    key="process"
                    type="link"
                    icon={isExtractingText && currentFilenameForModal === item.filename ? <LoadingOutlined /> : <FileTextOutlined />}
                    onClick={() => handleExtractText(item)} // Pass the full item which now includes originFileObj
                    disabled={isExtractingText && currentFilenameForModal === item.filename}
                  >
                    {isExtractingText && currentFilenameForModal === item.filename ? 'Processing...' : 'View & Process Text'}
                  </Button>
                );
              } else {
                 actions.push(<Text type="secondary" italic>Processing for this file type (e.g., DXF to graph) might be direct or via other tools.</Text>)
              }

              return (
                <List.Item actions={actions}>
                  <List.Item.Meta
                    avatar={<CheckCircleOutlined style={{ fontSize: '24px', color: 'green' }} />}
                    title={<Text strong>{item.filename}</Text>}
                  description={
                    <Space direction="vertical" size={2}>
                      <Text type="secondary">Size: {(item.size / 1024 / 1024).toFixed(2)} MB</Text>
                      <Text type="secondary">Type: {item.content_type}</Text>
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
        onCancel={handleModalClose}
        width="80%"
        style={{ top: 20 }}
        footer={[
          <Button key="buildGraph"
            type="primary"
            onClick={handleBuildGraph}
            loading={isBuildingGraph}
            icon={<ApartmentOutlined />}
            disabled={isExtractingText || isBuildingGraph || !currentFilenameForModal || (!currentFileContentForModal && !currentFilenameForModal.toLowerCase().endsWith('.dxf') && !currentFilenameForModal.toLowerCase().endsWith('.ifc'))}
          >
            {isBuildingGraph ? 'Building Graph...' : 'Build Knowledge Graph'}
          </Button>,
          <Button key="close" onClick={handleModalClose} disabled={isBuildingGraph}>
            Close
          </Button>,
        ]}
      >
        {isExtractingText && !modalContent ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <LoadingOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
            <Paragraph style={{ marginTop: '10px' }}>Extracting text...</Paragraph>
          </div>
        ) : (
          <>
            {currentFileContentForModal && (
                <Paragraph style={{ whiteSpace: 'pre-wrap', maxHeight: '40vh', overflowY: 'auto', marginBottom: '20px', border: '1px solid #f0f0f0', padding: '10px', borderRadius: '4px', background: '#f9f9f9' }}>
                    {currentFileContentForModal}
                </Paragraph>
            )}
            {modalContent && !currentFileContentForModal && /* For error messages or non-text previews */ (
                 <Paragraph style={{ whiteSpace: 'pre-wrap', maxHeight: '40vh', overflowY: 'auto', marginBottom: '20px', border: '1px solid #f0f0f0', padding: '10px', borderRadius: '4px' }}>
                    {modalContent}
                </Paragraph>
            )}

            {/* Graph Building Progress and Stats Display */}
            {(isBuildingGraph || graphBuildResult || graphBuildError) && <Divider>Knowledge Graph Construction</Divider>}

            {isBuildingGraph && (
              <div style={{ margin: '20px 0', textAlign: 'center' }}>
                <Progress type="circle" percent={graphBuildProgress.percent} style={{marginBottom: '10px'}} />
                <Paragraph>{graphBuildProgress.message}</Paragraph>
              </div>
            )}

            {!isBuildingGraph && graphBuildResult && (
              <div style={{ margin: '20px 0' }}>
                <Alert
                    message={`Graph Construction for "${graphBuildResult.document_name}"`}
                    description={graphBuildResult.status || "Process finished."}
                    type={graphBuildResult.status?.includes("complete") || graphBuildResult.status?.includes("success") ? "success" : "info"}
                    showIcon
                    style={{ marginBottom: '15px' }} />

                <Title level={5} style={{marginTop: '20px'}}>Build Summary:</Title>
                <Descriptions bordered column={1} size="small">
                  {graphBuildResult.unique_entities_processed !== undefined && (
                    <Descriptions.Item label="Unique Entities Processed">
                      <Text strong>{graphBuildResult.unique_entities_processed}</Text>
                    </Descriptions.Item>
                  )}
                  {graphBuildResult.entities_found_by_category && Object.keys(graphBuildResult.entities_found_by_category).length > 0 && (
                    <Descriptions.Item label="Processed Entity Categories">
                      {Object.entries(graphBuildResult.entities_found_by_category).map(([category, count]) => (
                        <Tag key={category} color={ENTITY_TYPE_COLORS[category] || 'default'} style={{ margin: '2px' }}>
                          {category}: {count}
                        </Tag>
                      ))}
                    </Descriptions.Item>
                  )}
                  {graphBuildResult.relationships_extracted !== undefined && (
                    <Descriptions.Item label="Relationships Extracted (Potential)">
                      <Text strong>{graphBuildResult.relationships_extracted}</Text>
                    </Descriptions.Item>
                  )}
                  {graphBuildResult.relationships_created_in_db !== undefined && (
                    <Descriptions.Item label="Relationships Created in DB">
                      <Text strong>{graphBuildResult.relationships_created_in_db}</Text>
                    </Descriptions.Item>
                  )}
                </Descriptions>

                {(graphBuildResult.status?.includes("complete") || graphBuildResult.status?.includes("success")) && graphBuildResult.unique_entities_processed > 0 && (
                    <Button
                        type="primary"
                        icon={<ArrowRightOutlined />}
                        style={{marginTop: '20px'}}
                        onClick={() => {
                            handleModalClose();
                            navigate('/graph-browser'); // Make sure this route is configured in App.jsx/tsx
                        }}
                    >
                        Explore in Graph Browser
                    </Button>
                )}
              </div>
            )}
            {!isBuildingGraph && graphBuildError && (
              <Alert message="Graph Construction Failed" description={graphBuildError} type="error" showIcon style={{ marginTop: '15px' }} />
            )}
          </>
        )}
      </Modal>
    </div>
  );
};

export default FileUpload;
