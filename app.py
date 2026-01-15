"""Main Streamlit application for the Semantic Truth Engine."""
import streamlit as st
from pathlib import Path
import sys
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config import config
from src.graph.neo4j_manager import Neo4jConnection
from src.pipeline.ingestion import IngestionPipeline
from src.agents.orchestrator import FactCheckingOrchestrator
from src.pipeline.text_to_cypher import TextToCypherConverter
from src.visualization.lineage import LineageTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Semantic Truth Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'neo4j_conn' not in st.session_state:
        st.session_state.neo4j_conn = None
    if 'ingestion_results' not in st.session_state:
        st.session_state.ingestion_results = []
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None


def connect_to_neo4j(uri: str, username: str, password: str):
    """Connect to Neo4j database."""
    try:
        conn = Neo4jConnection(uri, username, password)
        conn.connect()
        st.session_state.neo4j_conn = conn
        return True, "Successfully connected to Neo4j!"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def main():
    """Main application."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🧠 Semantic Truth Engine</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Agentic Knowledge Graph for Fact-Checking and RAG</p>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Neo4j connection
        st.subheader("Neo4j Database")
        neo4j_uri = st.text_input("URI", value="bolt://localhost:7687")
        neo4j_user = st.text_input("Username", value="neo4j")
        neo4j_pass = st.text_input("Password", type="password")
        
        if st.button("Connect to Neo4j"):
            with st.spinner("Connecting..."):
                success, message = connect_to_neo4j(neo4j_uri, neo4j_user, neo4j_pass)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Connection status
        if st.session_state.neo4j_conn:
            st.success("✅ Connected to Neo4j")
        else:
            st.warning("⚠️ Not connected to Neo4j")
        
        st.divider()
        
        # OpenAI configuration
        st.subheader("OpenAI Configuration")
        openai_key = st.text_input("API Key", type="password", value=config.openai_api_key)
        if openai_key:
            config.openai_api_key = openai_key
            st.success("✅ API Key configured")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Document Ingestion", "🔍 Query & Fact-Check", "🗺️ Graph Exploration", "ℹ️ About"])
    
    # Tab 1: Document Ingestion
    with tab1:
        st.markdown('<div class="sub-header">Document Ingestion Pipeline</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Upload documents (PDF, DOCX, TXT) to automatically extract entities and relationships
        and build your knowledge graph.
        """)
        
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Process Documents"):
            if not st.session_state.neo4j_conn:
                st.error("Please connect to Neo4j first!")
            elif not config.openai_api_key:
                st.error("Please configure OpenAI API key first!")
            else:
                with st.spinner("Processing documents..."):
                    pipeline = IngestionPipeline(st.session_state.neo4j_conn)
                    
                    for uploaded_file in uploaded_files:
                        # Save uploaded file
                        file_path = config.uploads_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Process document
                        result = pipeline.ingest_document(file_path)
                        st.session_state.ingestion_results.append(result)
                        
                        if result["success"]:
                            st.success(f"✅ Processed: {result['file_name']}")
                            with st.expander(f"Details for {result['file_name']}"):
                                st.json(result)
                        else:
                            st.error(f"❌ Failed: {result['file_name']}")
                            st.error(result.get('error', 'Unknown error'))
        
        # Show previous results
        if st.session_state.ingestion_results:
            st.markdown("### Previous Ingestion Results")
            for result in st.session_state.ingestion_results[-5:]:
                with st.expander(f"{result['file_name']} - {'✅' if result['success'] else '❌'}"):
                    st.json(result)
    
    # Tab 2: Query & Fact-Check
    with tab2:
        st.markdown('<div class="sub-header">Query the Knowledge Graph</div>', unsafe_allow_html=True)
        
        # Query mode selection
        query_mode = st.radio(
            "Query Mode",
            ["Natural Language", "Cypher Query", "Fact-Checking"],
            horizontal=True
        )
        
        if query_mode == "Natural Language":
            st.markdown("Ask questions in plain English. The system will translate to Cypher automatically.")
            query = st.text_area("Enter your question:", placeholder="E.g., What companies are owned by Company X?")
            
            if st.button("Execute Query") and query:
                if not st.session_state.neo4j_conn:
                    st.error("Please connect to Neo4j first!")
                else:
                    with st.spinner("Processing query..."):
                        converter = TextToCypherConverter(st.session_state.neo4j_conn)
                        result = converter.query(query)
                        
                        if result["success"]:
                            st.success(f"✅ Query executed successfully (Attempts: {result['attempts']})")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Generated Cypher:**")
                                st.code(result["cypher"], language="cypher")
                            
                            with col2:
                                st.markdown("**Results:**")
                                st.json(result["data"][:10])  # Show first 10 results
                        else:
                            st.error("❌ Query failed")
                            st.error(result.get("error", "Unknown error"))
        
        elif query_mode == "Cypher Query":
            st.markdown("Write Cypher queries directly.")
            cypher_query = st.text_area("Enter Cypher query:", placeholder="MATCH (n:Entity) RETURN n LIMIT 10")
            
            if st.button("Execute Query") and cypher_query:
                if not st.session_state.neo4j_conn:
                    st.error("Please connect to Neo4j first!")
                else:
                    with st.spinner("Executing query..."):
                        try:
                            result = st.session_state.neo4j_conn.execute_query(cypher_query)
                            st.success("✅ Query executed successfully")
                            st.json(result[:20])  # Show first 20 results
                        except Exception as e:
                            st.error(f"❌ Query failed: {str(e)}")
        
        elif query_mode == "Fact-Checking":
            st.markdown("Ask questions and get fact-checked answers with lineage tracking.")
            query = st.text_area("Enter your question:", placeholder="E.g., Is Company X owned by Company Y?")
            
            if st.button("Check Facts") and query:
                if not st.session_state.neo4j_conn:
                    st.error("Please connect to Neo4j first!")
                elif not config.openai_api_key:
                    st.error("Please configure OpenAI API key first!")
                else:
                    with st.spinner("Checking facts..."):
                        orchestrator = FactCheckingOrchestrator(st.session_state.neo4j_conn)
                        result = orchestrator.check_facts(query)
                        st.session_state.query_results = result
                        
                        if result["success"]:
                            st.success("✅ Fact-check completed")
                            
                            # Display confidence score
                            confidence = result.get("confidence_score", 0.0)
                            st.metric("Confidence Score", f"{confidence:.2%}")
                            
                            # Display answer
                            st.markdown("### Answer")
                            st.markdown(result.get("answer", "No answer generated"))
                            
                            # Display lineage
                            st.markdown("### Lineage Map")
                            tracker = LineageTracker(st.session_state.neo4j_conn)
                            lineage = tracker.generate_lineage_map(query, result["subgraph"])
                            st.markdown(lineage["explanation"])
                            
                            # Show detailed verification
                            with st.expander("Detailed Verification"):
                                st.json(result["verification"])
                        else:
                            st.warning(result.get("message", "No results found"))
    
    # Tab 3: Graph Exploration
    with tab3:
        st.markdown('<div class="sub-header">Explore the Knowledge Graph</div>', unsafe_allow_html=True)
        
        if not st.session_state.neo4j_conn:
            st.warning("Please connect to Neo4j first!")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Graph Statistics")
                if st.button("Get Statistics"):
                    with st.spinner("Fetching statistics..."):
                        # Get node count
                        node_count = st.session_state.neo4j_conn.execute_query("MATCH (n) RETURN count(n) as count")
                        # Get relationship count
                        rel_count = st.session_state.neo4j_conn.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
                        
                        st.metric("Total Nodes", node_count[0]["count"] if node_count else 0)
                        st.metric("Total Relationships", rel_count[0]["count"] if rel_count else 0)
            
            with col2:
                st.markdown("### Find Path Between Entities")
                start_entity = st.text_input("Start Entity Name")
                end_entity = st.text_input("End Entity Name")
                
                if st.button("Find Path") and start_entity and end_entity:
                    tracker = LineageTracker(st.session_state.neo4j_conn)
                    path_result = tracker.find_path_between_entities(start_entity, end_entity)
                    
                    if path_result["found"]:
                        st.success(f"✅ Path found (Length: {path_result['path_length']})")
                        st.markdown(path_result["explanation"])
                    else:
                        st.warning("No path found")
            
            # Sample entities
            st.markdown("### Sample Entities")
            if st.button("Show Sample Entities"):
                entities = st.session_state.neo4j_conn.execute_query(
                    "MATCH (n:Entity) RETURN n.name as name, n.type as type LIMIT 20"
                )
                if entities:
                    st.table(entities)
                else:
                    st.info("No entities found in the graph")
    
    # Tab 4: About
    with tab4:
        st.markdown('<div class="sub-header">About Semantic Truth Engine</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 Features
        
        - **Automated Graph Extraction**: Upload documents and automatically extract entities and relationships
        - **Agentic Fact-Checker**: Multi-agent system for verifying facts against ground truth
        - **Path-Based Lineage**: Visual lineage maps showing how conclusions are reached
        - **Natural Language to Cypher**: Query the graph using plain English with self-correction
        - **Interactive Visualization**: Explore your knowledge graph interactively
        
        ### 🛠️ Tech Stack
        
        - **Backend**: Python, LangChain, LlamaIndex
        - **Database**: Neo4j (Graph Database)
        - **LLM**: OpenAI GPT-4 / Claude 3.5
        - **Frontend**: Streamlit
        - **Verification**: Wikipedia API
        
        ### 📚 How to Use
        
        1. **Configure**: Set up Neo4j connection and OpenAI API key in the sidebar
        2. **Ingest**: Upload documents to build your knowledge graph
        3. **Query**: Ask questions in natural language or use Cypher
        4. **Verify**: Get fact-checked answers with confidence scores
        5. **Explore**: Visualize paths and relationships in your graph
        
        ### 🔗 Resources
        
        - [Neo4j Documentation](https://neo4j.com/docs/)
        - [LangChain Documentation](https://python.langchain.com/)
        - [GitHub Repository](https://github.com/yadavanujkumar/Semantic-Truth-Engine)
        """)


if __name__ == "__main__":
    main()
