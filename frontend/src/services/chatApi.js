/**
 * 聊天API服务
 * 支持文本聊天和图片+文本聊天，流式输出
 */

import api from './api';

class ChatAPI {
  /**
   * 发送纯文本消息（流式输出）
   * @param {string} message - 消息内容
   * @param {Array} conversationHistory - 对话历史
   * @param {Function} onChunk - 接收流式数据的回调函数
   * @param {Function} onComplete - 完成时的回调函数
   * @param {Function} onError - 错误时的回调函数
   */
  async streamTextChat(message, conversationHistory = [], onChunk, onComplete, onError) {
    try {
      // 获取认证信息
      const token = localStorage.getItem('access_token');
      const tokenType = localStorage.getItem('token_type') || 'bearer';
      
      if (!token) {
        throw new Error('未找到认证token，请重新登录');
      }

      const response = await fetch(`${api.defaults.baseURL}/chat/text/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `${tokenType.charAt(0).toUpperCase() + tokenType.slice(1)} ${token}`,
        },
        body: JSON.stringify({
          message,
          conversation_history: conversationHistory
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            onComplete && onComplete();
            break;
          }

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // 移除 'data: ' 前缀
              
              if (data === '[DONE]') {
                onComplete && onComplete();
                return;
              }
              
              if (data.trim()) {
                onChunk && onChunk(data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('流式聊天错误:', error);
      onError && onError(error.message);
    }
  }

  /**
   * 发送纯文本消息（非流式）
   * @param {string} message - 消息内容
   * @param {Array} conversationHistory - 对话历史
   * @returns {Promise<Object>} 响应数据
   */
  async sendTextMessage(message, conversationHistory = []) {
    try {
      const response = await api.post('/chat/text', {
        message,
        conversation_history: conversationHistory
      });
      return response.data;
    } catch (error) {
      console.error('文本聊天错误:', error);
      throw error;
    }
  }

  /**
   * 发送图片+文本消息
   * @param {string} message - 消息内容
   * @param {File} imageFile - 图片文件
   * @param {Array} conversationHistory - 对话历史
   * @returns {Promise<Object>} 响应数据
   */
  async sendImageMessage(message, imageFile, conversationHistory = []) {
    try {
      const formData = new FormData();
      formData.append('message', message);
      formData.append('image', imageFile);
      formData.append('conversation_history', JSON.stringify(conversationHistory));

      const response = await api.post('/chat/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      return response.data;
    } catch (error) {
      console.error('图片聊天错误:', error);
      throw error;
    }
  }

  /**
   * 获取聊天服务状态
   * @returns {Promise<Object>} 服务状态
   */
  async getStatus() {
    try {
      const response = await api.get('/chat/status');
      return response.data;
    } catch (error) {
      console.error('获取聊天状态错误:', error);
      throw error;
    }
  }
}

export const chatAPI = new ChatAPI();
export default chatAPI;