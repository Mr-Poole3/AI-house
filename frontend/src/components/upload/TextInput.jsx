import React, { useState } from 'react';
import { Card, Input, Button, Alert, Spin } from 'antd';
import { FileTextOutlined, ThunderboltOutlined } from '@ant-design/icons';
import api from '../../services/api';

const { TextArea } = Input;

const TextInput = ({ onParseResult, onParseError }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTextChange = (e) => {
    setText(e.target.value);
    if (error) {
      setError(null);
    }
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
        </div>
      }
      style={{ marginBottom: '24px' }}
    >
      <div style={{ marginBottom: '16px' }}>
        <TextArea
          value={text}
          onChange={handleTextChange}
          placeholder="请粘贴从微信等渠道获取的房源描述文本..."
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