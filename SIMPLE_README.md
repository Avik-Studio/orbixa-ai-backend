# Medical Bot Agent OS - Simplified Setup

Production-ready Medical AI Assistant powered by **Agno Agent OS** and **Gemini 3 Flash Preview**.

## Features

✅ **Gemini 3 Flash Preview** - Fast, accurate medical responses  
✅ **MongoDB** - Session and memory persistence  
✅ **Qdrant** - Medical knowledge base with hybrid search  
✅ **JWT Authentication** - Secure user identification  
✅ **Custom Routes** - PDF ingestion and book management  
✅ **AgentOS** - Built-in SSE streaming, session management, and API  

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your credentials:

```env
# Qdrant (Already configured)
QDRANT_URL=https://...
QDRANT_API_KEY=...
QDRANT_COLLECTION_NAME=medical_knowledge_base

# Gemini AI (Already configured)
GOOGLE_API_KEY=AIzaSyBWGThK...
GEMINI_MODEL_ID=gemini-3-flash-preview
GEMINI_TEMPERATURE=0.3

# MongoDB (Already configured)
MONGODB_URL=mongodb+srv://...
MONGODB_DATABASE=medical_bot
MONGODB_SESSION_TABLE=agent_sessions

# Server
PORT=8000
DEBUG=False
```

### 3. Run the Server

```bash
python app.py
```

Or with auto-reload for development:

```bash
# Set DEBUG=True in .env first
python app.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Built-in AgentOS Endpoints

- `POST /agents/medical-agent/runs` - Run the medical agent
- `GET /agents/medical-agent/sessions` - List all sessions
- `GET /agents/medical-agent/sessions/{session_id}` - Get session details
- `DELETE /agents/medical-agent/sessions/{session_id}` - Delete session
- `GET /docs` - Swagger API documentation
- `GET /redoc` - ReDoc API documentation

### Custom Knowledge Management Endpoints

#### Ingest PDF

```bash
POST /knowledge/ingest-pdf
Content-Type: multipart/form-data

# Upload a PDF file
# Supports formats:
# - bookname.pdf (single file)
# - bookname_Part17.pdf (multi-part book)
```

Example:
```bash
curl -X POST "http://localhost:8000/knowledge/ingest-pdf" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@Harrison_Part1.pdf"
```

#### Delete Book

```bash
DELETE /knowledge/delete-book/{book_name}

# Delete all chunks of a specific book
```

Example:
```bash
curl -X DELETE "http://localhost:8000/knowledge/delete-book/Harrison" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### List Books

```bash
GET /knowledge/books

# Get list of all books in the knowledge base
```

Example:
```bash
curl "http://localhost:8000/knowledge/books" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Project Structure

```
MEDBotv3/
├── app.py                      # Main AgentOS application with custom routes
├── agents/
│   └── medical_agent.py        # Gemini-powered medical agent
├── config/
│   ├── database.py             # MongoDB & Qdrant setup
│   ├── prompts.py              # System prompts loader
│   └── few_shot_examples.py    # Few-shot examples
├── knowledge/
│   ├── knowledge_base.py       # Knowledge base configuration
│   └── filter_validator.py     # Filter validation logic
├── middleware/
│   └── jwt_config.py           # JWT authentication
├── .env                        # Environment variables (configured)
└── requirements.txt            # Dependencies
```

## Key Features Explained

### 1. Output Schema

The agent returns structured responses:

```json
{
  "answer": "Based on clinical guidelines...",
  "confidence": 0.85,
  "references": [
    {
      "book_name": "Harrison's Principles",
      "page": 234,
      "relevance": 0.9
    }
  ],
  "follow_up_questions": [
    "What are the contraindications?",
    "What is the recommended dosage?"
  ]
}
```

### 2. Session Management

- **Automatic**: User ID extracted from JWT token
- **Session ID**: Provided in request payload
- **Persistence**: Conversations saved in MongoDB
- **Memory**: Context maintained across sessions

### 3. Knowledge Base

- **Hybrid Search**: Combines semantic and keyword search
- **Agentic Filters**: AI automatically determines search filters
- **Filter Validation**: Ensures one book per search
- **Metadata**: book_name, part, page filters available

### 4. Safety Settings

All Gemini safety filters are set to `BLOCK_NONE` for medical content.

## Running with AgentOS

The application uses `agent_os.serve()` for hosting:

```python
if __name__ == "__main__":
    agent_os.serve(
        app="app:app",
        port=8000,
        reload=True  # Set to False in production
    )
```

This provides:
- Built-in SSE streaming
- Session management
- Memory management
- Knowledge management
- Standard AgentOS API

## Development

### Adding Custom Routes

Custom routes are added directly to the FastAPI app:

```python
app = agent_os.get_app()

@app.get("/custom-route")
async def custom_route():
    return {"message": "Custom endpoint"}
```

### Environment Variables

All configuration is done via environment variables in `.env`:

```python
import os

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use a proper JWT verification key
3. Deploy with:
   - Docker
   - AWS ECS
   - Railway
   - Your cloud provider

## Troubleshooting

### Qdrant Connection Issues

Check your Qdrant URL and API key in `.env`:
```env
QDRANT_URL=https://your-cluster.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key
```

### MongoDB Connection Issues

Verify your MongoDB connection string:
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true
```

### JWT Authentication

Ensure you're sending the JWT token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Support

For issues or questions:
1. Check the API docs at `/docs`
2. Review the `.env` configuration
3. Check server logs for errors
