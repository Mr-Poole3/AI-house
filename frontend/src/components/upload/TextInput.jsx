import React, { useState } from 'react';
import { Card, Input, Button, Alert, Spin, message } from 'antd';
import { FileTextOutlined, ThunderboltOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { TextArea } = Input;

const TextInput = ({ onParseResult, onParseError, onImagesPaste }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTextChange = (e) => {
    setText(e.target.value);
    if (error) {
      setError(null);
    }
  };

  const handlePaste = (e) => {
    // 获取粘贴板数据
    const clipboardData = e.clipboardData || window.clipboardData;
    const textData = clipboardData.getData('text/plain');
    
    const imageFiles = [];
    const processedFiles = new Set(); // 用于去重
    
    // 优先使用clipboardData.files（更直接）
    if (clipboardData.files && clipboardData.files.length > 0) {
      const files = Array.from(clipboardData.files);
      files.forEach(file => {
        if (file.type.startsWith('image/') && 
            (file.type === 'image/jpeg' || file.type === 'image/png')) {
          const fileKey = `${file.name}-${file.size}-${file.type}`;
          if (!processedFiles.has(fileKey)) {
            imageFiles.push(file);
            processedFiles.add(fileKey);
          }
        }
      });
    }
    
    // 如果files为空，再检查items
    if (imageFiles.length === 0 && clipboardData.items && clipboardData.items.length > 0) {
      for (let i = 0; i < clipboardData.items.length; i++) {
        const item = clipboardData.items[i];
        
        if (item.type.startsWith('image/') && item.kind === 'file') {
          const file = item.getAsFile();
          if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
            const fileKey = `${file.name}-${file.size}-${file.type}`;
            if (!processedFiles.has(fileKey)) {
              imageFiles.push(file);
              processedFiles.add(fileKey);
            }
          }
        }
      }
    }

    // 如果有图片文件，通过回调传递给父组件
    if (imageFiles.length > 0 && onImagesPaste) {
      onImagesPaste(imageFiles);
      
      // 显示提示信息
      message.success(`检测到 ${imageFiles.length} 张图片，已自动添加到图片上传区域`);
    } else {
      // 如果没有检测到图片文件，但文本中包含图片标记，给出提示
      if (textData && textData.includes('[图片')) {
        message.info('检测到图片标记，但未能获取到图片文件。请尝试直接复制图片或使用其他方式上传。');
      }
    }

    // 文字内容正常处理（让默认行为继续）
    // 这里不需要阻止默认行为，让文字正常粘贴到文本框
  };

  const handleParse = async () => {
    if (!text.trim()) {
      setError('请输入房源描述文本');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/properties/parse', {
        text: text.trim()
      });

      const { parsed_data, success, message } = response.data;

      if (!success) {
        throw new Error(message || '解析失败');
      }

      // 调用父组件的回调函数传递解析结果
      if (onParseResult) {
        onParseResult({
          ...parsed_data,
          original_text: text.trim()
        });
      }

    } catch (err) {
      const errorMessage = err.response?.data?.error?.message || '文本解析失败，请重试';
      setError(errorMessage);
      
      if (onParseError) {
        onParseError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setText('');
    setError(null);
  };

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileTextOutlined />
          <span>房源文本输入</span>
          <span style={{ fontSize: '12px', color: '#999', fontWeight: 'normal' }}>
            （支持图文混合粘贴）
          </span>
        </div>
      }
      style={{ marginBottom: '24px' }}
    >
      <div style={{ marginBottom: '16px' }}>
        <TextArea
          value={text}
          onChange={handleTextChange}
          onPaste={handlePaste}
          placeholder="请粘贴从微信等渠道获取的房源描述文本（支持图文混合粘贴）..."
          rows={6}
          disabled={loading}
          style={{ fontSize: '14px' }}
        />
      </div>

      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
        <Button 
          onClick={handleClear}
          disabled={loading || !text.trim()}
        >
          清空
        </Button>
        <Button
          type="primary"
          icon={<ThunderboltOutlined />}
          onClick={handleParse}
          loading={loading}
          disabled={!text.trim()}
        >
          {loading ? '解析中...' : '智能解析'}
        </Button>
      </div>

      {loading && (
        <div style={{ 
          marginTop: '16px', 
          textAlign: 'center',
          padding: '20px',
          backgroundColor: '#f5f5f5',
          borderRadius: '6px'
        }}>
          <Spin size="large" />
          <div style={{ marginTop: '12px', color: '#666' }}>
            正在使用AI智能解析房源信息，请稍候...
          </div>
        </div>
      )}
    </Card>
  );
};

export default TextInput;