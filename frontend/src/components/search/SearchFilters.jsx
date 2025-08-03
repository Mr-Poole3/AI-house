import React, { useState, useEffect } from 'react';
import { Input, Button, Space, Form, Row, Col } from 'antd';
import { SearchOutlined, ClearOutlined } from '@ant-design/icons';

const { Search } = Input;

/**
 * 搜索筛选组件
 * 提供小区名和街道地址的搜索功能
 */
const SearchFilters = ({ onSearch, loading = false, initialValues = {} }) => {
  const [form] = Form.useForm();
  const [searchValues, setSearchValues] = useState({
    community: '',
    street: '',
    ...initialValues
  });

  // 当初始值变化时更新表单
  useEffect(() => {
    const newValues = {
      community: '',
      street: '',
      ...initialValues
    };
    setSearchValues(newValues);
    form.setFieldsValue(newValues);
  }, [initialValues, form]);

  /**
   * 处理搜索
   */
  const handleSearch = () => {
    const values = form.getFieldsValue();
    // 过滤空值
    const filteredValues = Object.keys(values).reduce((acc, key) => {
      if (values[key] && values[key].trim()) {
        acc[key] = values[key].trim();
      }
      return acc;
    }, {});
    
    setSearchValues(values);
    onSearch(filteredValues);
  };

  /**
   * 处理清空
   */
  const handleClear = () => {
    const emptyValues = {
      community: '',
      street: ''
    };
    form.setFieldsValue(emptyValues);
    setSearchValues(emptyValues);
    onSearch({});
  };

  /**
   * 处理回车搜索
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  /**
   * 处理输入变化
   */
  const handleInputChange = (field, value) => {
    setSearchValues(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="search-filters">
      <Form
        form={form}
        layout="vertical"
        initialValues={searchValues}
        style={{ marginBottom: 16 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Form.Item
              label="小区名称"
              name="community"
              style={{ marginBottom: 8 }}
            >
              <Search
                placeholder="请输入小区名称"
                allowClear
                onSearch={handleSearch}
                onChange={(e) => handleInputChange('community', e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12} md={8}>
            <Form.Item
              label="街道地址"
              name="street"
              style={{ marginBottom: 8 }}
            >
              <Search
                placeholder="请输入街道地址"
                allowClear
                onSearch={handleSearch}
                onChange={(e) => handleInputChange('street', e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={loading}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={24} md={8}>
            <Form.Item
              label=" "
              style={{ marginBottom: 8 }}
            >
              <Space>
                <Button
                  type="primary"
                  icon={<SearchOutlined />}
                  onClick={handleSearch}
                  loading={loading}
                >
                  搜索
                </Button>
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClear}
                  disabled={loading}
                >
                  清空
                </Button>
              </Space>
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </div>
  );
};

export default SearchFilters;
