import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  timeout: 60000, // 增加到30秒，适应LLM响应时间
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type') || 'bearer';
    const expiresAt = localStorage.getItem('expires_at');
    
    // 检查令牌是否存在且未过期
    if (token && expiresAt && Date.now() < parseInt(expiresAt)) {
      config.headers.Authorization = `${tokenType.charAt(0).toUpperCase() + tokenType.slice(1)} ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // 如果是401错误且不是登录请求，尝试刷新令牌
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/auth/login')) {
      originalRequest._retry = true;
      
      try {
        // 尝试刷新令牌
        const refreshResponse = await axios.post(
          `${api.defaults.baseURL}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `${localStorage.getItem('token_type') || 'bearer'} ${localStorage.getItem('access_token')}`
            }
          }
        );
        
        const { access_token, expires_in } = refreshResponse.data;
        
        // 更新令牌
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('expires_at', Date.now() + expires_in * 1000);
        
        // 重新发送原始请求
        originalRequest.headers.Authorization = `${localStorage.getItem('token_type')} ${access_token}`;
        return api(originalRequest);
        
      } catch (refreshError) {
        // 刷新失败，清除本地存储并跳转到登录页
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('expires_at');
        
        // 如果当前不在登录页，跳转到登录页
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;