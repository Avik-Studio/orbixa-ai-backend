"""
Orbixa AI Agent OS - Interactive Chat CLI

Interactive command-line interface for chatting with the Orbixa AI Agent OS
with real-time token usage tracking and word counts.

Usage:
    python interactive_chat.py

Commands:
    /help       - Show available commands
    /clear      - Start a new session
    /history    - Show conversation history
    /metrics    - Show session metrics summary
    /exit       - Exit the chat
"""
import asyncio
import json
import os
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import jwt
from agno.client.os import AgentOSClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
# Request timeout (seconds) for AgentOSClient operations
TIMEOUT = int(os.getenv("AGENTOS_TIMEOUT", "600"))

class InteractiveMedicalBotChat:
    """Interactive chat interface for Orbixa AI Agent OS."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the chat interface."""
        self.client = AgentOSClient(base_url=base_url)
        self.agent_id = "orbixa-agent"
        self.session_id: Optional[str] = None
        self.user_id = os.getenv("USER_ID", "interactive_user")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.jwt_token: Optional[str] = None
        self.message_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_input_words = 0
        self.total_output_words = 0
        
        # Generate JWT token
        self._generate_jwt_token()
    
    def _generate_jwt_token(self):
        """Generate a JWT token for authentication."""
        try:
            payload = {
                "userId": self.user_id,
                "exp": datetime.now(UTC) + timedelta(hours=24),
                "iat": datetime.now(UTC),
            }
            self.jwt_token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate JWT token: {e}")
            self.jwt_token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with JWT token."""
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers
    
    def print_header(self):
        """Print the chat header."""
        print("\n" + "=" * 80)
        print("  🤖 Orbixa AI Agent OS - Interactive Chat")
        print("=" * 80)
        print(f"  Base URL: {self.client.base_url}")
        print(f"  User ID: {self.user_id}")
        print(f"  Agent: {self.agent_id}")
        print("=" * 80)
        print("\n  Type '/help' for commands or start chatting!")
        print()
    
    def print_help(self):
        """Print available commands."""
        print("\n" + "─" * 80)
        print("  📚 Available Commands:")
        print("─" * 80)
        print("  /help       - Show this help message")
        print("  /clear      - Start a new session (clear conversation)")
        print("  /history    - Show conversation history")
        print("  /metrics    - Show cumulative session metrics")
        print("  /exit       - Exit the chat")
        print("─" * 80 + "\n")
    
    def count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())
    
    def format_metrics(self, metrics: Any, input_text: str, output_text: str) -> str:
        """Format metrics display."""
        lines = []
        lines.append("\n" + "─" * 80)
        lines.append("  📊 TOKEN USAGE & METRICS")
        lines.append("─" * 80)
        
        # Token metrics
        if hasattr(metrics, 'input_tokens'):
            input_tokens = metrics.input_tokens or 0
            output_tokens = metrics.output_tokens or 0
            total_tokens = metrics.total_tokens or 0
            
            lines.append(f"  🔢 Tokens:")
            lines.append(f"     Input:  {input_tokens:,} tokens")
            lines.append(f"     Output: {output_tokens:,} tokens")
            lines.append(f"     Total:  {total_tokens:,} tokens")
            
            # Update cumulative totals
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
        
        # Word counts
        input_words = self.count_words(input_text)
        output_words = self.count_words(output_text)
        
        lines.append(f"\n  📝 Word Count:")
        lines.append(f"     Input:  {input_words:,} words")
        lines.append(f"     Output: {output_words:,} words")
        
        # Update cumulative word counts
        self.total_input_words += input_words
        self.total_output_words += output_words
        
        # Performance metrics
        if hasattr(metrics, 'duration'):
            duration = metrics.duration or 0
            lines.append(f"\n  ⚡ Performance:")
            lines.append(f"     Duration: {duration:.2f}s")
            
            if duration > 0 and hasattr(metrics, 'total_tokens'):
                tokens_per_sec = (metrics.total_tokens or 0) / duration
                lines.append(f"     Speed:    {tokens_per_sec:.1f} tokens/sec")
        
        if hasattr(metrics, 'time_to_first_token') and metrics.time_to_first_token:
            lines.append(f"     TTFT:     {metrics.time_to_first_token:.2f}s")
        
        # Cost estimate (Gemini 3 Flash Preview pricing - Jan 2026)
        if hasattr(metrics, 'input_tokens') and hasattr(metrics, 'output_tokens'):
            input_cost = (metrics.input_tokens or 0) * 0.50 / 1_000_000
            output_cost = (metrics.output_tokens or 0) * 3.00 / 1_000_000
            total_cost = input_cost + output_cost
            
            lines.append(f"\n  💰 Cost Estimate (Gemini 3 Flash Preview):")
            lines.append(f"     Input:  ${input_cost:.6f}")
            lines.append(f"     Output: ${output_cost:.6f}")
            lines.append(f"     Total:  ${total_cost:.6f}")
        
        # Provider-specific metrics (Gemini raw data)
        if hasattr(metrics, 'provider_metrics') and metrics.provider_metrics:
            lines.append(f"\n  📈 Provider Metrics (Gemini):")
            for key, value in metrics.provider_metrics.items():
                lines.append(f"     {key}: {value}")
        
        lines.append("─" * 80)
        return "\n".join(lines)
    
    def format_tool_calls(self, messages: list) -> str:
        """Format tool calls from messages."""
        lines = []
        tool_calls_found = False
        
        for message in messages:
            if hasattr(message, 'role') and message.role == 'tool':
                if not tool_calls_found:
                    lines.append("\n" + "─" * 80)
                    lines.append("  🔧 TOOL CALLS")
                    lines.append("─" * 80)
                    tool_calls_found = True
                
                tool_name = message.tool_name if hasattr(message, 'tool_name') else 'Unknown'
                lines.append(f"\n  Tool: {tool_name}")
                
                if hasattr(message, 'content') and message.content:
                    content = str(message.content)
                    if len(content) > 200:
                        content = content[:200] + "..."
                    lines.append(f"  Response: {content}")
        
        if tool_calls_found:
            lines.append("─" * 80)
        
        return "\n".join(lines) if lines else ""
    
    def print_session_metrics(self):
        """Print cumulative session metrics."""
        print("\n" + "=" * 80)
        print("  📊 CUMULATIVE SESSION METRICS")
        print("=" * 80)
        print(f"  Messages sent: {self.message_count}")
        print(f"\n  🔢 Total Tokens:")
        print(f"     Input:  {self.total_input_tokens:,} tokens")
        print(f"     Output: {self.total_output_tokens:,} tokens")
        print(f"     Total:  {(self.total_input_tokens + self.total_output_tokens):,} tokens")
        print(f"\n  📝 Total Words:")
        print(f"     Input:  {self.total_input_words:,} words")
        print(f"     Output: {self.total_output_words:,} words")
        
        # Calculate total cost
        total_input_cost = self.total_input_tokens * 0.50 / 1_000_000
        total_output_cost = self.total_output_tokens * 3.00 / 1_000_000
        total_cost = total_input_cost + total_output_cost
        
        print(f"\n  💰 Total Cost Estimate (Gemini 3 Flash Preview):")
        print(f"     Input:  ${total_input_cost:.6f}")
        print(f"     Output: ${total_output_cost:.6f}")
        print(f"     Total:  ${total_cost:.6f}")
        print("=" * 80 + "\n")
    
    async def show_history(self):
        """Show conversation history."""
        if not self.session_id:
            print("\n❌ No active session. Start chatting to create one!\n")
            return
        
        try:
            print("\n⏳ Fetching conversation history...\n")
            session = await asyncio.wait_for(
                self.client.get_session(
                    session_id=self.session_id,
                    headers=self._get_headers()
                ),
                timeout=TIMEOUT,
            )
            
            print("=" * 80)
            print("  📜 CONVERSATION HISTORY")
            print("=" * 80)
            print(f"  Session ID: {self.session_id}")
            
            if hasattr(session, 'created_at'):
                print(f"  Created: {session.created_at}")
            
            if hasattr(session, 'messages') and session.messages:
                print(f"  Total messages: {len(session.messages)}\n")
                
                for idx, message in enumerate(session.messages, 1):
                    role = message.role if hasattr(message, 'role') else 'unknown'
                    content = message.content if hasattr(message, 'content') else ''
                    
                    if role == 'user':
                        print(f"\n  [{idx}] 👤 USER:")
                        print(f"      {content}")
                    elif role == 'assistant':
                        print(f"\n  [{idx}] 🤖 ASSISTANT:")
                        # Parse JSON OutputSchema (chat_response field)
                        try:
                            parsed = json.loads(content) if isinstance(content, str) else content
                            if isinstance(parsed, dict) and 'chat_response' in parsed:
                                summary = parsed['chat_response']
                                print(f"      {summary[:200]}{'...' if len(summary) > 200 else ''}")
                                
                                # Show if detailed content is available
                                if 'canvas_text' in parsed and parsed['canvas_text']:
                                    print(f"      [+ Detailed content available]")
                            else:
                                print(f"      {str(content)[:200]}...")
                        except:
                            print(f"      {str(content)[:200]}...")
            
            print("\n" + "=" * 80 + "\n")
            
        except Exception as e:
            print(f"\n❌ Failed to fetch history: {e}\n")
    
    async def clear_session(self):
        """Clear current session and start new."""
        self.session_id = None
        self.message_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_input_words = 0
        self.total_output_words = 0
        print("\n✅ Session cleared! Starting fresh conversation.\n")
    
    async def send_message(self, message: str) -> bool:
        """Send a message and display response with metrics."""
        try:
            print("\n⏳ Sending message...\n")
            
            response = await asyncio.wait_for(
                self.client.run_agent(
                    agent_id=self.agent_id,
                    message=message,
                    session_id=self.session_id,
                    headers=self._get_headers()
                ),
                timeout=TIMEOUT,
            )
            
            # Store session ID
            if hasattr(response, 'session_id'):
                if not self.session_id:
                    self.session_id = response.session_id
                    print(f"📝 New session created: {self.session_id}\n")
            
            self.message_count += 1
            
            # Extract and display response content
            print("─" * 80)
            print("  🤖 ASSISTANT RESPONSE")
            print("─" * 80)
            
            response_text = ""
            if hasattr(response, 'content'):
                content = response.content
                
                # Parse JSON (OutputSchema: chat_response + canvas_text)
                try:
                    if isinstance(content, str):
                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            # Display chat_response (brief summary)
                            if 'chat_response' in parsed:
                                response_text = parsed['chat_response']
                                print(f"\n{response_text}\n")
                            
                            # Display canvas_text (detailed content)
                            if 'canvas_text' in parsed and isinstance(parsed['canvas_text'], list):
                                print("─" * 80)
                                print("  📄 DETAILED CONTENT")
                                print("─" * 80)
                                
                                for idx, item in enumerate(parsed['canvas_text'], 1):
                                    if isinstance(item, dict):
                                        # Display text content
                                        if 'text' in item and item['text']:
                                            print(f"\n{item['text']}\n")
                                        
                                        # Display table if present
                                        if 'table' in item and item['table']:
                                            try:
                                                table = item['table']
                                                headers = table.get('column_headers', [])
                                                rows = table.get('rows', [])
                                                
                                                print("\n  📊 TABLE:")
                                                if headers:
                                                    print(f"  | {' | '.join(headers)} |")
                                                    print(f"  | {' | '.join(['---'] * len(headers))} |")
                                                for row in rows:
                                                    print(f"  | {' | '.join(str(c) for c in row)} |")
                                                print()
                                            except Exception as e:
                                                print(f"\n  [Table parsing error: {e}]\n")
                                        
                                        # Display keypoints if present
                                        if 'keypoints' in item and item['keypoints']:
                                            print("\n  🔑 KEY POINTS:")
                                            for point in item['keypoints']:
                                                print(f"     • {point}")
                                            print()
                                
                                print("─" * 80)
                        else:
                            response_text = str(content)
                            print(f"\n{response_text}\n")
                    else:
                        response_text = str(content)
                        print(f"\n{response_text}\n")
                except json.JSONDecodeError:
                    response_text = str(content)
                    print(f"\n{response_text}\n")
            
            print("─" * 80)
            
            # Display tool calls if any
            if hasattr(response, 'messages') and response.messages:
                tool_output = self.format_tool_calls(response.messages)
                if tool_output:
                    print(tool_output)
            
            # Display metrics
            if hasattr(response, 'metrics') and response.metrics:
                metrics_output = self.format_metrics(
                    response.metrics,
                    message,
                    response_text
                )
                print(metrics_output)
            else:
                print("\n⚠️  No metrics available for this response\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            return False
    
    async def run(self):
        """Run the interactive chat loop."""
        self.print_header()
        
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command == '/help':
                        self.print_help()
                    elif command == '/clear':
                        await self.clear_session()
                    elif command == '/history':
                        await self.show_history()
                    elif command == '/metrics':
                        self.print_session_metrics()
                    elif command == '/exit' or command == '/quit':
                        print("\n👋 Goodbye! Thanks for using Orbixa AI Agent OS.\n")
                        break
                    else:
                        print(f"\n❌ Unknown command: {command}")
                        print("   Type '/help' to see available commands.\n")
                    
                    continue
                
                # Send regular message
                await self.send_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using Orbixa AI Agent OS.\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Thanks for using Orbixa AI Agent OS.\n")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}\n")


async def main():
    """Main entry point."""
    base_url = os.getenv("AGENTOS_URL", "http://localhost:8000")
    
    # Check if server is running
    try:
        client = AgentOSClient(base_url=base_url)
        config = await asyncio.wait_for(client.aget_config(), timeout=TIMEOUT)
        print(f"✅ Connected to AgentOS at {base_url}")
    except Exception as e:
        print(f"\n❌ Failed to connect to AgentOS at {base_url}")
        print(f"   Error: {e}")
        print("\n   Please ensure the server is running:")
        print("   python app.py\n")
        return
    
    # Start interactive chat
    chat = InteractiveMedicalBotChat(base_url=base_url)
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())
