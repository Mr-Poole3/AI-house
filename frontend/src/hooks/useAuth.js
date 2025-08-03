import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/auth';

const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // 检查认证状态
  const checkAuth = useCallback(() => {
    const authenticated = authService.isAuthenticated();
    setIsAuthenticated(authenticated);
    return authenticated;
  }, []);

  // 自动刷新令牌
  const refreshToken = useCallback(async () => {
    if (!authService.getToken()) return false;
    
    try {
      setLoading(true);
      await authService.refreshToken();
      setIsAuthenticated(true);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      setIsAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // 登出
  const logout = useCallback(async () => {
    try {
      setLoading(true);
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
      authService.clearSession();
    } finally {
      setIsAuthenticated(false);
      setLoading(false);
      navigate('/login');
    }
  }, [navigate]);

  // 监听令牌过期
  useEffect(() => {
    const checkTokenExpiry = () => {
      if (authService.getToken() && authService.isTokenExpired()) {
        // 令牌过期，尝试刷新
        refreshToken().then(success => {
          if (!success) {
            // 刷新失败，跳转到登录页
            navigate('/login');
          }
        });
      }
    };

    // 立即检查一次
    checkTokenExpiry();

    // 每分钟检查一次令牌状态
    const interval = setInterval(checkTokenExpiry, 60000);

    return () => clearInterval(interval);
  }, [refreshToken, navigate]);

  // 监听存储变化（多标签页同步）
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'access_token') {
        checkAuth();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [checkAuth]);

  return {
    isAuthenticated,
    loading,
    checkAuth,
    refreshToken,
    logout
  };
};

export default useAuth;