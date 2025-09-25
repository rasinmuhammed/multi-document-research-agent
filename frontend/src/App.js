import React, { useState, useEffect, useRef } from 'react';
import { Search, FileText, Trash2, Upload, Send, BookOpen, Zap, Download, Eye, EyeOff, Loader, ChevronDown, ChevronRight, ExternalLink, File, User, Bot } from 'lucide-react';

const API_BASE = 'http://localhost:5001';

// Modern Message Component
const Message = ({ message }) => {
  const [showSteps, setShowSteps] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const isUser = message.type === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-6">
        <div className="flex items-start gap-3 max-w-4xl">
          <div className="message-content order-2">
            <div className="bg-gradient-to-br from-blue-600 to-purple-700 text-white rounded-2xl px-6 py-4 shadow-lg">
              <p className="leading-relaxed">{message.content}</p>
            </div>
            <div className="text-xs text-gray-500 mt-2 text-right">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg order-1">
            <User size={18} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-start gap-3 max-w-4xl">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-lg">
          <Bot size={18} />
        </div>
        <div className="message-content flex-1">
          <div className="bg-white rounded-2xl px-6 py-4 shadow-lg border border-gray-100">
            <div className="prose prose-sm max-w-none">
              {message.content.split('\n').map((line, i) => (
                <p key={i} className="mb-2 last:mb-0 leading-relaxed text-gray-800">{line}</p>
              ))}
            </div>
          </div>

          {/* Sources Section */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4">
              <button
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                onClick={() => setShowSources(!showSources)}
              >
                {showSources ? <EyeOff size={16} /> : <Eye size={16} />}
                <BookOpen size={16} />
                Sources ({message.sources.length})
                {showSources ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
              {showSources && (
                <div className="mt-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
                  <div className="space-y-3">
                    {message.sources.map((source, i) => (
                      <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-lg shadow-sm">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <File size={14} className="text-gray-400" />
                            {source.url ? (
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800 font-medium text-sm flex items-center gap-1 transition-colors"
                              >
                                {source.name}
                                <ExternalLink size={12} />
                              </a>
                            ) : (
                              <span className="font-medium text-gray-700 text-sm">{source.name}</span>
                            )}
                            <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600 uppercase">
                              {source.type}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Research Steps Section */}
          {message.research_steps && message.research_steps.length > 0 && (
            <div className="mt-4">
              <button
                className="flex items-center gap-2 text-sm text-emerald-600 hover:text-emerald-800 font-medium transition-colors"
                onClick={() => setShowSteps(!showSteps)}
              >
                {showSteps ? <EyeOff size={16} /> : <Eye size={16} />}
                <Zap size={16} />
                Research Process ({message.research_steps.length} steps)
                {showSteps ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
              {showSteps && (
                <div className="mt-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-100">
                  <div className="space-y-4">
                    {message.research_steps.map((step, i) => (
                      <div key={i} className="bg-white rounded-lg p-4 shadow-sm">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-xs font-bold">
                            {step.step}
                          </div>
                          <span className="text-xs px-3 py-1 rounded-full bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-700 font-medium">
                            {step.tool}
                          </span>
                        </div>
                        <div className="mb-2">
                          <p className="text-sm text-gray-600 mb-1 font-medium">Query:</p>
                          <p className="text-sm text-gray-800 bg-gray-50 rounded px-3 py-2">
                            {typeof step.input === 'object' ? step.input.query : step.input}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 mb-1 font-medium">Result:</p>
                          <div className="text-sm text-gray-700 bg-gray-50 rounded p-3 leading-relaxed">
                            {step.output}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Message Footer */}
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-500">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
            <div className="flex items-center gap-3">
              {message.confidence && (
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  message.confidence === 'high'
                    ? 'bg-green-100 text-green-700'
                    : message.confidence === 'medium'
                    ? 'bg-yellow-100 text-yellow-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {message.confidence} confidence
                </span>
              )}
              {message.research_id && (
                <GenerateReportButton researchId={message.research_id} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Generate Report Button Component
const GenerateReportButton = ({ researchId }) => {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
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
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <button 
      className="flex items-center gap-1 text-xs px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-sm disabled:opacity-50"
      onClick={handleGenerateReport}
      disabled={isGenerating}
    >
      {isGenerating ? <Loader size={12} className="animate-spin" /> : <Download size={12} />}
      {isGenerating ? 'Generating...' : 'Report'}
    </button>
  );
};

// Document List Component
const DocumentList = ({ documents, onDelete, onRefresh, isRefreshing }) => {
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    switch (type.toLowerCase()) {
      case 'pdf': return '📄';
      case 'md': return '📝';
      case 'txt': return '📄';
      default: return '📄';
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="text-blue-600" size={20} />
            <h3 className="font-semibold text-gray-800">Document Library</h3>
            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
              {documents.length}
            </span>
          </div>
          <button 
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            <Search size={16} className={isRefreshing ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        {documents.map((doc, i) => (
          <div key={i} className="flex items-center gap-4 p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors duration-200 group">
            <div className="text-2xl">
              {getFileIcon(doc.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-800 truncate">{doc.name}</div>
              <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                <span>{formatFileSize(doc.size)}</span>
                <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded uppercase font-medium">
                  {doc.type}
                </span>
              </div>
            </div>
            <button 
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all duration-200 opacity-0 group-hover:opacity-100"
              onClick={() => onDelete(doc.name)}
              title="Delete document"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
        {documents.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <BookOpen size={48} className="mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">No documents yet</p>
            <p className="text-sm">Upload PDF, MD, or TXT files to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

// File Upload Component
const FileUpload = ({ onUpload }) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (files) => {
    const file = files[0];
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

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  return (
    <div className="mb-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.md,.txt"
        onChange={(e) => handleFileUpload(e.target.files)}
        disabled={uploading}
        className="hidden"
      />
      <div
        className={`border-2 border-dashed rounded-2xl p-6 text-center transition-all duration-300 cursor-pointer ${
          dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : uploading
            ? 'border-gray-300 bg-gray-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onClick={() => !uploading && fileInputRef.current?.click()}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-3">
          {uploading ? (
            <Loader className="text-blue-500 animate-spin" size={24} />
          ) : (
            <Upload className="text-gray-400" size={24} />
          )}
          <div>
            <p className="font-medium text-gray-700">
              {uploading ? 'Uploading...' : dragActive ? 'Drop files here' : 'Upload Documents'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {uploading ? 'Processing your file...' : 'PDF, MD, TXT files supported'}
            </p>
          </div>
        </div>
      </div>
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
  const [showDocuments, setShowDocuments] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);

  useEffect(() => {
    fetchSystemStatus();
    fetchChatHistory();
  }, []);

  const fetchSystemStatus = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setSystemStatus(data);
      setDocuments(data.documents_list || []);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setIsRefreshing(false);
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
        content: `I encountered an error: ${error.message}`,
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
    if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;

    try {
      const response = await fetch(`${API_BASE}/api/delete-document/${filename}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      
      if (response.ok) {
        fetchSystemStatus();
        // Show success message briefly
        const successEl = document.createElement('div');
        successEl.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        successEl.textContent = `${filename} deleted successfully`;
        document.body.appendChild(successEl);
        setTimeout(() => successEl.remove(), 3000);
      } else {
        throw new Error(result.error || 'Delete failed');
      }
    } catch (error) {
      alert('Delete error: ' + error.message);
    }
  };

  const exampleQuestions = [
    "Summarize the key findings in my documents",
    "What are the latest developments in AI research?",
    "Compare the methodologies mentioned in my PDFs",
    "Find connections between concepts across my documents"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-700 rounded-xl flex items-center justify-center">
                <Search className="text-white" size={20} />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-700 bg-clip-text text-transparent">
                  Orbuculum.ai
                </h1>
                <p className="text-sm text-gray-600">AI-Powered Research Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${systemStatus?.agent_initialized ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {systemStatus?.agent_initialized ? 'Online' : 'Offline'}
                </span>
              </div>
              <button 
                className="px-4 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
                onClick={() => setShowDocuments(!showDocuments)}
              >
                <FileText size={16} />
                {showDocuments ? 'Hide' : 'Show'} Documents ({documents.length})
              </button>
              <button 
                className="px-4 py-2 text-sm bg-red-50 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 transition-colors flex items-center gap-2"
                onClick={clearChat}
              >
                <Trash2 size={16} />
                Clear Chat
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Sidebar */}
        {showDocuments && (
          <div className="w-96 p-6 border-r border-gray-200/50">
            <FileUpload onUpload={fetchSystemStatus} />
            <DocumentList 
              documents={documents}
              onDelete={deleteDocument}
              onRefresh={fetchSystemStatus}
              isRefreshing={isRefreshing}
            />
          </div>
        )}

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="max-w-4xl mx-auto text-center py-12">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Search className="text-white" size={32} />
                </div>
                <h2 className="text-3xl font-bold text-gray-800 mb-4">Welcome to Orbuculum.ai</h2>
                <p className="text-xl text-gray-600 mb-8">Your AI-powered research companion</p>
                <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                  Ask me anything about your documents or general research topics. I can search through your uploaded documents and the web to provide comprehensive answers.
                </p>
                <div className="grid gap-4 max-w-2xl mx-auto">
                  {exampleQuestions.map((question, i) => (
                    <button
                      key={i}
                      className="p-4 text-left bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-xl hover:bg-white hover:shadow-lg transition-all duration-200 group"
                      onClick={() => setInputMessage(question)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center group-hover:from-blue-200 group-hover:to-purple-200 transition-colors">
                          <Search size={16} className="text-blue-600" />
                        </div>
                        <span className="text-gray-700 group-hover:text-gray-900">{question}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto">
                {messages.map((message) => (
                  <Message
                    key={message.id}
                    message={message}
                    isUser={message.type === 'user'}
                  />
                ))}

                {isLoading && (
                  <div className="flex justify-start mb-6">
                    <div className="flex items-start gap-3 max-w-4xl">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-lg">
                        <Bot size={18} />
                      </div>
                      <div className="bg-white rounded-2xl px-6 py-4 shadow-lg border border-gray-100">
                        <div className="flex items-center gap-3 text-emerald-600">
                          <Loader className="animate-spin" size={20} />
                          <span className="font-medium">Researching your question...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200/50 bg-white/80 backdrop-blur-xl p-6">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-4 items-end">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about your documents or research topics..."
                    disabled={isLoading}
                    rows="1"
                    className="w-full px-4 py-3 border border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none transition-all duration-200 disabled:bg-gray-50 disabled:text-gray-500"
                    style={{ minHeight: '48px', maxHeight: '120px' }}
                  />
                </div>
                <button 
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="w-12 h-12 bg-gradient-to-r from-blue-600 to-purple-700 text-white rounded-2xl flex items-center justify-center hover:from-blue-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  {isLoading ? (
                    <Loader className="animate-spin" size={20} />
                  ) : (
                    <Send size={20} />
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Press Enter to send, Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;