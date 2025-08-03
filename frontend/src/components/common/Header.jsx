import React from 'react';
import { Layout, Menu, Button, message } from 'antd';
import { LogoutOutlined, UploadOutlined, SearchOutlined, MessageOutlined } from '@ant-design/icons';
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
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: 'AI聊天',
      onClick: () => navigate('/chat')
    }
  ];

  return (
    <AntHeader style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      background: '#fff',
      borderBottom: '1px solid #f0f0f0',
      padding: '0 24px',
      height: '64px'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center',
        flex: 1,
        minWidth: 0 // 防止flex溢出
      }}>
        <div style={{ 
          fontSize: '18px', 
          fontWeight: 'bold', 
          marginRight: '24px',
          color: '#1890ff',
          whiteSpace: 'nowrap'
        }}>
          房屋中介管理系统
        </div>
        
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ 
            border: 'none',
            minWidth: '360px',
            flex: 1,
            lineHeight: '64px'
          }}
          overflowedIndicator={null}
          inlineCollapsed={false}
        />
      </div>
      
      <Button 
        type="text" 
        icon={<LogoutOutlined />}
        onClick={handleLogout}
        loading={loading}
        style={{ 
          color: '#666',
          marginLeft: '16px',
          flexShrink: 0
        }}
      >
        登出
      </Button>
    </AntHeader>
  );
};

export default Header;