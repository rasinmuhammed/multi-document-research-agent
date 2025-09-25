import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'http://localhost:5001';

// Message Component
const Message = ({ message, isUser }) => {
  const [showSteps, setShowSteps] = useState(false);
  const [showSources, setShowSources] = useState(false);

  if (isUser) {
    return (
      <div className="message user-message">
        <div className="message-avatar">
          <span>👤</span>
        </div>
        <div className="message-content">
          <div className="message-text">{message.content}</div>
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="message assistant-message">
      <div className="message-avatar">
        <span>🔍</span>
      </div>
      <div className="message-content">
        <div className="message-text">
          {message.content.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
        
        {message.sources && message.sources.length > 0 && (
          <div className="message-metadata">
            <button 
              className="metadata-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              📚 Sources ({message.sources.length})
            </button>
            {showSources && (
              <div className="sources-list">
                {message.sources.map((source, i) => (
                  <div key={i} className="source-item">
                    <span className="source-badge">{i + 1}</span>
                    <span className="source-text">
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noopener noreferrer">
                          {source.name}
                        </a>
                      ) : (
                        source.name
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {message.research_steps && message.research_steps.length > 0 && (
          <div className="message-metadata">
            <button 
              className="metadata-toggle"
              onClick={() => setShowSteps(!showSteps)}
            >
              🔧 Research Process ({message.research_steps.length} steps)
            </button>
            {showSteps && (
              <div className="research-steps">
                {message.research_steps.map((step, i) => (
                  <div key={i} className="research-step">
                    <div className="step-header">
                      <span className="step-number">{step.step}</span>
                      <span className="step-tool">{step.tool}</span>
                    </div>
                    <div className="step-query">
                      Query: {typeof step.input === 'object' ? step.input.query : step.input}
                    </div>
                    <div className="step-result">{step.output}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="message-actions">
          <div className="message-time">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
          {message.confidence && (
            <span className={`confidence-badge ${message.confidence}`}>
              {message.confidence} confidence
            </span>
          )}
          {message.research_id && (
            <GenerateReportButton researchId={message.research_id} />
          )}
        </div>
      </div>
    </div>
  );
};

// Separate component for the Generate Report button
const GenerateReportButton = ({ researchId }) => {
  const handleGenerateReport = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/generate-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ research_id: researchId }),
      });

      const data = await response.json();
      
      if (response.ok) {
        window.open(`${API_BASE}/api/download-report/${researchId}`, '_blank');
      } else {
        throw new Error(data.error || 'Report generation failed');
      }
    } catch (error) {
      alert('Error generating report: ' + error.message);
    }
  };

  return (
    <button 
      className="action-button"
      onClick={handleGenerateReport}
    >
      📄 Generate Report
    </button>
  );
};

// Document List Component
const DocumentList = ({ documents, onDelete, onRefresh }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="documents-panel">
      <div className="documents-header">
        <h3>📚 Document Library</h3>
        <button className="refresh-button" onClick={onRefresh}>🔄</button>
      </div>
      <div className="documents-list">
        {documents.map((doc, i) => (
          <div key={i} className="document-item">
            <div className="document-info">
              <div className="document-name">{doc.name}</div>
              <div className="document-meta">
                <span className="document-size">{formatFileSize(doc.size)}</span>
                <span className="document-type">{doc.type.toUpperCase()}</span>
              </div>
            </div>
            <button 
              className="delete-button"
              onClick={() => onDelete(doc.name)}
              title="Delete document"
            >
              🗑️
            </button>
          </div>
        ))}
        {documents.length === 0 && (
          <div className="empty-state">
            No documents uploaded yet. Upload PDF, MD, or TXT files to get started.
          </div>
        )}
      </div>
    </div>
  );
};

// File Upload Component
const FileUpload = ({ onUpload }) => {
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/api/upload-document`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (response.ok) {
        onUpload(result.message);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error) {
      alert('Upload error: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.md,.txt"
        onChange={handleFileUpload}
        disabled={uploading}
        style={{ display: 'none' }}
      />
      <button 
        className="upload-button"
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
      >
        {uploading ? '📤 Uploading...' : '📁 Upload Document'}
      </button>
    </div>
  );
};

// Main App Component
const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [showDocuments, setShowDocuments] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSystemStatus();
    fetchChatHistory();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setSystemStatus(data);
      setDocuments(data.documents_list || []);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/chat-history`);
      const data = await response.json();
      setMessages(data.chat_history || []);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: inputMessage }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, data.message]);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`${API_BASE}/api/clear-chat`, { method: 'POST' });
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear chat:', error);
    }
  };

  const deleteDocument = async (filename) => {
    // Use window.confirm instead of confirm to avoid ESLint error
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/delete-document/${filename}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      
      if (response.ok) {
        fetchSystemStatus(); // Refresh document list
        alert(result.message);
      } else {
        throw new Error(result.error || 'Delete failed');
      }
    } catch (error) {
      alert('Delete error: ' + error.message);
    }
  };

  return (
    <div className="app">
      <div className="app-header">
        <h1>🔍 Research Agent</h1>
        <div className="header-controls">
          <div className="status-indicator">
            <div className={`status-dot ${systemStatus?.agent_initialized ? 'online' : 'offline'}`}></div>
            <span>{systemStatus?.agent_initialized ? 'Online' : 'Offline'}</span>
          </div>
          <button 
            className="docs-toggle"
            onClick={() => setShowDocuments(!showDocuments)}
          >
            📚 Documents ({documents.length})
          </button>
          <button className="clear-button" onClick={clearChat}>🗑️ Clear</button>
        </div>
      </div>

      <div className="app-body">
        {showDocuments && (
          <div className="sidebar">
            <FileUpload onUpload={fetchSystemStatus} />
            <DocumentList 
              documents={documents}
              onDelete={deleteDocument}
              onRefresh={fetchSystemStatus}
            />
          </div>
        )}

        <div className="chat-container">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-message">
                <h2>👋 Welcome to Research Agent</h2>
                <p>Ask me anything about your documents or general research topics!</p>
                <div className="example-questions">
                  <div className="example-question">
                    "Summarize the key findings in my documents"
                  </div>
                  <div className="example-question">
                    "What are the latest developments in AI?"
                  </div>
                  <div className="example-question">
                    "Compare different approaches mentioned in my PDFs"
                  </div>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <Message
                key={message.id}
                message={message}
                isUser={message.type === 'user'}
              />
            ))}

            {isLoading && (
              <div className="message assistant-message">
                <div className="message-avatar">
                  <span>🔍</span>
                </div>
                <div className="message-content">
                  <div className="loading-indicator">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <span>Researching...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a research question..."
                disabled={isLoading}
                rows="1"
              />
              <button 
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="send-button"
              >
                {isLoading ? '⏳' : '📤'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;