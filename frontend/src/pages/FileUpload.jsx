// frontend/src/pages/FileUpload.jsx
import React, { useState, useEffect } from 'react';
import { Upload, Button, message, List, Typography, Space, Tooltip, Progress, Card, Row, Col, Alert } from 'antd'; // Added Alert
import { UploadOutlined, FilePdfOutlined, FileWordOutlined, FileExcelOutlined, FilePptOutlined, FileImageOutlined, FileTextOutlined, FileZipOutlined, DeleteOutlined, DownloadOutlined, EyeOutlined, PaperClipOutlined, InboxOutlined, CloudUploadOutlined } from '@ant-design/icons'; // Added CloudUploadOutlined
// 假设我们有一个 apiClient 用于 API 调用
import apiClient from '../utils/axios'; // 确保路径正确

const { Dragger } = Upload;
const { Title, Text, Link } = Typography;

// 定义允许的文件类型和大小限制 (与后端保持一致或更严格)
const ALLOWED_FILE_TYPES = ['application/pdf', 'image/vnd.dxf', 'image/x-dwg', '.pdf', '.dxf', '.dwg']; // MIME类型 + 后缀
const MAX_FILE_SIZE_MB = 50; // MB
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

const FileUploadPage = () => {
  const [fileList, setFileList] = useState([]); // 用于 Upload 组件自身管理的文件列表
  const [uploadedFiles, setUploadedFiles] = useState([]); // 从后端获取的已上传文件列表
  const [uploading, setUploading] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // State for knowledge graph import
  const [importingFileId, setImportingFileId] = useState(null);
  const [importStatus, setImportStatus] = useState('idle'); // 'idle', 'loading', 'success', 'error'
  const [importMessage, setImportMessage] = useState('');

  // 获取已上传文件列表的函数
  const fetchUploadedFiles = async () => {
    setLoadingFiles(true);
    try {
      // 注意：这里的 apiClient 返回的是 response.data
      const response = await apiClient.get('/files/'); // 根据后端路由调整
      // 假设响应格式为 { total: number, items: [], page: number, size: number }
      setUploadedFiles(response.items || []); // response已经是data了
      message.success('文件列表已刷新');
    } catch (error) {
      console.error('获取文件列表失败:', error);
      message.error(`获取文件列表失败: ${error.response?.data?.detail || error.message || '未知错误'}`);
      setUploadedFiles([]); // 出错时清空或保留旧数据
    } finally {
      setLoadingFiles(false);
    }
  };

  // 组件加载时获取文件列表
  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  // 文件类型图标获取逻辑
  const getFileIcon = (filenameOrType) => {
    const extension = (filenameOrType.includes('.') ? filenameOrType.substring(filenameOrType.lastIndexOf('.')).toLowerCase() : filenameOrType.toLowerCase());
    if (extension.includes('pdf')) return <FilePdfOutlined style={{color: '#FF5733'}} />;
    if (extension.includes('doc') || extension.includes('docx')) return <FileWordOutlined style={{color: '#2A5699'}} />;
    if (extension.includes('xls') || extension.includes('xlsx')) return <FileExcelOutlined style={{color: '#1D6F42'}} />;
    if (extension.includes('ppt') || extension.includes('pptx')) return <FilePptOutlined style={{color: '#D04424'}} />;
    if (extension.includes('jpg') || extension.includes('jpeg') || extension.includes('png') || extension.includes('gif')) return <FileImageOutlined style={{color: '#33A1FF'}} />;
    if (extension.includes('txt') || extension.includes('dxf') || extension.includes('dwg')) return <FileTextOutlined style={{color: '#555555'}} />; // DXF, DWG 暂时用文本图标
    if (extension.includes('zip') || extension.includes('rar')) return <FileZipOutlined style={{color: '#FFC300'}} />;
    return <PaperClipOutlined style={{color: '#888888'}} />;
  };

  const handleUpload = async (options) => {
    const { onSuccess, onError, file, onProgress } = options;

    const formData = new FormData();
    formData.append('files', file); // 后端期望 'files'作为字段名，并且是一个列表

    setUploading(true);
    try {
      const response = await apiClient.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (event) => {
          const percent = Math.floor((event.loaded / event.total) * 100);
          onProgress({ percent }, file);
        },
      });
      // response 已经是 data 了，并且后端返回 List[FileMetadataResponse]
      // 如果上传单个文件，后端也应该返回列表，我们取第一个
      const uploadedFileMetadata = response && response.length > 0 ? response[0] : null;
      if (uploadedFileMetadata) {
        message.success(`${file.name} 上传成功。`);
        onSuccess(uploadedFileMetadata, file); // 将后端返回的元数据传递给 onSuccess
        fetchUploadedFiles(); // 重新加载列表
      } else {
        // 可能后端没有按预期返回元数据列表或为空
        message.warning(`${file.name} 上传完成，但未收到有效的元数据。`);
        onSuccess(null, file); // 仍然调用onSuccess表示完成，但可能没有数据
        fetchUploadedFiles();
      }
    } catch (error) {
      console.error('上传失败:', error);
      const errorMsg = error.response?.data?.detail || error.message || `${file.name} 上传失败`;
      message.error(errorMsg);
      onError(new Error(errorMsg), { file }); // Antd Upload期望Error对象
    } finally {
      setUploading(false);
    }
  };

  const beforeUpload = (file) => {
    const isAllowedType = ALLOWED_FILE_TYPES.some(type =>
        file.type ? file.type.includes(type.replace('.','')) : false || // 检查MIME类型
        file.name.toLowerCase().endsWith(type) // 检查文件后缀
    );

    if (!isAllowedType) {
      message.error(`${file.name}: 文件类型不被允许。请上传 ${ALLOWED_FILE_TYPES.filter(t => t.startsWith('.')).join(', ')} 文件。`);
      return Upload.LIST_IGNORE; // 阻止上传
    }
    const isLtSize = file.size <= MAX_FILE_SIZE_BYTES;
    if (!isLtSize) {
      message.error(`${file.name}: 文件大小超过 ${MAX_FILE_SIZE_MB}MB 限制。`);
      return Upload.LIST_IGNORE; // 阻止上传
    }
    return true; // 允许上传，将由 customRequest 处理
  };

  const handleFileRemoveFromList = (file) => {
    // 这个函数是当用户从 Upload 组件的UI中移除一个文件时调用 (上传前或上传失败后)
    // 如果文件已经上传成功并存在于 uploadedFiles 列表，则需要调用后端删除
    // 但 Upload 组件自身的 fileList 管理和我们后端的 uploadedFiles 是分开的
    // 这里我们主要处理的是 Upload 组件的 fileList
    const newAntdFileList = fileList.filter(item => item.uid !== file.uid);
    setFileList(newAntdFileList);
    message.info(`${file.name} 已从上传队列移除。`);
    return true; // 返回 true 以允许移除
  };

  const handleDeleteUploadedFile = async (fileId, fileName) => {
    try {
      await apiClient.delete(`/files/${fileId}`); // 后端API需要文件ID
      message.success(`文件 "${fileName}" 删除成功。`);
      fetchUploadedFiles(); // 重新加载列表
    } catch (error) {
      console.error('删除文件失败:', error);
      message.error(`删除文件 "${fileName}" 失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDownloadFile = (fileId, fileName) => {
    // 后端 /files/download/{file_id} 是 GET 请求
    // apiClient 默认处理 JSON，下载文件需要特殊处理
    const downloadUrl = `${apiClient.defaults.baseURL}/files/download/${fileId}`;
    // 可以直接用 <a> 标签下载，或者用 fetch/axios 获取 blob 再创建下载链接
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', fileName); // 设置下载的文件名
    // link.setAttribute('target', '_blank'); // 如果需要在新标签页打开（对于某些类型文件可能直接预览）
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    message.success(`开始下载文件: ${fileName}`);
  };

  // Upload 组件的 props
  const uploadProps = {
    name: 'files', // 与后端 FormData 字段名对应
    multiple: true,
    fileList: fileList, // 控制 Upload 组件显示的文件列表
    customRequest: handleUpload, // 自定义上传逻辑
    beforeUpload: beforeUpload, // 上传前校验
    onRemove: handleFileRemoveFromList, // 从 Upload 组件UI移除文件时
    onChange: (info) => { // 处理 Upload 组件内部状态变化
      setFileList(info.fileList); // 更新 antd 的 fileList
      if (info.file.status === 'done') {
        // onSuccess 已经在 customRequest 中处理了消息和列表刷新
      } else if (info.file.status === 'error') {
        // onError 已经在 customRequest 中处理了消息
        // message.error(`${info.file.name} 上传失败 (onChange)`);
      } else if (info.file.status === 'uploading') {
        // console.log('Uploading:', info.file, info.fileList);
      }
    },
    // progress: { // 自定义进度条样式 (可选)
    //   strokeColor: { '0%': '#108ee9', '100%': '#87d068' },
    //   strokeWidth: 3,
    //   format: percent => percent && `${parseFloat(percent.toFixed(2))}%`,
    // },
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>文件上传与管理 (DXF/PDF/DWG)</Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={10}>
          <Card title="上传文件">
            <Dragger {...uploadProps} style={{ marginBottom: '20px' }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个或批量上传。严格限制 .dxf, .pdf, .dwg 格式，大小不超过 {MAX_FILE_SIZE_MB}MB。
              </p>
            </Dragger>
            {/* <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />} loading={uploading}>
                {uploading ? '上传中...' : '选择文件'}
              </Button>
            </Upload> */}
          </Card>
        </Col>

        <Col xs={24} md={14}>
          <Card title="已上传文件列表">
            <List
              loading={loadingFiles}
              itemLayout="horizontal"
              dataSource={uploadedFiles}
              locale={{ emptyText: '暂无文件，请先上传。' }}
              renderItem={(item) => (
                <List.Item
                  key={item.id} // 后端返回的唯一ID
                  actions={[
                    <Tooltip title="下载">
                      <Button
                        type="link"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownloadFile(item.id, item.original_filename)}
                        // disabled={uploading} // 如果有全局uploading状态可以考虑
                      />
                    </Tooltip>,
                    // Add Import Knowledge Graph button for DXF files
                    ...(item.original_filename.toLowerCase().endsWith('.dxf') ? [
                      <Tooltip title="导入知识图谱" key={`import-${item.id}`}>
                        <Button
                          type="link"
                          icon={<CloudUploadOutlined />}
                          loading={importStatus === 'loading' && importingFileId === item.id}
                          disabled={importStatus === 'loading'} // Disable if any import is in progress
                          onClick={() => handleImportKnowledgeGraph(item.id, item.original_filename)}
                        />
                      </Tooltip>
                    ] : []),
                    /* 预览功能占位，当前 MVP 范围外
                    <Tooltip title="预览 (待实现)">
                      <Button type="link" icon={<EyeOutlined />} disabled />
                    </Tooltip>,
                    */
                    <Tooltip title="删除" key={`delete-${item.id}`}>
                      <Button
                        type="link"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeleteUploadedFile(item.id, item.original_filename)}
                      />
                    </Tooltip>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={getFileIcon(item.original_filename)}
                    title={<Text ellipsis={{ tooltip: item.original_filename }}>{item.original_filename}</Text>}
                    description={
                      <Space direction="vertical" size="small">
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          大小: {(item.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          上传时间: {new Date(item.uploaded_at).toLocaleString()}
                        </Text>
                        {/* Display import status for the specific file */}
                        {importingFileId === item.id && importStatus === 'success' && (
                          <Alert message={importMessage || "导入成功！"} type="success" showIcon style={{marginTop: '8px', fontSize: '12px', padding: '4px 8px'}} />
                        )}
                        {importingFileId === item.id && importStatus === 'error' && (
                          <Alert message={importMessage || "导入失败。"} type="error" showIcon style={{marginTop: '8px', fontSize: '12px', padding: '4px 8px'}}/>
                        )}
                        {/* <Text type="secondary" style={{fontSize: '12px'}}>ID: {item.id}</Text> */}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// Helper function to implement knowledge graph import
const handleImportKnowledgeGraph = async (fileId, fileName, setImportingFileId, setImportStatus, setImportMessage) => {
  setImportingFileId(fileId);
  setImportStatus('loading');
  setImportMessage(''); // Clear previous messages
  const key = `import-${fileId}`; // Unique key for Ant Design message
  message.loading({ content: `正在导入知识图谱: ${fileName}...`, key, duration: 0 });

  try {
    // Assuming the API endpoint is /api/v1/knowledge/import-dxf/{file_id}
    // and apiClient is already configured with baseURL
    const response = await apiClient.post(`/knowledge/import-dxf/${fileId}`);

    // Assuming backend returns a success message or relevant data
    // For example: { message: "Successfully imported knowledge from DXF file." }
    setImportStatus('success');
    const successMsg = response?.message || `文件 "${fileName}" 的知识图谱导入成功！`;
    setImportMessage(successMsg);
    message.success({ content: successMsg, key, duration: 5 });
    // Optionally, refresh related data or update UI further if needed
    // fetchUploadedFiles(); // Might not be necessary unless import changes file metadata shown

  } catch (error) {
    console.error(`导入知识图谱失败 (${fileName}):`, error);
    setImportStatus('error');
    const errorDetail = error.response?.data?.detail || error.message || '未知错误';
    const errorMsg = `文件 "${fileName}" 知识图谱导入失败: ${errorDetail}`;
    setImportMessage(errorMsg);
    message.error({ content: errorMsg, key, duration: 8 });
  } finally {
    // Keep importingFileId set to the last imported file to show status messages
    // setImportingFileId(null); // Or reset after a delay, or when user dismisses message
  }
};


export default FileUploadPage;
