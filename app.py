from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from agent.research_agent import ResearchAgent
import tempfile
import threading
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables
agent = None
research_cache = {}
active_sessions = {}

def initialize_agent():
    """Initialize the research agent."""
    global agent
    try:
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        agent = ResearchAgent(
            groq_api_key=groq_api_key,
            documents_dir="./documents"
        )
        logger.info("Research agent initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return False

class ResearchSession:
    def __init__(self, session_id, socket_id):
        self.session_id = session_id
        self.socket_id = socket_id
        self.messages = []
        self.current_research = None
        
    def add_message(self, message_type, content, metadata=None):
        message = {
            'id': str(uuid.uuid4()),
            'type': message_type,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        self.messages.append(message)
        return message

@app.route('/')
def index():
    """Main chat interface."""
    agent_status = agent is not None
    doc_count = 0
    
    if agent:
        try:
            vector_info = agent.vector_store.get_collection_info()
            doc_count = vector_info.get('count', 0)
        except:
            doc_count = 0
    
    return render_template('chat.html', 
                         agent_status=agent_status, 
                         doc_count=doc_count)

@socketio.on('connect')
def handle_connect():
    session_id = str(uuid.uuid4())
    active_sessions[request.sid] = ResearchSession(session_id, request.sid)
    
    emit('connected', {
        'session_id': session_id,
        'status': 'connected',
        'agent_ready': agent is not None
    })
    
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in active_sessions:
        del active_sessions[request.sid]
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming research questions."""
    if request.sid not in active_sessions:
        emit('error', {'message': 'Session not found'})
        return
    
    session = active_sessions[request.sid]
    question = data.get('message', '').strip()
    
    if not question:
        emit('error', {'message': 'No question provided'})
        return
    
    if not agent:
        emit('error', {'message': 'Research agent not initialized'})
        return
    
    # Add user message
    user_message = session.add_message('user', question)
    emit('new_message', user_message)
    
    # Start research in background
    def conduct_research():
        try:
            research_id = str(uuid.uuid4())
            session.current_research = research_id
            
            # Send research started message
            thinking_message = session.add_message('assistant_thinking', 'Starting research...', {
                'research_id': research_id,
                'status': 'starting'
            })
            socketio.emit('new_message', thinking_message, room=request.sid)
            
            # Conduct research with progress updates
            result = conduct_research_with_updates(question, session, research_id)
            
            # Cache result
            research_cache[research_id] = result
            
            # Send final answer
            answer_message = session.add_message('assistant', result['answer'], {
                'research_id': research_id,
                'confidence_level': result['confidence_level'],
                'sources_used': result['sources_used'],
                'steps_count': len(result['intermediate_steps']),
                'timestamp': result['timestamp']
            })
            
            socketio.emit('new_message', answer_message, room=request.sid)
            
        except Exception as e:
            logger.error(f"Research error: {e}")
            error_message = session.add_message('error', f'Research failed: {str(e)}')
            socketio.emit('new_message', error_message, room=request.sid)
    
    # Run research in thread
    thread = threading.Thread(target=conduct_research)
    thread.daemon = True
    thread.start()

def conduct_research_with_updates(question, session, research_id):
    """Conduct research with real-time updates."""
    
    # Step 1: Analyze question
    socketio.emit('research_update', {
        'research_id': research_id,
        'step': 'analyzing',
        'message': 'Analyzing your question and planning research strategy...',
        'progress': 10
    }, room=session.socket_id)
    
    time.sleep(0.5)
    
    # Step 2: Search local documents
    socketio.emit('research_update', {
        'research_id': research_id,
        'step': 'local_search',
        'message': 'Searching through local documents and knowledge base...',
        'progress': 30
    }, room=session.socket_id)
    
    # Conduct actual research
    result = agent.research(question)
    
    # Step 3: Web search if needed
    if len(result.get('intermediate_steps', [])) > 1:
        socketio.emit('research_update', {
            'research_id': research_id,
            'step': 'web_search',
            'message': 'Searching web resources for additional information...',
            'progress': 60
        }, room=session.socket_id)
        time.sleep(0.5)
    
    # Step 4: Synthesizing
    socketio.emit('research_update', {
        'research_id': research_id,
        'step': 'synthesizing',
        'message': 'Analyzing and synthesizing information from all sources...',
        'progress': 80
    }, room=session.socket_id)
    
    time.sleep(0.5)
    
    # Step 5: Complete
    socketio.emit('research_update', {
        'research_id': research_id,
        'step': 'complete',
        'message': 'Research complete!',
        'progress': 100
    }, room=session.socket_id)
    
    return result

@socketio.on('get_source_details')
def handle_source_details(data):
    """Get detailed information about a source."""
    research_id = data.get('research_id')
    source_id = data.get('source_id')
    
    if research_id in research_cache:
        result = research_cache[research_id]
        
        # Find the specific source details from intermediate steps
        source_details = []
        for step in result.get('intermediate_steps', []):
            if len(step) >= 2:
                observation = str(step[1])
                if source_id in observation:
                    source_details.append({
                        'tool': step[0].tool if hasattr(step[0], 'tool') else 'Unknown',
                        'query': step[0].tool_input if hasattr(step[0], 'tool_input') else 'N/A',
                        'content': observation
                    })
        
        emit('source_details', {
            'source_id': source_id,
            'details': source_details
        })

@socketio.on('export_conversation')
def handle_export(data):
    """Export conversation to markdown."""
    if request.sid not in active_sessions:
        emit('error', {'message': 'Session not found'})
        return
    
    session = active_sessions[request.sid]
    
    # Generate markdown report
    report = generate_conversation_report(session)
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.md', 
        delete=False,
        encoding='utf-8'
    )
    temp_file.write(report)
    temp_file.close()
    
    emit('export_ready', {
        'filename': f'research_conversation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    })

def generate_conversation_report(session):
    """Generate a markdown report of the conversation."""
    report = f"""# Research Conversation Report

**Session ID**: {session.session_id}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""
    
    for message in session.messages:
        if message['type'] == 'user':
            report += f"## 🙋‍♂️ User Question\n\n{message['content']}\n\n"
        elif message['type'] == 'assistant':
            report += f"## 🤖 AI Response\n\n{message['content']}\n\n"
            
            # Add metadata
            metadata = message.get('metadata', {})
            if metadata:
                report += f"**Research Details:**\n"
                report += f"- Confidence Level: {metadata.get('confidence_level', 'N/A')}\n"
                report += f"- Sources Used: {len(metadata.get('sources_used', []))}\n"
                report += f"- Research Steps: {metadata.get('steps_count', 0)}\n\n"
                
                if metadata.get('sources_used'):
                    report += f"**Sources:**\n"
                    for i, source in enumerate(metadata['sources_used'], 1):
                        report += f"{i}. {source}\n"
                    report += "\n"
        
        report += "---\n\n"
    
    report += "*Generated by AI Research Agent*\n"
    return report

@app.route('/api/status')
def status():
    """Get system status."""
    try:
        doc_count = 0
        agent_status = False
        
        if agent:
            agent_status = True
            try:
                vector_info = agent.vector_store.get_collection_info()
                doc_count = vector_info.get('count', 0)
            except:
                doc_count = 0
        
        return jsonify({
            'agent_initialized': agent_status,
            'documents_count': doc_count,
            'active_sessions': len(active_sessions),
            'model': 'Groq Llama-3.1-8b-instant',
            'vector_store': 'ChromaDB',
            'status': 'online' if agent_status else 'offline'
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize agent
    if not initialize_agent():
        print("❌ Failed to initialize research agent. Check your GROQ_API_KEY.")
        exit(1)
    
    print("🚀 Starting Enhanced Research Agent...")
    print("💬 Chat Interface with Real-time Updates")
    print("📱 Open http://localhost:5001 in your browser")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)