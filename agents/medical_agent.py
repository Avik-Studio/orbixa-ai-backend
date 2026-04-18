"""
Medical Agent configuration for Medical Bot Agent OS.
Creates and configures the main Medical AI agent with Gemini model.
"""
import os
import certifi
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.google import Gemini

from config.database import get_mongodb
from config.prompts import load_system_prompt, get_session_state_schema, FEW_SHOT_EXAMPLES
from knowledge.knowledge_base import create_knowledge_base


from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()
class TableModel(BaseModel):
    column_headers: List[str]
    columns_count: int
    rows_count: int
    rows: List[List[str]]

class CanvasItem(BaseModel):
    text: str
    table: Optional[TableModel] = None
    keypoints: Optional[List[str]] = None

class OutputSchema(BaseModel):
    chat_response: str
    canvas_text: Optional[List[CanvasItem]] = None

def create_medical_agent() -> Agent:
    """Create and configure the Medical AI Agent with Gemini."""
    
    # Load system prompt components
    system_prompt = load_system_prompt()
    
    # Create agent with proper configuration
    agent = Agent(
        # Basic configuration
        id="medical-agent",  # Hardcoded ID for stable API endpoints
        name="Assessli Medical AI Assistant",
        model=Gemini(
            id=os.getenv("GEMINI_MODEL_ID", "gemini-3-flash-preview"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.3")),
            top_p=float(os.getenv("GEMINI_TOP_P", "0.8")),
            # thinking_budget=0,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ],
        ),
        
        # Instructions and behavior
        instructions=system_prompt,
        description="Assessli AI Medical assistant made by Assessli company, for medical professionals providing clinical support and guidance, Advanced medical knowledge assistant with multi-book filtering capabilities",
        expected_output=FEW_SHOT_EXAMPLES,
        
        # Database and session management
        db=get_mongodb(),
        cache_session=False,
        
        # History settings
        add_history_to_context=True,
        search_session_history=False,
        num_history_runs=5,
        read_chat_history=True,
        
        # Session state
        session_state=get_session_state_schema(),
        enable_agentic_state=True,
        add_session_state_to_context=True,
        
        # Memory settings
        add_memories_to_context=True,
        enable_user_memories=True,
        enable_agentic_memory=True,
        
        # Knowledge and RAG settings
        knowledge=create_knowledge_base(),
        search_knowledge=True,
        enable_agentic_knowledge_filters=True,
        references_format="json",
        
        # Retry settings
        retries=3,
        exponential_backoff=True,
        
        # Output
        output_schema=OutputSchema,
        
        # Other settings
        add_datetime_to_context=True,
        debug_mode=os.getenv("DEBUG", "False").lower() == "true",
        store_media=False,
        markdown=True,
        store_tool_messages=False,
        tool_call_limit=30,
        telemetry=False,
    )
    
    return agent
