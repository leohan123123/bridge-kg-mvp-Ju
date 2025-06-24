import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Switch, List, Card, Spin, Alert, Typography } from 'antd';
import { SendOutlined } from '@ant-design/icons';

const { Text } = Typography;

const AIChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [knowledgeEnhanced, setKnowledgeEnhanced] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate unique ID for each message
  const generateMessageId = () => {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const currentInput = inputValue.trim();
    setInputValue(''); // Clear input immediately
    setError(null);

    // Add user message
    const userMessageId = generateMessageId();
    const userMessage = { 
      sender: 'user', 
      text: currentInput, 
      id: userMessageId 
    };
    
    setMessages(prevMessages => {
      console.log('Adding user message:', userMessage);
      return [...prevMessages, userMessage];
    });

    setIsLoading(true);

    try {
      console.log('Sending API request with message:', currentInput);
      
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          context: knowledgeEnhanced ? "Enhanced with knowledge base" : undefined,
        }),
      });

      console.log('API response status:', response.status);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Unknown error fetching AI response.' }));
        throw new Error(errData.detail || errData.message || `HTTP error! status: ${response.status}`);
      }

      // Parse the complete JSON response
      const aiResponse = await response.json();
      console.log('AI Response received:', aiResponse);
      
      // Extract content from API response
      const aiMessageText = aiResponse.content || aiResponse.text || "No response content";
      const aiRole = aiResponse.role || "assistant";
      const modelUsed = aiResponse.model_used || "unknown";

      // Add AI response message with unique ID
      const aiMessageId = generateMessageId();
      const aiMessage = {
        sender: 'ai',
        text: aiMessageText,
        id: aiMessageId,
        sources: aiResponse.sources || [],
        role: aiRole,
        model: modelUsed
      };

      console.log('Adding AI message:', aiMessage);

      setMessages(prevMessages => {
        const newMessages = [...prevMessages, aiMessage];
        console.log('Updated messages array:', newMessages);
        return newMessages;
      });

    } catch (err) {
      console.error("Error sending message:", err);
      setError(err.message || 'Failed to get response from AI. Please try again.');
      
      // Add error message to chat
      const errorMessageId = generateMessageId();
      const errorMessage = {
        sender: 'ai',
        text: `Error: ${err.message || 'Failed to load response.'}`,
        id: errorMessageId,
        error: true
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', border: '1px solid #f0f0f0', borderRadius: '8px', overflow: 'hidden' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <Text strong>AI Assistant ({messages.length} messages)</Text>
        <div>
          <Text style={{ marginRight: 8 }}>Knowledge Enhanced:</Text>
          <Switch checked={knowledgeEnhanced} onChange={setKnowledgeEnhanced} disabled={isLoading} />
        </div>
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '16px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#666', marginTop: '50px' }}>
            <Text>Start a conversation with the AI assistant!</Text>
          </div>
        )}
        
        <List
          dataSource={messages}
          rowKey={(item) => item.id}
          renderItem={(item, index) => (
            <List.Item style={{ borderBottom: 'none', padding: '8px 0' }}>
              <Card
                style={{
                  width: '100%',
                  textAlign: item.sender === 'user' ? 'right' : 'left',
                  backgroundColor: item.sender === 'user' ? '#e6f7ff' : (item.error ? '#fff1f0' : '#f5f5f5'),
                  alignSelf: item.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  marginLeft: item.sender === 'user' ? 'auto' : '0',
                  marginRight: item.sender === 'ai' ? 'auto' : '0',
                }}
                bodyStyle={{ padding: '10px 15px' }}
                size="small"
              >
                <div style={{ fontSize: '12px', color: '#999', marginBottom: '4px' }}>
                  {item.sender === 'user' ? 'You' : 'AI'} • Message {index + 1}
                </div>
                <Text style={{ color: item.error ? '#cf1322' : undefined, whiteSpace: 'pre-wrap' }}>
                  {item.text}
                </Text>
                {item.sender === 'ai' && !item.error && item.model && (
                  <div style={{ marginTop: '8px', fontSize: '0.8em', color: '#666' }}>
                    <Text type="secondary">Model: {item.model}</Text>
                  </div>
                )}
                {item.sender === 'ai' && !item.error && item.sources && item.sources.length > 0 && (
                  <div style={{ marginTop: '8px', fontSize: '0.9em' }}>
                    <Text strong>Sources:</Text>
                    <List
                      size="small"
                      dataSource={item.sources}
                      renderItem={(source, idx) => (
                        <List.Item style={{padding: '2px 0', borderBottom: 'none'}}>
                          <a href={source.url} target="_blank" rel="noopener noreferrer">
                            {source.name || `Source ${idx + 1}`}
                          </a>
                        </List.Item>
                      )}
                      rowKey={(source, idx) => `source_${idx}`}
                    />
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
        <div ref={messagesEndRef} />
        
        {isLoading && (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '8px' }}>
              <Text type="secondary">AI is thinking...</Text>
            </div>
          </div>
        )}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', flexShrink: 0 }}>
        <Input.Group compact style={{ display: 'flex' }}>
          <Input
            style={{ flexGrow: 1 }}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            disabled={isLoading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
            disabled={!inputValue.trim() || isLoading}
          >
            Send
          </Button>
        </Input.Group>
        {error && (
          <Alert message={error} type="error" showIcon style={{ marginTop: 10 }} closable onClose={() => setError(null)} />
        )}
      </div>
    </div>
  );
};

export default AIChatInterface;