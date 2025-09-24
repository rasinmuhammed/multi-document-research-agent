from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from agent.research_agent import ResearchAgent
import tempfile
import threading
import uuid
from werkzeug.utils import secure_filename
import shutil

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Enable CORS for React frontend
CORS(app, origins=["http://localhost:3000"])

# Configuration
UPLOAD_FOLDER = './documents'
ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables
agent = None
research_cache = {}
chat_history = []

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_agent():
    """Initialize the research agent."""
    global agent
    try:
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Ensure documents directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        agent = ResearchAgent(
            groq_api_key=groq_api_key,
            documents_dir=UPLOAD_FOLDER
        )
        logger.info("Research agent initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return False

@app.route('/')
def index():
    """Serve the React app (in production, this would serve built files)."""
    return jsonify({"message": "Research Agent API is running. Use the React frontend."})

@app.route('/api/status')
def status():
    """Get system status and document list."""
    try:
        doc_count = 0
        agent_status = False
        documents_list = []
        
        if agent:
            agent_status = True
            try:
                vector_info = agent.vector_store.get_collection_info()
                doc_count = vector_info.get('count', 0)
            except:
                doc_count = 0
        
        # Get list of documents
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename)):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file_stat = os.stat(file_path)
                    documents_list.append({
                        'name': filename,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'type': filename.split('.')[-1].lower()
                    })
        
        return jsonify({
            'agent_initialized': agent_status,
            'documents_count': doc_count,
            'documents_list': documents_list,
            'model': 'Groq Llama-3.1-8B-Instant',
            'vector_store': 'ChromaDB',
            'status': 'online' if agent_status else 'offline'
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """Upload a new document."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Avoid filename conflicts
            counter = 1
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1]
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                filename = f"{base_name}_{counter}.{extension}"
                counter += 1
            
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Reinitialize agent to load new documents
            if agent:
                try:
                    # Process the new document
                    documents = agent.doc_processor.load_documents(UPLOAD_FOLDER)
                    if documents:
                        # Clear and rebuild vector store
                        agent.vector_store = agent.vector_store.__class__(agent.vector_store.persist_directory)
                        agent.vector_store.add_documents(documents)
                        logger.info(f"Reindexed documents including {filename}")
                except Exception as e:
                    logger.error(f"Error reindexing documents: {e}")
            
            return jsonify({
                'message': f'File {filename} uploaded successfully',
                'filename': filename
            })
        else:
            return jsonify({'error': 'File type not allowed. Use PDF, MD, or TXT files.'}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-document/<filename>', methods=['DELETE'])
def delete_document(filename):
    """Delete a document."""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(file_path)
        
        # Reinitialize agent to reload documents
        if agent:
            try:
                documents = agent.doc_processor.load_documents(UPLOAD_FOLDER)
                # Clear and rebuild vector store
                agent.vector_store = agent.vector_store.__class__(agent.vector_store.persist_directory)
                if documents:
                    agent.vector_store.add_documents(documents)
                logger.info(f"Reindexed documents after deleting {filename}")
            except Exception as e:
                logger.error(f"Error reindexing documents: {e}")
        
        return jsonify({'message': f'File {filename} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and research."""
    global chat_history
    
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        if not agent:
            return jsonify({'error': 'Research agent not initialized'}), 500
        
        # Generate unique ID for this chat
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Add user message to history
        user_message = {
            'id': f"user_{chat_id}",
            'type': 'user',
            'content': message,
            'timestamp': timestamp
        }
        chat_history.append(user_message)
        
        # Conduct research
        logger.info(f"Starting research for: {message}")
        result = agent.research(message)
        
        # Cache result
        research_cache[chat_id] = result
        
        # Create assistant response with research steps
        research_steps = []
        for i, step in enumerate(result['intermediate_steps']):
            research_steps.append({
                'step': i + 1,
                'tool': step[0].tool if hasattr(step[0], 'tool') else 'Unknown',
                'input': step[0].tool_input if hasattr(step[0], 'tool_input') else 'N/A',
                'output': str(step[1])[:500] + '...' if len(str(step[1])) > 500 else str(step[1]),
                'timestamp': timestamp
            })
        
        assistant_message = {
            'id': f"assistant_{chat_id}",
            'type': 'assistant',
            'content': result['answer'],
            'timestamp': result['timestamp'],
            'research_steps': research_steps,
            'sources': result['sources_used'],
            'confidence': result['confidence_level'],
            'research_id': chat_id
        }
        
        chat_history.append(assistant_message)
        
        # Keep only last 50 messages
        if len(chat_history) > 50:
            chat_history = chat_history[-50:]
        
        return jsonify({
            'message': assistant_message,
            'chat_history': chat_history[-10:]  # Return last 10 messages
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat-history')
def get_chat_history():
    """Get chat history."""
    try:
        return jsonify({
            'chat_history': chat_history[-20:]  # Return last 20 messages
        })
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-chat', methods=['POST'])
def clear_chat():
    """Clear chat history."""
    global chat_history
    try:
        chat_history = []
        return jsonify({'message': 'Chat history cleared'})
    except Exception as e:
        logger.error(f"Clear chat error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate a full research report."""
    try:
        data = request.get_json()
        research_id = data.get('research_id')
        
        if not research_id or research_id not in research_cache:
            return jsonify({'error': 'Invalid research ID'}), 400
        
        result = research_cache[research_id]
        
        # Generate report
        report = agent.generate_report(result)
        
        return jsonify({
            'report_content': report,
            'download_url': f'/api/download-report/{research_id}'
        })
        
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-report/<research_id>')
def download_report(research_id):
    """Download research report."""
    try:
        if research_id not in research_cache:
            return jsonify({'error': 'Invalid research ID'}), 400
        
        result = research_cache[research_id]
        report = agent.generate_report(result)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.md', 
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(report)
        temp_file.close()
        
        filename = f"research_report_{result['timestamp'][:10]}.md"
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize agent
    if not initialize_agent():
        print("❌ Failed to initialize research agent. Check your GROQ_API_KEY.")
        exit(1)
    
    print("🚀 Starting Flask server...")
    print("🔍 Multi-Document Research Agent API")
    print("📱 Backend running on http://localhost:5001")
    print("🎨 Frontend should run on http://localhost:3000")
    
    app.run(debug=True, host='0.0.0.0', port=5001)