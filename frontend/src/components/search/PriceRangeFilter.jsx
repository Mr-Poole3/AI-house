import React, { useState, useEffect } from 'react';
import { InputNumber, Button, Space, Form, Row, Col, Typography } from 'antd';
import { FilterOutlined, ClearOutlined } from '@ant-design/icons';
import { PROPERTY_TYPES } from '../../utils/constants';

const { Text } = Typography;

/**
 * 价格范围筛选器组件
 * 根据房屋类型动态切换租金范围和售价范围
 */
const PriceRangeFilter = ({ 
  propertyType, 
  onPriceChange, 
  loading = false, 
  initialValues = {} 
}) => {
  const [form] = Form.useForm();
  const [priceRange, setPriceRange] = useState({
    minPrice: null,
    maxPrice: null,
    ...initialValues
  });

  // 根据房屋类型定义价格配置
  const getPriceConfig = (type) => {
    if (type === PROPERTY_TYPES.RENT) {
      return {
        label: '租金范围',
        unit: '元/月',
        minPlaceholder: '最低租金',
        maxPlaceholder: '最高租金',
        min: 0,
        max: 999999,
        step: 100,
        presets: [
          { label: '1000以下', min: null, max: 1000 },
          { label: '1000-2000', min: 1000, max: 2000 },
          { label: '2000-3000', min: 2000, max: 3000 },
          { label: '3000-5000', min: 3000, max: 5000 },
          { label: '5000-8000', min: 5000, max: 8000 },
          { label: '8000以上', min: 8000, max: null }
        ]
      };
    } else {
      return {
        label: '售价范围',
        unit: '万元',
        minPlaceholder: '最低售价',
        maxPlaceholder: '最高售价',
        min: 0,
        max: 99999,
        step: 10,
        presets: [
          { label: '100万以下', min: null, max: 100 },
          { label: '100-200万', min: 100, max: 200 },
          { label: '200-300万', min: 200, max: 300 },
          { label: '300-500万', min: 300, max: 500 },
          { label: '500-800万', min: 500, max: 800 },
          { label: '800万以上', min: 800, max: null }
        ]
      };
    }
  };

  const priceConfig = getPriceConfig(propertyType);

  // 当房屋类型或初始值变化时重置表单
  useEffect(() => {
    const newValues = {
      minPrice: null,
      maxPrice: null,
      ...initialValues
    };
    setPriceRange(newValues);
    form.setFieldsValue(newValues);
  }, [propertyType, initialValues, form]);

  /**
   * 处理价格变化
   */
  const handlePriceChange = (field, value) => {
    const newRange = {
      ...priceRange,
      [field]: value
    };
    setPriceRange(newRange);
  };

  /**
   * 应用价格筛选
   */
  const handleApplyFilter = () => {
    const values = form.getFieldsValue();
    // 过滤空值并验证范围
    const filteredValues = {};
    
    if (values.minPrice !== null && values.minPrice !== undefined) {
      filteredValues.minPrice = values.minPrice;
    }
    
    if (values.maxPrice !== null && values.maxPrice !== undefined) {
      filteredValues.maxPrice = values.maxPrice;
    }

    // 验证价格范围
    if (filteredValues.minPrice && filteredValues.maxPrice) {
      if (filteredValues.minPrice > filteredValues.maxPrice) {
        form.setFields([
          {
            name: 'maxPrice',
            errors: ['最高价格不能小于最低价格']
          }
        ]);
        return;
      }
    }

    onPriceChange(filteredValues);
  };

  /**
   * 清空价格筛选
   */
  const handleClearFilter = () => {
    const emptyValues = {
      minPrice: null,
      maxPrice: null
    };
    form.setFieldsValue(emptyValues);
    setPriceRange(emptyValues);
    onPriceChange({});
  };

  /**
   * 应用预设价格范围
   */
  const handlePresetClick = (preset) => {
    const newValues = {
      minPrice: preset.min,
      maxPrice: preset.max
    };
    form.setFieldsValue(newValues);
    setPriceRange(newValues);
    onPriceChange({
      ...(preset.min !== null && { minPrice: preset.min }),
      ...(preset.max !== null && { maxPrice: preset.max })
    });
  };

  return (
    <div className="price-range-filter">
      <Form
        form={form}
        layout="vertical"
        initialValues={priceRange}
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Text strong>{priceConfig.label} ({priceConfig.unit})</Text>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Form.Item
              name="minPrice"
              style={{ marginBottom: 8 }}
            >
              <InputNumber
                placeholder={priceConfig.minPlaceholder}
                min={priceConfig.min}
                max={priceConfig.max}
                step={priceConfig.step}
                style={{ width: '100%' }}
                onChange={(value) => handlePriceChange('minPrice', value)}
                disabled={loading}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Form.Item
              name="maxPrice"
              style={{ marginBottom: 8 }}
            >
              <InputNumber
                placeholder={priceConfig.maxPlaceholder}
                min={priceConfig.min}
                max={priceConfig.max}
                step={priceConfig.step}
                style={{ width: '100%' }}
                onChange={(value) => handlePriceChange('maxPrice', value)}
                disabled={loading}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={24} md={12}>
            <Space wrap>
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={handleApplyFilter}
                loading={loading}
              >
                应用筛选
              </Button>
              <Button
                icon={<ClearOutlined />}
                onClick={handleClearFilter}
                disabled={loading}
              >
                清空
              </Button>
            </Space>
          </Col>
        </Row>
        
        {/* 快速选择预设 */}
        <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
          <Col span={24}>
            <Text type="secondary" style={{ fontSize: '12px' }}>快速选择：</Text>
          </Col>
          {priceConfig.presets.map((preset, index) => (
            <Col key={index}>
              <Button
                size="small"
                type="text"
                onClick={() => handlePresetClick(preset)}
                disabled={loading}
                style={{ 
                  fontSize: '12px', 
                  height: '24px',
                  padding: '0 8px'
                }}
              >
                {preset.label}
              </Button>
            </Col>
          ))}
        </Row>
      </Form>
    </div>
  );
};

export default PriceRangeFilter;
