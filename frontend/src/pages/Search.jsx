import React, { useState, useEffect, useCallback } from 'react';
import { Typography, message, Pagination, Card, Divider } from 'antd';
import PropertyTypeToggle from '../components/common/PropertyTypeToggle';
import PropertyList from '../components/search/PropertyList';
import SearchFilters from '../components/search/SearchFilters';
import PriceRangeFilter from '../components/search/PriceRangeFilter';
import propertyApiService from '../services/propertyApi';
import { PROPERTY_TYPES } from '../utils/constants';

const { Title } = Typography;

const Search = () => {
  // 状态管理
  const [activeType, setActiveType] = useState(PROPERTY_TYPES.RENT);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  });
  const [typeCounts, setTypeCounts] = useState({});

  // 搜索和筛选状态
  const [searchFilters, setSearchFilters] = useState({});
  const [priceFilters, setPriceFilters] = useState({});

  /**
   * 加载房源列表
   * @param {string} type - 房屋类型
   * @param {number} page - 页码
   * @param {number} size - 每页数量
   * @param {Object} filters - 搜索和筛选条件
   */
  const loadProperties = useCallback(async (
    type = activeType,
    page = 1,
    size = 20,
    filters = {}
  ) => {
    try {
      setLoading(true);

      let response;
      // 合并所有筛选条件
      const params = {
        page,
        size,
        ...searchFilters,
        ...priceFilters,
        ...filters
      };

      if (type === PROPERTY_TYPES.RENT) {
        // 对于租房API，将价格参数重命名
        if (params.minPrice) {
          params.min_rent = params.minPrice;
          delete params.minPrice;
        }
        if (params.maxPrice) {
          params.max_rent = params.maxPrice;
          delete params.maxPrice;
        }
        response = await propertyApiService.getRentProperties(params);
      } else {
        // 对于售房API，保持原有的价格参数名
        if (params.minPrice) {
          params.min_price = params.minPrice;
          delete params.minPrice;
        }
        if (params.maxPrice) {
          params.max_price = params.maxPrice;
          delete params.maxPrice;
        }
        response = await propertyApiService.getSaleProperties(params);
      }

      setProperties(response.items || []);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize: size,
        total: response.total || 0,
      }));

    } catch (error) {
      console.error('加载房源列表失败:', error);
      message.error('加载房源列表失败，请稍后重试');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [activeType, searchFilters, priceFilters]);

  /**
   * 加载类型统计数据
   */
  const loadTypeCounts = async () => {
    try {
      // 并行获取租房和售房的总数
      const [rentResponse, saleResponse] = await Promise.all([
        propertyApiService.getRentProperties({ page: 1, size: 1 }),
        propertyApiService.getSaleProperties({ page: 1, size: 1 })
      ]);
      
      setTypeCounts({
        [PROPERTY_TYPES.RENT]: rentResponse.total || 0,
        [PROPERTY_TYPES.SALE]: saleResponse.total || 0,
      });
    } catch (error) {
      console.error('加载类型统计失败:', error);
    }
  };

  /**
   * 处理房屋类型切换
   * @param {string} type - 新的房屋类型
   */
  const handleTypeChange = (type) => {
    setActiveType(type);
    // 清空价格筛选（因为租房和售房的价格范围不同）
    setPriceFilters({});
    // 重置到第一页
    loadProperties(type, 1, pagination.pageSize);
  };

  /**
   * 处理分页变化
   * @param {number} page - 页码
   * @param {number} pageSize - 每页数量
   */
  const handlePaginationChange = (page, pageSize) => {
    loadProperties(activeType, page, pageSize);
  };

  /**
   * 处理搜索
   * @param {Object} filters - 搜索条件
   */
  const handleSearch = (filters) => {
    setSearchFilters(filters);
    // 重置到第一页
    loadProperties(activeType, 1, pagination.pageSize, filters);
  };

  /**
   * 处理价格筛选
   * @param {Object} filters - 价格筛选条件
   */
  const handlePriceChange = (filters) => {
    setPriceFilters(filters);
    // 重置到第一页
    loadProperties(activeType, 1, pagination.pageSize, { ...searchFilters, ...filters });
  };

  /**
   * 处理房源点击
   * @param {Object} property - 房源对象
   */
  const handlePropertyClick = (property) => {
    // 导航到房源详情页面
    window.location.href = `/property/${property.id}`;
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadProperties();
    loadTypeCounts();
  }, [loadProperties]);

  return (
    <div className="container">
      <div className="page-header">
        <Title level={2}>房源检索</Title>
      </div>
      
      <div className="content-wrapper">
        {/* 房屋类型切换标签 */}
        <PropertyTypeToggle
          activeType={activeType}
          onChange={handleTypeChange}
          counts={typeCounts}
        />

        {/* 搜索和筛选区域 */}
        <Card style={{ marginBottom: 16 }}>
          {/* 搜索筛选 */}
          <SearchFilters
            onSearch={handleSearch}
            loading={loading}
            initialValues={searchFilters}
          />

          <Divider style={{ margin: '16px 0' }} />

          {/* 价格范围筛选 */}
          <PriceRangeFilter
            propertyType={activeType}
            onPriceChange={handlePriceChange}
            loading={loading}
            initialValues={priceFilters}
          />
        </Card>

        {/* 房源列表 */}
        <PropertyList
          properties={properties}
          loading={loading}
          onPropertyClick={handlePropertyClick}
        />
        
        {/* 分页组件 */}
        {!loading && properties.length > 0 && (
          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <Pagination
              {...pagination}
              onChange={handlePaginationChange}
              onShowSizeChange={handlePaginationChange}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;