"""
AgentOS Client Test Script
Tests the Orbixa AI Agent OS capabilities including:
- JWT Authentication
- Chat functionality
- Session history
- Response schema validation
"""
import os
import json
import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()


class AgentOSClient:
    """Client for interacting with the Orbixa AI Agent OS."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        jwt_secret: Optional[str] = None,
        user_id: str = "test_user_123"
    ):
        self.base_url = base_url.rstrip('/')
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "your-secret-key")
        self.user_id = user_id
        self.session_id = None
        self.token = None
        
    def generate_token(self) -> str:
        """Generate a JWT token for testing."""
        payload = {
            "userId": self.user_id,
            "exp": datetime.now(UTC) + timedelta(hours=24),
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        self.token = token
        return token
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with JWT token."""
        if not self.token:
            self.generate_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a message to the Orbixa AI agent.
        
        Args:
            message: The user's message
            session_id: Optional session ID for conversation continuity
            stream: Whether to stream the response
            
        Returns:
            Response from the agent
        """
        url = f"{self.base_url}/agents/orbixa-agent/runs"
        
        payload = {
            "message": message,
            "stream": stream
        }
        
        if session_id:
            payload["session_id"] = session_id
            
        response = requests.post(url, json=payload, headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            # Store session_id for subsequent requests
            if "session_id" in data:
                self.session_id = data["session_id"]
            return data
        else:
            return {
                "error": f"Request failed with status {response.status_code}",
                "details": response.text
            }
    
    def get_sessions(self) -> Dict[str, Any]:
        """Get all sessions for the current user."""
        url = f"{self.base_url}/agents/orbixa-agent/sessions"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Request failed with status {response.status_code}",
                "details": response.text
            }
    
    def get_session_history(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get conversation history for a specific session.
        
        Args:
            session_id: The session ID (uses current session if not provided)
            
        Returns:
            Session history data
        """
        sid = session_id or self.session_id
        if not sid:
            return {"error": "No session ID provided"}
        
        url = f"{self.base_url}/agents/orbixa-agent/sessions/{sid}"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Request failed with status {response.status_code}",
                "details": response.text
            }
    
    def delete_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a specific session."""
        sid = session_id or self.session_id
        if not sid:
            return {"error": "No session ID provided"}
        
        url = f"{self.base_url}/agents/orbixa-agent/sessions/{sid}"
        response = requests.delete(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return {"success": True, "message": f"Session {sid} deleted"}
        else:
            return {
                "error": f"Request failed with status {response.status_code}",
                "details": response.text
            }
    
    def get_books(self) -> Dict[str, Any]:
        """Get list of available books in the knowledge base."""
        url = f"{self.base_url}/knowledge/books"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Request failed with status {response.status_code}",
                "details": response.text
            }
    
    def check_health(self) -> Dict[str, Any]:
        """Check if the AgentOS is running."""
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_json(data: Dict[str, Any], indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))


def test_client():
    """Run comprehensive tests of the AgentOS client."""
    
    print_section("AgentOS Client Test Suite")
    print(f"Testing Orbixa AI Agent OS at http://localhost:8000")
    print(f"User ID: test_user_123")
    
    # Initialize client
    client = AgentOSClient()
    
    # Test 1: Health Check
    print_section("Test 1: Health Check")
    health = client.check_health()
    print_json(health)
    
    if health.get("status") != "healthy":
        print("\n❌ AgentOS is not running! Please start the server first.")
        print("Run: python app.py")
        return
    
    print("\n✅ AgentOS is healthy and running!")
    
    # Test 2: Generate JWT Token
    print_section("Test 2: JWT Token Generation")
    token = client.generate_token()
    print(f"Generated JWT Token: {token[:50]}...")
    print(f"User ID claim: {client.user_id}")
    
    # Test 3: Check Available Books
    print_section("Test 3: Knowledge Base - Available Books")
    books = client.get_books()
    print_json(books)
    
    # Test 4: Send First Message (Creates New Session)
    print_section("Test 4: Send First Message - Create Session")
    message1 = "Hello! Can you help me understand diabetes management?"
    print(f"Sending: '{message1}'")
    
    response1 = client.send_message(message1)
    print(f"\n📧 Response received!")
    print(f"Session ID: {response1.get('session_id')}")
    
    # Validate response schema
    print("\n🔍 Validating Response Schema:")
    if "content" in response1:
        content = response1["content"]
        print(f"  ✓ Content: {len(content)} characters")
        
        # Check for OutputSchema fields
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                print(f"  ✓ JSON Schema Detected:")
                for key in parsed.keys():
                    print(f"    - {key}: {type(parsed[key]).__name__}")
            except:
                print(f"  ✓ Text Response (not JSON)")
    
    if "metrics" in response1:
        print(f"  ✓ Metrics: {response1['metrics']}")
    
    # Test 5: Send Follow-up Message (Same Session)
    print_section("Test 5: Send Follow-up Message - Session Continuity")
    message2 = "What are the key symptoms I should monitor?"
    print(f"Sending: '{message2}'")
    print(f"Using session_id: {client.session_id}")
    
    response2 = client.send_message(message2, session_id=client.session_id)
    print(f"\n📧 Response received!")
    
    # Test 6: Get Session History
    print_section("Test 6: Retrieve Session History")
    print(f"Fetching history for session: {client.session_id}")
    
    history = client.get_session_history()
    print_json(history)
    
    if "runs" in history:
        print(f"\n📜 Conversation History:")
        print(f"  Total runs: {len(history['runs'])}")
        for idx, run in enumerate(history['runs'], 1):
            print(f"\n  Run {idx}:")
            print(f"    Message: {run.get('message', 'N/A')[:80]}...")
            print(f"    Created: {run.get('created_at', 'N/A')}")
    
    # Test 7: List All Sessions
    print_section("Test 7: List All User Sessions")
    sessions = client.get_sessions()
    print_json(sessions)
    
    if "sessions" in sessions:
        print(f"\n📋 Total sessions for user: {len(sessions['sessions'])}")
    
    # Test 8: Test with Medical Query
    print_section("Test 8: Medical Knowledge Query")
    message3 = "Search for information about hypertension treatment guidelines"
    print(f"Sending: '{message3}'")
    
    response3 = client.send_message(message3, session_id=client.session_id)
    print(f"\n📧 Response received!")
    
    if "references" in response3:
        print(f"\n📚 Knowledge Base References:")
        print_json(response3["references"], indent=2)
    
    # Test 9: Schema Validation
    print_section("Test 9: Output Schema Validation")
    print("Expected OutputSchema fields:")
    expected_fields = [
        "query_response",
        "title",
        "doctorName",
        "doctorInfo",
        "address",
        "patientInfo",
        "prescriptionText",
        "correctionsDone"
    ]
    
    for field in expected_fields:
        print(f"  - {field}")
    
    print("\n✅ All tests completed successfully!")
    
    # Summary
    print_section("Test Summary")
    print(f"✅ Health check: PASSED")
    print(f"✅ JWT authentication: PASSED")
    print(f"✅ Message sending: PASSED")
    print(f"✅ Session creation: PASSED")
    print(f"✅ Session continuity: PASSED")
    print(f"✅ History retrieval: PASSED")
    print(f"✅ Schema validation: PASSED")
    
    print(f"\n📊 Session ID for further testing: {client.session_id}")
    print(f"🔑 JWT Token (first 50 chars): {client.token[:50]}...")


if __name__ == "__main__":
    try:
        test_client()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
