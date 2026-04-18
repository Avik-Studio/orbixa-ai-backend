"""
Medical Bot Agent OS - Main Application
Production-ready FastAPI application powered by Agno Agent OS with Gemini.
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from fastapi import UploadFile, File, Request
from fastapi.responses import JSONResponse
from agno.os import AgentOS
from agno.os.middleware import JWTMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from agents.medical_agent import create_medical_agent
from knowledge.knowledge_base import ingest_pdf_file, delete_book_by_name, get_all_books

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create AgentOS instance
agent_os = AgentOS(
    id="medical-os",
    description=os.getenv("AGENTOS_DESCRIPTION", "Production runtime for Assessli medical AI assistant"),
    agents=[create_medical_agent()],
)

# Get the FastAPI app
app = agent_os.get_app()

# Add JWT middleware
jwt_secret = os.getenv("JWT_SECRET")
app.add_middleware(
    JWTMiddleware,
    verification_keys=[jwt_secret] if jwt_secret else None,
    algorithm="HS256",
    user_id_claim="userId",
    dependencies_claims=["userId"],
    validate=True,
    excluded_route_paths=[
        "/",
        "/health",
        "/v1/health",
        "/v1",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/config",
    ],
)


# Custom logging middleware for /agents/medical-agent endpoints
class AgentRunLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log for specific endpoints
        should_log = (
            request.url.path == "/agents/medical-agent/runs" or
            request.url.path.startswith("/sessions")
        )
        
        if should_log:
            logger.info("=" * 80)
            logger.info(f"📨 INCOMING REQUEST to {request.url.path}")
            logger.info("=" * 80)
            
            # Log request method and URL
            logger.info(f"Method: {request.method}")
            logger.info(f"URL: {request.url}")
            logger.info(f"Client: {request.client.host}:{request.client.port}" if request.client else "Client: Unknown")
            
            # Log headers (excluding sensitive auth data)
            logger.info("\n📋 Headers:")
            for header_name, header_value in request.headers.items():
                if header_name.lower() == "authorization":
                    logger.info(f"  {header_name}: Bearer <token_hidden>")
                else:
                    logger.info(f"  {header_name}: {header_value}")
            
            # Log query parameters
            if request.query_params:
                logger.info("\n🔍 Query Parameters:")
                for key, value in request.query_params.items():
                    logger.info(f"  {key}: {value}")
            
            # Log request body
            try:
                # Read the body
                body = await request.body()
                if body:
                    # Check content type to determine how to log
                    content_type = request.headers.get('content-type', '')
                    
                    # Handle multipart/form-data (file uploads, form data)
                    if 'multipart/form-data' in content_type:
                        logger.info(f"\n📦 Request Body: <multipart/form-data - {len(body)} bytes>")
                        logger.info(f"   Likely contains files or form fields")
                    # Handle binary data
                    elif len(body) > 0 and body[0] in (0x89, 0xFF, 0x25, 0x50):  # PNG, JPEG, PDF, etc.
                        logger.info(f"\n📦 Request Body: <binary data - {len(body)} bytes>")
                    else:
                        # Try to decode and parse as text/JSON
                        try:
                            body_str = body.decode('utf-8')
                            try:
                                body_json = json.loads(body_str)
                                logger.info("\n📦 Request Body (JSON):")
                                logger.info(json.dumps(body_json, indent=2))
                                
                                # Log specific fields
                                if "message" in body_json:
                                    logger.info(f"\n💬 Message: {body_json['message']}")
                                if "session_id" in body_json:
                                    logger.info(f"🔑 Session ID: {body_json['session_id']}")
                                if "user_id" in body_json:
                                    logger.info(f"👤 User ID: {body_json['user_id']}")
                                if "stream" in body_json:
                                    logger.info(f"📡 Stream: {body_json['stream']}")
                            except json.JSONDecodeError:
                                logger.info("\n📦 Request Body (Text):")
                                logger.info(body_str[:500])  # First 500 chars
                        except UnicodeDecodeError:
                            logger.info(f"\n📦 Request Body: <binary data - {len(body)} bytes>")
                    
                    # Important: Recreate request with body for downstream processing
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                else:
                    logger.info("\n📦 Request Body: <empty>")
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
            
            logger.info("=" * 80)
        
        # Continue processing request
        response = await call_next(request)
        
        # Log response for the specific endpoints
        if should_log:
            logger.info("\n" + "=" * 80)
            logger.info(f"📤 RESPONSE from {request.url.path}")
            logger.info("=" * 80)
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # For DELETE requests, try to read response body
            if request.method == "DELETE":
                # Read response body to check if it's empty
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                if response_body:
                    try:
                        body_str = response_body.decode('utf-8')
                        logger.info(f"Response Body: {body_str}")
                    except:
                        logger.info(f"Response Body: <binary - {len(response_body)} bytes>")
                else:
                    logger.info("⚠️  Response Body: <EMPTY> - This will cause JSON parse error!")
                
                # Recreate response with body
                from starlette.responses import Response
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            
            logger.info("=" * 80 + "\n")
        
        return response


# Add the logging middleware
app.add_middleware(AgentRunLoggingMiddleware)


# Custom endpoints for PDF ingestion and book management
@app.post("/knowledge/ingest-pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    """
    Ingest a PDF file into the knowledge base.
    Supports formats: bookname.pdf or bookname_Part17.pdf
    """
    try:
        # Create temp directory
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        temp_file = temp_dir / file.filename
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Call the helper function to ingest the PDF
        result = await ingest_pdf_file(temp_file, file.filename)
        
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
        
        # Return appropriate status code
        if result["success"]:
            return JSONResponse(result)
        else:
            status_code = 400 if result.get("error_type") == "invalid_file" else 500
            return JSONResponse(status_code=status_code, content=result)
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_file' in locals() and temp_file.exists():
            temp_file.unlink()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": f"Failed to ingest {file.filename}"
            }
        )


@app.delete("/knowledge/delete-book/{book_name}")
async def delete_book(book_name: str):
    """Delete all chunks of a specific book from the knowledge base."""
    result = await delete_book_by_name(book_name)
    
    if result["success"]:
        return JSONResponse(result)
    else:
        status_code = 404 if "not found" in result.get("message", "") else 500
        return JSONResponse(status_code=status_code, content=result)


@app.get("/knowledge/books")
async def list_books():
    """Get list of all books in the knowledge base with chunk counts and parts."""
    result = await get_all_books()
    
    if result["success"]:
        return JSONResponse(result)
    else:
        return JSONResponse(status_code=500, content=result)


if __name__ == "__main__":
    agent_os.serve(
        app="app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "False").lower() == "true",
    )


