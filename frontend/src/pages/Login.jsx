import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Typography, Alert, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/auth';

const { Title } = Typography;

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // 获取登录前的页面路径
  const from = location.state?.from?.pathname || '/upload';

  // 检查是否已登录
  useEffect(() => {
    if (authService.isAuthenticated()) {
      navigate(from, { replace: true });
    }
  }, [navigate, from]);

  const onFinish = async (values) => {
    setLoading(true);
    setError('');
    
    try {
      await authService.login(values.username, values.password);
      
      message.success('登录成功！');
      
      // 跳转到登录前的页面或默认页面
      navigate(from, { replace: true });
      
    } catch (error) {
      console.error('Login error:', error);
      
      if (error.response?.status === 401) {
        setError('用户名或密码错误');
      } else if (error.response?.status === 429) {
        setError('登录尝试过于频繁，请稍后再试');
      } else if (error.response?.data?.error?.message) {
        setError(error.response.data.error.message);
      } else {
        setError('登录失败，请检查网络连接');
      }
    } finally {
      setLoading(false);
    }
  };

  const onFinishFailed = (errorInfo) => {
    console.log('Failed:', errorInfo);
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Card style={{ width: 400 }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 24 }}>
          房屋中介管理系统
        </Title>
        
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        <Form
          name="login"
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名！' },
              { min: 3, message: '用户名至少3个字符！' },
              { max: 50, message: '用户名不能超过50个字符！' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码！' },
              { min: 6, message: '密码至少6个字符！' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              style={{ width: '100%' }}
            >
              {loading ? '登录中...' : '登录'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Login;