import React from 'react';
import { Card, Row, Col, Tag, Image, Typography, Empty, Spin } from 'antd';
import { HomeOutlined, EnvironmentOutlined, DollarOutlined } from '@ant-design/icons';
import { PROPERTY_TYPES, PROPERTY_TYPE_LABELS } from '../../utils/constants';

const { Text, Title } = Typography;

/**
 * 房源列表组件
 * @param {Object} props - 组件属性
 * @param {Array} props.properties - 房源列表
 * @param {boolean} props.loading - 加载状态
 * @param {Function} props.onPropertyClick - 房源点击回调
 */
const PropertyList = ({ properties = [], loading = false, onPropertyClick }) => {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载房源信息...</Text>
        </div>
      </div>
    );
  }

  if (!properties || properties.length === 0) {
    return (
      <Empty
        description="暂无房源信息"
        style={{ padding: '50px' }}
      />
    );
  }

  /**
   * 格式化价格显示
   * @param {string} propertyType - 房屋类型
   * @param {number} price - 价格
   * @returns {string} 格式化后的价格
   */
  const formatPrice = (propertyType, price) => {
    if (propertyType === PROPERTY_TYPES.RENT) {
      return `¥${price}/月`;
    } else {
      return `¥${price}万`;
    }
  };

  /**
   * 获取房屋类型标签颜色
   * @param {string} propertyType - 房屋类型
   * @returns {string} 标签颜色
   */
  const getPropertyTypeColor = (propertyType) => {
    return propertyType === PROPERTY_TYPES.RENT ? 'blue' : 'green';
  };

  /**
   * 转换图片URL为完整的后端URL
   * @param {string} imageUrl - 图片URL
   * @returns {string} 完整URL
   */
  const getFullImageUrl = (imageUrl) => {
    if (!imageUrl) return '';
    
    // 如果已经是完整URL，直接返回
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return imageUrl;
    }
    
    // 如果是相对URL，转换为完整的后端URL
    const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const apiBaseUrl = baseUrl.replace('/api', ''); // 移除/api后缀
    
    return `${apiBaseUrl}${imageUrl}`;
  };

  /**
   * 获取房源主图
   * @param {Array} images - 图片列表
   * @returns {string} 主图URL
   */
  const getPrimaryImage = (images) => {
    if (!images || images.length === 0) {
      return null;
    }
    
    // 查找主图
    const primaryImage = images.find(img => img.is_primary);
    if (primaryImage) {
      // 优先使用image_url，如果没有则使用file_path转换
      const imageUrl = primaryImage.image_url || `/api/upload/images/${primaryImage.file_name}`;
      return getFullImageUrl(imageUrl);
    }
    
    // 如果没有主图，返回第一张图片
    const firstImage = images[0];
    const imageUrl = firstImage.image_url || `/api/upload/images/${firstImage.file_name}`;
    return getFullImageUrl(imageUrl);
  };

  /**
   * 处理房源卡片点击
   * @param {Object} property - 房源对象
   */
  const handlePropertyClick = (property) => {
    if (onPropertyClick) {
      onPropertyClick(property);
    }
  };

  return (
    <Row gutter={[16, 16]}>
      {properties.map((property) => {
        const primaryImage = getPrimaryImage(property.images);
        
        return (
          <Col xs={24} sm={12} md={8} lg={6} key={property.id}>
            <Card
              hoverable
              style={{ height: '100%' }}
              cover={
                primaryImage ? (
                  <div style={{ height: 200, overflow: 'hidden' }}>
                    <Image
                      alt={property.community_name}
                      src={primaryImage}
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover' 
                      }}
                      preview={false}
                    />
                  </div>
                ) : (
                  <div 
                    style={{ 
                      height: 200, 
                      backgroundColor: '#f5f5f5',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <HomeOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                  </div>
                )
              }
              onClick={() => handlePropertyClick(property)}
            >
              <Card.Meta
                title={
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Title level={5} style={{ margin: 0, fontSize: 16 }}>
                        {property.community_name}
                      </Title>
                      <Tag 
                        color={getPropertyTypeColor(property.property_type)}
                        style={{ margin: 0 }}
                      >
                        {PROPERTY_TYPE_LABELS[property.property_type]}
                      </Tag>
                    </div>
                  </div>
                }
                description={
                  <div>
                    {/* 地址信息 */}
                    <div style={{ marginBottom: 8 }}>
                      <EnvironmentOutlined style={{ marginRight: 4, color: '#666' }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {property.street_address}
                      </Text>
                    </div>
                    
                    {/* 房间信息 */}
                    {property.room_count && (
                      <div style={{ marginBottom: 8 }}>
                        <HomeOutlined style={{ marginRight: 4, color: '#666' }} />
                        <Text style={{ fontSize: 12 }}>
                          {property.room_count}
                        </Text>
                        {property.area && (
                          <Text style={{ fontSize: 12, marginLeft: 8 }}>
                            {property.area}㎡
                          </Text>
                        )}
                      </div>
                    )}
                    
                    {/* 楼层信息 */}
                    {property.floor_info && (
                      <div style={{ marginBottom: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {property.floor_info}
                        </Text>
                      </div>
                    )}
                    
                    {/* 价格信息 */}
                    <div style={{ marginTop: 12 }}>
                      <DollarOutlined style={{ marginRight: 4, color: '#ff4d4f' }} />
                      <Text strong style={{ color: '#ff4d4f', fontSize: 16 }}>
                        {formatPrice(property.property_type, property.price)}
                      </Text>
                    </div>
                  </div>
                }
              />
            </Card>
          </Col>
        );
      })}
    </Row>
  );
};

export default PropertyList;