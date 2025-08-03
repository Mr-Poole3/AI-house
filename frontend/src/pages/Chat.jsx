/**
 * 聊天页面
 * 支持与豆包大模型进行文本和图片聊天，包含流式输出
 */

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatAPI } from '../services/chatApi';
import Loading from '../components/common/Loading';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 获取服务状态
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await chatAPI.getStatus();
        setServiceStatus(status);
      } catch (error) {
        console.error('获取服务状态失败:', error);
      }
    };
    checkStatus();
  }, []);

  // 处理图片选择
  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('请选择有效的图片文件');
        return;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB限制
        alert('图片文件大小不能超过10MB');
        return;
      }

      setSelectedImage(file);
      
      // 创建预览
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 清除图片选择
  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim() && !selectedImage) {
      return;
    }

    if (!serviceStatus?.available) {
      alert('聊天服务当前不可用，请稍后再试');
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      image: imagePreview,
      timestamp: new Date()
    };

    // 添加用户消息
    setMessages(prev => [...prev, userMessage]);
    
    // 准备对话历史（简化版本，只包含文本）
    const conversationHistory = messages
      .filter(msg => !msg.image) // 暂时只包含纯文本历史
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }))
      .slice(-10); // 只保留最近10条消息

    const messageText = inputMessage;
    const imageFile = selectedImage;

    // 清空输入
    setInputMessage('');
    clearImage();
    setIsLoading(true);

    try {
      if (imageFile) {
        // 图片+文本聊天（模拟流式效果）
        const assistantMessageId = Date.now() + 1;
        const assistantMessage = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true
        };
        
        // 先添加空的助手消息
        setMessages(prev => [...prev, assistantMessage]);
        
        const response = await chatAPI.sendImageMessage(
          messageText, 
          imageFile, 
          conversationHistory
        );

        if (response.success) {
          // 使用打字机效果显示响应
          typeMessage(assistantMessageId, response.message);
        } else {
          // 错误消息也用打字机效果
          typeMessage(assistantMessageId, `错误：${response.error || '聊天失败'}`);
        }
      } else {
        // 纯文本聊天（流式）
        const assistantMessageId = Date.now() + 1;
        const assistantMessage = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setStreamingMessageId(assistantMessageId);

        await chatAPI.streamTextChat(
          messageText,
          conversationHistory,
          // onChunk - 接收流式数据
          (chunk) => {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: msg.content + chunk }
                : msg
            ));
          },
          // onComplete - 完成
          () => {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, isStreaming: false }
                : msg
            ));
            setStreamingMessageId(null);
          },
          // onError - 错误
          (error) => {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: `错误: ${error}`, isStreaming: false }
                : msg
            ));
            setStreamingMessageId(null);
          }
        );
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `抱歉，发生了错误：${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 处理键盘事件
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  // 格式化时间
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 模拟打字机效果
  const typeMessage = (messageId, text) => {
    let index = 0;
    setStreamingMessageId(messageId);
    
    const typeNextChar = () => {
      if (index < text.length) {
        const currentChar = text[index];
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, content: text.slice(0, index + 1), isStreaming: true }
            : msg
        ));
        index++;
        
        // 中文字符稍慢一点
        const delay = currentChar.charCodeAt(0) > 127 ? 60 : 40;
        setTimeout(typeNextChar, delay);
      } else {
        // 完成打字
        setMessages(prev => prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, isStreaming: false }
            : msg
        ));
        setStreamingMessageId(null);
      }
    };
    
    // 开始打字
    typeNextChar();
  };

  return (
    <div className="chat-container">
      {/* 顶部标题栏 */}
      <div className="chat-top-bar">
        <div className="chat-title">豆包</div>
        <div className="service-status">
          {serviceStatus ? (
            <span className={serviceStatus.available ? 'status-online' : 'status-offline'}>
              {serviceStatus.available ? '●' : '○'}
            </span>
          ) : (
            <span className="status-unknown">○</span>
          )}
        </div>
      </div>

      <div className="chat-content">
        {messages.length === 0 ? (
          // 初始状态 - 显示欢迎界面
          <div className="welcome-screen">
            <h1 className="welcome-title">有什么可以帮忙的？</h1>
          </div>
        ) : (
          // 对话状态 - 显示消息列表
          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-content">
                  {message.image && (
                    <div className="message-image">
                      <img src={message.image} alt="用户上传" />
                    </div>
                  )}
                  <div className="message-text">
                    {message.role === 'assistant' ? (
                      <div className="markdown-content">
                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>
                        {message.isStreaming && <span className="cursor">●</span>}
                      </div>
                    ) : (
                      <>
                        {message.content}
                        {message.isStreaming && <span className="cursor">●</span>}
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 底部输入区域 */}
      <div className="chat-input-area">
        {imagePreview && (
          <div className="image-preview-wrapper">
            <div className="image-preview">
              <img src={imagePreview} alt="预览" />
              <button className="remove-image" onClick={clearImage}>
                ×
              </button>
            </div>
          </div>
        )}
        
        <div className="chat-input-wrapper">
          <div className="chat-input">
            <button 
              className="attachment-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              title="上传图片"
            >
              📎
            </button>
            
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="询问任何问题"
              disabled={isLoading}
              rows="1"
            />
            
            <button 
              className="send-button"
              onClick={sendMessage}
              disabled={isLoading || (!inputMessage.trim() && !selectedImage)}
            >
              {isLoading ? (
                <div className="loading-spinner">⟳</div>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M7 11L12 6L17 11M12 18V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </button>
          </div>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImageSelect}
          accept="image/*"
          style={{ display: 'none' }}
        />
      </div>
    </div>
  );
};

export default Chat;