import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import useAuth from '../../hooks/useAuth';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { isAuthenticated, loading } = useAuth();
  
  // 显示加载状态
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh' 
      }}>
        <Spin size="large" tip="验证身份中..." />
      </div>
    );
  }
  
  // 检查用户是否已认证
  if (!isAuthenticated) {
    // 保存当前路径，登录后可以重定向回来
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
};

export default ProtectedRoute;