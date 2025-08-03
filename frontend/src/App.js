import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './App.css';
import './forced-colors.css';

// 组件
import ProtectedRoute from './components/common/ProtectedRoute';
import Header from './components/common/Header';
import SessionTimeout from './components/common/SessionTimeout';

// 页面组件
import Login from './pages/Login';
import Upload from './pages/Upload';
import Search from './pages/Search';
import PropertyDetail from './pages/PropertyDetail';
import Chat from './pages/Chat';

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

// 创建路由配置
const router = createBrowserRouter([
  {
    path: "/login",
    element: <Login />
  },
  {
    path: "/upload",
    element: (
      <ProtectedRoute>
        <AuthenticatedLayout>
          <Upload />
        </AuthenticatedLayout>
      </ProtectedRoute>
    )
  },
  {
    path: "/search",
    element: (
      <ProtectedRoute>
        <AuthenticatedLayout>
          <Search />
        </AuthenticatedLayout>
      </ProtectedRoute>
    )
  },
  {
    path: "/property/:id",
    element: (
      <ProtectedRoute>
        <AuthenticatedLayout>
          <PropertyDetail />
        </AuthenticatedLayout>
      </ProtectedRoute>
    )
  },
  {
    path: "/chat",
    element: (
      <ProtectedRoute>
        <AuthenticatedLayout>
          <Chat />
        </AuthenticatedLayout>
      </ProtectedRoute>
    )
  },
  {
    path: "/",
    element: authService.isAuthenticated() ? 
      <Navigate to="/upload" replace /> : 
      <Navigate to="/login" replace />
  },
  {
    path: "*",
    element: <Navigate to="/" replace />
  }
], {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true
  }
});

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div className="App">
        <RouterProvider router={router} />
      </div>
    </ConfigProvider>
  );
}

export default App;