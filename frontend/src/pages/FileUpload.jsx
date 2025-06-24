import React, { useState } from 'react';
import { Upload, message, Button, List, Typography, Progress, Space, Alert } from 'antd';
import { InboxOutlined, FileTextOutlined, UploadOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from '../utils/axios'; // Assuming axios is configured for backend calls

const { Dragger } = Upload;
const { Text, Link } = Typography;

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_FILE_TYPES = ['.dxf', '.pdf', '.ifc'];
const UPLOAD_URL = '/v1/files/upload'; // Backend endpoint

const FileUpload = () => {
  const [fileList, setFileList] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [overallProgress, setOverallProgress] = useState(0); // For overall progress of a batch
  const [uploadError, setUploadError] = useState(null);
  const [uploadedFilesInfo, setUploadedFilesInfo] = useState([]);

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
            renderItem={(item) => (
              <List.Item
                actions={[<CheckCircleOutlined style={{ color: 'green', fontSize: '24px' }} />]}
              >
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
    </div>
  );
};

export default FileUpload;
