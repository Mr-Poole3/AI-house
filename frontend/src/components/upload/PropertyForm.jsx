import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Radio, 
  Button, 
  Alert,
  Row,
  Col,
  Divider,
  Typography
} from 'antd';
import { 
  HomeOutlined, 
  DollarOutlined, 
  EnvironmentOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons';
import ImageUpload from './ImageUpload';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

// 价格配置（移除限制）
const priceConfig = {
  rent: {
    label: '月租金',
    suffix: '元/月',
    placeholder: '请输入月租金'
  },
  sale: {
    label: '售价',
    suffix: '万元',
    placeholder: '请输入售价'
  }
};

const PropertyForm = React.forwardRef(({ 
  initialData = null, 
  onSubmit, 
  onFieldChange,
  loading = false 
}, ref) => {
  const [form] = Form.useForm();
  
  // 暴露表单实例给父组件
  React.useImperativeHandle(ref, () => ({
    resetFields: () => {
      form.resetFields();
      setPropertyType('rent');
      setPriceError(null);
    },
    getFieldsValue: () => form.getFieldsValue(),
    setFieldsValue: (values) => form.setFieldsValue(values)
  }));
  const [propertyType, setPropertyType] = useState('rent');
  const [priceError, setPriceError] = useState(null);

  // 价格验证（仅检查是否为正数）
  const validatePrice = useCallback((price, type) => {
    if (price <= 0) {
      setPriceError(`${priceConfig[type].label}必须大于0`);
      return false;
    }
    setPriceError(null);
    return true;
  }, [setPriceError]);

  // 当初始数据变化时更新表单
  useEffect(() => {
    if (initialData) {
      const formData = {
        ...initialData,
        property_type: initialData.property_type || 'rent'
      };
      
      setPropertyType(formData.property_type);
      form.setFieldsValue(formData);
      
      // 验证价格范围
      if (formData.price) {
        validatePrice(formData.price, formData.property_type);
      }
    }
  }, [initialData, form, validatePrice]);

  // 处理房屋类型变化
  const handlePropertyTypeChange = (value) => {
    setPropertyType(value);
    setPriceError(null);
    
    // 重新验证价格
    const currentPrice = form.getFieldValue('price');
    if (currentPrice) {
      validatePrice(currentPrice, value);
    }

    if (onFieldChange) {
      onFieldChange('property_type', value);
    }
  };

  // 处理价格变化
  const handlePriceChange = (value) => {
    if (value) {
      validatePrice(value, propertyType);
    } else {
      setPriceError(null);
    }

    if (onFieldChange) {
      onFieldChange('price', value);
    }
  };

  // 处理表单提交
  const handleSubmit = async (values) => {
    // 最终价格验证
    if (values.price && !validatePrice(values.price, values.property_type)) {
      return;
    }

    if (onSubmit) {
      await onSubmit({
        ...values,
        property_type: propertyType
      });
    }
  };

  // 处理表单字段变化
  const handleFieldChange = (changedFields, allFields) => {
    changedFields.forEach(({ name, value }) => {
      if (onFieldChange && name && name.length > 0) {
        onFieldChange(name[0], value);
      }
    });
  };

  const currentPriceConfig = priceConfig[propertyType];

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <HomeOutlined />
          <span>房源信息表单</span>
        </div>
      }
      style={{ marginBottom: '24px' }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        onFieldsChange={handleFieldChange}
        initialValues={{
          property_type: 'rent'
        }}
      >
        {/* 房屋类型选择 - 置顶显示 */}
        <Card 
          size="small" 
          style={{ 
            marginBottom: '24px', 
            backgroundColor: '#f0f2f5',
            border: '2px solid #1890ff'
          }}
        >
          <Form.Item
            name="property_type"
            label={
              <Text strong style={{ fontSize: '16px' }}>
                <InfoCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                房屋类型
              </Text>
            }
            rules={[{ required: true, message: '请选择房屋类型' }]}
          >
            <Radio.Group 
              value={propertyType}
              onChange={(e) => handlePropertyTypeChange(e.target.value)}
              size="large"
            >
              <Radio.Button value="rent" style={{ minWidth: '120px', textAlign: 'center' }}>
                🏠 租房
              </Radio.Button>
              <Radio.Button value="sale" style={{ minWidth: '120px', textAlign: 'center' }}>
                🏡 售房
              </Radio.Button>
            </Radio.Group>
          </Form.Item>
        </Card>

        <Row gutter={16}>
          {/* 基本信息 */}
          <Col xs={24} md={12}>
            <Form.Item
              name="community_name"
              label="小区名称"
              rules={[
                { required: true, message: '请输入小区名称' },
                { max: 100, message: '小区名称不能超过100个字符' }
              ]}
            >
              <Input 
                prefix={<EnvironmentOutlined />}
                placeholder="请输入小区名称" 
              />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item
              name="street_address"
              label="街道地址"
              rules={[
                { required: true, message: '请输入街道地址' },
                { max: 200, message: '街道地址不能超过200个字符' }
              ]}
            >
              <Input 
                prefix={<EnvironmentOutlined />}
                placeholder="请输入详细街道地址" 
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col xs={24} md={8}>
            <Form.Item
              name="floor_info"
              label="楼层信息"
              rules={[{ max: 50, message: '楼层信息不能超过50个字符' }]}
            >
              <Input placeholder="如：6/18层" />
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item
              name="room_count"
              label="房间配置"
              rules={[{ max: 20, message: '房间配置不能超过20个字符' }]}
            >
              <Input placeholder="如：2室1厅1卫" />
            </Form.Item>
          </Col>

          <Col xs={24} md={8}>
            <Form.Item
              name="area"
              label="建筑面积"
              rules={[
                { type: 'number', min: 10, max: 1000, message: '面积应在10-1000平米之间' }
              ]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="请输入面积"
                suffix="平米"
                min={10}
                max={1000}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* 价格信息 - 动态标签和验证 */}
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Form.Item
              name="price"
              label={
                <span>
                  <DollarOutlined style={{ marginRight: '4px' }} />
                  {currentPriceConfig.label}
                </span>
              }
              rules={[
                { required: true, message: `请输入${currentPriceConfig.label}` },
                { type: 'number', min: 0.01, message: `${currentPriceConfig.label}必须大于0` }
              ]}
              validateStatus={priceError ? 'error' : ''}
              help={priceError}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder={currentPriceConfig.placeholder}
                suffix={currentPriceConfig.suffix}
                min={currentPriceConfig.min}
                max={currentPriceConfig.max}
                onChange={handlePriceChange}
              />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item
              name="decoration_status"
              label="装修情况"
              rules={[{ max: 100, message: '装修情况不能超过100个字符' }]}
            >
              <Select placeholder="请选择装修情况" allowClear>
                <Option value="毛坯">毛坯</Option>
                <Option value="简装">简装</Option>
                <Option value="精装">精装</Option>
                <Option value="豪装">豪装</Option>
                <Option value="其他">其他</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        {/* 详细描述 */}
        <Form.Item
          name="furniture_appliances"
          label="家具家电配置"
          rules={[{ max: 500, message: '家具家电配置不能超过500个字符' }]}
        >
          <TextArea
            rows={3}
            placeholder="请描述家具家电配置情况，如：全套家具、空调、洗衣机、冰箱等"
          />
        </Form.Item>

        <Form.Item
          name="description"
          label="补充说明"
          rules={[{ max: 1000, message: '补充说明不能超过1000个字符' }]}
        >
          <TextArea
            rows={4}
            placeholder="其他补充说明信息..."
          />
        </Form.Item>

        {/* 图片上传 */}
        <Form.Item
          name="images"
          label="房源图片"
          rules={[
            { 
              validator: (_, value) => {
                if (!value || value.length === 0) {
                  return Promise.reject(new Error('请至少上传一张房源图片'));
                }
                return Promise.resolve();
              }
            }
          ]}
        >
          <ImageUpload 
            maxCount={10}
            disabled={loading}
          />
        </Form.Item>

        <Divider />

        {/* 提交按钮 */}
        <Form.Item>
          <div style={{ textAlign: 'center' }}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={loading}
              disabled={!!priceError}
              style={{ minWidth: '120px' }}
            >
              {loading ? '保存中...' : '保存房源'}
            </Button>
          </div>
        </Form.Item>
      </Form>

      {/* 价格提示 */}
      <Alert
        message={`${currentPriceConfig.label}提示`}
        description={`请输入真实的${currentPriceConfig.label}，系统不限制价格范围`}
        type="info"
        showIcon
        style={{ marginTop: '16px' }}
      />
    </Card>
  );
});

PropertyForm.displayName = 'PropertyForm';

export default PropertyForm;