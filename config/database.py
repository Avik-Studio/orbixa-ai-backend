"""
Database configuration module for Medical Bot Agent OS.
Sets up MongoDB and Qdrant connections using Agno's built-in classes.
"""
import os
from agno.db.mongo import MongoDb
from agno.vectordb.qdrant import Qdrant
from agno.vectordb.search import SearchType
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder

def get_mongodb() -> MongoDb:
    """Create and return a MongoDB instance for agent storage."""
    return MongoDb(
        id="medical_bot_db",
        db_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
        db_name=os.getenv("MONGODB_DATABASE", "medical_bot"),
        # session_table=os.getenv("MONGODB_SESSION_TABLE", "agent_sessions"),
    )


def get_qdrant() -> Qdrant:
    """Create and return a Qdrant vector database instance for knowledge base."""
    qdrant_config = {
        "collection": os.getenv("QDRANT_COLLECTION_NAME", "medical_knowledge_base"),
        "url": os.getenv("QDRANT_URL", "http://localhost:6333"),
        "search_type": SearchType.vector,  # Use vector search (not hybrid to avoid sparse vector requirement)
        "embedder": FastEmbedEmbedder(),
        "prefer_grpc": False,  # Use HTTP instead of gRPC to avoid SSL issues
        "verify": False,  # Disable SSL verification for local/dev environments
    }
    
    api_key = os.getenv("QDRANT_API_KEY")
    if api_key:
        qdrant_config["api_key"] = api_key
    
    return Qdrant(**qdrant_config)
