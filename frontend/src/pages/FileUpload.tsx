import React, { useState, useEffect, ChangeEvent } from 'react';
import { Upload, message, Button, List, Typography, Progress, Space, Alert, Modal, Tag, Divider, Descriptions } from 'antd';
import type { UploadProps, UploadFile, UploadChangeParam } from 'antd/es/upload/interface';
import { InboxOutlined, FileTextOutlined, CheckCircleOutlined, LoadingOutlined, ExperimentOutlined, ApartmentOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Dragger } = Upload;
const { Text, Paragraph, Title } = Typography; // Link was unused

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

// Interface for backend file upload response
interface FileUploadResponse {
  filename: string;
  content_type: string;
  size: number;
  uploaded_at: string; // Assuming ISO string date
  file_path: string; // Relative path on server
  // Include originFileObj for client-side operations if needed, but not from backend
  originFileObj?: File; // Ant Design's UploadFile has this
}

// Interface for PDF extraction response
interface PdfExtractResponse {
  text_content: string;
  num_pages?: number; // Optional
}

// Interface for Graph Build API response
interface GraphBuildResponse {
  document_name: string;
  status: string;
  unique_entities_processed?: number;
  entities_found_by_category?: Record<string, number>;
  relationships_extracted?: number;
  relationships_created_in_db?: number;
  error?: string;
  // Any other fields backend might return
}

interface GraphBuildProgressState {
  step: string;
  percent: number;
  message: string;
}

interface PageProps {} // No props expected

interface PageState {
  fileList: UploadFile[]; // From Ant Design
  uploading: boolean;
  overallProgress: number;
  uploadError: string | null;
  uploadedFilesInfo: FileUploadResponse[]; // Store info from backend for successfully uploaded files

  isModalVisible: boolean;
  modalContent: string;
  modalTitle: string;
  isExtractingText: boolean;
  currentFilenameForModal: string;
  currentFileContentForModal: string;

  isBuildingGraph: boolean;
  graphBuildProgress: GraphBuildProgressState;
  graphBuildResult: GraphBuildResponse | null;
  graphBuildError: string | null;
}


const FileUpload: React.FC<PageProps> = () => {
  const navigate = useNavigate();
  const [fileList, setFileList] = useState<PageState['fileList']>([]);
  const [uploading, setUploading] = useState<PageState['uploading']>(false);
  const [overallProgress, setOverallProgress] = useState<PageState['overallProgress']>(0);
  const [uploadError, setUploadError] = useState<PageState['uploadError']>(null);
  const [uploadedFilesInfo, setUploadedFilesInfo] = useState<PageState['uploadedFilesInfo']>([]);

  const [isModalVisible, setIsModalVisible] = useState<PageState['isModalVisible']>(false);
  const [modalContent, setModalContent] = useState<PageState['modalContent']>('');
  const [modalTitle, setModalTitle] = useState<PageState['modalTitle']>('');
  const [isExtractingText, setIsExtractingText] = useState<PageState['isExtractingText']>(false);
  const [currentFilenameForModal, setCurrentFilenameForModal] = useState<PageState['currentFilenameForModal']>('');
  const [currentFileContentForModal, setCurrentFileContentForModal] = useState<PageState['currentFileContentForModal']>('');

  const [isBuildingGraph, setIsBuildingGraph] = useState<PageState['isBuildingGraph']>(false);
  const [graphBuildProgress, setGraphBuildProgress] = useState<PageState['graphBuildProgress']>({ step: '', percent: 0, message: '' });
  const [graphBuildResult, setGraphBuildResult] = useState<PageState['graphBuildResult']>(null);
  const [graphBuildError, setGraphBuildError] = useState<PageState['graphBuildError']>(null);

  const handleExtractText = async (fileInfo: FileUploadResponse) => { // fileInfo is from our backend FileUploadResponse
    // If not PDF, maybe just read as text for .txt, .md
    if (!fileInfo.filename.toLowerCase().endsWith('.pdf')) {
        // For non-PDFs, attempt to read as plain text directly if it's a text-based format
        // fileInfo from uploadedFilesInfo might not have originFileObj if not added carefully.
        // It's better to pass the AntD UploadFile object or ensure originFileObj is correctly propagated.
        // For this function, let's assume fileInfo *could* have originFileObj if it's from the initial list.
        const antFile = fileList.find(f => f.name === fileInfo.filename); // Try to find original AntD file

        if (antFile?.originFileObj && (fileInfo.filename.toLowerCase().endsWith('.txt') || fileInfo.filename.toLowerCase().endsWith('.md'))) {
            const reader = new FileReader();
            reader.onload = (e: ProgressEvent<FileReader>) => {
                setModalContent(e.target?.result as string || '');
                setCurrentFileContentForModal(e.target?.result as string || '');
                setModalTitle(`Content of ${fileInfo.filename}`);
                setIsModalVisible(true);
                setCurrentFilenameForModal(fileInfo.filename);
            };
            reader.onerror = () => {
                message.error(`Failed to read content from ${fileInfo.filename}`);
                setModalContent(`Failed to read content from ${fileInfo.filename}`);
                setIsModalVisible(true);
            }
            reader.readAsText(antFile.originFileObj);
            return;
        }
      message.info('Text extraction is primarily for PDF files. For other types, content will be used as is if possible.');
      setModalContent(`Text extraction/preview not available for ${fileInfo.filename}. You can try to build graph directly if applicable.`);
      setCurrentFileContentForModal('');
      setModalTitle(`File: ${fileInfo.filename}`);
      setIsModalVisible(true);
      setCurrentFilenameForModal(fileInfo.filename);
      return;
    }

    setIsExtractingText(true);
    setGraphBuildResult(null);
    setGraphBuildError(null);
    setCurrentFilenameForModal(fileInfo.filename);
    setModalTitle(`Extracting text from ${fileInfo.filename}...`);
    setModalContent('');
    setIsModalVisible(true);

    try {
      const relativePath = fileInfo.file_path || fileInfo.filename; // Prefer file_path from backend if available
      const response = await axios.post<PdfExtractResponse>(PDF_EXTRACT_URL, { file_path: relativePath });
      setModalTitle(`Text from ${fileInfo.filename}`);
      if (response.data && response.data.text_content) {
        setModalContent(response.data.text_content);
        setCurrentFileContentForModal(response.data.text_content);
      } else {
        setModalContent('No text found or an error occurred during extraction.');
        setCurrentFileContentForModal('');
      }
    } catch (error: any) {
      console.error('Error extracting PDF text:', error);
      let errorText = 'Failed to extract text.';
      if (error.response?.data?.detail) {
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

  const handleModalClose = (): void => {
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

  const handleBuildGraph = async (): Promise<void> => {
    if (!currentFileContentForModal && !currentFilenameForModal.toLowerCase().endsWith('.dxf') && !currentFilenameForModal.toLowerCase().endsWith('.ifc')) {
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
      setGraphBuildProgress({ step: 'Step 1/3', percent: 30, message: 'Sending document to backend for processing...' });

      const payload = {
        text_content: currentFileContentForModal,
        document_name: currentFilenameForModal,
      };

      const response = await axios.post<GraphBuildResponse>(BUILD_GRAPH_URL, payload);

      setGraphBuildProgress({ step: 'Step 2/3', percent: 70, message: 'Backend processing entities and relationships...' });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate delay

      if (response.data) {
        if (response.data.status?.includes("complete") || response.data.status?.includes("success")) {
          setGraphBuildResult(response.data);
          message.success(`Graph built for ${response.data.document_name}: ${response.data.status}`);
          setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: 'Graph construction finished!' });
        } else if (response.data.status?.includes("No entities found")) {
            setGraphBuildResult(response.data);
            message.warning(`Graph construction for ${response.data.document_name}: ${response.data.status}`);
            setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: response.data.status });
        } else if (response.data.error) { // Explicit error field from backend
             throw new Error(response.data.error);
        }
        else { // Other non-error statuses
            setGraphBuildResult(response.data);
            message.info(`Graph construction for ${response.data.document_name}: ${response.data.status || 'Process reported an unknown status.'}`);
            setGraphBuildProgress({ step: 'Step 3/3', percent: 100, message: response.data.status || 'Process finished with unknown status.' });
        }
      } else {
        throw new Error('Unexpected empty response from build graph endpoint.');
      }

    } catch (error: any) {
      console.error('Error building knowledge graph:', error);
      let errorMsg = 'Failed to build knowledge graph.';
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.message) {
        errorMsg = error.message;
      }
      message.error(errorMsg);
      setGraphBuildError(errorMsg);
      setGraphBuildProgress({ step: 'Error', percent: 100, message: 'An error occurred during graph construction.' });
    } finally {
      setIsBuildingGraph(false);
    }
  };

  const handleFileChange = (info: UploadChangeParam<UploadFile<FileUploadResponse | FileUploadResponse[]>>) => {
    let newFileList = [...info.fileList];
    setFileList(newFileList);

    const { status, response, name: fileName, originFileObj } = info.file;

    if (status === 'uploading') {
        setUploading(true);
        setUploadError(null);
    } else if (status === 'done') {
        message.success(`${fileName} file uploaded successfully.`);
        // AntD's UploadFile<T> has `response` of type T.
        // If backend returns a list for 'files' param, but customRequest sends one by one,
        // the response for a single file should be FileUploadResponse, not FileUploadResponse[].
        // Assuming response is FileUploadResponse based on `onSuccess(response.data[0] ...)` below.
        const uploadedFileResponse = info.file.response as FileUploadResponse;


        if (uploadedFileResponse && uploadedFileResponse.filename) {
            setUploadedFilesInfo(prev => {
                const existingFile = prev.find(f => f.filename === uploadedFileResponse.filename);
                if (!existingFile) {
                    // Add originFileObj to the stored info if available from AntD file object
                    return [...prev, { ...uploadedFileResponse, originFileObj: originFileObj }];
                }
                return prev.map(f => f.filename === uploadedFileResponse.filename ? { ...uploadedFileResponse, originFileObj: originFileObj } : f);
            });
        }
        if (newFileList.every(f => f.status === 'done' || f.status === 'error')) {
            setUploading(false);
        }
    } else if (status === 'error') {
        const errorMsg = info.file.error?.message || `${fileName} file upload failed.`;
        message.error(errorMsg);
        setUploadError(errorMsg);
        if (newFileList.every(f => f.status === 'done' || f.status === 'error')) {
            setUploading(false);
        }
    }
};

  const draggerProps: UploadProps = {
    name: 'files',
    multiple: true,
    accept: ALLOWED_FILE_TYPES.join(','),
    fileList: fileList,
    beforeUpload: (file: File): boolean | string => { // AntD type for beforeUpload
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
      return true; // Or Upload.LIST_IGNORE if returning string
    },
    customRequest: async (options) => { // options is RcCustomRequestOptions
      const { file, onSuccess, onError, onProgress } = options;
      const formData = new FormData();
      // Ensure 'file' is treated as File object. AntD might pass RcFile which extends File.
      formData.append('files', file as File);

      try {
        // Assuming UPLOAD_URL expects a list of files and returns a list of responses.
        // If customRequest processes one file, backend should ideally handle single file in 'files' field
        // and return FileUploadResponse[] with one item.
        const response = await axios.post<FileUploadResponse[]>(UPLOAD_URL, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (event: ProgressEvent) => {
            if (event.lengthComputable && onProgress) {
              const percent = Math.round((event.loaded / event.total) * 100);
              onProgress({ percent });
              setOverallProgress(percent);
            }
          },
        });
        // Assuming backend returns an array, and for a single file upload, it's an array with one element.
        if (onSuccess && response.data && response.data.length > 0) {
          onSuccess(response.data[0]); // Pass the single FileUploadResponse object
        } else if (onSuccess && response.data) { // Fallback if backend returns single object not in array
           onSuccess(response.data as any); // This case should be clarified with backend spec
        }
         else {
          throw new Error("Upload succeeded but response format was unexpected.");
        }
      } catch (err: any) {
        console.error("Upload error in customRequest:", err);
        let errorMessage = "Upload failed.";
        if (err.response) {
            errorMessage = err.response.data?.detail || `Server error: ${err.response.status}`;
        } else if (err.request) {
            errorMessage = "No response from server.";
        } else {
            errorMessage = err.message;
        }
        if (onError) {
          onError(new Error(errorMessage), err.response?.data);
        }
      }
    },
    onChange: handleFileChange,
    onRemove: (file: UploadFile): boolean => {
      setFileList(prev => prev.filter(item => item.uid !== file.uid));
      setUploadedFilesInfo(prev => prev.filter(item => item.filename !== file.name));
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
