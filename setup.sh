#!/bin/bash

# Multi-Document Research Agent Setup Script
echo "🚀 Setting up Multi-Document Research Agent..."

# Create project structure
echo "📁 Creating project structure..."
mkdir -p documents data/chroma_db outputs/reports agent

# Create __init__.py files
touch agent/__init__.py

# Create sample .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOF
# Groq API Key - Get from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Optional: LangSmith for debugging (get from: https://smith.langchain.com/)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key_optional
EOF
    echo "⚠️  Please edit .env file and add your GROQ_API_KEY"
fi

# Create sample documents
echo "📄 Creating sample documents..."

# Sample Markdown document
cat > documents/sample_quantum_computing.md << 'EOF'
# Quantum Computing and Cybersecurity

## Introduction

Quantum computing represents a fundamental shift in computational paradigms, leveraging quantum mechanical phenomena such as superposition and entanglement to process information in ways that classical computers cannot.

## Impact on Cybersecurity

### Cryptographic Vulnerabilities

Current public-key cryptographic systems, including RSA, ECC, and DSA, rely on the computational difficulty of certain mathematical problems:
- Integer factorization (RSA)
- Discrete logarithm problem (ECC, DSA)

Quantum computers, when sufficiently powerful, could solve these problems efficiently using:
- **Shor's Algorithm**: For integer factorization and discrete logarithms
- **Grover's Algorithm**: For symmetric key cryptography (reduces security by half)

### Timeline and Threat Assessment

- **NISQ Era** (2020-2030): Noisy Intermediate-Scale Quantum computers
- **Fault-Tolerant Era** (2030+): Large-scale quantum computers capable of breaking current cryptography

## Mitigation Strategies

### 1. Post-Quantum Cryptography (PQC)

NIST has standardized several quantum-resistant algorithms:
- **CRYSTALS-Kyber**: Key encapsulation mechanism
- **CRYSTALS-Dilithium**: Digital signatures
- **FALCON**: Digital signatures (compact)
- **SPHINCS+**: Hash-based signatures

### 2. Crypto-Agility

Organizations should implement crypto-agile systems that can:
- Rapidly switch between cryptographic algorithms
- Support hybrid classical-quantum resistant schemes
- Enable seamless updates as new standards emerge

### 3. Quantum Key Distribution (QKD)

For high-security applications:
- Point-to-point quantum-secured communication
- Detection of eavesdropping attempts
- Currently limited by distance and infrastructure

## Implementation Timeline

1. **Immediate (2024-2025)**: Begin PQC evaluation and testing
2. **Short-term (2025-2027)**: Pilot deployments of hybrid systems
3. **Medium-term (2027-2030)**: Full migration to PQC standards
4. **Long-term (2030+)**: Quantum-native security architectures

## Conclusion

The quantum threat to cybersecurity is real but manageable with proper preparation. Organizations must begin transitioning to quantum-resistant cryptography now to ensure long-term security.
EOF

# Sample AI/ML document
cat > documents/sample_transformer_architectures.md << 'EOF'
# Transformer Architectures in Natural Language Processing

## Evolution of Transformer Models

### Original Transformer (2017)
- **Paper**: "Attention Is All You Need" by Vaswani et al.
- **Key Innovation**: Self-attention mechanism replacing RNNs/CNNs
- **Architecture**: Encoder-Decoder with multi-head attention

### BERT (2018)
- **Bidirectional**: Processes text in both directions simultaneously  
- **Masked Language Modeling**: Predicts masked tokens in sequence
- **Applications**: Question answering, sentiment analysis, NER

### GPT Series
- **GPT-1 (2018)**: 117M parameters, unsupervised pre-training
- **GPT-2 (2019)**: 1.5B parameters, demonstrated scaling laws
- **GPT-3 (2020)**: 175B parameters, few-shot learning capabilities
- **GPT-4 (2023)**: Multimodal capabilities, improved reasoning

## Recent Developments (2023-2024)

### Mixture of Experts (MoE)
- **Switch Transformer**: Sparse expert routing
- **PaLM-2**: Improved efficiency through expert specialization
- **Benefits**: Increased model capacity without proportional compute increase

### Retrieval-Augmented Generation (RAG)
- **Combines**: Parametric knowledge with external retrieval
- **Applications**: Question answering, fact-checking, knowledge synthesis
- **Architectures**: RAG, FiD (Fusion-in-Decoder), REALM

### Long Context Models
- **Longformer**: Extended attention for long documents
- **BigBird**: Sparse attention patterns
- **GPT-4 Turbo**: 128k context window
- **Claude-2**: 200k context window

### Efficient Architectures
- **Reformer**: Reversible layers and locality-sensitive hashing
- **Linformer**: Linear complexity attention
- **Performer**: FAVOR+ attention approximation

## Current Research Directions

### 1. Scaling Laws
- **Chinchilla**: Optimal compute allocation between model size and training data
- **PaLM**: Demonstrates continued benefits of scale
- **Emergent Abilities**: Capabilities that appear at certain scales

### 2. Alignment and Safety
- **RLHF**: Reinforcement Learning from Human Feedback
- **Constitutional AI**: Training models to follow principles
- **Red Teaming**: Systematic testing for harmful outputs

### 3. Multimodal Integration
- **CLIP**: Vision-language understanding
- **DALL-E**: Text-to-image generation
- **GPT-4V**: Integrated vision capabilities
- **Flamingo**: Few-shot learning across modalities

### 4. Efficiency Improvements
- **Quantization**: 8-bit and 4-bit inference
- **Pruning**: Structured and unstructured sparsity
- **Knowledge Distillation**: Transfer from large to small models
- **Model Parallelism**: Efficient distributed inference

## Limitations and Challenges

### Current Limitations
- **Hallucination**: Generation of factually incorrect information
- **Context Window**: Limited memory for long conversations
- **Reasoning**: Struggles with multi-step logical reasoning
- **Grounding**: Difficulty with real-world knowledge updates

### Technical Challenges
- **Computational Cost**: Training and inference requirements
- **Data Quality**: Dependence on high-quality training data
- **Evaluation**: Difficulty in comprehensive model assessment
- **Interpretability**: Understanding model decision-making

## Future Directions

### Architectural Innovations
- **State Space Models**: Mamba, structured state spaces
- **Retrieval Integration**: Native RAG architectures
- **Modular Systems**: Composable transformer components
- **Neuromorphic Computing**: Hardware-software co-design

### Applications
- **Scientific Research**: Protein folding, drug discovery
- **Code Generation**: Software engineering assistance
- **Creative AI**: Writing, art, music generation
- **Personal Assistants**: Contextual, personalized AI

## Conclusion

Transformer architectures continue to evolve rapidly, with improvements in efficiency, capability, and safety. The field is moving toward more capable, aligned, and accessible models while addressing fundamental challenges in reasoning and grounding.
EOF

echo "✅ Sample documents created!"

# Create requirements.txt (already provided in artifacts above)

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Add your GROQ_API_KEY to the .env file"
echo "2. Place your documents in the 'documents/' folder"
echo "3. Run the Streamlit app: streamlit run main.py"
echo "4. Or use CLI: python cli_example.py 'Your question here'"
echo ""
echo "📖 For more information, see the implementation guide in rag_agent_guide.md"