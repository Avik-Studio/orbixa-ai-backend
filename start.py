#!/usr/bin/env python
"""
Startup script for Orbixa AI Agent OS.
Checks dependencies, validates configuration, and starts the server.
"""
import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_env_file():
    """Check if .env file exists."""
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found")
        print("   Creating from .env.example...")
        
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file")
            print("⚠️  Please edit .env with your configuration before continuing")
            sys.exit(1)
        else:
            print("❌ Error: .env.example not found")
            sys.exit(1)
    print("✓ .env file found")


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "agno",
        "fastapi",
        "uvicorn",
        "pymongo",
        "qdrant_client",
        "pydantic",
        "python_dotenv",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✓ All required packages installed")


def validate_config():
    """Validate configuration from .env."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "MONGODB_URL",
        "QDRANT_URL",
        "JWT_VERIFICATION_KEY",
        "MODEL_API_KEY",
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please configure them in .env file")
        sys.exit(1)
    
    print("✓ Configuration validated")


def check_services():
    """Check if MongoDB and Qdrant are accessible."""
    from pymongo import MongoClient
    from qdrant_client import QdrantClient
    import os
    
    # Check MongoDB
    try:
        mongodb_url = os.getenv("MONGODB_URL")
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✓ MongoDB connection successful")
    except Exception as e:
        print(f"⚠️  Warning: MongoDB connection failed: {e}")
        print("   The application will try to connect at startup")
    
    # Check Qdrant
    try:
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Parse URL for client
        if qdrant_url.startswith("http://"):
            url = qdrant_url.replace("http://", "")
            port = 6333
            if ":" in url:
                url, port = url.split(":")
                port = int(port)
            client = QdrantClient(host=url, port=port, api_key=qdrant_api_key, timeout=5)
        else:
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=5)
        
        client.get_collections()
        print("✓ Qdrant connection successful")
    except Exception as e:
        print(f"⚠️  Warning: Qdrant connection failed: {e}")
        print("   The application will try to connect at startup")


def start_server():
    """Start the AgentOS server."""
    import uvicorn
    from config.env import settings
    
    print("\n" + "="*60)
    print(f"  {settings.agentos.name}")
    print("="*60)
    print(f"Starting server on {settings.agentos.host}:{settings.agentos.port}")
    print(f"Debug mode: {settings.debug}")
    print(f"Reload: {settings.agentos.reload}")
    print("\nEndpoints:")
    print(f"  - API Docs: http://localhost:{settings.agentos.port}/docs")
    print(f"  - ReDoc: http://localhost:{settings.agentos.port}/redoc")
    print(f"  - Health: http://localhost:{settings.agentos.port}/health")
    print("="*60 + "\n")
    
    uvicorn.run(
        "app:app",
        host=settings.agentos.host,
        port=settings.agentos.port,
        reload=settings.agentos.reload,
        log_level="debug" if settings.debug else "info",
    )


def main():
    """Main startup function."""
    print("\n" + "="*60)
    print("  Orbixa AI Agent OS - Startup")
    print("="*60 + "\n")
    
    try:
        print("Checking system requirements...")
        check_python_version()
        check_env_file()
        check_dependencies()
        
        print("\nValidating configuration...")
        validate_config()
        
        print("\nChecking external services...")
        check_services()
        
        print("\n✓ All checks passed!")
        print("\nStarting server...\n")
        
        start_server()
        
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        if os.getenv("DEBUG", "false").lower() == "true":
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
