# Quick Start Guide - Medical Bot Agent OS

This guide will get you up and running in 5 minutes.

## Prerequisites

- Python 3.10+
- MongoDB running (local or cloud)
- Qdrant running (local or cloud)
- OpenAI API key

## Quick Setup

### 1. Install Dependencies (1 min)

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment (2 min)

Copy the example environment file:
```bash
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
```

Edit `.env` with your credentials:
```env
# MongoDB - Use local or MongoDB Atlas
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=medical_bot

# Qdrant - Use local or Qdrant Cloud
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=medical_documents

# JWT - Use any secret for development
JWT_VERIFICATION_KEY=dev_secret_key_change_in_production
JWT_ALGORITHM=HS256

# OpenAI - Add your API key
MODEL_API_KEY=sk-your-openai-api-key-here
MODEL_MODEL_ID=gpt-4o
```

### 3. Start Services (Optional - if running locally)

**MongoDB:**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB Community Edition
# https://www.mongodb.com/try/download/community
```

**Qdrant:**
```bash
# Using Docker
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant:latest

# Or download Qdrant
# https://qdrant.tech/documentation/quick-start/
```

### 4. Run the Application (1 min)

**Option A: Using startup script (recommended)**
```bash
python start.py
```

**Option B: Direct run**
```bash
python app.py
```

**Option C: Using uvicorn**
```bash
uvicorn app:app --reload
```

### 5. Test the API (1 min)

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Using the API

### 1. Generate a JWT Token (for testing)

For development, create a simple JWT token:

```python
import jwt
import time

payload = {
    "sub": "test-user-123",
    "session_id": "test-session-abc",
    "email": "test@example.com",
    "exp": int(time.time()) + 3600,  # Expires in 1 hour
    "iat": int(time.time())
}

token = jwt.encode(payload, "dev_secret_key_change_in_production", algorithm="HS256")
print(f"Token: {token}")
```

### 2. Make API Request

**Using curl:**
```bash
curl -X POST http://localhost:8000/agents/medical-agent/run \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the common causes of hypertension?",
    "stream": false
  }'
```

**Using Python:**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "message": "What are the common causes of hypertension?",
    "stream": False
}

response = requests.post(
    "http://localhost:8000/agents/medical-agent/run",
    headers=headers,
    json=data
)

print(response.json())
```

**Using JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/agents/medical-agent/run', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'What are the common causes of hypertension?',
    stream: false
  })
});

const data = await response.json();
console.log(data);
```

## Common Operations

### Create a Session
```bash
POST /agents/medical-agent/run
{
  "message": "Hello, I need help with a medical query",
  "stream": false
}
```

### Continue a Session
```bash
POST /agents/medical-agent/run
{
  "message": "Can you elaborate on that?",
  "session_id": "previous-session-id",
  "stream": false
}
```

### Search Knowledge Base
```bash
POST /knowledge/search
{
  "query": "hypertension treatment",
  "filters": {
    "book_name": "Harrison.pdf"
  },
  "num_documents": 5
}
```

### Get Session History
```bash
GET /agents/medical-agent/sessions/{session_id}
```

## Testing with Swagger UI

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Enter: `Bearer YOUR_JWT_TOKEN`
4. Try the `/agents/medical-agent/run` endpoint
5. Enter your message and execute

## Knowledge Base Setup

### Add Medical Documents to Qdrant

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)

# Create collection (if not exists)
client.create_collection(
    collection_name="medical_documents",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Now use Agno to add documents
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.qdrant import Qdrant

vector_db = Qdrant(
    collection="medical_documents",
    url="http://localhost:6333"
)

knowledge = Knowledge(vector_db=vector_db)

# Add PDF document
knowledge.add_content(
    name="Harrison's Principles",
    path="path/to/harrisons.pdf",
    metadata={"book_name": "Harrison.pdf"}
)
```

## Troubleshooting

### MongoDB Connection Error
```
Error: MongoDB connection failed
```

**Solution:**
- Check MongoDB is running: `mongosh --eval "db.runCommand({ ping: 1 })"`
- Verify MONGODB_URL in .env
- For cloud MongoDB, ensure IP is whitelisted

### Qdrant Connection Error
```
Error: Qdrant connection failed
```

**Solution:**
- Check Qdrant is running: `curl http://localhost:6333/collections`
- Verify QDRANT_URL in .env
- Check collection exists in Qdrant

### JWT Authentication Error
```
Error: Unauthenticated access
```

**Solution:**
- Ensure Authorization header is set: `Authorization: Bearer YOUR_TOKEN`
- Verify JWT_VERIFICATION_KEY matches between token generation and .env
- Check token hasn't expired

### OpenAI API Error
```
Error: Invalid API key
```

**Solution:**
- Verify MODEL_API_KEY in .env
- Check API key is active at https://platform.openai.com/api-keys
- Ensure you have credits available

## Next Steps

1. **Add Medical Documents**: Upload your medical textbooks to Qdrant
2. **Configure Prompts**: Customize prompts in `Prompts.md`
3. **Set Up Production**: Follow deployment guide in README.md
4. **Add Custom Tools**: Extend agent capabilities
5. **Monitor Usage**: Set up logging and monitoring

## Development Mode

Enable debug mode for verbose logging:

```env
DEBUG=true
AGENTOS_RELOAD=true
```

This will show:
- Configuration details
- Knowledge base searches
- Filter validations
- Tool calls
- Session state updates

## Production Checklist

Before deploying to production:

- [ ] Use production MongoDB (MongoDB Atlas)
- [ ] Use production Qdrant (Qdrant Cloud)
- [ ] Generate strong JWT keys (RS256 recommended)
- [ ] Set DEBUG=false
- [ ] Configure proper CORS settings
- [ ] Add rate limiting
- [ ] Set up monitoring/logging
- [ ] Enable HTTPS
- [ ] Configure backup strategy
- [ ] Test all endpoints
- [ ] Document API for your team

## Getting Help

- Check README.md for detailed documentation
- Review IMPLEMENTATION_PLAN.md for architecture details
- Examine example code in each module
- Enable debug mode for troubleshooting

## Quick Commands Cheat Sheet

```bash
# Start application
python start.py

# Run with auto-reload
uvicorn app:app --reload

# Test health endpoint
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# Check logs
# See terminal output

# Stop application
# Press Ctrl+C

# Restart MongoDB
docker restart mongodb

# Restart Qdrant
docker restart qdrant
```

## Success! 🎉

Your Medical Bot Agent OS is now running!

Access the Swagger UI at http://localhost:8000/docs to explore and test all available endpoints.
