import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Typography, 
  Card, 
  Row, 
  Col, 
  Image, 
  Descriptions, 
  Button, 
  Space, 
  message, 
  Modal, 
  Spin,
  Tag,

} from 'antd';
import { 
  EditOutlined, 
  DeleteOutlined, 
  ArrowLeftOutlined,
  HomeOutlined,
  EnvironmentOutlined,
  DollarOutlined
} from '@ant-design/icons';
import propertyApiService from '../services/propertyApi';
import PropertyEditForm from '../components/property/PropertyEditForm';
import { PROPERTY_TYPES } from '../utils/constants';

const { Title, Text } = Typography;
const { confirm } = Modal;

/**
 * 房源详情页面组件
 */
const PropertyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [property, setProperty] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);

  /**
   * 加载房源详情
   */
  const loadPropertyDetail = async () => {
    try {
      setLoading(true);
      const response = await propertyApiService.getPropertyById(id);
      setProperty(response);
    } catch (error) {
      console.error('加载房源详情失败:', error);
      message.error('加载房源详情失败，请稍后重试');
      navigate('/search');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 处理编辑
   */
  const handleEdit = () => {
    setEditMode(true);
  };

  /**
   * 处理编辑保存
   */
  const handleEditSave = (updatedProperty) => {
    setProperty(updatedProperty);
    setEditMode(false);
    message.success('房源信息更新成功');
  };

  /**
   * 处理编辑取消
   */
  const handleEditCancel = () => {
    setEditMode(false);
  };

  /**
   * 处理删除
   */
  const handleDelete = () => {
    confirm({
      title: '确认删除',
      content: '确定要删除这个房源吗？此操作不可恢复。',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await propertyApiService.deleteProperty(id);
          message.success('房源删除成功');
          navigate('/search');
        } catch (error) {
          console.error('删除房源失败:', error);
          message.error('删除房源失败，请稍后重试');
        }
      },
    });
  };

  /**
   * 返回搜索页面
   */
  const handleBack = () => {
    navigate('/search');
  };

  /**
   * 格式化价格显示
   */
  const formatPrice = (price, propertyType) => {
    if (propertyType === PROPERTY_TYPES.RENT) {
      return `${price} 元/月`;
    } else {
      return `${price} 万元`;
    }
  };

  /**
   * 获取房屋类型标签
   */
  const getPropertyTypeTag = (type) => {
    if (type === PROPERTY_TYPES.RENT) {
      return <Tag color="blue">租房</Tag>;
    } else {
      return <Tag color="green">售房</Tag>;
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    if (id) {
      loadPropertyDetail();
    }
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>加载房源详情中...</Text>
        </div>
      </div>
    );
  }

  if (!property) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Text>房源不存在</Text>
      </div>
    );
  }

  return (
    <div className="container">
      {/* 页面头部 */}
      <div className="page-header">
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={handleBack}
          >
            返回
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            房源详情
          </Title>
        </Space>
        
        {!editMode && (
          <Space>
            <Button
              type="primary"
              icon={<EditOutlined />}
              onClick={handleEdit}
            >
              编辑
            </Button>
            <Button
              danger
              icon={<DeleteOutlined />}
              onClick={handleDelete}
            >
              删除
            </Button>
          </Space>
        )}
      </div>

      <div className="content-wrapper">
        {/* 编辑模式 */}
        {editMode ? (
          <PropertyEditForm
            property={property}
            onSave={handleEditSave}
            onCancel={handleEditCancel}
            loading={loading}
          />
        ) : (
          <>
            {/* 基本信息卡片 */}
            <Card style={{ marginBottom: 16 }}>
          <Row gutter={[24, 24]}>
            <Col span={24}>
              <Space size="large">
                <Title level={3} style={{ margin: 0 }}>
                  {property.community_name}
                </Title>
                {getPropertyTypeTag(property.property_type)}
              </Space>
            </Col>
            
            <Col span={24}>
              <Space size="large" wrap>
                <Space>
                  <EnvironmentOutlined style={{ color: '#1890ff' }} />
                  <Text>{property.street_address}</Text>
                </Space>
                
                <Space>
                  <DollarOutlined style={{ color: '#52c41a' }} />
                  <Text strong style={{ fontSize: '18px', color: '#f5222d' }}>
                    {formatPrice(property.price, property.property_type)}
                  </Text>
                </Space>
                
                {property.area && (
                  <Space>
                    <HomeOutlined style={{ color: '#722ed1' }} />
                    <Text>{property.area} 平米</Text>
                  </Space>
                )}
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 详细信息 */}
        <Card title="详细信息" style={{ marginBottom: 16 }}>
          <Descriptions column={2} bordered>
            <Descriptions.Item label="小区名称">
              {property.community_name}
            </Descriptions.Item>
            <Descriptions.Item label="街道地址">
              {property.street_address}
            </Descriptions.Item>
            <Descriptions.Item label="房屋类型">
              {property.property_type === PROPERTY_TYPES.RENT ? '租房' : '售房'}
            </Descriptions.Item>
            <Descriptions.Item label="价格">
              {formatPrice(property.price, property.property_type)}
            </Descriptions.Item>
            {property.floor_info && (
              <Descriptions.Item label="楼层信息">
                {property.floor_info}
              </Descriptions.Item>
            )}
            {property.room_count && (
              <Descriptions.Item label="房间数量">
                {property.room_count}
              </Descriptions.Item>
            )}
            {property.area && (
              <Descriptions.Item label="面积">
                {property.area} 平米
              </Descriptions.Item>
            )}
            {property.decoration_status && (
              <Descriptions.Item label="装修情况">
                {property.decoration_status}
              </Descriptions.Item>
            )}
            {property.furniture_appliances && (
              <Descriptions.Item label="家具家电" span={2}>
                {property.furniture_appliances}
              </Descriptions.Item>
            )}
            {property.description && (
              <Descriptions.Item label="房源描述" span={2}>
                {property.description}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="创建时间">
              {new Date(property.created_at).toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {new Date(property.updated_at).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* 房源图片 */}
        {property.images && property.images.length > 0 && (
          <Card title="房源图片">
            <Row gutter={[16, 16]}>
              {property.images.map((image, index) => (
                <Col xs={24} sm={12} md={8} lg={6} key={image.id || index}>
                  <Image
                    src={image.image_url}
                    alt={`房源图片 ${index + 1}`}
                    style={{ 
                      width: '100%', 
                      height: '200px', 
                      objectFit: 'cover',
                      borderRadius: '8px'
                    }}
                    placeholder={
                      <div style={{ 
                        height: '200px', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        backgroundColor: '#f5f5f5'
                      }}>
                        <Text type="secondary">加载中...</Text>
                      </div>
                    }
                  />
                </Col>
              ))}
            </Row>
          </Card>
        )}
          </>
        )}
      </div>
    </div>
  );
};

export default PropertyDetail;
