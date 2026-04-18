# Medical Bot Agent OS - Frontend API Integration Documentation

## Base URL
```
http://localhost:8000
```
For production, replace with your deployed URL.

---

## Authentication

All endpoints (except health/docs) require JWT authentication.

### JWT Token Format
```json
{
  "userId": "user_123",
  "exp": 1735689600,
  "iat": 1735603200
}
```

### Headers Required
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

The JWT token must include:
- **userId** claim: Unique identifier for the user
- **exp** claim: Token expiration timestamp
- **iat** claim: Token issued at timestamp

---

## 1. Chat Endpoint - Send Message

### Endpoint
```
POST /agents/medical-agent/run
```

### Description
Send a message to the medical AI agent. Creates a new session if no session_id is provided, or continues an existing conversation if session_id is included.

### Request Headers
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

### Request Body
```json
{
  "message": "What are the symptoms of diabetes?",
  "session_id": "session_123",  // Optional - omit for new session
  "stream": false  // Optional - set to true for streaming
}
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | string | ✅ Yes | The user's message/question |
| session_id | string | ❌ No | Session ID for continuing conversation (omit for new session) |
| stream | boolean | ❌ No | Enable streaming response (default: false) |

### Response (Non-streaming)

#### Success Response (200 OK)
```json
{
  "run_id": "run_abc123",
  "session_id": "session_xyz789",
  "agent_id": "medical-agent",
  "content": "{\"query_response\":\"Diabetes symptoms include...\",\"title\":\"Diabetes Overview\",\"doctorName\":\"\",\"doctorInfo\":\"\",\"address\":\"\",\"patientInfo\":\"\",\"prescriptionText\":\"\",\"correctionsDone\":false}",
  "content_type": "OutputSchema",
  "messages": [...],
  "metrics": {
    "time": 2.34,
    "input_tokens": 150,
    "output_tokens": 300
  },
  "created_at": "2026-01-11T10:30:00Z"
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| run_id | string | Unique ID for this specific interaction |
| session_id | string | **IMPORTANT**: Session ID (save this for continuing conversation) |
| agent_id | string | Agent identifier |
| content | string | JSON string containing structured medical response |
| content_type | string | Type of response (OutputSchema) |
| metrics | object | Performance metrics (time, tokens) |
| created_at | string | ISO timestamp |

#### Content Schema (Parsed JSON)
The `content` field is a JSON string that should be parsed:
```json
{
  "query_response": "Detailed medical response text...",
  "title": "Response title",
  "doctorName": "Dr. Smith (if prescription)",
  "doctorInfo": "Specialization info",
  "address": "Clinic address",
  "patientInfo": "Patient details",
  "prescriptionText": "Prescription details if applicable",
  "correctionsDone": false
}
```

### Response (Streaming)

#### When stream=true
Server-Sent Events (SSE) stream with incremental content chunks.

```javascript
// Example streaming chunk
{
  "event": "on_agent_run_chunk",
  "data": {
    "content": "partial text...",
    "run_id": "run_abc123",
    "session_id": "session_xyz789"
  }
}
```

### Code Examples

#### JavaScript/TypeScript
```javascript
async function sendMessage(message, sessionId = null) {
  const response = await fetch('http://localhost:8000/agents/medical-agent/run', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${YOUR_JWT_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      ...(sessionId && { session_id: sessionId }),
      stream: false
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  
  // Parse the content JSON
  const parsedContent = JSON.parse(data.content);
  
  return {
    sessionId: data.session_id,
    runId: data.run_id,
    response: parsedContent.query_response,
    title: parsedContent.title,
    metrics: data.metrics
  };
}

// Usage - New conversation
const result = await sendMessage("What are the symptoms of diabetes?");
console.log("Session ID:", result.sessionId); // Save this!
console.log("Response:", result.response);

// Usage - Continue conversation
const followUp = await sendMessage(
  "What are the treatments?", 
  result.sessionId // Use saved session ID
);
```

#### Python
```python
import requests
import json

def send_message(message: str, session_id: str = None) -> dict:
    url = "http://localhost:8000/agents/medical-agent/run"
    headers = {
        "Authorization": f"Bearer {YOUR_JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {"message": message, "stream": False}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    content = json.loads(data["content"])
    
    return {
        "session_id": data["session_id"],
        "run_id": data["run_id"],
        "response": content["query_response"],
        "title": content["title"],
        "metrics": data["metrics"]
    }

# New conversation
result = send_message("What are the symptoms of diabetes?")
print(f"Session ID: {result['session_id']}")

# Continue conversation
follow_up = send_message("What are the treatments?", result['session_id'])
```

#### cURL
```bash
# New conversation
curl -X POST "http://localhost:8000/agents/medical-agent/run" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the symptoms of diabetes?",
    "stream": false
  }'

# Continue conversation
curl -X POST "http://localhost:8000/agents/medical-agent/run" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the treatments?",
    "session_id": "session_xyz789",
    "stream": false
  }'
```

### Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid or missing JWT token"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_SERVER_ERROR"
}
```

---

## 2. Auto Chat Naming Endpoint

### ⚠️ NOT CURRENTLY IMPLEMENTED

**Status**: This endpoint does not exist in the current AgentOS implementation.

### Recommended Implementation Options

#### Option A: Generate Title from First Message (Frontend)
```javascript
function generateChatTitle(firstMessage) {
  // Extract first 50 characters or first sentence
  return firstMessage.length > 50 
    ? firstMessage.substring(0, 47) + "..."
    : firstMessage;
}
```

#### Option B: Use AI Response Title (Recommended)
The OutputSchema already includes a `title` field in responses:
```javascript
const data = await sendMessage("What is diabetes?");
const content = JSON.parse(data.content);
const chatTitle = content.title; // Use this as session title
```

#### Option C: Custom Endpoint (Future Implementation)
If you want to add this feature, create a custom endpoint:
```python
@app.post("/sessions/generate-title")
async def generate_session_title(session_id: str, user_id: str):
    # Get first message from session
    # Use LLM to generate a concise title
    # Return title
    pass
```

---

## 3. Fetch All Session Names

### Endpoint
```
GET /agents/medical-agent/sessions
```

### Description
Retrieves all chat sessions for the authenticated user. The `userId` is automatically extracted from the JWT token.

### Request Headers
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

### Query Parameters
None required - user_id is extracted from JWT token automatically.

### Response

#### Success Response (200 OK)
```json
[
  {
    "id": "session_xyz789",
    "agent_id": "medical-agent",
    "user_id": "user_123",
    "created_at": "2026-01-11T10:00:00Z",
    "updated_at": "2026-01-11T10:30:00Z",
    "runs": [
      {
        "run_id": "run_abc123",
        "message": "What are the symptoms of diabetes?",
        "content": "...",
        "created_at": "2026-01-11T10:00:00Z"
      }
    ],
    "session_state": {}
  },
  {
    "id": "session_abc456",
    "agent_id": "medical-agent",
    "user_id": "user_123",
    "created_at": "2026-01-10T15:00:00Z",
    "updated_at": "2026-01-10T15:45:00Z",
    "runs": [...]
  }
]
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| id | string | Session ID |
| agent_id | string | Agent identifier |
| user_id | string | User ID (from JWT) |
| created_at | string | ISO timestamp when session was created |
| updated_at | string | ISO timestamp of last update |
| runs | array | Array of all runs (messages) in this session |
| session_state | object | Session state data |

### Code Examples

#### JavaScript/TypeScript
```javascript
async function fetchAllSessions() {
  const response = await fetch('http://localhost:8000/agents/medical-agent/sessions', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${YOUR_JWT_TOKEN}`
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const sessions = await response.json();
  
  // Transform to display format
  return sessions.map(session => ({
    sessionId: session.id,
    title: extractSessionTitle(session),
    lastMessage: session.runs[session.runs.length - 1]?.message || "",
    createdAt: new Date(session.created_at),
    updatedAt: new Date(session.updated_at),
    messageCount: session.runs.length
  }));
}

function extractSessionTitle(session) {
  // Use first message as title
  const firstMessage = session.runs[0]?.message || "New Chat";
  return firstMessage.length > 50 
    ? firstMessage.substring(0, 47) + "..."
    : firstMessage;
}

// Usage
const sessions = await fetchAllSessions();
console.log(`Found ${sessions.length} sessions`);
sessions.forEach(session => {
  console.log(`${session.title} - ${session.messageCount} messages`);
});
```

#### React Hook Example
```typescript
import { useState, useEffect } from 'react';

interface ChatSession {
  sessionId: string;
  title: string;
  lastMessage: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
}

function useChatSessions(jwtToken: string) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchSessions() {
      try {
        const response = await fetch('http://localhost:8000/agents/medical-agent/sessions', {
          headers: {
            'Authorization': `Bearer ${jwtToken}`
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch sessions');
        
        const data = await response.json();
        const transformed = data.map((session: any) => ({
          sessionId: session.id,
          title: session.runs[0]?.message.substring(0, 50) || "New Chat",
          lastMessage: session.runs[session.runs.length - 1]?.message || "",
          createdAt: new Date(session.created_at),
          updatedAt: new Date(session.updated_at),
          messageCount: session.runs.length
        }));
        
        setSessions(transformed);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchSessions();
  }, [jwtToken]);

  return { sessions, loading, error };
}
```

#### Python
```python
import requests

def fetch_all_sessions(jwt_token: str) -> list:
    url = "http://localhost:8000/agents/medical-agent/sessions"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    sessions = response.json()
    
    # Transform for display
    return [
        {
            "session_id": session["id"],
            "title": session["runs"][0]["message"][:50] if session["runs"] else "New Chat",
            "message_count": len(session["runs"]),
            "created_at": session["created_at"],
            "updated_at": session["updated_at"]
        }
        for session in sessions
    ]
```

#### cURL
```bash
curl -X GET "http://localhost:8000/agents/medical-agent/sessions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Notes
- Sessions are automatically filtered by the `userId` from JWT token
- Sessions are returned in chronological order (newest first typically)
- Each session includes all runs (messages) for that session
- Empty array `[]` returned if user has no sessions

---

## 4. Delete Specific Session

### Endpoint
```
DELETE /agents/medical-agent/sessions/{session_id}
```

### Description
Permanently deletes a specific chat session and all its associated messages (runs).

### Request Headers
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | ✅ Yes | The ID of the session to delete |

### Response

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

### Code Examples

#### JavaScript/TypeScript
```javascript
async function deleteSession(sessionId) {
  const response = await fetch(
    `http://localhost:8000/agents/medical-agent/sessions/${sessionId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${YOUR_JWT_TOKEN}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete session: ${response.status}`);
  }

  return await response.json();
}

// Usage
try {
  await deleteSession("session_xyz789");
  console.log("Session deleted successfully");
  // Refresh session list
  await fetchAllSessions();
} catch (error) {
  console.error("Delete failed:", error);
}
```

#### React Example with Confirmation
```typescript
function SessionList({ sessions, onDelete }: Props) {
  const handleDelete = async (sessionId: string) => {
    if (!confirm("Are you sure you want to delete this chat?")) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/agents/medical-agent/sessions/${sessionId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${jwtToken}`
          }
        }
      );

      if (response.ok) {
        onDelete(sessionId); // Remove from UI
        toast.success("Chat deleted successfully");
      }
    } catch (error) {
      toast.error("Failed to delete chat");
    }
  };

  return (
    <div>
      {sessions.map(session => (
        <div key={session.sessionId}>
          <span>{session.title}</span>
          <button onClick={() => handleDelete(session.sessionId)}>
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}
```

#### Python
```python
def delete_session(session_id: str, jwt_token: str) -> dict:
    url = f"http://localhost:8000/agents/medical-agent/sessions/{session_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Usage
try:
    result = delete_session("session_xyz789", jwt_token)
    print("Session deleted successfully")
except requests.exceptions.HTTPError as e:
    print(f"Delete failed: {e}")
```

#### cURL
```bash
curl -X DELETE "http://localhost:8000/agents/medical-agent/sessions/session_xyz789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Error Responses

#### 404 Not Found
```json
{
  "detail": "Session not found",
  "error_code": "NOT_FOUND"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid or missing JWT token"
}
```

### Notes
- Deletion is **permanent** and cannot be undone
- All messages (runs) in the session are also deleted
- You can only delete sessions belonging to your userId
- Session IDs from other users will return 404

---

## 5. Load Chat Messages of a Session

### Endpoint
```
GET /agents/medical-agent/sessions/{session_id}
```

### Description
Retrieves all messages (runs) and details for a specific chat session.

### Request Headers
```javascript
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | ✅ Yes | The ID of the session to retrieve |

### Response

#### Success Response (200 OK)
```json
{
  "id": "session_xyz789",
  "agent_id": "medical-agent",
  "user_id": "user_123",
  "created_at": "2026-01-11T10:00:00Z",
  "updated_at": "2026-01-11T10:30:00Z",
  "session_state": {},
  "runs": [
    {
      "run_id": "run_abc123",
      "session_id": "session_xyz789",
      "agent_id": "medical-agent",
      "user_id": "user_123",
      "run_input": "What are the symptoms of diabetes?",
      "content": "{\"query_response\":\"Diabetes symptoms include increased thirst...\",\"title\":\"Diabetes Symptoms\"}",
      "content_type": "OutputSchema",
      "metrics": {
        "time": 2.34,
        "input_tokens": 150,
        "output_tokens": 300
      },
      "messages": [
        {
          "role": "user",
          "content": "What are the symptoms of diabetes?"
        },
        {
          "role": "assistant",
          "content": "Diabetes symptoms include..."
        }
      ],
      "created_at": "2026-01-11T10:00:00Z"
    },
    {
      "run_id": "run_def456",
      "run_input": "What are the treatments?",
      "content": "{\"query_response\":\"Diabetes treatments include...\",\"title\":\"Diabetes Treatment\"}",
      "created_at": "2026-01-11T10:15:00Z"
    }
  ]
}
```

#### Response Fields
| Field | Type | Description |
|-------|------|-------------|
| id | string | Session ID |
| agent_id | string | Agent identifier |
| user_id | string | User ID (from JWT) |
| created_at | string | ISO timestamp of session creation |
| updated_at | string | ISO timestamp of last update |
| session_state | object | Session state data |
| runs | array | **All messages in chronological order** |

#### Run Object Fields
| Field | Type | Description |
|-------|------|-------------|
| run_id | string | Unique ID for this message |
| run_input | string | User's message/query |
| content | string | JSON string with agent's response |
| content_type | string | Type of response |
| metrics | object | Performance metrics |
| messages | array | Full message history (user + assistant) |
| created_at | string | ISO timestamp of this message |

### Code Examples

#### JavaScript/TypeScript
```javascript
async function loadChatMessages(sessionId) {
  const response = await fetch(
    `http://localhost:8000/agents/medical-agent/sessions/${sessionId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${YOUR_JWT_TOKEN}`
      }
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const session = await response.json();
  
  // Transform runs into chat messages format
  const messages = session.runs.flatMap(run => {
    const parsedContent = JSON.parse(run.content);
    return [
      {
        id: `${run.run_id}-user`,
        role: 'user',
        content: run.run_input,
        timestamp: new Date(run.created_at)
      },
      {
        id: `${run.run_id}-assistant`,
        role: 'assistant',
        content: parsedContent.query_response,
        title: parsedContent.title,
        timestamp: new Date(run.created_at)
      }
    ];
  });

  return {
    sessionId: session.id,
    messages: messages,
    createdAt: new Date(session.created_at),
    updatedAt: new Date(session.updated_at)
  };
}

// Usage
const chatData = await loadChatMessages("session_xyz789");
console.log(`Loaded ${chatData.messages.length} messages`);
chatData.messages.forEach(msg => {
  console.log(`${msg.role}: ${msg.content}`);
});
```

#### React Component Example
```typescript
import { useState, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

function ChatView({ sessionId, jwtToken }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMessages() {
      try {
        const response = await fetch(
          `http://localhost:8000/agents/medical-agent/sessions/${sessionId}`,
          {
            headers: {
              'Authorization': `Bearer ${jwtToken}`
            }
          }
        );
        
        const session = await response.json();
        
        const msgs = session.runs.flatMap((run: any) => {
          const parsed = JSON.parse(run.content);
          return [
            {
              id: `${run.run_id}-user`,
              role: 'user' as const,
              content: run.run_input,
              timestamp: new Date(run.created_at)
            },
            {
              id: `${run.run_id}-assistant`,
              role: 'assistant' as const,
              content: parsed.query_response,
              timestamp: new Date(run.created_at)
            }
          ];
        });
        
        setMessages(msgs);
      } catch (error) {
        console.error("Failed to load messages:", error);
      } finally {
        setLoading(false);
      }
    }

    loadMessages();
  }, [sessionId, jwtToken]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="chat-container">
      {messages.map(msg => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div className="content">{msg.content}</div>
          <div className="timestamp">
            {msg.timestamp.toLocaleTimeString()}
          </div>
        </div>
      ))}
    </div>
  );
}
```

#### Python
```python
def load_chat_messages(session_id: str, jwt_token: str) -> dict:
    url = f"http://localhost:8000/agents/medical-agent/sessions/{session_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    session = response.json()
    
    # Transform to message list
    messages = []
    for run in session["runs"]:
        content = json.loads(run["content"])
        messages.extend([
            {
                "id": f"{run['run_id']}-user",
                "role": "user",
                "content": run["run_input"],
                "timestamp": run["created_at"]
            },
            {
                "id": f"{run['run_id']}-assistant",
                "role": "assistant",
                "content": content["query_response"],
                "timestamp": run["created_at"]
            }
        ])
    
    return {
        "session_id": session["id"],
        "messages": messages,
        "created_at": session["created_at"]
    }
```

#### cURL
```bash
curl -X GET "http://localhost:8000/agents/medical-agent/sessions/session_xyz789" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Error Responses

#### 404 Not Found
```json
{
  "detail": "Session not found",
  "error_code": "NOT_FOUND"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid or missing JWT token"
}
```

### Notes
- Returns all messages in chronological order (oldest to newest)
- Each run contains both the user's message and agent's response
- The `content` field is a JSON string that must be parsed
- Use this endpoint when:
  - Loading an existing chat session
  - Displaying conversation history
  - Resuming a previous conversation

---

## Additional Endpoints

### Health Check
```
GET /health
```
Returns server health status (no authentication required).

### API Documentation
```
GET /docs
```
Interactive Swagger UI documentation (no authentication required).

```
GET /redoc
```
Alternative ReDoc documentation (no authentication required).

---

## Common Patterns

### 1. Starting a New Chat
```javascript
// 1. Send first message without session_id
const result = await sendMessage("Hello, I need medical advice");

// 2. Save the session_id from response
const sessionId = result.session_id;
localStorage.setItem('currentSessionId', sessionId);

// 3. Add to session list
await fetchAllSessions(); // Refresh list
```

### 2. Continuing a Chat
```javascript
// 1. Get saved session_id
const sessionId = localStorage.getItem('currentSessionId');

// 2. Send message with session_id
const result = await sendMessage("Follow-up question", sessionId);

// 3. Display response
displayMessage(result.response);
```

### 3. Loading Chat History on Page Load
```javascript
async function initializeChatView(sessionId) {
  // 1. Load all messages
  const chatData = await loadChatMessages(sessionId);
  
  // 2. Display in UI
  displayMessages(chatData.messages);
  
  // 3. Scroll to bottom
  scrollToBottom();
}
```

### 4. Deleting Old Chats
```javascript
async function cleanupOldChats() {
  // 1. Get all sessions
  const sessions = await fetchAllSessions();
  
  // 2. Find old sessions (e.g., > 30 days)
  const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
  const oldSessions = sessions.filter(
    s => new Date(s.createdAt) < thirtyDaysAgo
  );
  
  // 3. Delete them
  for (const session of oldSessions) {
    await deleteSession(session.sessionId);
  }
}
```

---

## Error Handling Best Practices

### JavaScript Example
```javascript
async function apiCall(endpoint, options) {
  try {
    const response = await fetch(endpoint, options);
    
    // Check HTTP status
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    // Network error
    if (error instanceof TypeError) {
      console.error('Network error:', error);
      throw new Error('Unable to connect to server');
    }
    
    // API error
    console.error('API error:', error);
    throw error;
  }
}
```

### Token Expiration Handling
```javascript
async function sendMessageWithRetry(message, sessionId) {
  try {
    return await sendMessage(message, sessionId);
  } catch (error) {
    // If 401, try refreshing token
    if (error.message.includes('401')) {
      await refreshAuthToken();
      return await sendMessage(message, sessionId);
    }
    throw error;
  }
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement client-side debouncing for typing indicators
- Add request queuing for multiple rapid messages
- Consider server-side rate limiting middleware

---

## WebSocket/Streaming Support

The `/agents/medical-agent/run` endpoint supports Server-Sent Events (SSE) streaming when `stream: true`.

### Streaming Example
```javascript
async function sendMessageStreaming(message, sessionId, onChunk) {
  const response = await fetch('http://localhost:8000/agents/medical-agent/run', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${YOUR_JWT_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    onChunk(chunk); // Call callback with each chunk
  }
}

// Usage
await sendMessageStreaming(
  "What is diabetes?",
  sessionId,
  (chunk) => {
    console.log("Received:", chunk);
    // Update UI with chunk
  }
);
```

---

## Testing

### Test Credentials
For development, use the test JWT generation from `client_test.py`:

```python
import jwt
from datetime import datetime, timedelta, UTC

def generate_test_token(user_id="test_user_123"):
    payload = {
        "userId": user_id,
        "exp": datetime.now(UTC) + timedelta(hours=24),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, "your-secret-key", algorithm="HS256")
```

### Postman Collection
Import these endpoints into Postman:
1. Create environment variable `jwt_token`
2. Set Authorization header: `Bearer {{jwt_token}}`
3. Test each endpoint sequentially

---

## Production Checklist

- [ ] Replace `localhost:8000` with production URL
- [ ] Use HTTPS (not HTTP)
- [ ] Implement proper JWT token refresh mechanism
- [ ] Add request timeout handling
- [ ] Implement retry logic for failed requests
- [ ] Add logging for API errors
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Implement rate limiting
- [ ] Add request caching where appropriate
- [ ] Test with production JWT tokens
- [ ] Configure CORS properly on backend
- [ ] Add loading states in UI
- [ ] Implement optimistic UI updates
- [ ] Add offline detection and queuing

---

## Support

For questions or issues:
- Check `/docs` endpoint for live API documentation
- Review error messages in response `detail` field
- Check JWT token validity and expiration
- Verify network connectivity
- Ensure Authorization header is properly formatted

---

**Last Updated**: January 11, 2026  
**API Version**: AgentOS 2.3.24  
**Backend Framework**: Agno Agent OS with FastAPI
