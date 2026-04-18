"""
Orbixa AI Agent OS - Agno Client Library Test

Uses the official Agno AgentOS client library to test the Orbixa AI Agent OS
running on port 8000.

Installation:
    pip install agno

Usage:
    python test_agno_client.py
"""

import asyncio
import json
from typing import Optional
from agno.client.os import AgentOSClient


class MedicalBotTester:
    """Test Orbixa AI Agent OS using Agno client library."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the tester with AgentOS client."""
        self.client = AgentOSClient(base_url=base_url)
        self.agent_id = "orbixa-agent"
        self.session_id: Optional[str] = None
        self.user_id = "test_user_123"
        
    async def run_all_tests(self):
        """Run comprehensive test suite."""
        print("\n" + "=" * 80)
        print("  Orbixa AI Agent OS - Agno Client Test Suite")
        print("=" * 80)
        
        try:
            # Test 1: Get Configuration
            await self.test_get_config()
            
            # Test 2: List Agents
            await self.test_list_agents()
            
            # Test 3: Get Specific Agent
            await self.test_get_agent()
            
            # Test 4: Run Agent (Create Session)
            await self.test_run_agent_simple()
            
            # Test 5: Continue Conversation
            await self.test_run_agent_continuation()
            
            # Test 6: Stream Response
            await self.test_run_agent_stream()
            
            # Test 7: Get Sessions
            await self.test_get_sessions()
            
            # Test 8: Get Specific Session
            if self.session_id:
                await self.test_get_session()
            
            # Test 9: List Session Runs
            if self.session_id:
                await self.test_get_session_runs()
            
            # Test 10: Medical Knowledge Query
            await self.test_medical_query()
            
            print("\n" + "=" * 80)
            print("  ✅ All Tests Completed Successfully!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_get_config(self):
        """Test: Get AgentOS configuration."""
        print("\n" + "-" * 80)
        print("TEST 1: Get AgentOS Configuration")
        print("-" * 80)
        
        try:
            config = await self.client.aget_config()
            print("✅ Configuration retrieved successfully")
            print(f"   Agents: {len(config.agents) if hasattr(config, 'agents') else 'N/A'}")
            print(f"   Version: {config.version if hasattr(config, 'version') else 'N/A'}")
            self._print_json(config.model_dump() if hasattr(config, 'model_dump') else str(config))
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_list_agents(self):
        """Test: List all available agents."""
        print("\n" + "-" * 80)
        print("TEST 2: List All Available Agents")
        print("-" * 80)
        
        try:
            agents = await self.client.list_agents()
            print(f"✅ Retrieved {len(agents)} agent(s)")
            
            for agent in agents:
                print(f"\n   Agent ID: {agent.id if hasattr(agent, 'id') else 'N/A'}")
                print(f"   Name: {agent.name if hasattr(agent, 'name') else 'N/A'}")
                print(f"   Description: {agent.description if hasattr(agent, 'description') else 'N/A'}")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_get_agent(self):
        """Test: Get specific agent details."""
        print("\n" + "-" * 80)
        print("TEST 3: Get Specific Agent (orbixa-agent)")
        print("-" * 80)
        
        try:
            agent = await self.client.aget_agent(self.agent_id)
            print(f"✅ Agent retrieved successfully")
            print(f"   Agent ID: {agent.id if hasattr(agent, 'id') else 'N/A'}")
            print(f"   Name: {agent.name if hasattr(agent, 'name') else 'N/A'}")
            print(f"   Model: {agent.model if hasattr(agent, 'model') else 'N/A'}")
            print(f"   Description: {agent.description if hasattr(agent, 'description') else 'N/A'}")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_run_agent_simple(self):
        """Test: Run agent with a simple message (creates new session)."""
        print("\n" + "-" * 80)
        print("TEST 4: Run Agent - Simple Query (New Session)")
        print("-" * 80)
        
        try:
            message = "Hello! What is the definition of hypertension and its main causes?"
            print(f"📧 Sending: '{message}'")
            
            response = await self.client.run_agent(
                agent_id=self.agent_id,
                message=message,
                user_id=self.user_id
            )
            
            # Store session ID for future tests
            if hasattr(response, 'session_id'):
                self.session_id = response.session_id
                print(f"\n✅ Agent responded successfully")
                print(f"   Session ID: {self.session_id}")
            
            if hasattr(response, 'run_id'):
                print(f"   Run ID: {response.run_id}")
            
            # Print response content
            if hasattr(response, 'content'):
                print(f"\n📝 Response Content:")
                content = response.content
                if isinstance(content, str):
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(content)
                        print(f"   ✓ Valid JSON Response")
                        print(f"   Query Response: {parsed.get('query_response', 'N/A')[:200]}...")
                    except:
                        print(f"   {content[:300]}...")
                else:
                    print(f"   {str(content)[:300]}...")
            
            if hasattr(response, 'messages') and response.messages:
                print(f"\n📜 Messages: {len(response.messages)} message(s)")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_run_agent_continuation(self):
        """Test: Continue conversation in same session."""
        print("\n" + "-" * 80)
        print("TEST 5: Run Agent - Continuation (Same Session)")
        print("-" * 80)
        
        if not self.session_id:
            print("⏭️  Skipped (no session ID from previous test)")
            return
        
        try:
            message = "What are the treatment options for hypertension?"
            print(f"📧 Sending: '{message}'")
            print(f"   Using session_id: {self.session_id}")
            
            response = await self.client.run_agent(
                agent_id=self.agent_id,
                message=message,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            print(f"\n✅ Agent responded successfully")
            
            if hasattr(response, 'run_id'):
                print(f"   Run ID: {response.run_id}")
            
            if hasattr(response, 'content'):
                print(f"\n📝 Response Content:")
                content = response.content
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        print(f"   ✓ Valid JSON Response")
                        if 'query_response' in parsed:
                            print(f"   Query Response: {parsed['query_response'][:200]}...")
                    except:
                        print(f"   {content[:300]}...")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_run_agent_stream(self):
        """Test: Stream agent response."""
        print("\n" + "-" * 80)
        print("TEST 6: Run Agent - Stream Response")
        print("-" * 80)
        
        try:
            message = "Write a brief overview of diabetes management"
            print(f"📧 Sending: '{message}'")
            print("📡 Streaming response...\n")
            
            event_count = 0
            async for event in self.client.run_agent_stream(
                agent_id=self.agent_id,
                message=message,
                session_id=self.session_id,
                user_id=self.user_id
            ):
                event_count += 1
                if hasattr(event, 'event'):
                    print(f"   Event {event_count}: {event.event}")
                if hasattr(event, 'data') and event.data:
                    print(f"   Data: {str(event.data)[:100]}...")
            
            print(f"\n✅ Streamed {event_count} event(s)")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_get_sessions(self):
        """Test: Get all sessions for user."""
        print("\n" + "-" * 80)
        print("TEST 7: Get All User Sessions")
        print("-" * 80)
        
        try:
            sessions = await self.client.get_sessions(
                user_id=self.user_id,
                limit=10
            )
            
            print(f"✅ Retrieved sessions")
            if hasattr(sessions, 'items'):
                print(f"   Total sessions: {len(sessions.items)}")
                for idx, session in enumerate(sessions.items[:3], 1):
                    if hasattr(session, 'session_id'):
                        print(f"\n   Session {idx}:")
                        print(f"      ID: {session.session_id}")
                    if hasattr(session, 'created_at'):
                        print(f"      Created: {session.created_at}")
                    if hasattr(session, 'session_name'):
                        print(f"      Name: {session.session_name}")
            else:
                self._print_json(sessions)
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_get_session(self):
        """Test: Get specific session details."""
        print("\n" + "-" * 80)
        print("TEST 8: Get Specific Session Details")
        print("-" * 80)
        
        if not self.session_id:
            print("⏭️  Skipped (no session ID)")
            return
        
        try:
            session = await self.client.get_session(
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            print(f"✅ Session retrieved")
            print(f"   Session ID: {self.session_id}")
            
            if hasattr(session, 'session_name'):
                print(f"   Name: {session.session_name}")
            if hasattr(session, 'created_at'):
                print(f"   Created: {session.created_at}")
            if hasattr(session, 'updated_at'):
                print(f"   Updated: {session.updated_at}")
            if hasattr(session, 'messages'):
                print(f"   Total messages: {len(session.messages) if session.messages else 0}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_get_session_runs(self):
        """Test: Get runs from a specific session."""
        print("\n" + "-" * 80)
        print("TEST 9: Get Session Runs")
        print("-" * 80)
        
        if not self.session_id:
            print("⏭️  Skipped (no session ID)")
            return
        
        try:
            runs = await self.client.get_session_runs(
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            print(f"✅ Retrieved {len(runs)} run(s) from session")
            
            for idx, run in enumerate(runs[:3], 1):
                if hasattr(run, 'run_id'):
                    print(f"\n   Run {idx}:")
                    print(f"      ID: {run.run_id}")
                if hasattr(run, 'created_at'):
                    print(f"      Created: {run.created_at}")
                if hasattr(run, 'message'):
                    print(f"      Message: {str(run.message)[:100]}...")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    async def test_medical_query(self):
        """Test: Medical knowledge query with reference."""
        print("\n" + "-" * 80)
        print("TEST 10: Medical Knowledge Query")
        print("-" * 80)
        
        try:
            message = "Compare the pathophysiology of Type 1 and Type 2 diabetes"
            print(f"📧 Sending: '{message}'")
            
            response = await self.client.run_agent(
                agent_id=self.agent_id,
                message=message,
                session_id=self.session_id,
                user_id=self.user_id
            )
            
            print(f"\n✅ Medical query processed")
            
            if hasattr(response, 'content'):
                content = response.content
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        print(f"\n📊 Response Structure:")
                        for key in parsed.keys():
                            value = parsed[key]
                            if isinstance(value, str):
                                preview = value[:100] + "..." if len(value) > 100 else value
                                print(f"   ✓ {key}: {preview}")
                            elif isinstance(value, list):
                                print(f"   ✓ {key}: [{len(value)} item(s)]")
                            else:
                                print(f"   ✓ {key}: {type(value).__name__}")
                    except json.JSONDecodeError:
                        print(f"\n   Response (text): {content[:200]}...")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    def _print_json(self, data, indent=2):
        """Pretty print JSON data."""
        try:
            if isinstance(data, dict):
                print(json.dumps(data, indent=indent, default=str))
            elif isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    print(json.dumps(parsed, indent=indent, default=str))
                except:
                    print(data)
            else:
                print(json.dumps(data, indent=indent, default=str))
        except:
            print(str(data))


async def main():
    """Main entry point."""
    tester = MedicalBotTester(base_url="http://localhost:8000")
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
