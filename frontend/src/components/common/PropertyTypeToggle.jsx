import React from 'react';
import { Tabs } from 'antd';
import { HomeOutlined, ShopOutlined } from '@ant-design/icons';
import { PROPERTY_TYPES, PROPERTY_TYPE_LABELS } from '../../utils/constants';

/**
 * 房屋类型切换组件
 * @param {Object} props - 组件属性
 * @param {string} props.activeType - 当前激活的类型
 * @param {Function} props.onChange - 类型切换回调
 * @param {Object} props.counts - 各类型数量统计
 */
const PropertyTypeToggle = ({ 
  activeType = PROPERTY_TYPES.RENT, 
  onChange, 
  counts = {} 
}) => {
  /**
   * 处理标签页切换
   * @param {string} key - 标签页key
   */
  const handleTabChange = (key) => {
    if (onChange) {
      onChange(key);
    }
  };

  /**
   * 构建标签页项目
   */
  const tabItems = [
    {
      key: PROPERTY_TYPES.RENT,
      label: (
        <span>
          <HomeOutlined />
          {PROPERTY_TYPE_LABELS[PROPERTY_TYPES.RENT]}
          {counts[PROPERTY_TYPES.RENT] !== undefined && (
            <span style={{ marginLeft: 4, color: '#666' }}>
              ({counts[PROPERTY_TYPES.RENT]})
            </span>
          )}
        </span>
      ),
    },
    {
      key: PROPERTY_TYPES.SALE,
      label: (
        <span>
          <ShopOutlined />
          {PROPERTY_TYPE_LABELS[PROPERTY_TYPES.SALE]}
          {counts[PROPERTY_TYPES.SALE] !== undefined && (
            <span style={{ marginLeft: 4, color: '#666' }}>
              ({counts[PROPERTY_TYPES.SALE]})
            </span>
          )}
        </span>
      ),
    },
  ];

  return (
    <Tabs
      activeKey={activeType}
      onChange={handleTabChange}
      items={tabItems}
      size="large"
      style={{ marginBottom: 16 }}
    />
  );
};

export default PropertyTypeToggle;