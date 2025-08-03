import React from 'react';
import { Layout, Menu, Button, message } from 'antd';
import { LogoutOutlined, UploadOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';

const { Header: AntHeader } = Layout;

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, loading } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      message.success('已成功登出');
    } catch (error) {
      console.error('Logout error:', error);
      message.error('登出失败，请重试');
    }
  };

  const menuItems = [
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: '房源上传',
      onClick: () => navigate('/upload')
    },
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: '房源检索',
      onClick: () => navigate('/search')
    }
  ];

  return (
    <AntHeader style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      background: '#fff',
      borderBottom: '1px solid #f0f0f0',
      padding: '0 24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ 
          fontSize: '18px', 
          fontWeight: 'bold', 
          marginRight: '32px',
          color: '#1890ff'
        }}>
          房屋中介管理系统
        </div>
        
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ 
            border: 'none',
            minWidth: '200px'
          }}
        />
      </div>
      
      <Button 
        type="text" 
        icon={<LogoutOutlined />}
        onClick={handleLogout}
        loading={loading}
        style={{ color: '#666' }}
      >
        登出
      </Button>
    </AntHeader>
  );
};

export default Header;