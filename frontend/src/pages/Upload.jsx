import React, { useState, useRef } from 'react';
import { Typography, message, Alert, Button, Card, Space, Divider } from 'antd';
import { ReloadOutlined, CheckCircleOutlined, EditOutlined } from '@ant-design/icons';
import TextInput from '../components/upload/TextInput';
import PropertyForm from '../components/upload/PropertyForm';
import api from '../services/api';

const { Title, Text } = Typography;

const Upload = () => {
  const [parsedData, setParsedData] = useState(null);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [formModified, setFormModified] = useState(false);
  const [pastedImages, setPastedImages] = useState([]);
  const formRef = useRef();

  const handleParseResult = (result) => {
    setParsedData(result);
    setFormModified(false);
    
    message.success({
      content: `文本解析成功！置信度: ${(result.confidence * 100).toFixed(1)}%`,
      duration: 3,
    });

    // 滚动到表单区域
    setTimeout(() => {
      const formElement = document.querySelector('.property-form-container');
      if (formElement) {
        formElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  const handleParseError = (error) => {
    message.error(error);
    console.error('解析错误:', error);
  };

  const handleImagesPaste = (imageFiles) => {
    // 将粘贴的图片文件存储到状态中
    setPastedImages(prevImages => [...prevImages, ...imageFiles]);
    setFormModified(true);
  };

  const handleFieldChange = (fieldName, value) => {
    setFormModified(true);
    // console.log('Field changed:', fieldName, value); // 移除调试日志
  };

  const handleFormSubmit = async (values) => {
    setSubmitLoading(true);
    
    try {
      // 准备提交数据，包含图片信息
      const submitData = {
        ...values,
        // 如果有图片，提取图片路径
        image_paths: values.images ? values.images.map(img => img.url).filter(Boolean) : []
      };
      
      // 移除images字段，因为后端期望的是image_paths
      delete submitData.images;

      const response = await api.post('/properties', submitData);
      
      message.success({
        content: '房源信息保存成功！',
        duration: 3,
      });
      
      // 清空所有状态
      setParsedData(null);
      setFormModified(false);
      setPastedImages([]); // 清空粘贴的图片
      
      // 重置表单
      if (formRef.current) {
        formRef.current.resetFields();
      }
      
      console.log('保存成功:', response.data);
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || '保存失败，请重试';
      message.error(errorMessage);
      console.error('保存错误:', error);
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleReset = () => {
    setParsedData(null);
    setFormModified(false);
    setPastedImages([]);
    if (formRef.current) {
      formRef.current.resetFields();
    }
    message.info('表单已重置');
  };

  const getParsingQualityColor = (confidence) => {
    if (confidence >= 0.8) return '#52c41a'; // 绿色 - 高质量
    if (confidence >= 0.6) return '#faad14'; // 橙色 - 中等质量
    return '#ff4d4f'; // 红色 - 低质量
  };

  const getParsingQualityText = (confidence) => {
    if (confidence >= 0.8) return '解析质量：优秀';
    if (confidence >= 0.6) return '解析质量：良好';
    return '解析质量：需要检查';
  };

  return (
    <div className="container">
      <div className="page-header">
        <Title level={2}>房源上传</Title>
        <Text type="secondary">
          粘贴房源文本，AI智能解析后完善表单信息并保存
        </Text>
      </div>
      
      <TextInput 
        onParseResult={handleParseResult}
        onParseError={handleParseError}
        onImagesPaste={handleImagesPaste}
      />

      {parsedData && (
        <Card style={{ marginBottom: '24px' }}>
          <Alert
            message={
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <CheckCircleOutlined style={{ marginRight: '8px' }} />
                  解析完成
                </div>
                <div style={{ fontSize: '12px' }}>
                  <Text 
                    style={{ 
                      color: getParsingQualityColor(parsedData.confidence),
                      fontWeight: 'bold'
                    }}
                  >
                    {getParsingQualityText(parsedData.confidence)} ({(parsedData.confidence * 100).toFixed(1)}%)
                  </Text>
                </div>
              </div>
            }
            description={
              <div>
                <div style={{ marginBottom: '12px' }}>
                  AI已自动解析房源信息并填入下方表单。请仔细检查各字段内容，特别是房屋类型和价格信息。
                </div>
                
                {/* 解析结果摘要 */}
                <div style={{ 
                  padding: '12px', 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: '6px',
                  fontSize: '13px'
                }}>
                  <Space split={<Divider type="vertical" />} wrap>
                    <Text>
                      <strong>类型:</strong> {parsedData.property_type === 'rent' ? '🏠 租房' : '🏡 售房'}
                    </Text>
                    <Text>
                      <strong>小区:</strong> {parsedData.community_name || '未识别'}
                    </Text>
                    <Text>
                      <strong>价格:</strong> {parsedData.price ? 
                        `${parsedData.price} ${parsedData.property_type === 'rent' ? '元/月' : '万元'}` : 
                        '未识别'
                      }
                    </Text>
                    <Text>
                      <strong>房型:</strong> {parsedData.room_count || '未识别'}
                    </Text>
                  </Space>
                </div>

                {parsedData.confidence < 0.6 && (
                  <Alert
                    message="解析质量较低，请仔细检查表单内容"
                    type="warning"
                    showIcon
                    style={{ marginTop: '12px' }}
                  />
                )}
              </div>
            }
            type="success"
            showIcon
          />
        </Card>
      )}

      <div className="property-form-container">
        <PropertyForm
          ref={formRef}
          initialData={parsedData}
          onSubmit={handleFormSubmit}
          onFieldChange={handleFieldChange}
          loading={submitLoading}
          pastedImages={pastedImages}
        />
      </div>

      {/* 操作按钮 */}
      {parsedData && (
        <Card style={{ marginTop: '16px', textAlign: 'center' }}>
          <Space size="large">
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
              disabled={submitLoading}
            >
              重新开始
            </Button>
            
            {formModified && (
              <Alert
                message={
                  <span>
                    <EditOutlined style={{ marginRight: '4px' }} />
                    表单内容已修改
                  </span>
                }
                type="info"
                showIcon={false}
                style={{ 
                  display: 'inline-block', 
                  padding: '4px 12px',
                  margin: 0
                }}
              />
            )}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default Upload;