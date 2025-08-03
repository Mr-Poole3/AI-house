/**
 * 聊天页面
 * 支持与豆包大模型进行文本和图片聊天，包含流式输出
 */

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatAPI } from '../services/chatApi';
import api from '../services/api';
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
  const [pendingIntent, setPendingIntent] = useState(null);
  
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

  // 解析意图数据
  const extractIntentData = (content) => {
    // 先尝试解析嵌入的JSON数据
    const intentPattern = /<!-- INTENT_DATA: (.+?) -->/s;
    const match = content.match(intentPattern);
    
    if (match) {
      try {
        const intentData = JSON.parse(match[1]);
        return intentData;
      } catch (error) {
        console.error('解析嵌入意图数据失败:', error);
      }
    }
    
    // 尝试解析回复中的JSON代码块
    const jsonPattern = /```json\s*(\{[\s\S]*?\})\s*```/;
    const jsonMatch = content.match(jsonPattern);
    if (jsonMatch) {
      try {
        const intentData = JSON.parse(jsonMatch[1]);
        if (intentData.intent_type === "property_query") {
          console.log('✅ 从JSON代码块提取到意图数据:', intentData);
          return intentData;
        }
      } catch (error) {
        console.error('解析JSON代码块失败:', error);
      }
    }
    
    return null;
  };

  // 清除意图数据标记
  const cleanContentFromIntent = (content) => {
    return content.replace(/<!-- INTENT_DATA: .+? -->/g, '').trim();
  };

  // 添加步骤消息
  const addStepMessage = (content, isComplete = false) => {
    const stepMessage = {
      id: Date.now() + Math.random(), // 确保唯一性
      role: 'assistant',
      content: content,
      timestamp: new Date(),
      isStep: true,
      isComplete: isComplete
    };
    setMessages(prev => [...prev, stepMessage]);
    return stepMessage.id;
  };

  // 更新步骤消息
  const updateStepMessage = (messageId, content, isComplete = false) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content: content, isComplete: isComplete }
        : msg
    ));
  };

  // 添加技术细节消息
  const addTechnicalDetailMessage = (content) => {
    const detailMessage = {
      id: Date.now() + Math.random(),
      role: 'assistant',
      content: content,
      timestamp: new Date(),
      isTechnicalDetail: true
    };
    setMessages(prev => [...prev, detailMessage]);
    return detailMessage.id;
  };

  // 模拟打字机效果
  const typeWriterEffect = async (messageId, content, speed = 20) => {
    for (let i = 0; i <= content.length; i++) {
      const currentText = content.slice(0, i);
      setMessages(prev => prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, content: currentText }
          : msg
      ));
      await new Promise(resolve => setTimeout(resolve, speed));
    }
  };

  // 确认房源查询 - 先回到工作版本，然后逐步改进
  const confirmPropertyQuery = async (intentData) => {
    if (!intentData) return;

    setPendingIntent(null);
    setIsLoading(true);

    const confirmMessage = {
      id: Date.now(),
      role: 'user',
      content: '确认查询',
      timestamp: new Date(),
      isConfirmation: true
    };

    // 添加确认消息
    setMessages(prev => [...prev, confirmMessage]);

    // 立即显示初始加载状态
    const loadingId = addStepMessage('🔄 正在启动房源查询系统...');

    try {
      // 发送查询请求到后端
      const confirmationMessage = `PROPERTY_QUERY_CONFIRM:${JSON.stringify(intentData)}`;
      
      // 更新加载状态
      updateStepMessage(loadingId, '📡 正在连接数据库服务器...', false);
      
      const response = await chatAPI.sendTextMessage(confirmationMessage, []);

      if (!response.success) {
        updateStepMessage(loadingId, '❌ 连接失败', true);
        throw new Error(response.error || '查询失败');
      }

      // 更新加载状态
      updateStepMessage(loadingId, '✅ 服务器连接成功，正在处理查询...', false);

      // 解析后端返回的结构化数据
      const responseData = response.message;
      let queryResult;
      
      if (responseData.startsWith('QUERY_RESULT:')) {
        queryResult = JSON.parse(responseData.slice('QUERY_RESULT:'.length));
        updateStepMessage(loadingId, '✅ 查询处理完成', true);
      } else {
        updateStepMessage(loadingId, '❌ 数据解析失败', true);
        throw new Error('无法解析查询结果');
      }

      // 短暂延迟让用户看到完成状态
      await new Promise(resolve => setTimeout(resolve, 500));

      // 步骤1: 分析查询参数
      const step1Id = addStepMessage('🔍 正在分析查询参数...');
      await new Promise(resolve => setTimeout(resolve, 300));
      updateStepMessage(step1Id, '🔍 查询参数分析完成', true);
      
      // 显示参数详情
      const paramDetailId = addTechnicalDetailMessage('');
      const paramContent = `**🔍 查询参数分析**：\n\`\`\`json\n${JSON.stringify(queryResult.query_params, null, 2)}\n\`\`\``;
      await typeWriterEffect(paramDetailId, paramContent, 10);

      // 步骤2: 生成SQL查询
      await new Promise(resolve => setTimeout(resolve, 500));
      const step2Id = addStepMessage('📝 正在生成SQL查询...');
      await new Promise(resolve => setTimeout(resolve, 800));
      updateStepMessage(step2Id, '📝 SQL查询生成完成', true);

      if (queryResult.sql_info) {
        // 显示SQL详情
        const sqlDetailId = addTechnicalDetailMessage('');
        const sqlContent = `**📝 生成的SQL查询**：\n\`\`\`sql\n${queryResult.sql_info.sql}\n\`\`\``;
        await typeWriterEffect(sqlDetailId, sqlContent, 8);
        
        // 显示查询参数
        await new Promise(resolve => setTimeout(resolve, 300));
        const paramDetailId2 = addTechnicalDetailMessage('');
        const paramContent2 = `**🔧 查询参数**：\n\`\`\`json\n${JSON.stringify(queryResult.sql_info.params, null, 2)}\n\`\`\``;
        await typeWriterEffect(paramDetailId2, paramContent2, 10);
        
        // 显示查询说明  
        await new Promise(resolve => setTimeout(resolve, 300));
        const descDetailId = addTechnicalDetailMessage('');
        const descContent = `**📋 查询说明**：${queryResult.sql_info.description}`;
        await typeWriterEffect(descDetailId, descContent, 15);
      }

      // 步骤3: 执行查询
      await new Promise(resolve => setTimeout(resolve, 500));
      const step3Id = addStepMessage('🔄 正在执行数据库查询...');
      await new Promise(resolve => setTimeout(resolve, 600));
      updateStepMessage(step3Id, '🔄 数据库查询完成', true);

      // 步骤4: 整理结果
      const step4Id = addStepMessage(`✅ 查询完成：找到 ${queryResult.found_count || 0} 套房源`, true);

      // 最终结果展示
      await new Promise(resolve => setTimeout(resolve, 400));
      if (queryResult.found_count > 0) {
        const finalResultId = addStepMessage('');
        await typeWriterEffect(finalResultId, queryResult.formatted_answer, 25);
      } else {
        const noResultId = addStepMessage('');
        await typeWriterEffect(noResultId, queryResult.message, 25);
      }

    } catch (error) {
      console.error('确认查询失败:', error);
      
      // 如果有加载消息，更新为失败状态
      try {
        updateStepMessage(loadingId, '❌ 查询失败', true);
      } catch (e) {
        // 忽略更新失败的错误
      }
      
      const errorMessage = {
        id: Date.now() + 2,
        role: 'assistant',
        content: `确认查询失败：${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // 取消房源查询
  const cancelPropertyQuery = () => {
    setPendingIntent(null);
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
          const cleanContent = cleanContentFromIntent(response.message);
          const intentData = extractIntentData(response.message);
          
          if (intentData) {
            // 发现意图识别，设置待确认状态
            setPendingIntent({ data: intentData, messageId: assistantMessageId });
            // 直接显示内容，不用打字机效果
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: cleanContent, isStreaming: false, hasIntent: true }
                : msg
            ));
          } else {
            // 使用打字机效果显示响应
            typeMessage(assistantMessageId, cleanContent);
          }
        } else {
          // 错误消息也用打字机效果
          typeMessage(assistantMessageId, `错误：${response.error || '聊天失败'}`);
        }
      } else {
        // 纯文本聊天（非流式，前端模拟打字机效果）
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
        
        // 使用非流式请求获取完整响应
        const response = await chatAPI.sendTextMessage(messageText, conversationHistory);

        if (response.success) {
          const cleanContent = cleanContentFromIntent(response.message);
          const intentData = extractIntentData(response.message);
          
          if (intentData) {
            // 发现意图识别，设置待确认状态，直接显示（不用打字机效果）
            setPendingIntent({ data: intentData, messageId: assistantMessageId });
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessageId 
                ? { ...msg, content: cleanContent, isStreaming: false, hasIntent: true }
                : msg
            ));
          } else {
            // 正常聊天，使用打字机效果显示响应
            typeMessage(assistantMessageId, cleanContent);
          }
        } else {
          // 错误消息也用打字机效果
          typeMessage(assistantMessageId, `错误：${response.error || '聊天失败'}`);
        }
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
            <h1 className="welcome-title">👋 你好，有什么可以帮忙的？😊</h1>
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
                      <div className={`markdown-content ${message.isStep ? 'step-message' : ''} ${message.isComplete ? 'step-complete' : ''} ${message.isTechnicalDetail ? 'technical-detail' : ''}`}>
                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>
                        {message.isStreaming && <span className="cursor">●</span>}
                        
                        {/* 显示意图确认按钮 */}
                        {message.hasIntent && pendingIntent && pendingIntent.messageId === message.id && (
                          <div className="intent-confirmation">
                            <div className="confirmation-buttons">
                              <button 
                                className="btn btn-primary"
                                onClick={() => confirmPropertyQuery(pendingIntent.data)}
                                disabled={isLoading}
                              >
                                {isLoading ? (
                                  <>
                                    <span className="loading-spinner">⏳</span>
                                    正在查询...
                                  </>
                                ) : (
                                  <>
                                    🔍 确认查询
                                  </>
                                )}
                              </button>
                              <button 
                                className="btn btn-secondary"
                                onClick={cancelPropertyQuery}
                                disabled={isLoading}
                              >
                                ❌ 取消
                              </button>
                            </div>
                          </div>
                        )}
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