# Deployment Guide - Medical Bot Agent OS

This guide covers deploying the Medical Bot Agent OS to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Database Setup](#database-setup)
6. [Security Hardening](#security-hardening)
7. [Monitoring & Logging](#monitoring--logging)
8. [Scaling](#scaling)

## Pre-Deployment Checklist

### Essential Tasks
- [ ] Test application locally with production-like settings
- [ ] Set up production MongoDB (MongoDB Atlas recommended)
- [ ] Set up production Qdrant (Qdrant Cloud recommended)
- [ ] Generate production JWT keys (RS256 recommended)
- [ ] Configure environment variables for production
- [ ] Add medical documents to Qdrant knowledge base
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for your frontend domain
- [ ] Set up monitoring and logging
- [ ] Create backup strategy
- [ ] Document runbook for operations team

### Security Checklist
- [ ] Use strong JWT signing keys
- [ ] Enable HTTPS/TLS
- [ ] Set secure CORS origins
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Configure network security groups
- [ ] Enable audit logging
- [ ] Review and minimize IAM permissions

## Environment Setup

### Production Environment Variables

Create a production `.env` file:

```env
# Production Mode
DEBUG=false
AGENTOS_RELOAD=false
AGENTOS_HOST=0.0.0.0
AGENTOS_PORT=8000

# MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/medical_bot?retryWrites=true&w=majority
MONGODB_DATABASE=medical_bot
MONGODB_SESSION_TABLE=agent_sessions

# Qdrant Cloud
QDRANT_URL=https://your-cluster-id.qdrant.io
QDRANT_API_KEY=your_production_api_key
QDRANT_COLLECTION_NAME=medical_documents

# JWT Configuration (RS256 for production)
JWT_VERIFICATION_KEY="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhki...\n-----END PUBLIC KEY-----"
JWT_ALGORITHM=RS256
JWT_USER_ID_CLAIM=sub
JWT_SESSION_ID_CLAIM=session_id
JWT_VALIDATE=true
JWT_AUTHORIZATION=true
JWT_VERIFY_AUDIENCE=true
JWT_AUDIENCE=medical-ai-production

# OpenAI
MODEL_PROVIDER=openai
MODEL_API_KEY=sk-prod-your-production-key
MODEL_MODEL_ID=gpt-4o
MODEL_TEMPERATURE=0.7

# AgentOS
AGENTOS_NAME=Medical AI Agent OS
AGENTOS_DESCRIPTION=Production Medical AI Assistant
```

### Secrets Management

**AWS Secrets Manager:**
```bash
# Store secrets
aws secretsmanager create-secret \
  --name medical-bot/jwt-key \
  --secret-string "your-jwt-key"

# Retrieve in application
import boto3
secret = boto3.client('secretsmanager').get_secret_value(SecretId='medical-bot/jwt-key')
```

**Google Secret Manager:**
```bash
# Store secrets
gcloud secrets create jwt-key --data-file=key.txt

# Access in application
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/jwt-key/versions/latest"
response = client.access_secret_version(request={"name": name})
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (with services)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - QDRANT_URL=http://qdrant:6333
      - JWT_VERIFICATION_KEY=${JWT_VERIFICATION_KEY}
      - MODEL_API_KEY=${MODEL_API_KEY}
    depends_on:
      - mongodb
      - qdrant
    restart: unless-stopped
    networks:
      - medical-bot-network

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb-data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=medical_bot
    restart: unless-stopped
    networks:
      - medical-bot-network

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant-data:/qdrant/storage
    restart: unless-stopped
    networks:
      - medical-bot-network

volumes:
  mongodb-data:
  qdrant-data:

networks:
  medical-bot-network:
    driver: bridge
```

### Build and Run

```bash
# Build image
docker build -t medical-bot-agentos:latest .

# Run container
docker run -d \
  --name medical-bot \
  -p 8000:8000 \
  --env-file .env.production \
  medical-bot-agentos:latest

# Or use docker-compose
docker-compose up -d
```

## Cloud Deployment

### AWS (ECS with Fargate)

#### 1. Create ECR Repository
```bash
aws ecr create-repository --repository-name medical-bot-agentos
```

#### 2. Build and Push Image
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t medical-bot-agentos .
docker tag medical-bot-agentos:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/medical-bot-agentos:latest

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/medical-bot-agentos:latest
```

#### 3. Create ECS Task Definition

`task-definition.json`:
```json
{
  "family": "medical-bot-agentos",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "medical-bot",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/medical-bot-agentos:latest",
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "AGENTOS_PORT", "value": "8000"}
    ],
    "secrets": [
      {"name": "JWT_VERIFICATION_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
      {"name": "MODEL_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/medical-bot",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

#### 4. Create ECS Service
```bash
aws ecs create-service \
  --cluster medical-bot-cluster \
  --service-name medical-bot-service \
  --task-definition medical-bot-agentos \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Railway

#### Deploy to Railway

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login and Initialize:**
```bash
railway login
railway init
```

3. **Configure:**
Create `railway.json`:
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

4. **Deploy:**
```bash
railway up
```

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT-ID/medical-bot-agentos

# Deploy to Cloud Run
gcloud run deploy medical-bot-agentos \
  --image gcr.io/PROJECT-ID/medical-bot-agentos \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URL=xxx,QDRANT_URL=xxx \
  --set-secrets JWT_VERIFICATION_KEY=jwt-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10
```

## Database Setup

### MongoDB Atlas

1. **Create Cluster:**
   - Go to https://cloud.mongodb.com
   - Create new cluster (M10+ for production)
   - Select region close to your application
   - Enable backups

2. **Configure Access:**
   - Add IP whitelist (or allow all: 0.0.0.0/0)
   - Create database user
   - Get connection string

3. **Connection String:**
```
mongodb+srv://username:password@cluster.mongodb.net/medical_bot?retryWrites=true&w=majority
```

### Qdrant Cloud

1. **Create Cluster:**
   - Go to https://cloud.qdrant.io
   - Create new cluster
   - Select region and plan

2. **Get API Key:**
   - Generate API key
   - Note cluster URL

3. **Configuration:**
```env
QDRANT_URL=https://your-cluster-id.qdrant.io
QDRANT_API_KEY=your_api_key
```

## Security Hardening

### 1. HTTPS/TLS Configuration

**Using Nginx as reverse proxy:**

`nginx.conf`:
```nginx
server {
    listen 80;
    server_name api.medical-bot.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.medical-bot.com;

    ssl_certificate /etc/letsencrypt/live/api.medical-bot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.medical-bot.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Rate Limiting

Add to `app.py`:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/agents/medical-agent/run")
@limiter.limit("10/minute")
async def run_agent(request: Request):
    # ... existing code
```

### 3. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Monitoring & Logging

### Structured Logging

Install: `pip install structlog`

```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request_started", method=request.method, path=request.url.path)
    response = await call_next(request)
    logger.info("request_completed", status_code=response.status_code)
    return response
```

### Sentry Integration

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
    environment="production"
)
```

### CloudWatch Logs (AWS)

Already configured in ECS task definition with awslogs driver.

## Scaling

### Horizontal Scaling

**ECS Auto Scaling:**
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/cluster/medical-bot-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/cluster/medical-bot-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

### Vertical Scaling

Increase resources in task definition:
```json
{
  "cpu": "2048",
  "memory": "4096"
}
```

## Health Checks

### Liveness Probe
```bash
curl http://localhost:8000/health
```

### Readiness Probe
```bash
curl http://localhost:8000/config
```

## Backup Strategy

### MongoDB Backup
```bash
# Automated backups in Atlas
# Or manual backup
mongodump --uri="mongodb+srv://..." --out=/backup/$(date +%Y%m%d)
```

### Qdrant Backup
```bash
# Create snapshot
curl -X POST 'http://localhost:6333/collections/medical_documents/snapshots'
```

## Rollback Plan

```bash
# AWS ECS rollback
aws ecs update-service \
  --cluster medical-bot-cluster \
  --service medical-bot-service \
  --task-definition medical-bot-agentos:previous-version

# Docker rollback
docker pull medical-bot-agentos:previous-tag
docker stop medical-bot && docker rm medical-bot
docker run -d --name medical-bot medical-bot-agentos:previous-tag
```

## Cost Optimization

1. **Use spot instances/preemptible VMs for non-critical workloads**
2. **Enable auto-scaling to scale down during low usage**
3. **Use reserved instances for baseline capacity**
4. **Implement caching where appropriate**
5. **Monitor and optimize API call costs**

## Post-Deployment Verification

- [ ] Health endpoint returns 200
- [ ] API documentation accessible
- [ ] JWT authentication works
- [ ] Agent responds correctly
- [ ] Knowledge search works
- [ ] Sessions persist correctly
- [ ] Logs are being captured
- [ ] Monitoring dashboards show data
- [ ] SSL certificate valid
- [ ] CORS working for frontend

## Troubleshooting Production Issues

### High CPU Usage
- Check agent token usage
- Review knowledge base search queries
- Monitor concurrent requests
- Scale horizontally if needed

### Memory Leaks
- Monitor container memory usage
- Check for unclosed connections
- Review session cleanup

### Database Connection Errors
- Verify connection strings
- Check IP whitelist
- Monitor connection pool
- Review timeout settings

---

For additional support with deployment, consult the main README.md and PROJECT_SUMMARY.md files.
