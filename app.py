from flask import Flask, render_template, request, jsonify, send_file
import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from agent.research_agent import ResearchAgent
import tempfile
import threading
import uuid

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global variables
agent = None
research_cache = {}

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

@app.route('/')
def index():
    """Main page."""
    # Check if agent is initialized
    agent_status = agent is not None
    doc_count = 0
    
    if agent:
        try:
            vector_info = agent.vector_store.get_collection_info()
            doc_count = vector_info.get('count', 0)
        except:
            doc_count = 0
    
    return render_template('index.html', 
                         agent_status=agent_status, 
                         doc_count=doc_count)

@app.route('/api/research', methods=['POST'])
def research():
    """Conduct research on the given question."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        if not agent:
            return jsonify({'error': 'Research agent not initialized'}), 500
        
        # Generate unique ID for this research
        research_id = str(uuid.uuid4())
        
        # Conduct research
        logger.info(f"Starting research for: {question}")
        result = agent.research(question)
        
        # Cache result
        research_cache[research_id] = result
        
        # Structure response
        response = {
            'research_id': research_id,
            'question': result['question'],
            'answer': result['answer'],
            'timestamp': result['timestamp'],
            'confidence_level': result['confidence_level'],
            'sources_count': len(result['sources_used']),
            'steps_count': len(result['intermediate_steps']),
            'sources_used': result['sources_used'],
            'intermediate_steps': [
                {
                    'step': i + 1,
                    'tool': step[0].tool if hasattr(step[0], 'tool') else 'Unknown',
                    'input': step[0].tool_input if hasattr(step[0], 'tool_input') else 'N/A',
                    'output': str(step[1])[:500] + '...' if len(str(step[1])) > 500 else str(step[1])
                }
                for i, step in enumerate(result['intermediate_steps'])
            ]
        }
        
        logger.info(f"Research completed successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Research error: {e}")
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
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.md', 
            delete=False,
            encoding='utf-8'
        )
        temp_file.write(report)
        temp_file.close()
        
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
            'model': 'Groq Llama-3-70B',
            'vector_store': 'ChromaDB',
            'status': 'online' if agent_status else 'offline'
        })
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

# Template for the HTML interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Multi-Document Research Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 25%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #ffffff;
            padding: 2rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #64ffda 0%, #bb86fc 50%, #03dac6 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .input-group {
            margin-bottom: 2rem;
        }

        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
        }

        .question-input {
            width: 100%;
            min-height: 120px;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            color: #ffffff;
            font-size: 1rem;
            resize: vertical;
            font-family: inherit;
        }

        .question-input:focus {
            outline: none;
            border-color: #64ffda;
            box-shadow: 0 0 0 2px rgba(100, 255, 218, 0.2);
        }

        .btn {
            padding: 0.8rem 2rem;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 1rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, #64ffda 0%, #03dac6 100%);
            color: #0f0f1a;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(100, 255, 218, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }

        .loading.visible {
            display: block;
        }

        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(100, 255, 218, 0.1);
            border-top: 3px solid #64ffda;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .results {
            display: none;
        }

        .results.visible {
            display: block;
        }

        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.03);
            padding: 1rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4caf50;
            box-shadow: 0 0 10px #4caf50;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Multi-Document Research Agent</h1>
            <p>Powered by Groq • LangChain • RAG</p>
        </div>

        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>{{ 'Online' if agent_status else 'Offline' }}</span>
            </div>
            <div>
                <span>Documents: {{ doc_count }}</span>
            </div>
        </div>

        <div class="glass-card">
            <div class="input-group">
                <label for="question">🎯 Ask Your Research Question:</label>
                <textarea id="question" class="question-input" placeholder="e.g., Explain how quantum computing affects cybersecurity and propose mitigation strategies"></textarea>
            </div>
            
            <button class="btn btn-primary" onclick="startResearch()">🔍 Start Research</button>
            <button class="btn btn-secondary" onclick="clearAll()">🗑️ Clear</button>
        </div>

        <div class="glass-card loading" id="loading">
            <div class="loading-spinner"></div>
            <h3>🔍 Researching...</h3>
            <p>Analyzing documents and web resources</p>
        </div>

        <div class="glass-card results" id="results">
            <h2>📋 Research Results</h2>
            <div id="answer"></div>
            <div id="details"></div>
        </div>
    </div>

    <script>
        async function startResearch() {
            const question = document.getElementById('question').value.trim();
            if (!question) {
                alert('Please enter a research question!');
                return;
            }

            document.getElementById('loading').classList.add('visible');
            document.getElementById('results').classList.remove('visible');

            try {
                const response = await fetch('/api/research', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });

                const data = await response.json();
                
                if (response.ok) {
                    showResults(data);
                } else {
                    throw new Error(data.error || 'Research failed');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            } finally {
                document.getElementById('loading').classList.remove('visible');
            }
        }

        function showResults(data) {
            const resultsDiv = document.getElementById('results');
            const answerDiv = document.getElementById('answer');
            const detailsDiv = document.getElementById('details');

            answerDiv.innerHTML = `<div style="line-height: 1.8; margin-bottom: 2rem;">${data.answer.replace(/\\n/g, '<br>')}</div>`;
            
            detailsDiv.innerHTML = `
                <h3>📊 Research Details</h3>
                <p><strong>Confidence:</strong> ${data.confidence_level}</p>
                <p><strong>Sources Used:</strong> ${data.sources_count}</p>
                <p><strong>Research Steps:</strong> ${data.steps_count}</p>
                
                <h3>🔗 Sources</h3>
                <ul>${data.sources_used.map(source => `<li>${source}</li>`).join('')}</ul>
                
                <h3>🔧 Research Process</h3>
                ${data.intermediate_steps.map(step => `
                    <div style="margin-bottom: 1rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 8px;">
                        <strong>Step ${step.step}: ${step.tool}</strong><br>
                        <span style="color: rgba(255,255,255,0.7);">Query: ${step.input}</span><br>
                        <span style="color: rgba(255,255,255,0.7);">Result: ${step.output}</span>
                    </div>
                `).join('')}
                
                <button class="btn btn-primary" onclick="generateReport('${data.research_id}')">📄 Generate Report</button>
            `;

            resultsDiv.classList.add('visible');
        }

        async function generateReport(researchId) {
            try {
                const response = await fetch('/api/generate-report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ research_id: researchId })
                });

                const data = await response.json();
                
                if (response.ok) {
                    // Open download link
                    window.open(`/api/download-report/${researchId}`, '_blank');
                } else {
                    throw new Error(data.error || 'Report generation failed');
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function clearAll() {
            document.getElementById('question').value = '';
            document.getElementById('results').classList.remove('visible');
            document.getElementById('loading').classList.remove('visible');
        }
    </script>
</body>
</html>
'''

# Create templates directory and save template
def create_template():
    """Create the HTML template."""
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)

# Create template before server starts
create_template()


if __name__ == '__main__':
    # Initialize agent
    if not initialize_agent():
        print("❌ Failed to initialize research agent. Check your GROQ_API_KEY.")
        exit(1)
    
    print("🚀 Starting Flask server...")
    print("🔍 Multi-Document Research Agent")
    print("📱 Open http://localhost:5001 in your browser")
    
    app.run(debug=True, host='0.0.0.0', port=5001)