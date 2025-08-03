import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  Card, 
  Button, 
  Image, 
  Progress, 
  Alert, 
  Modal, 
  Row, 
  Col,
  Typography,
  message
} from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  PictureOutlined
} from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

const ImageUpload = ({ 
  value = [], 
  onChange, 
  maxCount = 10,
  disabled = false 
}) => {
  const [fileList, setFileList] = useState(value || []);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  // 处理文件上传前的验证
  const beforeUpload = (file) => {
    const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
    if (!isJpgOrPng) {
      message.error('只能上传 JPG/PNG 格式的图片!');
      return false;
    }
    
    const isLt5M = file.size / 1024 / 1024 < 5;
    if (!isLt5M) {
      message.error('图片大小不能超过 5MB!');
      return false;
    }

    if (fileList.length >= maxCount) {
      message.error(`最多只能上传 ${maxCount} 张图片!`);
      return false;
    }

    return true;
  };

  // 自定义上传处理
  const customUpload = useCallback(async ({ file, onProgress, onSuccess, onError }) => {
    const formData = new FormData();
    formData.append('files', file);

    try {
      setUploading(true);
      setUploadProgress(prev => ({ ...prev, [file.uid]: 0 }));

      const response = await api.post('/upload/images', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(prev => ({ ...prev, [file.uid]: percent }));
          onProgress({ percent });
        },
      });

      const { uploaded_files } = response.data;
      if (uploaded_files && uploaded_files.length > 0) {
        const uploadedFile = {
          uid: file.uid,
          name: file.name,
          status: 'done',
          url: uploaded_files[0], // 服务器返回的文件路径
          response: response.data,
        };

        setFileList(prev => {
          const newList = [...prev, uploadedFile];
          if (onChange) {
            onChange(newList);
          }
          return newList;
        });

        onSuccess(response.data, file);
        message.success(`${file.name} 上传成功`);
      }
    } catch (error) {
      console.error('上传失败:', error);
      const errorMessage = error.response?.data?.error?.message || '上传失败';
      message.error(`${file.name} 上传失败: ${errorMessage}`);
      onError(error);
    } finally {
      setUploading(false);
      setUploadProgress(prev => {
        const newProgress = { ...prev };
        delete newProgress[file.uid];
        return newProgress;
      });
    }
  }, [onChange]);

  // 处理文件删除
  const handleRemove = (file) => {
    const newFileList = fileList.filter(item => item.uid !== file.uid);
    setFileList(newFileList);
    
    if (onChange) {
      onChange(newFileList);
    }

    // 如果文件已上传到服务器，调用删除API
    if (file.status === 'done' && file.url) {
      const filename = file.url.split('/').pop();
      api.delete(`/upload/images/${filename}`)
        .catch(error => {
          console.error('删除服务器文件失败:', error);
        });
    }

    message.success(`${file.name} 已删除`);
  };

  // 处理预览
  const handlePreview = async (file) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj);
    }

    setPreviewImage(file.url || file.preview);
    setPreviewVisible(true);
    setPreviewTitle(file.name || file.url.substring(file.url.lastIndexOf('/') + 1));
  };

  // 获取文件的base64编码用于预览
  const getBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onError = error => reject(error);
    });
  };

  // 上传按钮
  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传图片</div>
    </div>
  );

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PictureOutlined />
          <span>房源图片</span>
          <Text type="secondary" style={{ fontSize: '12px', fontWeight: 'normal' }}>
            ({fileList.length}/{maxCount})
          </Text>
        </div>
      }
      style={{ marginBottom: '24px' }}
    >
      {/* 上传提示 */}
      <Alert
        message="图片上传说明"
        description="支持 JPG、PNG 格式，单张图片不超过 5MB，最多上传 10 张图片"
        type="info"
        showIcon
        style={{ marginBottom: '16px' }}
      />

      {/* 上传区域 */}
      <Upload
        customRequest={customUpload}
        listType="picture-card"
        fileList={fileList}
        onPreview={handlePreview}
        onRemove={handleRemove}
        beforeUpload={beforeUpload}
        disabled={disabled || uploading || fileList.length >= maxCount}
        multiple
        accept="image/jpeg,image/png"
      >
        {fileList.length >= maxCount ? null : uploadButton}
      </Upload>

      {/* 上传进度显示 */}
      {Object.keys(uploadProgress).length > 0 && (
        <div style={{ marginTop: '16px' }}>
          {Object.entries(uploadProgress).map(([uid, percent]) => {
            const file = fileList.find(f => f.uid === uid);
            return (
              <div key={uid} style={{ marginBottom: '8px' }}>
                <Text style={{ fontSize: '12px' }}>
                  正在上传: {file?.name || '未知文件'}
                </Text>
                <Progress percent={percent} size="small" />
              </div>
            );
          })}
        </div>
      )}

      {/* 批量操作按钮 */}
      {fileList.length > 0 && (
        <div style={{ marginTop: '16px', textAlign: 'center' }}>
          <Button
            icon={<DeleteOutlined />}
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: '确定要删除所有图片吗？',
                onOk: () => {
                  // 删除服务器文件
                  fileList.forEach(file => {
                    if (file.status === 'done' && file.url) {
                      const filename = file.url.split('/').pop();
                      api.delete(`/upload/images/${filename}`)
                        .catch(error => {
                          console.error('删除服务器文件失败:', error);
                        });
                    }
                  });
                  
                  setFileList([]);
                  if (onChange) {
                    onChange([]);
                  }
                  message.success('所有图片已删除');
                }
              });
            }}
            disabled={disabled || uploading}
          >
            清空所有图片
          </Button>
        </div>
      )}

      {/* 图片预览模态框 */}
      <Modal
        open={previewVisible}
        title={previewTitle}
        footer={null}
        onCancel={() => setPreviewVisible(false)}
        width={800}
      >
        <Image
          alt="预览"
          style={{ width: '100%' }}
          src={previewImage}
        />
      </Modal>

      {/* 图片列表概览 */}
      {fileList.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <Text strong>已上传图片:</Text>
          <Row gutter={[8, 8]} style={{ marginTop: '8px' }}>
            {fileList.map((file, index) => (
              <Col key={file.uid} span={6}>
                <div style={{ 
                  padding: '4px', 
                  border: '1px solid #d9d9d9', 
                  borderRadius: '4px',
                  textAlign: 'center',
                  fontSize: '12px'
                }}>
                  <div style={{ marginBottom: '4px' }}>
                    图片 {index + 1}
                  </div>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    gap: '4px' 
                  }}>
                    <Button 
                      size="small" 
                      icon={<EyeOutlined />}
                      onClick={() => handlePreview(file)}
                    />
                    <Button 
                      size="small" 
                      icon={<DeleteOutlined />}
                      danger
                      onClick={() => handleRemove(file)}
                      disabled={disabled || uploading}
                    />
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      )}
    </Card>
  );
};

export default ImageUpload;