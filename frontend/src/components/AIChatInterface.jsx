import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Switch, List, Card, Spin, Alert, Typography } from 'antd';
import { SendOutlined } from '@ant-design/icons';
// We will use fetch for streaming, so axios might not be directly used here for chat.
// import axios from '../utils/axios';

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

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { sender: 'user', text: inputValue, id: Date.now() };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    // Add a placeholder for AI message that will be updated with streamed content
    const aiMessageId = Date.now() + 1;
    const initialAiMessage = { sender: 'ai', text: '', id: aiMessageId, sources: [] };
    setMessages(prevMessages => [...prevMessages, initialAiMessage]);

    try {
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          knowledge_enhanced: knowledgeEnhanced,
          // Assuming the backend expects a stream parameter or handles it by default if 'Accept' is 'text/event-stream'
          // stream: true, // This might be implicit or set via Accept header depending on backend
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ message: 'Unknown error fetching AI response.' }));
        throw new Error(errData.message || `HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let currentAiText = '';
      let currentSources = [];

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          // Assuming backend sends JSON objects line by line for streaming, or plain text chunks.
          // This needs to be robust to handle partial JSON if that's the streaming format.
          // For simplicity, let's assume each chunk is a self-contained piece of text or a JSON object.
          // A more robust SSE (Server-Sent Events) parser would be better if the backend supports it.
          // Example: data: {"text_chunk": "hello", "sources": []}\n\n
          // For now, let's assume plain text chunks and sources come at the end, or are part of a more complex JSON structure per chunk.
          // Let's refine this if the API sends structured stream data (e.g. JSON objects per chunk)

          // Simple text stream accumulation:
          // currentAiText += chunk;

          // Attempt to parse chunk as JSON (if backend sends structured stream like {"delta": "...", "sources": [...]})
          // This is a common pattern for streaming LLM responses.
          // We might get multiple JSON objects in a single chunk, or a partial one.
          // A simple split by newline might work if each JSON is on its own line.
          const chunkLines = chunk.split('\n').filter(line => line.trim() !== '');
          for (const line of chunkLines) {
            try {
              // Remove "data: " prefix if it's SSE
              const jsonData = JSON.parse(line.replace(/^data: /, ''));
              if (jsonData.text_chunk) {
                currentAiText += jsonData.text_chunk;
              }
              if (jsonData.sources && jsonData.sources.length > 0) {
                // Simple replacement, or could merge if sources come in chunks
                currentSources = jsonData.sources;
              }
            } catch (e) {
              // If not JSON, or malformed, append as plain text.
              // This part needs to be robust based on actual stream format.
              // If the stream is purely text, this JSON parsing is not needed.
              // Let's assume for now the backend *might* send JSON and fallback to text.
              // For a simple text stream:
              // currentAiText += line; // Or just `currentAiText += chunk;` before splitting
              console.warn("Received non-JSON chunk or malformed JSON, appending as text:", line);
              currentAiText += line; // Fallback for non-JSON or if parsing fails
            }
          }

          setMessages(prevMessages =>
            prevMessages.map(msg =>
              msg.id === aiMessageId ? { ...msg, text: currentAiText, sources: currentSources } : msg
            )
          );
        }
      }
    } catch (err) {
      console.error("Error sending message or processing stream:", err);
      setError(err.message || 'Failed to get response from AI. Please try again.');
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === aiMessageId ? { ...msg, text: `Error: ${err.message || 'Failed to load response.'}` , error: true } : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Adjust height based on App.tsx's content div minHeight
  // Original: height: 'calc(100vh - 120px)'
  // App.tsx content minHeight: 'calc(100vh - 180px)'
  // The AIChatInterface is directly inside this content div.
  // So, its height should be 100% of the parent, or manage its own height within that constraint.
  // Let's make it take full height of its container.
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', border: '1px solid #f0f0f0', borderRadius: '8px', overflow: 'hidden' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <Text strong>AI Assistant</Text>
        <div>
          <Text style={{ marginRight: 8 }}>Knowledge Enhanced:</Text>
          <Switch checked={knowledgeEnhanced} onChange={setKnowledgeEnhanced} disabled={isLoading} />
        </div>
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '16px' }}>
        <List
          dataSource={messages}
          rowKey="id" // Add unique key for list items
          renderItem={(item) => ( // Removed index as key, using item.id
            <List.Item style={{ borderBottom: 'none', padding: '8px 0' }}>
              <Card
                style={{
                  width: '100%',
                  textAlign: item.sender === 'user' ? 'right' : 'left',
                  backgroundColor: item.sender === 'user' ? '#e6f7ff' : (item.error ? '#fff1f0' : '#f5f5f5'),
                  alignSelf: item.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%', // Increased from 70% for better use of space on smaller screens
                  marginLeft: item.sender === 'user' ? 'auto' : '0',
                  marginRight: item.sender === 'ai' ? 'auto' : '0',
                }}
                bodyStyle={{ padding: '10px 15px' }}
              >
                <Text style={{ color: item.error ? '#cf1322' : undefined }}>{item.text}</Text>
                {item.sender === 'ai' && !item.error && item.sources && item.sources.length > 0 && (
                  <div style={{ marginTop: '8px', fontSize: '0.9em' }}>
                    <Text strong>Sources:</Text>
                    <List
                      size="small"
                      dataSource={item.sources}
                      renderItem={source => ( // Assuming source is an object like {name: string, url: string}
                        <List.Item style={{padding: '2px 0', borderBottom: 'none'}}>
                          <a href={source.url} target="_blank" rel="noopener noreferrer">{source.name}</a>
                        </List.Item>
                      )}
                      rowKey={(source, idx) => source.url || idx} // Add key for source list
                    />
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
        <div ref={messagesEndRef} />
        {isLoading && messages.length > 0 && messages[messages.length-1].sender === 'user' && ( // Show spin only when waiting for AI
          <div style={{ textAlign: 'center', padding: '10px' }}>
            <Spin />
          </div>
        )}
        {/* Global error display can be removed if errors are shown inline with messages */}
        {/* {error && !messages.some(msg => msg.error) && ( // Show global error if not displayed inline
          <Alert message={error} type="error" showIcon style={{ marginTop: 10 }} />
        )} */}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid #f0f0f0', flexShrink: 0 }}>
        <Input.Group compact style={{ display: 'flex' }}>
          <Input
            style={{ flexGrow: 1 }}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleSendMessage}
            placeholder="Type your message here..."
            disabled={isLoading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
          >
            Send
          </Button>
        </Input.Group>
        {error && ( // Display general error near input as well, if not shown inline
          <Alert message={error} type="error" showIcon style={{ marginTop: 10 }} />
        )}
      </div>
    </div>
  );
};

export default AIChatInterface;
