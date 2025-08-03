import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './App.css';

// 组件
import ProtectedRoute from './components/common/ProtectedRoute';
import Header from './components/common/Header';
import SessionTimeout from './components/common/SessionTimeout';

// 页面组件
import Login from './pages/Login';
import Upload from './pages/Upload';
import Search from './pages/Search';
import PropertyDetail from './pages/PropertyDetail';

// 认证服务
import authService from './services/auth';

const { Content } = Layout;

// 布局组件，用于需要认证的页面
const AuthenticatedLayout = ({ children }) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Content style={{ padding: '24px' }}>
        {children}
      </Content>
      <SessionTimeout />
    </Layout>
  );
};

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <div className="App">
          <Routes>
            {/* 登录页面 */}
            <Route path="/login" element={<Login />} />
            
            {/* 受保护的页面 */}
            <Route 
              path="/upload" 
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <Upload />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              } 
            />
            <Route
              path="/search"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <Search />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/property/:id"
              element={
                <ProtectedRoute>
                  <AuthenticatedLayout>
                    <PropertyDetail />
                  </AuthenticatedLayout>
                </ProtectedRoute>
              }
            />
            
            {/* 根路径重定向 */}
            <Route 
              path="/" 
              element={
                authService.isAuthenticated() ? 
                  <Navigate to="/upload" replace /> : 
                  <Navigate to="/login" replace />
              } 
            />
            
            {/* 404页面重定向 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </ConfigProvider>
  );
}

export default App;