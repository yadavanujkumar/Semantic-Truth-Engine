# 🧠 Semantic Truth Engine

An Agentic Knowledge Graph (Fact-Checking RAG) Platform that transforms unstructured corporate data into a structured, verifiable semantic network.

## 🎯 Overview

The Semantic Truth Engine is a sophisticated fact-checking and knowledge retrieval system that combines:
- **Automated Knowledge Graph Construction** from unstructured documents
- **Multi-Agent Verification System** for fact-checking against ground truth
- **Path-Based Explainability** showing exactly how conclusions are reached
- **Natural Language Interface** with intelligent query translation

## ✨ Key Features

### 1. Automated Graph Extraction Pipeline
- Upload PDF, DOCX, or TXT documents
- Automatically extract entities (people, organizations, products, etc.) and relationships
- Store structured data in Neo4j graph database
- LLM-powered entity recognition and relationship extraction

### 2. Agentic Fact-Checker
- **Extractor Agent**: Finds relevant sub-graphs based on your query
- **Verification Agent**: Cross-references facts against ground truth (Wikipedia, external sources)
- Multi-agent orchestration for comprehensive fact-checking
- Confidence scoring for verification results

### 3. Path-Based Lineage & Explainability
- Visual lineage maps showing query resolution paths
- Track exactly which nodes and relationships led to each conclusion
- Example: `Company X → [OWNED_BY] → Parent Corp → [LOCATED_IN] → Country Y`

### 4. Natural Language to Cypher
- Ask questions in plain English
- Automatic translation to Cypher queries
- Self-correction loop for query optimization
- Retries on syntax errors or empty results

## 🛠️ Tech Stack

- **Python 3.9+**
- **Neo4j** - Graph database for knowledge storage
- **LangChain** - LLM orchestration and chains
- **LlamaIndex** - Document processing and indexing
- **OpenAI GPT-4** / **Claude 3.5** - Language understanding
- **Streamlit** - Interactive web interface
- **Wikipedia API** - Ground truth verification

## 📋 Prerequisites

1. **Python 3.9 or higher**
2. **Neo4j Database** (local or cloud)
   - Download from: https://neo4j.com/download/
   - Or use Neo4j Aura (cloud): https://neo4j.com/cloud/aura/
3. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yadavanujkumar/Semantic-Truth-Engine.git
cd Semantic-Truth-Engine
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Neo4j

**Option A: Local Neo4j**
```bash
# Download and install Neo4j Desktop or Community Edition
# Start Neo4j and note your connection details:
# - URI: bolt://localhost:7687
# - Username: neo4j
# - Password: (set during first login)
```

**Option B: Neo4j Aura (Cloud)**
```bash
# Create a free account at https://neo4j.com/cloud/aura/
# Create a new instance and save connection details
```

### 5. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and add your credentials:
# - OPENAI_API_KEY=your_key_here
# - NEO4J_URI=bolt://localhost:7687
# - NEO4J_USERNAME=neo4j
# - NEO4J_PASSWORD=your_password
```

## 💻 Usage

### Start the Streamlit Application
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Using the Application

#### 1. Configure Connection
- In the sidebar, enter your Neo4j connection details
- Click "Connect to Neo4j"
- Enter your OpenAI API key

#### 2. Ingest Documents
- Go to the "Document Ingestion" tab
- Upload PDF, DOCX, or TXT files
- Click "Process Documents"
- Wait for extraction and graph building to complete

#### 3. Query the Knowledge Graph

**Natural Language Queries:**
```
- "What companies does Microsoft own?"
- "Who works at Google?"
- "What products are manufactured by Tesla?"
```

**Cypher Queries:**
```cypher
MATCH (c:Entity {type: "Company"})-[r:OWNS]->(s:Entity)
RETURN c.name, s.name
LIMIT 10
```

**Fact-Checking:**
- Enter a factual question
- Get verified answers with confidence scores
- View lineage maps showing reasoning paths
- See ground truth sources

#### 4. Explore the Graph
- View graph statistics (nodes, relationships)
- Find paths between specific entities
- Browse sample entities

## 📁 Project Structure

```
Semantic-Truth-Engine/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
│
├── src/
│   ├── config.py             # Configuration management
│   │
│   ├── agents/               # Multi-agent system
│   │   ├── extractor_agent.py      # Sub-graph extraction
│   │   ├── verification_agent.py   # Fact verification
│   │   └── orchestrator.py         # Agent orchestration
│   │
│   ├── graph/                # Graph database operations
│   │   ├── neo4j_manager.py        # Neo4j connection & queries
│   │   └── graph_builder.py        # Graph construction
│   │
│   ├── pipeline/             # Data processing pipelines
│   │   ├── entity_extractor.py     # LLM-based entity extraction
│   │   ├── ingestion.py            # Document ingestion
│   │   └── text_to_cypher.py       # Natural language to Cypher
│   │
│   ├── utils/                # Utility functions
│   │   └── document_processor.py   # Document parsing (PDF, DOCX)
│   │
│   └── visualization/        # Visualization and lineage
│       └── lineage.py              # Lineage tracking & maps
│
└── data/                     # Data storage
    ├── uploads/              # Uploaded documents
    └── graphs/               # Graph exports
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here

# Application Settings
MAX_RETRIES=3
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## 🎓 How It Works

### 1. Document Ingestion Flow
```
Document Upload → Text Extraction → Chunking → 
Entity Extraction (LLM) → Graph Construction → Neo4j Storage
```

### 2. Fact-Checking Flow
```
User Query → Extractor Agent (finds relevant subgraph) →
Verification Agent (checks against Wikipedia) →
Confidence Scoring → Answer Generation → Lineage Map
```

### 3. Natural Language Query Flow
```
Natural Language → LLM Translation → Cypher Query →
Execute on Neo4j → Self-Correction (if needed) → Results
```

## 📊 Example Use Cases

1. **Corporate Knowledge Management**: Build a knowledge graph from company documents and policies
2. **Research Verification**: Verify research claims against established sources
3. **Due Diligence**: Check corporate relationships and ownership structures
4. **Compliance**: Track regulatory relationships and requirements
5. **Competitive Intelligence**: Map industry relationships and partnerships

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Neo4j Connection Issues
- Ensure Neo4j is running
- Check firewall settings for port 7687
- Verify credentials in `.env` file

### API Key Issues
- Confirm OpenAI API key is valid
- Check API quota and billing

### Module Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Empty Query Results
- Verify documents have been ingested
- Check Neo4j database has data: `MATCH (n) RETURN count(n)`

## 📧 Support

For questions or issues, please open an issue on GitHub.

## 🙏 Acknowledgments

- Neo4j for graph database technology
- LangChain and LlamaIndex teams
- OpenAI for language models
- Streamlit for the web framework