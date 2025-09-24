#!/usr/bin/env python3
"""
Production-grade startup script for Enhanced AI Research Agent
"""

import os
import sys
import logging
import signal
import time
from pathlib import Path
from dotenv import load_dotenv
import colorlog

def setup_logging():
    """Setup enhanced logging with colors and file output."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Setup color logging for console
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    
    # Setup file logging
    file_handler = logging.FileHandler(
        logs_dir / f"research_agent_{time.strftime('%Y%m%d')}.log"
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('chromadb').setLevel(logging.WARNING)

def check_environment():
    """Check environment setup and requirements."""
    logger = logging.getLogger(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Fix HuggingFace tokenizers parallelism warning
    if 'TOKENIZERS_PARALLELISM' not in os.environ:
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        logger.info("🔧 Set TOKENIZERS_PARALLELISM=false to avoid threading warnings")
    
    # Check required environment variables
    required_vars = ['GROQ_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please create a .env file with the following variables:")
        for var in missing_vars:
            logger.info(f"  {var}=your_value_here")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        return False
    
    # Check if documents directory exists
    docs_dir = Path("documents")
    if not docs_dir.exists():
        logger.warning("⚠️  Documents directory not found, creating it...")
        docs_dir.mkdir(exist_ok=True)
        logger.info("📁 Created documents directory. Add your PDF/MD files here.")
    else:
        doc_count = len([f for f in docs_dir.glob("*") if f.suffix.lower() in ['.pdf', '.md']])
        logger.info(f"📚 Found {doc_count} documents in ./documents/")
    
    # Check data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    logger.info("✅ Environment check passed")
    return True

def check_dependencies():
    """Check if all required packages are installed."""
    logger = logging.getLogger(__name__)
    
    required_packages = [
        'flask', 'flask_socketio', 'langchain', 'langchain_groq',
        'chromadb', 'sentence_transformers', 'beautifulsoup4',
        'pypdf', 'unstructured', 'python_dotenv', 'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('_', '-'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Missing required packages: {', '.join(missing_packages)}")
        logger.info("Install missing packages with:")
        logger.info(f"  pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("✅ All dependencies are installed")
    return True

def display_banner():
    """Display startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🔬 Enhanced AI Research Agent v2.0                      ║
║                                                                      ║
║              Production-Grade Multi-Document Research                ║
║              Powered by Groq • LangChain • ChromaDB                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def setup_signal_handlers():
    """Setup graceful shutdown handlers."""
    def signal_handler(signum, frame):
        logger = logging.getLogger(__name__)
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_health_checks():
    """Run system health checks."""
    logger = logging.getLogger(__name__)
    
    try:
        # Test Groq API connection
        from langchain_groq import ChatGroq
        llm = ChatGroq(
            groq_api_key=os.getenv('GROQ_API_KEY'),
            model_name="llama-3.1-8b-instant"
        )
        test_response = llm.invoke("Test connection")
        logger.info("✅ Groq API connection successful")
        
        # Test vector store initialization
        from agent.vector_store import VectorStoreManager
        vector_store = VectorStoreManager()
        logger.info("✅ Vector store initialization successful")
        
        # Test web search
        from agent.web_searcher import EnhancedWebSearcher
        web_searcher = EnhancedWebSearcher()
        logger.info("✅ Web searcher initialization successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False

def start_server():
    """Start the Flask-SocketIO server."""
    logger = logging.getLogger(__name__)
    
    try:
        # Import and run the main application
        from app import socketio, app, initialize_agent
        
        # Initialize the research agent
        logger.info("🔄 Initializing research agent...")
        if not initialize_agent():
            logger.error("❌ Failed to initialize research agent")
            return False
        
        logger.info("✅ Research agent initialized successfully")
        
        # Get configuration
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5001))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"🚀 Starting server on {host}:{port}")
        logger.info(f"💬 Chat interface: http://localhost:{port}")
        logger.info(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
        
        # Start the server
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True,
            log_output=not debug
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        return False
    
    return True

def create_sample_env():
    """Create a sample .env file if it doesn't exist."""
    env_file = Path('.env')
    if not env_file.exists():
        sample_env = """# Enhanced AI Research Agent Configuration

# Required: Get your API key from https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Optional: Server configuration
HOST=0.0.0.0
PORT=5001
DEBUG=False

# Optional: Advanced settings
MAX_TOKENS=4000
TEMPERATURE=0.1
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
"""
        env_file.write_text(sample_env)
        print(f"📝 Created sample .env file: {env_file}")
        print("Please edit it with your actual API keys and settings.")

def main():
    """Main startup function."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Display banner
    display_banner()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Create sample .env if needed
    create_sample_env()
    
    # Run checks
    logger.info("🔍 Running startup checks...")
    
    if not check_environment():
        sys.exit(1)
    
    
    if not run_health_checks():
        logger.warning("⚠️  Some health checks failed, but attempting to start anyway...")
    
    # Start the server
    logger.info("🎯 All checks passed, starting Enhanced AI Research Agent...")
    start_server()

if __name__ == "__main__":
    main()