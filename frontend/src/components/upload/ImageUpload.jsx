import React, { useState, useCallback, useEffect, useRef } from 'react';
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
  message,
  Space
} from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  PictureOutlined,
  InboxOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import api from '../../services/api';

const { Text } = Typography;

const ImageUpload = ({ 
  value = [], 
  onChange, 
  maxCount = 10,
  disabled = false,
  pastedImages = []
}) => {
  const [fileList, setFileList] = useState(value || []);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [pasteReady, setPasteReady] = useState(false);
  const containerRef = useRef(null);

  // 同步外部 value 和内部 fileList 状态
  useEffect(() => {
    // 确保value是数组
    const normalizedValue = Array.isArray(value) ? value : [];
    
    // 检查是否需要更新fileList
    const needsUpdate = JSON.stringify(normalizedValue) !== JSON.stringify(fileList);
    
    if (needsUpdate) {
      setFileList(normalizedValue);
    }
  }, [value, fileList]); // 监听value和fileList的变化

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
          url: uploaded_files[0].url, // 正确获取服务器返回的URL
          response: response.data,
        };

        setFileList(prev => [...prev, uploadedFile]);

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

  // 监听 fileList 变化并调用 onChange
  useEffect(() => {
    if (onChange) {
      onChange(fileList);
    }
  }, [fileList, onChange]);

  // 处理文件删除
  const handleRemove = (file) => {
    const newFileList = fileList.filter(item => item.uid !== file.uid);
    setFileList(newFileList);

    // 如果文件已上传到服务器，调用删除API
    if (file.status === 'done' && file.url && typeof file.url === 'string') {
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
    setPreviewTitle(file.name || (typeof file.url === 'string' ? file.url.substring(file.url.lastIndexOf('/') + 1) : '未知文件'));
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

  // 处理粘贴事件
  const handlePaste = useCallback((event) => {
    // 检查是否禁用或已达到最大数量
    if (disabled || uploading || fileList.length >= maxCount) {
      return;
    }

    const clipboardData = event.clipboardData || window.clipboardData;
    const items = clipboardData.items;
    
    if (!items) return;

    const imageFiles = [];
    
    // 遍历粘贴板内容，找出图片文件
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      // 检查是否为图片类型
      if (item.type.indexOf('image/') === 0) {
        const file = item.getAsFile();
        if (file) {
          // 验证文件格式
          const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
          const isLt5M = file.size / 1024 / 1024 < 5;
          
          if (isJpgOrPng && isLt5M) {
            imageFiles.push(file);
          } else if (!isJpgOrPng) {
            message.warning(`粘贴的图片格式不支持：${file.type}，仅支持 JPG/PNG`);
          } else if (!isLt5M) {
            message.warning(`粘贴的图片过大：${(file.size / 1024 / 1024).toFixed(1)}MB，限制 5MB`);
          }
        }
      }
    }

    // 检查数量限制
    if (imageFiles.length > 0) {
      const totalAfterPaste = fileList.length + imageFiles.length;
      if (totalAfterPaste > maxCount) {
        const allowedCount = maxCount - fileList.length;
        message.warning(`最多只能上传 ${maxCount} 张图片，当前已有 ${fileList.length} 张，只能再粘贴 ${allowedCount} 张`);
        imageFiles.splice(allowedCount); // 只保留允许的数量
      }

      // 处理粘贴的图片文件
      imageFiles.forEach((file, index) => {
        // 生成唯一ID，包含索引确保唯一性
        const uid = `paste-${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`;
        const fileWithUid = Object.assign(file, { uid });
        
        // 调用上传处理
        customUpload({
          file: fileWithUid,
          onProgress: ({ percent }) => {
            setUploadProgress(prev => ({ ...prev, [uid]: percent }));
          },
          onSuccess: (response) => {
            message.success(`粘贴的图片上传成功: ${file.name || '未知文件名'}`);
          },
          onError: (error) => {
            message.error(`粘贴的图片上传失败: ${error.message || '未知错误'}`);
          }
        });
      });

      if (imageFiles.length > 0) {
        message.success(`检测到 ${imageFiles.length} 张粘贴的图片，正在上传...`);
      }
    }
  }, [disabled, uploading, fileList.length, maxCount, customUpload]);

  // 处理容器聚焦状态
  const handleContainerFocus = useCallback(() => {
    setPasteReady(true);
  }, []);

  const handleContainerBlur = useCallback(() => {
    setPasteReady(false);
  }, []);

  // 添加全局粘贴事件监听
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('paste', handlePaste);
    container.addEventListener('focus', handleContainerFocus);
    container.addEventListener('blur', handleContainerBlur);
    
    // 设置容器可聚焦
    container.tabIndex = 0;
    container.style.outline = 'none';

    return () => {
      container.removeEventListener('paste', handlePaste);
      container.removeEventListener('focus', handleContainerFocus);
      container.removeEventListener('blur', handleContainerBlur);
    };
  }, [handlePaste, handleContainerFocus, handleContainerBlur]);

  // 处理从文本框粘贴过来的图片
  const processedPastedRef = useRef(new Set());
  
  useEffect(() => {
    if (pastedImages.length > 0) {
      // 过滤掉已经处理过的图片
      const newImages = pastedImages.filter(file => {
        const fileKey = `${file.name}-${file.size}-${file.lastModified || file.type}`;
        if (processedPastedRef.current.has(fileKey)) {
          return false;
        }
        processedPastedRef.current.add(fileKey);
        return true;
      });

      if (newImages.length === 0) return;

      // 检查是否超出数量限制
      const totalAfterPaste = fileList.length + newImages.length;
      if (totalAfterPaste > maxCount) {
        const allowedCount = maxCount - fileList.length;
        message.warning(`最多只能上传 ${maxCount} 张图片，当前已有 ${fileList.length} 张，只能处理 ${allowedCount} 张粘贴图片`);
        newImages.splice(allowedCount); // 只保留允许的数量
      }

      // 自动上传粘贴的图片
      newImages.forEach((file, index) => {
        // 生成唯一ID
        const uid = `text-paste-${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`;
        const fileWithUid = Object.assign(file, { uid });
        
        // 调用上传处理
        customUpload({
          file: fileWithUid,
          onProgress: ({ percent }) => {
            setUploadProgress(prev => ({ ...prev, [uid]: percent }));
          },
          onSuccess: (response) => {
            // 不显示成功消息，避免过多提示
          },
          onError: (error) => {
            message.error(`图片上传失败: ${error.message || '未知错误'}`);
          }
        });
      });
    }
  }, [pastedImages]);

  // 上传按钮
  const uploadButton = (
    <div>
      <PlusOutlined />
      <div style={{ marginTop: 8 }}>上传图片</div>
    </div>
  );

  return (
    <Card 
      ref={containerRef}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PictureOutlined />
          <span>房源图片（可选）</span>
          <Text type="secondary" style={{ fontSize: '12px', fontWeight: 'normal' }}>
            ({fileList.length}/{maxCount})
          </Text>
          {pasteReady && (
            <Text type="secondary" style={{ fontSize: '12px', color: '#1890ff' }}>
              [可粘贴]
            </Text>
          )}
        </div>
      }
      style={{ 
        marginBottom: '24px',
        border: pasteReady ? '2px solid #1890ff' : undefined,
        transition: 'border 0.3s ease'
      }}
    >
      {/* 上传提示 */}
      <Alert
        message="图片上传说明（可选）"
        description="您可以选择上传房源图片，也可以跳过此步骤。支持：① 点击选择文件 ② 拖拽图片到区域 ③ 复制图片后粘贴（Ctrl+V） ④ 在文本框中图文混合粘贴。格式：JPG、PNG，单张不超过 5MB，最多 10 张图片"
        type="info"
        showIcon
        style={{ marginBottom: '16px' }}
      />

      {/* 拖拽上传区域 */}
      <div style={{ marginBottom: '20px' }}>
        <Upload.Dragger
          name="files"
          multiple
          accept="image/jpeg,image/png"
          customRequest={customUpload}
          beforeUpload={beforeUpload}
          disabled={disabled || uploading || fileList.length >= maxCount}
          showUploadList={false}
          onDrop={(e) => {
            setDragOver(false);
            const files = Array.from(e.dataTransfer.files);
            const validFiles = files.filter(file => {
              const isImage = file.type === 'image/jpeg' || file.type === 'image/png';
              const isSizeValid = file.size / 1024 / 1024 < 5;
              return isImage && isSizeValid;
            });
            
            if (validFiles.length !== files.length) {
              message.warning('部分文件格式不正确或超过大小限制，仅处理有效图片');
            }
            
            if (fileList.length + validFiles.length > maxCount) {
              message.warning(`最多只能上传 ${maxCount} 张图片，当前已有 ${fileList.length} 张`);
            }
          }}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            // 只有当离开的是拖拽区域本身时才取消高亮
            if (!e.currentTarget.contains(e.relatedTarget)) {
              setDragOver(false);
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          style={{
            backgroundColor: dragOver ? '#f0f8ff' : '#fafafa',
            border: dragOver ? '2px dashed #1890ff' : '2px dashed #d9d9d9',
            borderRadius: '8px',
            transition: 'all 0.3s ease'
          }}
        >
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <p className="ant-upload-drag-icon">
              {dragOver ? (
                <CloudUploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              ) : pasteReady ? (
                <InboxOutlined style={{ 
                  fontSize: '48px', 
                  color: '#1890ff'
                }} />
              ) : (
                <InboxOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
              )}
            </p>
            <p className="ant-upload-text" style={{ 
              fontSize: '16px', 
              marginBottom: '8px',
              color: dragOver ? '#1890ff' : pasteReady ? '#1890ff' : '#333',
              fontWeight: dragOver || pasteReady ? 'bold' : 'normal'
            }}>
              {dragOver ? (
                '松开鼠标即可上传'
              ) : pasteReady ? (
                '按 Ctrl+V 粘贴图片'
              ) : (
                '点击、拖拽或粘贴图片到此区域上传（可选）'
              )}
            </p>
            <p className="ant-upload-hint" style={{ 
              color: dragOver || pasteReady ? '#1890ff' : '#999', 
              fontSize: '14px' 
            }}>
              {dragOver ? (
                '支持 JPG、PNG 格式'
              ) : pasteReady ? (
                '支持复制粘贴上传，快速便捷'
              ) : (
                `支持多种上传方式。最多 ${maxCount} 张，每张不超过 5MB`
              )}
            </p>
            {fileList.length >= maxCount && (
              <p style={{ color: '#ff4d4f', fontSize: '14px', marginTop: '8px' }}>
                已达到最大上传数量
              </p>
            )}
            {uploading && (
              <p style={{ color: '#1890ff', fontSize: '14px', marginTop: '8px' }}>
                正在上传中...
              </p>
            )}
            {!uploading && !dragOver && fileList.length === 0 && (
              <p style={{ color: '#999', fontSize: '12px', marginTop: '12px' }}>
                💡 小贴士：您可以在任何地方复制图片，然后点击此区域并按 Ctrl+V 快速粘贴上传
              </p>
            )}
          </div>
        </Upload.Dragger>
      </div>

      {/* 已上传图片展示区域 */}
      {fileList.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <Text strong style={{ marginBottom: '12px', display: 'block' }}>
            已上传图片 ({fileList.length}/{maxCount})
          </Text>
          <Upload
            customRequest={customUpload}
            listType="picture-card"
            fileList={fileList}
            onPreview={handlePreview}
            onRemove={handleRemove}
            beforeUpload={beforeUpload}
            disabled={disabled || uploading}
            multiple
            accept="image/jpeg,image/png"
            showUploadList={{
              showPreviewIcon: true,
              showRemoveIcon: true,
              showDownloadIcon: false,
            }}
          >
            {fileList.length >= maxCount ? null : uploadButton}
          </Upload>
        </div>
      )}

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
        <div style={{ marginTop: '20px', textAlign: 'center' }}>
          <Button
            type="default"
            icon={<DeleteOutlined />}
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: '确定要删除所有图片吗？',
                onOk: () => {
                  // 删除服务器文件
                  fileList.forEach(file => {
                    if (file.status === 'done' && file.url && typeof file.url === 'string') {
                      const filename = file.url.split('/').pop();
                      api.delete(`/upload/images/${filename}`)
                        .catch(error => {
                          console.error('删除服务器文件失败:', error);
                        });
                    }
                  });
                  
                  setFileList([]);
                  message.success('所有图片已删除');
                }
              });
            }}
            disabled={disabled || uploading}
            style={{ 
              borderRadius: '6px',
              minWidth: '120px'
            }}
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


    </Card>
  );
};

export default ImageUpload;