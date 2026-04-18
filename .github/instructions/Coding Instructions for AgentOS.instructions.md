---
applyTo: '**'
---
# Medical Bot Agent OS Backend - Implementation Plan

## Project Overview
Build a production-ready Agent OS backend for the Medical Bot using:
- **Database**: MongoDB for session/state storage
- **Vector Database**: Qdrant for knowledge base
- **Authentication**: JWT middleware from Agno Agent OS
- **Knowledge Base**: Current Qdrant configuration with lambda filter validation
- **Prompts**: System prompts and few-shot examples from Prompts.md

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     AgentOS (FastAPI)                    │
├─────────────────────────────────────────────────────────┤
│  JWT Middleware (Extract user_id, session_id)           │
├─────────────────────────────────────────────────────────┤
│  Medical Agent                                           │
│  ├─ MongoDB (Session State, Memory)                     │
│  ├─ Qdrant (Knowledge Base with PDF documents)          │
│  ├─ Custom Filter Validator (Lambda function)           │
│  └─ System Prompts + Few-Shot Examples                  │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. MongoDB Integration
- **Purpose**: Store agent sessions, conversation history, and state
- **Agno Class**: `MongoDb` from `agno.db.mongo`
- **Configuration**:
  - Connection URL from environment variable
  - Session table for agent conversations
  - State persistence across runs

### 2. Qdrant Vector Database
- **Purpose**: Store and search medical PDF documents
- **Agno Class**: `Qdrant` from `agno.vectordb.qdrant`
- **Configuration**:
  - Use existing collection name
  - Connect to existing Qdrant instance
  - Support for metadata filtering
  - Hybrid search capability

### 3. JWT Middleware
- **Purpose**: Authenticate requests and extract user context
- **Agno Class**: `JWTMiddleware` from `agno.os.middleware`
- **Features**:
  - Validates JWT tokens from Authorization header
  - Extracts `user_id` from token claims (typically `sub`)
  - Extracts `session_id` from request payload
  - Injects these as parameters into endpoints automatically
  - Supports RBAC if needed

### 4. Knowledge Base Configuration
- **Purpose**: Medical document search with custom filters
- **Agno Class**: `Knowledge` from `agno.knowledge.knowledge`
- **Features**:
  - Agentic knowledge filters (AI determines filters)
  - Custom lambda validator for filter validation
  - Metadata filtering (book_name, part, page)

### 5. Medical Agent
- **Purpose**: Main AI agent for medical queries
- **Configuration**:
  - System prompts from Prompts.md
  - Few-shot examples for JSON formatting
  - Custom knowledge retriever with filter validation
  - Session state management
  - Agentic state enabled

## Implementation Steps

### Phase 1: Environment Setup
- [x] Review documentation
- [ ] Create environment configuration file
- [ ] Set up MongoDB connection
- [ ] Set up Qdrant connection
- [ ] Configure environment variables

### Phase 2: Knowledge Base Setup
- [ ] Create Knowledge instance with Qdrant
- [ ] Implement filter validator lambda function
- [ ] Test knowledge base search
- [ ] Add metadata filters (book_name, part, page)
- [ ] Configure custom knowledge retriever

### Phase 3: Agent Configuration
- [ ] Load system prompts from Prompts.md
- [ ] Load few-shot examples from config
- [ ] Create Medical Agent with:
  - MongoDB storage
  - Knowledge base
  - System prompts
  - Session state
  - Custom tools/filters
- [ ] Configure agentic session state

### Phase 4: JWT Middleware Setup
- [ ] Configure JWTMiddleware
- [ ] Set up token validation
- [ ] Configure claim extraction (user_id, session_id)
- [ ] Test authentication flow

### Phase 5: AgentOS Setup
- [ ] Create AgentOS instance
- [ ] Register Medical Agent
- [ ] Add JWT middleware
- [ ] Configure FastAPI app
- [ ] Set up API endpoints

### Phase 6: Testing & Validation
- [ ] Test MongoDB connection and persistence
- [ ] Test Qdrant search with filters
- [ ] Test JWT authentication
- [ ] Test agent responses with prompts
- [ ] Test session continuity
- [ ] Validate JSON output format

## File Structure

```
MEDBotv3/
├── app.py                          # Main AgentOS application
├── config/
│   ├── __init__.py
│   ├── env.py                      # Environment configuration
│   ├── few_shot_examples.py       # Few-shot examples (existing)
│   ├── prompts.py                  # System prompts loader
│   └── database.py                 # Database configurations
├── agents/
│   ├── __init__.py
│   └── medical_agent.py            # Medical agent setup
├── knowledge/
│   ├── __init__.py
│   ├── qdrant_config.py           # Qdrant configuration
│   ├── filter_validator.py        # Lambda filter validator
│   └── knowledge_base.py           # Knowledge base setup
├── middleware/
│   ├── __init__.py
│   └── jwt_config.py               # JWT middleware configuration
├── utils/
│   ├── __init__.py
│   └── helpers.py                  # Helper functions
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
└── Prompts.md                      # System prompts (existing)
```

## Dependencies Required

```txt
# Core Agno
agno>=2.1.0
agno[mongodb]
agno[qdrant]

# FastAPI & Server
fastapi>=0.115.0
uvicorn[standard]>=0.31.0

# Database
pymongo>=4.0.0
motor>=3.0.0  # Async MongoDB

# Qdrant
qdrant-client>=1.7.0

# JWT & Auth
pyjwt>=2.8.0
python-jose[cryptography]>=3.3.0

# Environment
python-dotenv>=1.0.0

# AI Models (OpenAI or others)
openai>=1.0.0

# Utilities
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

## Environment Variables

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=medical_bot
MONGODB_SESSION_TABLE=agent_sessions

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION_NAME=medical_documents

# JWT Configuration
JWT_VERIFICATION_KEY=your_jwt_secret_or_public_key
JWT_ALGORITHM=RS256
JWT_USER_ID_CLAIM=sub
JWT_SESSION_ID_CLAIM=session_id

# OpenAI Configuration (or other model provider)
OPENAI_API_KEY=your_openai_api_key
MODEL_ID=gpt-4o

# AgentOS Configuration
AGENTOS_NAME=Medical AI Agent OS
AGENTOS_DESCRIPTION=Production runtime for medical AI assistant
AGENTOS_PORT=8000
```

## Key Implementation Details

### 1. Filter Validator Lambda
The lambda function validates that filters conform to the rules:
- Only ONE book_name per search
- Valid filter keys: book_name, part, page
- Proper filter structure validation

```python
def validate_filters(filters: Dict[str, Any]) -> bool:
    """
    Validates knowledge base filters according to medical bot rules.
    Returns True if valid, False otherwise.
    """
    if not filters:
        return True
    
    # Check valid keys
    valid_keys = {'book_name', 'part', 'page'}
    if not all(key in valid_keys for key in filters.keys()):
        return False
    
    # Ensure only one book per search
    if 'book_name' in filters:
        # Must be a single string, not a list
        if isinstance(filters['book_name'], list):
            return False
    
    return True
```

### 2. JWT Middleware Configuration
```python
from agno.os.middleware import JWTMiddleware

app.add_middleware(
    JWTMiddleware,
    verification_keys=[JWT_VERIFICATION_KEY],
    algorithm=JWT_ALGORITHM,
    user_id_claim=JWT_USER_ID_CLAIM,
    session_id_claim=JWT_SESSION_ID_CLAIM,
    validate=True,
    authorization=False,  # Set to True if RBAC needed
    verify_audience=False,  # Set to True if audience verification needed
)
```

### 3. MongoDB Configuration
```python
from agno.db.mongo import MongoDb

db = MongoDb(
    id="medical_bot_db",
    db_url=MONGODB_URL,
    db_name=MONGODB_DATABASE,
    session_table=MONGODB_SESSION_TABLE,
)
```

### 4. Qdrant Knowledge Base
```python
from agno.vectordb.qdrant import Qdrant
from agno.knowledge.knowledge import Knowledge

vector_db = Qdrant(
    collection=QDRANT_COLLECTION_NAME,
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    search_type=SearchType.hybrid,  # Enable hybrid search
)

knowledge = Knowledge(
    name="Medical Knowledge Base",
    description="Medical textbooks and documentation",
    vector_db=vector_db,
    enable_agentic_filters=True,  # Let AI determine filters
)
```

### 5. Medical Agent Setup
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

medical_agent = Agent(
    id="medical-agent",
    name="Medical AI Assistant",
    description="Expert medical assistant for healthcare professionals",
    model=OpenAIChat(id=MODEL_ID),
    db=db,
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
    session_state={
        "topics_to_write": [],
        "books_to_search": [],
        "preferred_books": [],
        "writing_progress": {}
    },
    add_session_state_to_context=True,
    enable_agentic_state=True,
    instructions=system_prompt,  # From Prompts.md
    markdown=True,
)
```

### 6. AgentOS Setup
```python
from agno.os import AgentOS

agent_os = AgentOS(
    name=AGENTOS_NAME,
    description=AGENTOS_DESCRIPTION,
    agents=[medical_agent],
)

app = agent_os.get_app()

# Add JWT middleware
app.add_middleware(JWTMiddleware, ...)

if __name__ == "__main__":
    agent_os.serve(app="app:app", port=AGENTOS_PORT, reload=True)
```

## API Endpoints (Auto-generated by AgentOS)

### Core Agent Endpoints
- `POST /agents/{agent_id}/run` - Run agent with message
- `GET /agents/{agent_id}/sessions` - List agent sessions
- `GET /agents/{agent_id}/sessions/{session_id}` - Get session details
- `DELETE /agents/{agent_id}/sessions/{session_id}` - Delete session

### Knowledge Endpoints
- `POST /knowledge/search` - Search knowledge base
- `GET /knowledge/contents` - List knowledge contents

### Configuration Endpoint
- `GET /config` - Get AgentOS configuration

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc UI

## Security Considerations

1. **JWT Token Validation**
   - Verify token signature
   - Check expiration
   - Validate issuer/audience if needed

2. **Environment Variables**
   - Never commit .env files
   - Use secure key management in production
   - Rotate JWT secrets regularly

3. **Database Security**
   - Use MongoDB authentication
   - Encrypt connections (TLS)
   - Implement proper access controls

4. **API Rate Limiting**
   - Add rate limiting middleware if needed
   - Protect against abuse

## Testing Strategy

### Unit Tests
- Filter validator function
- System prompt loading
- Database connections

### Integration Tests
- End-to-end agent conversation
- JWT authentication flow
- Knowledge base search with filters
- Session persistence

### Manual Testing
- Test with real medical queries
- Verify JSON output format
- Check multi-book search handling
- Validate session continuity

## Deployment Considerations

1. **Containerization**
   - Create Dockerfile
   - Use docker-compose for local dev
   - Include MongoDB and Qdrant services

2. **Production Deployment**
   - Use managed MongoDB (Atlas)
   - Use managed Qdrant (Cloud)
   - Deploy on AWS ECS, Railway, or similar
   - Set up CI/CD pipeline

3. **Monitoring**
   - Add logging
   - Set up error tracking (Sentry)
   - Monitor API performance
   - Track agent usage metrics

## Success Criteria

- ✅ AgentOS runs successfully with JWT authentication
- ✅ MongoDB stores and retrieves sessions correctly
- ✅ Qdrant searches return relevant medical documents
- ✅ Filter validator enforces one-book-per-search rule
- ✅ Agent responds with proper JSON format
- ✅ System prompts and few-shot examples work correctly
- ✅ Session state persists across requests
- ✅ User ID and Session ID are correctly extracted from JWT/payload

## Timeline Estimate

- **Phase 1**: 1-2 hours (Environment setup)
- **Phase 2**: 2-3 hours (Knowledge base)
- **Phase 3**: 2-3 hours (Agent configuration)
- **Phase 4**: 1-2 hours (JWT middleware)
- **Phase 5**: 1-2 hours (AgentOS setup)
- **Phase 6**: 2-3 hours (Testing)

**Total Estimated Time**: 9-15 hours

## Next Steps

1. Review and approve this implementation plan
2. Set up development environment
3. Begin Phase 1: Environment Setup
4. Implement components sequentially
5. Test each phase before moving forward
6. Deploy to staging for testing
7. Deploy to production

---

**Note**: This plan leverages Agno's built-in features for MongoDB, Qdrant, JWT middleware, and session management. No custom caching or architecture handling is needed - we use Agno's predefined methods as per the official documentation.
