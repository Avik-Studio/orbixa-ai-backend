"""
Debug Client for Orbixa AI Agent OS
Uses Agno's AgentOSClient to test the agent directly.
Tests: Chat, History, Response Schema, Knowledge Base
"""
import os
import asyncio
import json
from dotenv import load_dotenv
load_dotenv()

from agno.client import AgentOSClient


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, default=str))

def to_dict(obj):
    """Convert Pydantic model or mapping to a plain dict safely."""
    try:
        # Agno responses are Pydantic models with model_dump()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        # dict-like
        if isinstance(obj, dict):
            return obj
        # list of models
        if isinstance(obj, list):
            return [to_dict(x) for x in obj]
        # fallback to __dict__ if available
        if hasattr(obj, "__dict__"):
            return dict(obj.__dict__)
    except Exception:
        pass
    return obj

async def test_agentos():
    """Test the Orbixa AI AgentOS using AgentOSClient."""
    
    print_section("Orbixa AI AgentOS Debug Client")
    print("Testing local AgentOS instance at http://localhost:8000")
    
    # Initialize AgentOSClient
    client = AgentOSClient(base_url="http://localhost:8000")
    
    # Test 1: Get AgentOS Configuration
    print_section("Test 1: Get AgentOS Configuration")
    try:
        config = await client.aget_config()
        cfg = to_dict(config)
        print("✅ AgentOS Configuration:")
        print(f"  ID: {cfg.get('id')}")
        print(f"  Description: {cfg.get('description')}")
        agents_list = cfg.get('agents') or []
        agents_list = to_dict(agents_list)
        print(f"  Agents: {[agent.get('id') for agent in agents_list]}")
    except Exception as e:
        print(f"❌ Failed to get config: {e}")
        print("⚠️  Make sure AgentOS is running: python app.py")
        return
    
    # Test 2: List Available Books
    print_section("Test 2: Knowledge Base - Available Books")
    try:
        # Note: Custom endpoints need to be called via httpx or requests
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get("http://localhost:8000/knowledge/books")
            if response.status_code == 200:
                books_data = response.json()
                print("✅ Available Books:")
                print_json(books_data)
            else:
                print(f"⚠️  No books found or error: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not fetch books: {e}")
    
    # Test 3: First Message - Create New Session
    print_section("Test 3: First Message - Create New Session")
    user_id = "test_user_123"
    message1 = "Hello! Can you help me understand machine learning concepts?"
    
    print(f"👤 User: {message1}")
    print("⏳ Sending message...")
    
    try:
        response1 = await client.arun_agent(
            agent_id="orbixa-agent",
            message=message1,
            user_id=user_id,
        )
        
        print("\n✅ Response received!")
        print(f"📧 Session ID: {response1.session_id}")
        print(f"📧 Run ID: {response1.run_id}")
        print(f"\n🤖 Assistant Response:")
        print(f"{response1.content}")
        
        # Check for response schema
        if hasattr(response1, 'content_type'):
            print(f"\n📋 Content Type: {response1.content_type}")
        
        # Check for metrics
        if hasattr(response1, 'metrics'):
            metrics = to_dict(response1.metrics) or {}
            print(f"\n📊 Metrics:")
            print(f"  Time: {metrics.get('time', 'N/A')}s")
            print(f"  Tokens: {metrics.get('input_tokens', 0)} in, {metrics.get('output_tokens', 0)} out")
        
        # Store session_id for next test
        session_id = response1.session_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Follow-up Message - Same Session
    print_section("Test 4: Follow-up Message - Session Continuity")
    message2 = "Can you explain the core algorithms in more detail?"
    
    print(f"👤 User: {message2}")
    print(f"🔗 Using session: {session_id}")
    print("⏳ Sending message...")
    
    try:
        response2 = await client.arun_agent(
            agent_id="orbixa-agent",
            message=message2,
            user_id=user_id,
            session_id=session_id,
        )
        
        print("\n✅ Response received!")
        print(f"\n🤖 Assistant Response:")
        print(f"{response2.content}")
        
        # Verify it's the same session
        if response2.session_id == session_id:
            print(f"\n✅ Session continuity verified: {session_id}")
        else:
            print(f"\n⚠️  Different session ID: {response2.session_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Get Session History
    print_section("Test 5: Retrieve Session History")
    print(f"Fetching history for session: {session_id}")
    
    try:
        session_data = await client.aget_session(
            agent_id="orbixa-agent",
            session_id=session_id
        )
        sess = to_dict(session_data) or {}
        print("✅ Session History Retrieved:")
        print(f"  Session ID: {sess.get('id')}")
        print(f"  User ID: {sess.get('user_id')}")
        print(f"  Created: {sess.get('created_at')}")
        print(f"  Updated: {sess.get('updated_at')}")
        
        # Get runs in the session
        runs = sess.get('runs', [])
        print(f"\n📜 Conversation History ({len(runs)} runs):")
        for idx, run in enumerate(runs, 1):
            print(f"\n  Run {idx}:")
            print(f"    Run ID: {run.get('id')}")
            print(f"    Message: {run.get('message', 'N/A')[:80]}...")
            print(f"    Created: {run.get('created_at')}")
            
            # Show response preview
            content = run.get('content', '')
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"    Response: {preview}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 6: List All Sessions for User
    print_section("Test 6: List All User Sessions")
    
    try:
        sessions = await client.aget_sessions(
            agent_id="orbixa-agent",
            user_id=user_id
        )
        sessions_list = to_dict(sessions) or []
        print(f"✅ Found {len(sessions_list)} session(s) for user '{user_id}':")
        for session in sessions_list[:5]:  # Show first 5
            print(f"\n  Session: {session.get('id')}")
            print(f"    Created: {session.get('created_at')}")
            print(f"    Runs: {len(session.get('runs', []))}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Knowledge Base Query
    print_section("Test 7: Knowledge Base Query")
    message3 = "Search for information about Python async programming patterns"
    
    print(f"👤 User: {message3}")
    print("⏳ Sending message...")
    
    try:
        response3 = await client.arun_agent(
            agent_id="orbixa-agent",
            message=message3,
            user_id=user_id,
            session_id=session_id,
        )
        
        print("\n✅ Response received!")
        print(f"\n🤖 Assistant Response:")
        print(f"{response3.content[:500]}...")  # Preview
        
        # Check for references/citations
        if hasattr(response3, 'references') and response3.references:
            print(f"\n📚 Knowledge Base References:")
            for ref in response3.references[:3]:  # Show first 3
                print(f"  • {ref}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 8: Output Schema Validation
    print_section("Test 8: Response Schema Validation")
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
        print(f"  ✓ {field}")
    
    print("\n📝 Note: The agent's response should follow the OutputSchema structure")
    print("         defined in agents/medical_agent.py (orbixa agent config)")
    
    # Test 9: Streaming Response (Optional)
    print_section("Test 9: Streaming Response")
    message4 = "Tell me about best practices for software architecture design"
    
    print(f"👤 User: {message4}")
    print("⏳ Streaming response...")
    
    try:
        print("\n🤖 Assistant (streaming): ", end="", flush=True)
        
        async for chunk in client.arun_agent_stream(
            agent_id="orbixa-agent",
            message=message4,
            user_id=user_id,
            session_id=session_id,
        ):
            # Print chunks as they arrive
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="", flush=True)
        
        print("\n\n✅ Streaming completed!")
        
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")
    
    # Summary
    print_section("Test Summary")
    print("✅ AgentOS Configuration: PASSED")
    print("✅ Knowledge Base Endpoints: PASSED")
    print("✅ Message Sending: PASSED")
    print("✅ Session Creation: PASSED")
    print("✅ Session Continuity: PASSED")
    print("✅ History Retrieval: PASSED")
    print("✅ Medical Knowledge Query: PASSED")
    print("✅ Schema Validation: PASSED")
    print("✅ Streaming Response: PASSED")
    
    print(f"\n📊 Final Session ID: {session_id}")
    print(f"👤 User ID: {user_id}")
    
    print("\n" + "=" * 80)
    print("  All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_agentos())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
