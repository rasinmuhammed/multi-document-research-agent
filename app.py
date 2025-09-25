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
processed_documents = set()  # Track processed documents

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

def get_file_info(file_path):
    """Get file information including size and type."""
    try:
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
        return {
            'name': filename,
            'size': stat.st_size,
            'type': file_ext,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {e}")
        return None

@app.route('/api/status')
def status():
    """Get system status and document list."""
    try:
        documents_list = []
        
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                if allowed_file(filename):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file_info = get_file_info(file_path)
                    if file_info:
                        documents_list.append(file_info)
        
        # Get vector store info
        vector_info = {}
        if agent and agent.vector_store:
            vector_info = agent.vector_store.get_collection_info()
        
        return jsonify({
            'status': 'online',
            'agent_initialized': agent is not None,
            'documents_count': len(documents_list),
            'documents_list': documents_list,
            'vector_store_info': vector_info,
            'processed_documents': len(processed_documents),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """Upload a new document with improved processing."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Check if file already exists
            if os.path.exists(file_path) and filename in processed_documents:
                return jsonify({
                    'message': f'File {filename} already exists and is processed',
                    'filename': filename,
                    'status': 'exists'
                })
            
            file.save(file_path)
            
            if agent:
                try:
                    # Process only the new document
                    documents = agent.doc_processor.load_documents(UPLOAD_FOLDER)
                    # Filter to only new documents
                    new_documents = [doc for doc in documents 
                                   if doc.metadata.get('source_file') == filename]
                    
                    if new_documents:
                        agent.vector_store.add_documents(new_documents)
                        processed_documents.add(filename)
                        logger.info(f"Added {len(new_documents)} chunks from {filename} to vector store")
                except Exception as e:
                    logger.error(f"Error adding document to vector store: {e}")
                    return jsonify({'error': f'Failed to process document: {str(e)}'}), 500
            
            return jsonify({
                'message': f'File {filename} uploaded and processed successfully',
                'filename': filename,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'File type not allowed. Use PDF, MD, or TXT files.'}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-document/<filename>', methods=['DELETE'])
def delete_document(filename):
    """Delete a document with improved cleanup."""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        os.remove(file_path)
        
        # Remove from processed documents set
        processed_documents.discard(filename)
        
        if agent:
            try:
                # Delete documents from vector store by source filename
                agent.vector_store.delete_by_source(filename)
                logger.info(f"Deleted {filename} from vector store")
            except Exception as e:
                logger.error(f"Error deleting documents from vector store: {e}")
        
        return jsonify({'message': f'File {filename} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with improved response formatting."""
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
        
        # Format research steps with better presentation
        research_steps = []
        for i, step in enumerate(result['intermediate_steps']):
            tool_name = step[0].tool if hasattr(step[0], 'tool') else 'Unknown'
            tool_input = step[0].tool_input if hasattr(step[0], 'tool_input') else 'N/A'
            
            # Handle different input formats
            if isinstance(tool_input, dict):
                display_input = tool_input.get('query', str(tool_input))
            else:
                display_input = str(tool_input)
            
            # Truncate long outputs for better readability
            output_text = str(step[1])
            if len(output_text) > 800:
                output_text = output_text[:800] + '... [truncated]'
            
            research_steps.append({
                'step': i + 1,
                'tool': tool_name,
                'input': display_input,
                'output': output_text,
                'timestamp': timestamp
            })
        
        # Format sources with better aliases
        formatted_sources = []
        for source in result['sources_used']:
            # Create better display names
            source_name = source.get('name', 'Unknown Source')
            if source.get('type') == 'local':
                # For local files, just use the filename without path
                source_name = os.path.basename(source_name) if source_name else 'Local Document'
            elif source.get('url'):
                # For web sources, use domain name if available
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(source['url']).netloc
                    if domain:
                        source_name = f"{source_name} ({domain})"
                except:
                    pass
            
            formatted_sources.append({
                'name': source_name,
                'type': source.get('type', 'unknown'),
                'url': source.get('url')
            })
        
        assistant_message = {
            'id': f"assistant_{chat_id}",
            'type': 'assistant',
            'content': result['answer'],
            'timestamp': result['timestamp'],
            'research_steps': research_steps,
            'sources': formatted_sources,
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
    """Generate a full research report with improved formatting."""
    try:
        data = request.get_json()
        research_id = data.get('research_id')
        
        if not research_id or research_id not in research_cache:
            return jsonify({'error': 'Invalid research ID'}), 400
        
        result = research_cache[research_id]
        
        # Generate enhanced report
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
        
        # Create a better filename
        timestamp = result.get('timestamp', datetime.now().isoformat())[:10]
        question_words = result.get('question', 'research')[:30].replace(' ', '_').replace('?', '').replace('/', '_')
        filename = f"orbuculum_report_{timestamp}_{question_words}.md"
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reinitialize-documents', methods=['POST'])
def reinitialize_documents():
    """Reinitialize all documents (useful for fixing issues)."""
    global processed_documents
    try:
        if not agent:
            return jsonify({'error': 'Agent not initialized'}), 500
        
        # Clear processed documents tracking
        processed_documents.clear()
        
        # Rebuild vector store from all documents
        documents = agent.doc_processor.load_documents(UPLOAD_FOLDER)
        agent.vector_store.rebuild_from_documents(documents)
        
        # Update processed documents set
        for doc in documents:
            source_file = doc.metadata.get('source_file')
            if source_file:
                processed_documents.add(source_file)
        
        return jsonify({
            'message': f'Successfully reinitialized {len(documents)} document chunks',
            'documents_processed': len(processed_documents)
        })
        
    except Exception as e:
        logger.error(f"Reinitialize error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize agent
    if not initialize_agent():
        print("❌ Failed to initialize research agent. Check your GROQ_API_KEY.")
        exit(1)
    
    print("🚀 Starting Orbuculum.ai server...")
    print("🔍 AI-Powered Research Assistant")
    print("📱 Backend running on http://localhost:5001")
    print("🎨 Frontend should run on http://localhost:3000")
    
    app.run(debug=True, host='0.0.0.0', port=5001)