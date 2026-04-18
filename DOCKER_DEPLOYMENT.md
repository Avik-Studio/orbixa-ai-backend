# Medical Bot Agent OS - Docker Deployment Guide

## Quick Start with Docker

### Build and Run
```bash
# Build the image
docker build -t medical-bot-agentos:latest .

# Run with environment file
docker run -d \
  --name medical-bot \
  -p 8000:8000 \
  --env-file .env \
  medical-bot-agentos:latest

# Check logs
docker logs -f medical-bot
```

### Using Docker Compose (Recommended)
```bash
# Start all services (app + MongoDB)
docker-compose up -d

# View logs
docker-compose logs -f medical-bot

# Stop services
docker-compose down
```

## Environment Variables Required

```env
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=medical_bot

# Qdrant (Cloud)
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_api_key
QDRANT_COLLECTION_NAME=medical_knowledge_base

# Google AI
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL_ID=gemini-3-flash-preview

# JWT
JWT_SECRET=your_secret_key

# Server
PORT=8000
DEBUG=False
```

## Health Check
```bash
curl http://localhost:8000/health
```

## Production Deployment

### AWS ECS / Railway / Google Cloud Run
See included `docker-compose.yml` and `Dockerfile` for configuration.

### Security Features
- ✅ Non-root user (UID 1000)
- ✅ Minimal base image (Python 3.11 slim)
- ✅ Health checks included
- ✅ Environment variable configuration

## Monitoring
```bash
# View logs
docker-compose logs -f

# Check stats
docker stats medical-bot

# Inspect container
docker inspect medical-bot
```
