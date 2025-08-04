import React, { useState, useEffect } from 'react';
import { 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Button, 
  Space, 
  message, 
  Row, 
  Col,
  Card
} from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { PROPERTY_TYPES } from '../../utils/constants';
import propertyApiService from '../../services/propertyApi';
import { safeFormValue } from '../../utils/displayUtils';

const { TextArea } = Input;
const { Option } = Select;

/**
 * 房源编辑表单组件
 */
const PropertyEditForm = ({ property, onSave, onCancel, loading = false }) => {
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  // 初始化表单数据
  useEffect(() => {
    if (property) {
      form.setFieldsValue({
        community_name: property.community_name,
        street_address: property.street_address,
        floor_info: property.floor_info,
        price: property.price,
        property_type: property.property_type,
        contact_phone: safeFormValue(property.contact_phone), // 安全处理null值
        furniture_appliances: property.furniture_appliances,
        decoration_status: property.decoration_status,
        room_count: property.room_count,
        area: property.area,
        other_info: property.other_info,
        description: property.description
      });
    }
  }, [property, form]);

  /**
   * 处理表单提交
   */
  const handleSubmit = async (values) => {
    try {
      setSaving(true);
      
      // 调用API更新房源
      const updatedProperty = await propertyApiService.updateProperty(property.id, values);
      
      message.success('房源信息更新成功');
      onSave(updatedProperty);
      
    } catch (error) {
      console.error('更新房源失败:', error);
      message.error('更新房源失败，请稍后重试');
    } finally {
      setSaving(false);
    }
  };

  /**
   * 处理表单验证失败
   */
  const handleSubmitFailed = (errorInfo) => {
    console.log('表单验证失败:', errorInfo);
    message.error('请检查表单信息是否完整');
  };

  /**
   * 获取价格标签和验证规则
   */
  const getPriceConfig = (propertyType) => {
    if (propertyType === PROPERTY_TYPES.RENT) {
      return {
        label: '月租金',
        suffix: '元/月',
        min: 500,
        max: 20000,
        placeholder: '请输入月租金'
      };
    } else {
      return {
        label: '售价',
        suffix: '万元',
        min: 30,
        max: 2000,
        placeholder: '请输入售价'
      };
    }
  };

  const propertyType = Form.useWatch('property_type', form);
  const priceConfig = getPriceConfig(propertyType);

  return (
    <Card title="编辑房源信息">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        onFinishFailed={handleSubmitFailed}
        disabled={loading || saving}
      >
        <Row gutter={[16, 16]}>
          {/* 基本信息 */}
          <Col span={24}>
            <h4>基本信息</h4>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="小区名称"
              name="community_name"
              rules={[
                { required: true, message: '请输入小区名称' },
                { max: 100, message: '小区名称不能超过100个字符' }
              ]}
            >
              <Input placeholder="请输入小区名称" />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="街道地址"
              name="street_address"
              rules={[
                { required: true, message: '请输入街道地址' },
                { max: 200, message: '街道地址不能超过200个字符' }
              ]}
            >
              <Input placeholder="请输入街道地址" />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="房屋类型"
              name="property_type"
              rules={[{ required: true, message: '请选择房屋类型' }]}
            >
              <Select placeholder="请选择房屋类型">
                <Option value={PROPERTY_TYPES.RENT}>租房</Option>
                <Option value={PROPERTY_TYPES.SALE}>售房</Option>
              </Select>
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label={priceConfig.label}
              name="price"
              rules={[
                { required: true, message: `请输入${priceConfig.label}` },
                {
                  type: 'number',
                  min: 0.01,
                  message: `${priceConfig.label}必须大于0`
                }
              ]}
            >
              <InputNumber
                placeholder={priceConfig.placeholder}
                suffix={priceConfig.suffix}
                style={{ width: '100%' }}
                min={0.01}
                precision={2}
              />
            </Form.Item>
          </Col>
          
          {/* 详细信息 */}
          <Col span={24}>
            <h4>详细信息</h4>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="楼层信息"
              name="floor_info"
              rules={[{ max: 50, message: '楼层信息不能超过50个字符' }]}
            >
              <Input placeholder="如：3楼/共6楼" />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="房间数量"
              name="room_count"
              rules={[{ max: 20, message: '房间数量不能超过20个字符' }]}
            >
              <Input placeholder="如：2室1厅1卫" />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="面积"
              name="area"
              rules={[
                { type: 'number', min: 1, max: 1000, message: '面积应在1-1000平米范围内' }
              ]}
            >
              <InputNumber
                placeholder="请输入面积"
                suffix="平米"
                style={{ width: '100%' }}
                min={1}
                max={1000}
                precision={2}
              />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="装修情况"
              name="decoration_status"
              rules={[{ max: 100, message: '装修情况不能超过100个字符' }]}
            >
              <Input placeholder="如：精装修、简装、毛坯" />
            </Form.Item>
          </Col>
          
          <Col xs={24} sm={12}>
            <Form.Item
              label="联系电话"
              name="contact_phone"
              rules={[
                { max: 20, message: '电话号码不能超过20个字符' },
                {
                  validator: (_, value) => {
                    if (!value || value.trim() === '') {
                      return Promise.resolve(); // 允许空值
                    }
                    const phonePattern = /^1[3-9]\d{9}$|^0\d{2,3}[-\s]?\d{7,8}$|^\d{7,8}$/;
                    if (phonePattern.test(value.trim())) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('请输入有效的电话号码'));
                  }
                }
              ]}
            >
              <Input placeholder="请输入联系电话" />
            </Form.Item>
          </Col>
          
          <Col span={24}>
            <Form.Item
              label="家具家电配置"
              name="furniture_appliances"
            >
              <TextArea
                placeholder="请描述家具家电配置情况"
                rows={3}
                maxLength={500}
                showCount
              />
            </Form.Item>
          </Col>
          
          <Col span={24}>
            <Form.Item
              label="其他信息"
              name="other_info"
            >
              <TextArea
                placeholder="请填写其他重要信息，如：交通便利情况、周边配套、停车位、物业费等"
                rows={3}
                maxLength={1000}
                showCount
              />
            </Form.Item>
          </Col>
          
          <Col span={24}>
            <Form.Item
              label="房源描述"
              name="description"
            >
              <TextArea
                placeholder="请输入房源详细描述"
                rows={4}
                maxLength={1000}
                showCount
              />
            </Form.Item>
          </Col>
          
          {/* 操作按钮 */}
          <Col span={24}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={saving}
              >
                保存修改
              </Button>
              <Button
                icon={<CloseOutlined />}
                onClick={onCancel}
                disabled={saving}
              >
                取消编辑
              </Button>
            </Space>
          </Col>
        </Row>
      </Form>
    </Card>
  );
};

export default PropertyEditForm;
