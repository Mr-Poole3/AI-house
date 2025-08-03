import api from './api';

/**
 * 房源相关API服务
 */
class PropertyApiService {
  /**
   * 获取房源列表
   * @param {Object} params - 查询参数
   * @returns {Promise} API响应
   */
  async getProperties(params = {}) {
    const response = await api.get('/properties', { params });
    return response.data;
  }

  /**
   * 获取租房列表
   * @param {Object} params - 查询参数
   * @returns {Promise} API响应
   */
  async getRentProperties(params = {}) {
    const response = await api.get('/properties/rent', { params });
    return response.data;
  }

  /**
   * 获取售房列表
   * @param {Object} params - 查询参数
   * @returns {Promise} API响应
   */
  async getSaleProperties(params = {}) {
    const response = await api.get('/properties/sale', { params });
    return response.data;
  }

  /**
   * 获取房源详情
   * @param {number} id - 房源ID
   * @returns {Promise} API响应
   */
  async getPropertyById(id) {
    const response = await api.get(`/properties/${id}`);
    return response.data;
  }

  /**
   * 更新房源
   * @param {number} id - 房源ID
   * @param {Object} data - 更新数据
   * @returns {Promise} API响应
   */
  async updateProperty(id, data) {
    const response = await api.put(`/properties/${id}`, data);
    return response.data;
  }

  /**
   * 删除房源
   * @param {number} id - 房源ID
   * @returns {Promise} API响应
   */
  async deleteProperty(id) {
    const response = await api.delete(`/properties/${id}`);
    return response.data;
  }
}

const propertyApiService = new PropertyApiService();
export default propertyApiService;