import api from './api';

class AuthService {
  // 获取存储的令牌
  getToken() {
    return localStorage.getItem('access_token');
  }

  // 获取令牌类型
  getTokenType() {
    return localStorage.getItem('token_type') || 'bearer';
  }

  // 检查令牌是否过期
  isTokenExpired() {
    const expiresAt = localStorage.getItem('expires_at');
    if (!expiresAt) return true;
    
    return Date.now() >= parseInt(expiresAt);
  }

  // 检查用户是否已登录
  isAuthenticated() {
    const token = this.getToken();
    return token && !this.isTokenExpired();
  }

  // 获取认证头
  getAuthHeader() {
    const token = this.getToken();

    if (token && !this.isTokenExpired()) {
      return `Bearer ${token}`;
    }
    return null;
  }

  // 登录
  async login(username, password) {
    try {
      const response = await api.post('/auth/login', {
        username,
        password
      });
      
      const { access_token, token_type, expires_in } = response.data;
      
      // 存储令牌信息
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('token_type', token_type);
      localStorage.setItem('expires_at', Date.now() + expires_in * 1000);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // 刷新令牌
  async refreshToken() {
    try {
      const response = await api.post('/auth/refresh');
      const { access_token, expires_in } = response.data;
      
      // 更新令牌信息
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('expires_at', Date.now() + expires_in * 1000);
      
      return response.data;
    } catch (error) {
      // 刷新失败，清除本地存储
      this.logout();
      throw error;
    }
  }

  // 登出
  async logout() {
    try {
      // 调用后端登出API
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // 清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('token_type');
      localStorage.removeItem('expires_at');
    }
  }

  // 清除本地会话（不调用API）
  clearSession() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('expires_at');
  }
}

const authService = new AuthService();
export default authService;