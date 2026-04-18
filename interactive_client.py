"""
Interactive AgentOS Client
A simple interactive client to chat with the Orbixa AI Agent OS.
"""
import os
import json
import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()


class InteractiveMedicalBot:
    """Interactive client for Orbixa AI."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.user_id = None
        self.session_id = None
        self.token = None
        
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token."""
        payload = {
            "userId": user_id,
            "exp": datetime.now(UTC) + timedelta(hours=24),
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        self.token = token
        return token
    
    def get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, message: str) -> Optional[dict]:
        """Send message to the agent."""
        url = f"{self.base_url}/agents/orbixa-agent/runs"
        
        payload = {"message": message}
        if self.session_id:
            payload["session_id"] = self.session_id
        
        try:
            response = requests.post(url, json=payload, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if "session_id" in data:
                    self.session_id = data["session_id"]
                return data
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def get_history(self) -> Optional[dict]:
        """Get session history."""
        if not self.session_id:
            print("❌ No active session")
            return None
        
        url = f"{self.base_url}/agents/orbixa-agent/sessions/{self.session_id}"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error: Status {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def format_response(self, response: dict):
        """Format and display the agent's response."""
        print("\n" + "─" * 80)
        print("🤖 Medical Assistant:")
        print("─" * 80)
        
        # Extract content
        content = response.get("content", "")
        
        # Try to parse as JSON
        try:
            if isinstance(content, str) and content.strip().startswith("{"):
                parsed = json.loads(content)
                
                # Display query_response
                if "query_response" in parsed:
                    print(parsed["query_response"])
                
                # Display references if available
                if "references" in response and response["references"]:
                    print("\n📚 References:")
                    for ref in response["references"]:
                        book = ref.get("book_name", "Unknown")
                        page = ref.get("page", "?")
                        relevance = ref.get("relevance", 0)
                        print(f"  • {book} (Page {page}) - Relevance: {relevance:.2f}")
                
                # Display other schema fields if present
                if "title" in parsed and parsed["title"]:
                    print(f"\n📋 Title: {parsed['title']}")
                
                if "doctorName" in parsed and parsed["doctorName"]:
                    print(f"\n👨‍⚕️ Doctor: {parsed['doctorName']}")
                
            else:
                # Plain text response
                print(content)
                
        except json.JSONDecodeError:
            # Not JSON, print as-is
            print(content)
        
        # Display metrics
        if "metrics" in response:
            metrics = response["metrics"]
            time_taken = metrics.get("time", 0)
            print(f"\n⏱️  Response time: {time_taken:.2f}s")
        
        print("─" * 80)
    
    def show_history(self):
        """Display conversation history."""
        history = self.get_history()
        
        if not history:
            return
        
        print("\n" + "=" * 80)
        print("📜 Conversation History")
        print("=" * 80)
        
        runs = history.get("runs", [])
        
        if not runs:
            print("No messages in this session yet.")
            return
        
        for idx, run in enumerate(runs, 1):
            print(f"\n[{idx}] {run.get('created_at', 'Unknown time')}")
            print(f"👤 You: {run.get('message', 'N/A')}")
            
            # Show brief response
            content = run.get("content", "")
            if len(content) > 150:
                content = content[:150] + "..."
            print(f"🤖 Bot: {content}")
        
        print("\n" + "=" * 80)
    
    def run(self):
        """Run the interactive client."""
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "Orbixa AI Interactive Client" + " " * 28 + "║")
        print("╚" + "═" * 78 + "╝")
        
        # Setup
        print("\n🔐 Authentication Setup")
        user_id = input("Enter your user ID (default: test_user): ").strip()
        if not user_id:
            user_id = "test_user"
        
        self.user_id = user_id
        self.generate_token(user_id)
        print(f"✅ Logged in as: {user_id}")
        
        # Check connection
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Connected to Orbixa AI Agent OS")
            else:
                print("⚠️  Warning: Server might not be running properly")
        except:
            print("❌ Cannot connect to server. Make sure it's running at", self.base_url)
            return
        
        print("\n" + "─" * 80)
        print("Commands:")
        print("  /history - Show conversation history")
        print("  /new     - Start a new session")
        print("  /exit    - Exit the client")
        print("─" * 80)
        
        # Main loop
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() == "/exit":
                    print("\n👋 Goodbye!")
                    break
                
                elif user_input.lower() == "/history":
                    self.show_history()
                    continue
                
                elif user_input.lower() == "/new":
                    self.session_id = None
                    print("✅ Started new session")
                    continue
                
                # Send message
                print("\n⏳ Thinking...")
                response = self.send_message(user_input)
                
                if response:
                    self.format_response(response)
                    
                    # Show session ID on first message
                    if not hasattr(self, '_showed_session'):
                        print(f"\n🔑 Session ID: {self.session_id}")
                        self._showed_session = True
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    client = InteractiveMedicalBot()
    client.run()
