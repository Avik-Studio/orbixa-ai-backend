# Orbixa AI - Backend

A production-ready Agent OS backend for **Orbixa AI**, a powerful generative AI assistant built by **Avik Modak**. Powered by Agno framework, FastAPI, MongoDB, Qdrant, and Google Gemini.

## Features

- 🤖 **Orbixa AI Agent**: Versatile generative AI assistant — coding, writing, research, math, science, creative tasks
- 🗄️ **MongoDB**: Persistent session storage and state management
- 🔍 **Qdrant**: Vector database for document search with hybrid search
- 🔐 **JWT Authentication**: Secure API with user/session extraction
- 📚 **Knowledge Base**: Upload and search custom documents with intelligent filtering
- 🎯 **Agentic State**: Autonomous session state management
- ⚡ **FastAPI**: High-performance REST API with SSE streaming
- 📊 **Custom Prompts**: Generative AI system prompts and few-shot examples

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AgentOS (FastAPI)                    │
├─────────────────────────────────────────────────────────┤
│  JWT Middleware (Extract user_id, session_id)           │
├─────────────────────────────────────────────────────────┤
│  Orbixa AI Agent                                         │
│  ├─ MongoDB (Session State, Memory)                     │
│  ├─ Qdrant (Knowledge Base with uploaded documents)     │
│  ├─ Custom Filter Validator (Lambda function)           │
│  └─ System Prompts + Few-Shot Examples                  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- MongoDB (local or cloud)
- Qdrant (local or cloud)
- OpenAI API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd MEDBotv3
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DATABASE=orbixa_ai

   # Qdrant
   QDRANT_URL=http://localhost:6333
   QDRANT_COLLECTION_NAME=orbixa_knowledge_base

   # JWT
   JWT_SECRET=your_secret_key
   JWT_ALGORITHM=HS256

   # Gemini
   GOOGLE_API_KEY=your-google-api-key
   GEMINI_MODEL_ID=gemini-2.0-flash
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   
   Or with Uvicorn:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Project Structure

```
orbixa-ai-backend/
├── app.py                          # Main AgentOS application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
│
├── config/                         # Configuration modules
│   ├── __init__.py
│   ├── database.py                 # Database connections
│   ├── prompts.py                  # Prompt loader
│   └── promptsBig.py               # Extended prompts
│
├── agents/                         # Agent definitions
│   ├── __init__.py
│   └── medical_agent.py            # Orbixa AI agent
│
├── knowledge/                      # Knowledge base
│   ├── __init__.py
│   ├── filter_validator.py         # Filter validation
│   └── knowledge_base.py           # Qdrant configuration
│
└── middleware/                     # Middleware
    ├── __init__.py
    └── jwt_config.py               # JWT authentication
```

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /config` - AgentOS configuration

### Agent Endpoints

- `POST /agents/orbixa-agent/run` - Run agent with message
- `GET /agents/orbixa-agent/sessions` - List sessions
- `GET /agents/orbixa-agent/sessions/{session_id}` - Get session
- `DELETE /agents/orbixa-agent/sessions/{session_id}` - Delete session

### Knowledge Endpoints
- `POST /knowledge/search` - Search knowledge base
- `GET /knowledge/contents` - List knowledge contents

## Authentication

All endpoints require JWT authentication via the `Authorization` header:

```bash
Authorization: Bearer <your-jwt-token>
```

### JWT Token Structure

```json
{
  "sub": "user-123",
  "session_id": "session-abc-xyz",
  "email": "user@example.com",
  "name": "Avik Modak",
  "exp": 1735689600,
  "iat": 1735603200
}
```

The middleware automatically extracts:
- `user_id` from the `sub` claim
- `session_id` from the `session_id` claim

## Knowledge Base Filters

The knowledge base supports metadata filtering with validation:

### Valid Filters

- `source_name`: Uploaded document name (e.g., "guide.pdf")
- `part`: Section within a document (e.g., "Part_1")
- `page`: Specific page number

### Filter Rules

1. **One Source Per Search**: Only ONE `source_name` per search
2. **Sequential Multi-Source**: Search multiple sources sequentially
3. **Valid Keys Only**: Only use the allowed filter keys

### Example Usage

```python
# Single source search
filters = {"source_name": "guide.pdf"}

# Source with section
filters = {"source_name": "guide.pdf", "part": "Part_1"}

# Source with page
filters = {"source_name": "guide.pdf", "page": 125}
```

## Session State

The agent maintains session state automatically:

```python
{
  "topics_to_write": [],
  "sources_to_search": [],
  "preferred_sources": [],
  "writing_progress": {}
}
```

State is:
- Persisted in MongoDB
- Automatically loaded on session resume
- Updated autonomously by the agent
- Available in agent context

## Response Format

All agent responses follow a JSON schema:

```json
{
  "chat_response": "Brief conversational summary of what was done",
  "canvas_text": [
    {
      "text": "Detailed content with Markdown and LaTeX",
      "table": {
        "column_headers": ["Col1", "Col2"],
        "columns_count": 2,
        "rows_count": 1,
        "rows": [["Val1", "Val2"]]
      },
      "keypoints": ["Key point 1", "Key point 2"]
    }
  ]
}
```

## Development

### Running in Debug Mode

```bash
# Set debug mode in .env
DEBUG=true

# Run application
python app.py
```

Debug mode provides:
- Verbose logging
- Tool call visibility
- Configuration details
- Filter validation messages

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=.

# Specific test
pytest tests/test_filters.py
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy .
```

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production

```bash
# Using Gunicorn with Uvicorn workers
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Environment Variables

Production environment should set:

```env
DEBUG=false
AGENTOS_RELOAD=false
AGENTOS_HOST=0.0.0.0
AGENTOS_PORT=8000

# Use production MongoDB
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/

# Use production Qdrant
QDRANT_URL=https://your-cluster.qdrant.cloud
QDRANT_API_KEY=your_production_key

# Use strong JWT keys
JWT_VERIFICATION_KEY=your_production_secret
JWT_ALGORITHM=RS256
```

## Configuration

### MongoDB

Configure MongoDB connection in `.env`:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=medical_bot
MONGODB_SESSION_TABLE=agent_sessions
```

### Qdrant

Configure Qdrant connection in `.env`:

```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key
QDRANT_COLLECTION_NAME=medical_documents
```

### JWT

Configure JWT authentication in `.env`:

```env
JWT_VERIFICATION_KEY=your_secret_or_public_key
JWT_ALGORITHM=RS256  # or HS256
JWT_USER_ID_CLAIM=sub
JWT_SESSION_ID_CLAIM=session_id
JWT_VALIDATE=true
JWT_AUTHORIZATION=false
```

### Model

Configure AI model in `.env`:

```env
MODEL_PROVIDER=openai
MODEL_API_KEY=sk-your-api-key
MODEL_MODEL_ID=gpt-4o
MODEL_TEMPERATURE=0.7
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Medical AI Agent OS",
  "version": "1.0.0"
}
```

### Logs

Application logs include:
- Request/response information
- Agent interactions
- Knowledge base searches
- Filter validation results
- Error tracking

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
mongosh --eval "db.runCommand({ ping: 1 })"

# Test connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017').server_info())"
```

### Qdrant Connection Issues

```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Test connection
python -c "from qdrant_client import QdrantClient; print(QdrantClient('localhost', port=6333).get_collections())"
```

### JWT Issues

- Verify JWT_VERIFICATION_KEY is correct
- Check token expiration
- Ensure algorithm matches (RS256 vs HS256)
- Validate token structure

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Check the documentation
- Review the implementation plan
- Contact the development team

## Acknowledgments

Built with:
- [Agno](https://docs.agno.com) - AI Agent framework
- [FastAPI](https://fastapi.tiangolo.com) - Modern web framework
- [MongoDB](https://www.mongodb.com) - Document database
- [Qdrant](https://qdrant.tech) - Vector database
- [OpenAI](https://openai.com) - AI models
