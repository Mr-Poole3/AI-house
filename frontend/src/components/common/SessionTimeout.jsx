import React, { useState, useEffect } from 'react';
import { Modal, Button, message } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import authService from '../../services/auth';

const SessionTimeout = () => {
  const [visible, setVisible] = useState(false);
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    const checkSessionTimeout = () => {
      const expiresAt = localStorage.getItem('expires_at');
      if (!expiresAt) return;

      const timeLeft = parseInt(expiresAt) - Date.now();
      const fiveMinutes = 5 * 60 * 1000; // 5分钟

      // 如果令牌在5分钟内过期，显示警告
      if (timeLeft > 0 && timeLeft <= fiveMinutes && !visible) {
        setVisible(true);
        setCountdown(Math.floor(timeLeft / 1000));
      }
    };

    // 每30秒检查一次
    const interval = setInterval(checkSessionTimeout, 30000);
    
    // 立即检查一次
    checkSessionTimeout();

    return () => clearInterval(interval);
  }, [visible]);

  useEffect(() => {
    let timer;
    if (visible && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (visible && countdown <= 0) {
      // 倒计时结束，自动登出
      handleTimeout();
    }

    return () => clearTimeout(timer);
  }, [visible, countdown]);

  const handleExtendSession = async () => {
    try {
      await authService.refreshToken();
      setVisible(false);
      message.success('会话已延长');
    } catch (error) {
      console.error('Failed to extend session:', error);
      message.error('延长会话失败，请重新登录');
      handleTimeout();
    }
  };

  const handleTimeout = () => {
    setVisible(false);
    authService.clearSession();
    message.warning('会话已过期，请重新登录');
    window.location.href = '/login';
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <ExclamationCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
          会话即将过期
        </div>
      }
      open={visible}
      closable={false}
      maskClosable={false}
      footer={[
        <Button key="logout" onClick={handleTimeout}>
          立即登出
        </Button>,
        <Button key="extend" type="primary" onClick={handleExtendSession}>
          延长会话
        </Button>
      ]}
    >
      <p>您的登录会话将在 <strong>{formatTime(countdown)}</strong> 后过期。</p>
      <p>请选择延长会话或重新登录。</p>
    </Modal>
  );
};

export default SessionTimeout;