# 🔬 Enhanced AI Research Agent v2.0

A production-grade AI research assistant that combines local document analysis with intelligent web search to provide comprehensive, well-sourced answers to complex questions.

![Research Agent Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Version](https://img.shields.io/badge/Version-2.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Key Features

### 🧠 Intelligent Research Capabilities
- **Multi-Source Research**: Combines local documents (PDF, Markdown) with real-time web search
- **Advanced RAG**: Retrieval-Augmented Generation with ChromaDB vector store
- **Smart Query Enhancement**: Automatically improves search queries for better results
- **Source Quality Assessment**: Ranks and filters sources based on reliability and relevance

### 💬 Modern Chat Interface
- **Real-time Communication**: WebSocket-based chat with instant responses
- **Research Progress Tracking**: Live updates showing research steps and progress
- **Interactive Source Citations**: Click on sources to view detailed content
- **Export Conversations**: Download research sessions as formatted reports

### 🎯 Production-Grade Architecture
- **Scalable Backend**: Flask-SocketIO with async processing
- **Enhanced Error Handling**: Graceful fallbacks and comprehensive logging
- **Caching System**: Intelligent caching for improved performance
- **Docker Support**: Complete containerization with multi-stage builds

### 📊 Advanced Analytics
- **Confidence Scoring**: AI-powered confidence assessment for each answer
- **Research Quality Metrics**: Depth, diversity, and reliability scoring
- **Source Categorization**: Automatic classification of academic, technical, and reference sources

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Groq API Key (get from [console.groq.com](https://console.groq.com/))
- 4GB+ RAM recommended

### Option 1: Standard Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/ai-research-agent.git
   cd ai-research-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

4. **Add your documents**
   ```bash
   mkdir documents
   # Copy your PDF and Markdown files to the documents/ directory
   ```

5. **Start the application**
   ```bash
   python run.py
   ```

6. **Access the interface**
   - Open http://localhost:5001 in your browser
   - Start asking research questions!

### Option 2: Docker Installation

1. **Using Docker Compose (Recommended)**
   ```bash
   git clone https://github.com/your-repo/ai-research-agent.git
   cd ai-research-agent
   
   # Copy and edit environment file
   cp .env.example .env
   
   # Start all services
   docker-compose up -d
   ```

2. **Using Docker only**
   ```bash
   docker build -t research-agent .
   docker run -p 5001:5001 -e GROQ_API_KEY=your_key -v $(pwd)/documents:/app/documents research-agent
   ```

## 🎯 Usage Examples

### Basic Research Questions
```
"Explain quantum computing and its impact on cybersecurity"
"Compare renewable energy technologies and their efficiency"
"What are the latest developments in AI ethics?"
```

### Advanced Research Queries
```
"Analyze the trade-offs between different machine learning architectures for natural language processing"
"Provide a comprehensive overview of blockchain scalability solutions with technical comparisons"
"Research the current state of autonomous vehicle safety regulations across different countries"
```

### Domain-Specific Questions
```
"What are the best practices for implementing zero-trust security architecture?"
"Compare the effectiveness of different cancer immunotherapy approaches"
"Analyze the economic impact of remote work on urban development"
```

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *required* | Your Groq API key |
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `5001` | Server port |
| `DEBUG` | `False` | Enable debug mode |
| `MAX_TOKENS` | `4000` | Maximum tokens per LLM request |
| `TEMPERATURE` | `0.1` | LLM temperature (creativity) |
| `CHUNK_SIZE` | `1000` | Document chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap for context |

### Advanced Configuration

Create a `config.py` file for advanced settings:

```python
# Advanced Research Agent Configuration
RESEARCH_CONFIG = {
    "max_search_iterations": 8,
    "source_quality_threshold": 0.6,
    "cache_ttl_seconds": 3600,
    "max_concurrent_searches": 3,
    "preferred_sources": [
        "arxiv.org", "wikipedia.org", "github.com"
    ]
}
```

## 📁 Project Structure

```
ai-research-agent/
├── agent/
│   ├── __init__.py
│   ├── research_agent.py      # Enhanced research logic
│   ├── document_processor.py  # Document loading and processing
│   ├── vector_store.py        # ChromaDB vector store management
│   └── web_searcher.py        # Enhanced web search capabilities
├── templates/
│   └── chat.html             # Modern chat interface
├── documents/                # Your PDF/MD documents go here
├── data/                    # Vector database storage
├── logs/                    # Application logs
├── app.py                   # Flask-SocketIO server
├── run.py                   # Production startup script
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-service setup
└── README.md               # This documentation
```

## 🔧 API Documentation

### WebSocket Events

#### Client → Server Events

**`send_message`**
```javascript
socket.emit('send_message', {
    message: "Your research question here"
});
```

**`get_source_details`**
```javascript
socket.emit('get_source_details', {
    research_id: "uuid-here",
    source_id: "LOCAL-chunk_123"
});
```

#### Server → Client Events

**`new_message`**
```javascript
socket.on('new_message', (data) => {
    // data contains: type, content, metadata, timestamp
});
```

**`research_update`**
```javascript
socket.on('research_update', (update) => {
    // update contains: step, message, progress
});
```

### REST API Endpoints

**GET `/api/status`**
```json
{
    "agent_initialized": true,
    "documents_count": 42,
    "active_sessions": 3,
    "status": "online"
}
```

## 📊 Performance Metrics

### Research Quality Indicators

- **Confidence Levels**: `very_low` | `low` | `medium` | `high` | `very_high`
- **Research Depth**: `minimal` | `adequate` | `thorough` | `comprehensive`
- **Source Diversity**: `limited` | `fair` | `good` | `excellent`

### System Performance

- **Average Response Time**: 5-15 seconds for complex queries
- **Memory Usage**: ~2GB with 1000 documents indexed
- **Concurrent Users**: Supports 10+ simultaneous research sessions
- **Document Processing**: ~1000 documents in under 2 minutes

## 🔐 Security Features

- **Input Sanitization**: All user inputs are validated and sanitized
- **API Rate Limiting**: Prevents abuse with configurable rate limits
- **Secure Headers**: HTTPS-ready with security headers
- **Non-root Container**: Docker container runs as non-privileged user
- **Environment Isolation**: Sensitive data isolated in environment variables

## 🐛 Troubleshooting

### Common Issues

**"Research agent not initialized"**
```bash
# Check your GROQ_API_KEY in .env file
echo $GROQ_API_KEY
# Verify API key validity at console.groq.com
```

**"No relevant documents found"**
```bash
# Check documents directory
ls -la documents/
# Ensure PDF/MD files are present and readable
# Check logs for processing errors
tail -f logs/research_agent_*.log
```

**Connection issues**
```bash
# Check if port 5001 is available
netstat -tulpn | grep 5001
# Try different port
PORT=5002 python run.py
```

### Debug Mode

Enable detailed logging:
```bash
DEBUG=True python run.py
```

Check system status:
```bash
curl http://localhost:5001/api/status
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Build production image**
   ```bash
   docker-compose -f docker-compose.yml build
   ```

2. **Deploy with load balancer**
   ```bash
   docker-compose --profile production up -d
   ```

3. **Scale horizontally**
   ```bash
   docker-compose up -d --scale research-agent=3
   ```

### Cloud Deployment

**AWS ECS**
```bash
# Build and push to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-west-2.amazonaws.com
docker build -t research-agent .
docker tag research-agent:latest your-account.dkr.ecr.us-west-2.amazonaws.com/research-agent:latest
docker push your-account.dkr.ecr.us-west-2.amazonaws.com/research-agent:latest
```

**Google Cloud Run**
```bash
gcloud run deploy research-agent \
    --image gcr.io/your-project/research-agent \
    --port 5001 \
    --memory 4Gi \
    --cpu 2 \
    --max-instances 10
```

## 🔄 Updates and Maintenance

### Updating the Application

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. **Restart services**
   ```bash
   docker-compose restart research-agent
   ```

### Database Maintenance

```bash
# Clear vector database cache
rm -rf data/chroma_db/*

# Reindex all documents
python -c "from agent.research_agent import ResearchAgent; agent = ResearchAgent('your-api-key'); agent._load_initial_documents()"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork and clone**
   ```bash
   git clone https://github.com/your-username/ai-research-agent.git
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

