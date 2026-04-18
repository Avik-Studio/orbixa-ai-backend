# Orbixa AI — Frontend API Documentation

**Base URL (local):** `http://localhost:8000`  
**Base URL (production):** _replace with your deployed URL_

**Created by:** Avik Modak  
**Version:** 1.0.0  
**Last updated:** April 2026

---

## Table of Contents

1. [Authentication Overview](#authentication-overview)
2. [Auth Endpoints](#auth-endpoints)
   - [Register](#1-register)
   - [Login](#2-login)
   - [Forgot Password](#3-forgot-password)
   - [Reset Password](#4-reset-password)
   - [Google Sign-In](#5-google-sign-in)
3. [Verify Token / Get Current User](#6-verify-token--get-current-user)
4. [Chat Endpoints](#chat-endpoints)
   - [Send Message](#6-send-message)
   - [List Sessions](#7-list-all-sessions)
   - [Get Session](#8-get-session-by-id)
4. [Knowledge Base Endpoints](#knowledge-base-endpoints)
   - [Upload PDF](#9-upload-pdf)
   - [List Books](#10-list-books)
   - [Delete Book](#11-delete-book)
5. [Utility Endpoints](#utility-endpoints)
6. [Error Reference](#error-reference)
7. [TypeScript Types](#typescript-types)
8. [Quick Start Code](#quick-start-code)

---

## Authentication Overview

After login/register, you receive a **JWT token**. Send it in the `Authorization` header for every protected request.

```
Authorization: Bearer <your_jwt_token>
```

The token contains:
```json
{
  "userId": "68012abc...",
  "email": "user@example.com",
  "name": "Avik Modak",
  "iat": 1745000000,
  "exp": 1745604800
}
```

**Token validity:** 7 days  
**Algorithm:** HS256

> ⚠️ **Public routes** (no token required): `/auth/register`, `/auth/login`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/google`, `/`, `/health`, `/docs`  
> All other routes require a valid JWT.

---

## Auth Endpoints

### 1. Register

Create a new Orbixa AI account.

```
POST /auth/register
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Avik Modak",
  "email": "avik@example.com",
  "password": "mypassword123"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `name` | string | ✅ | 2–100 characters |
| `email` | string | ✅ | Valid email format |
| `password` | string | ✅ | 8–128 characters |

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Registration successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2ODAx...",
  "user": {
    "id": "68012abc3f4e1d2c9b000001",
    "name": "Avik Modak",
    "email": "avik@example.com"
  }
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 409 | `"Email already registered"` | Email already in use |
| 422 | Validation error object | Invalid email format or password too short |

---

### 2. Login

Sign in with email and password.

```
POST /auth/login
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "avik@example.com",
  "password": "mypassword123"
}
```

| Field | Type | Required |
|-------|------|----------|
| `email` | string | ✅ |
| `password` | string | ✅ |

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2ODAx...",
  "user": {
    "id": "68012abc3f4e1d2c9b000001",
    "name": "Avik Modak",
    "email": "avik@example.com"
  }
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 401 | `"Invalid email or password"` | Wrong credentials |
| 401 | `"This account uses Google sign-in. Please log in with Google."` | Account was created via Google |
| 422 | Validation error | Invalid email format |

---

### 3. Forgot Password

Request a password reset link. Always returns success to prevent email enumeration.

```
POST /auth/forgot-password
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "avik@example.com"
}
```

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "If that email exists, a reset link has been sent.",
  "token": null,
  "user": null
}
```

> ℹ️ **How it works:** The backend generates a reset token, saves it in MongoDB (valid for **1 hour**), and will email a link like:  
> `https://your-frontend.com/reset-password?token=<reset_token>`  
> 
> The frontend should redirect users to the `/reset-password` page where they enter their new password and include the token from the URL.

---

### 4. Reset Password

Set a new password using the token from the reset email link.

```
POST /auth/reset-password
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "token": "Xk9mT2pBvQcR4sN8wLyU5aJdZeKfHgOi6rVtCn1A",
  "new_password": "mynewsecurepassword"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `token` | string | ✅ | The token from the reset email URL |
| `new_password` | string | ✅ | 8–128 characters |

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Password has been reset successfully",
  "token": null,
  "user": null
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 400 | `"Invalid or expired reset token"` | Token wrong or expired (>1 hour old) |

> ✅ After success, redirect the user to the login page.

---

### 5. Google Sign-In

Authenticate using a Google ID token (from Google Sign-In / Firebase Auth / `@react-oauth/google`). Works for both new and existing users.

```
POST /auth/google
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlOWdkazcifQ..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id_token` | string | ✅ | Google ID token from `google.accounts.id.initialize` callback or Firebase |

**How to get the `id_token` in React:**
```tsx
import { GoogleLogin } from '@react-oauth/google';

<GoogleLogin
  onSuccess={(credentialResponse) => {
    const idToken = credentialResponse.credential; // Send this
    await fetch('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken })
    });
  }}
/>
```

**Success Response — 200 OK (new user):**
```json
{
  "success": true,
  "message": "Google authentication successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "68012abc3f4e1d2c9b000002",
    "name": "Avik Modak",
    "email": "avik@gmail.com"
  }
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 401 | `"Invalid Google ID token"` | Token verification failed |
| 400 | `"Google account has no email"` | Google account missing email |

---

### 6. Verify Token / Get Current User

Verify a JWT token and return the authenticated user's profile. Use this on app load to check if a stored token is still valid.

```
GET /auth/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Authenticated",
  "token": null,
  "user": {
    "id": "68012abc3f4e1d2c9b000001",
    "name": "Avik Modak",
    "email": "avik@example.com"
  }
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 401 | `"Missing or invalid Authorization header"` | No `Bearer` token in header |
| 401 | `"Token has expired"` | JWT past 7-day expiry |
| 401 | `"Invalid token"` | Tampered or malformed JWT |
| 404 | `"User not found"` | Valid token but user deleted from DB |

> ✅ **Common usage:** On app startup, read the token from `localStorage`, call `GET /auth/me`. If 200 → user is logged in. If 401 → clear token and redirect to login.

---

## Chat Endpoints

> 🔒 **All chat endpoints require `Authorization: Bearer <token>` header.**

### 6. Send Message

Send a message to Orbixa AI and get a response. Omit `session_id` to start a new conversation; include it to continue an existing one.

```
POST /agents/orbixa-agent/runs
```

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Explain how async/await works in Python",
  "session_id": "sess_abc123",
  "stream": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `message` | string | ✅ | — | The user's message |
| `session_id` | string | ❌ | auto-generated | Omit to start a new chat; include to continue |
| `stream` | boolean | ❌ | `false` | Set `true` for streaming (SSE) |

---

**Success Response — 200 OK:**
```json
{
  "run_id": "run_7f3a2b1c",
  "session_id": "sess_abc123",
  "agent_id": "orbixa-agent",
  "content": "{\"chat_response\":\"Async/await in Python is built on top of coroutines...\",\"canvas_text\":[{\"text\":\"Key Concepts\",\"keypoints\":[\"async def defines a coroutine\",\"await suspends execution\",\"asyncio.run() starts the event loop\"]}]}",
  "content_type": "OutputSchema",
  "messages": [],
  "metrics": {
    "time": 2.14,
    "input_tokens": 120,
    "output_tokens": 340
  },
  "created_at": "2026-04-18T10:30:00Z"
}
```

**⚠️ Important:** The `content` field is a **JSON string** — you must parse it:

```ts
const raw = await response.json();
const parsed = JSON.parse(raw.content);
// parsed.chat_response  → string (the main reply text, may contain markdown)
// parsed.canvas_text    → array | null (structured data panels)
```

---

#### Parsed `content` Schema

```json
{
  "chat_response": "Async/await in Python is built on top of coroutines...",
  "canvas_text": [
    {
      "text": "Key Concepts",
      "keypoints": [
        "async def defines a coroutine",
        "await suspends execution",
        "asyncio.run() starts the event loop"
      ],
      "table": null
    },
    {
      "text": "Comparison Table",
      "keypoints": null,
      "table": {
        "column_headers": ["Feature", "Sync", "Async"],
        "columns_count": 3,
        "rows_count": 3,
        "rows": [
          ["Blocking", "Yes", "No"],
          ["Performance", "Single-threaded", "Concurrent I/O"],
          ["Syntax", "Normal", "async/await"]
        ]
      }
    }
  ]
}
```

#### `canvas_text` item types

| Case | What's set | What's null | How to render |
|------|-----------|-------------|---------------|
| Text + keypoints | `text`, `keypoints` | `table` | Bullet-point list with heading |
| Text + table | `text`, `table` | `keypoints` | Data table with heading |
| Text only | `text` | `table`, `keypoints` | Paragraph/info card |

> 📌 **Save `session_id` from the first response** and pass it in all follow-up messages to maintain conversation context.

---

**Streaming Response (when `stream: true`):**

Returns Server-Sent Events. Each chunk:
```
data: {"content": "Async/await ", "run_id": "run_7f3a2b1c", "session_id": "sess_abc123"}

data: {"content": "in Python is ", "run_id": "run_7f3a2b1c", "session_id": "sess_abc123"}

data: [DONE]
```

---

### 7. List All Sessions

Get all chat sessions for the currently authenticated user.

```
GET /agents/orbixa-agent/sessions
```

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response — 200 OK:**
```json
[
  {
    "id": "sess_abc123",
    "agent_id": "orbixa-agent",
    "user_id": "68012abc3f4e1d2c9b000001",
    "created_at": "2026-04-18T09:00:00Z",
    "updated_at": "2026-04-18T10:30:00Z",
    "runs": [
      {
        "run_id": "run_001",
        "message": "Explain how async/await works in Python",
        "content": "{...}",
        "created_at": "2026-04-18T09:00:00Z"
      },
      {
        "run_id": "run_002",
        "message": "Show me a practical example",
        "content": "{...}",
        "created_at": "2026-04-18T10:30:00Z"
      }
    ],
    "session_state": {}
  }
]
```

> 💡 **Suggested frontend display:** Use `runs[0].message` (truncated to 50 chars) as the chat title. Group sessions by `created_at` date (Today / Yesterday / Earlier).

---

### 8. Get Session by ID

Get all messages for a specific session.

```
GET /agents/orbixa-agent/sessions/{session_id}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameter:**

| Param | Type | Description |
|-------|------|-------------|
| `session_id` | string | The session ID |

**Success Response — 200 OK:**
```json
{
  "id": "sess_abc123",
  "agent_id": "orbixa-agent",
  "user_id": "68012abc3f4e1d2c9b000001",
  "created_at": "2026-04-18T09:00:00Z",
  "updated_at": "2026-04-18T10:30:00Z",
  "runs": [
    {
      "run_id": "run_001",
      "message": "Explain how async/await works in Python",
      "content": "{\"chat_response\":\"...\",\"canvas_text\":null}",
      "created_at": "2026-04-18T09:00:00Z"
    }
  ],
  "session_state": {}
}
```

**Error Responses:**

| Status | When |
|--------|------|
| 404 | Session not found |
| 403 | Session belongs to a different user |

---

## Knowledge Base Endpoints

> 🔒 **All knowledge base endpoints require `Authorization: Bearer <token>` header.**

### 9. Upload PDF

Upload a PDF file to add to Orbixa AI's knowledge base.

```
POST /knowledge/ingest-pdf
```

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | PDF file. Name format: `bookname.pdf` or `bookname_Part3.pdf` |

**JavaScript Example:**
```ts
const formData = new FormData();
formData.append('file', pdfFile); // pdfFile is a File object

const response = await fetch('/knowledge/ingest-pdf', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
  // ⚠️ Do NOT set Content-Type header — browser sets it automatically with boundary
});
```

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Successfully ingested 'machine_learning.pdf' — 142 chunks added",
  "book_name": "machine_learning",
  "chunks_added": 142
}
```

**Error Responses:**

| Status | Detail | When |
|--------|--------|------|
| 400 | `"Invalid file type..."` | Non-PDF file uploaded |
| 500 | Error message | Processing failed |

---

### 10. List Books

Get all documents currently in the knowledge base.

```
GET /knowledge/books
```

**Headers:**
```
Authorization: Bearer <token>
```

**Success Response — 200 OK:**
```json
{
  "success": true,
  "books": [
    {
      "name": "machine_learning",
      "chunk_count": 142,
      "parts": ["machine_learning_Part1", "machine_learning_Part2"]
    },
    {
      "name": "python_handbook",
      "chunk_count": 89,
      "parts": ["python_handbook"]
    }
  ],
  "total_books": 2,
  "total_chunks": 231
}
```

---

### 11. Delete Book

Remove all chunks of a specific document from the knowledge base.

```
DELETE /knowledge/delete-book/{book_name}
```

**Headers:**
```
Authorization: Bearer <token>
```

**Path Parameter:**

| Param | Type | Description |
|-------|------|-------------|
| `book_name` | string | The book name (without `.pdf`, e.g., `machine_learning`) |

**Success Response — 200 OK:**
```json
{
  "success": true,
  "message": "Book 'machine_learning' deleted — 142 chunks removed",
  "chunks_removed": 142
}
```

**Error Responses:**

| Status | When |
|--------|------|
| 404 | Book not found in knowledge base |
| 500 | Deletion failed |

---

## Utility Endpoints

### Health Check

```
GET /health
```

No authentication required.

**Response — 200 OK:**
```json
{
  "status": "ok"
}
```

### API Docs (Swagger UI)

Open in browser — no auth required:
```
GET /docs
```

---

## Error Reference

All error responses follow this shape:

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors (422) have a more detailed shape:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email address",
      "type": "value_error"
    }
  ]
}
```

### Global HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid input (e.g., expired token) |
| 401 | Unauthorized | Wrong credentials or missing/invalid JWT |
| 403 | Forbidden | Valid JWT but not allowed to access this resource |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Email already registered |
| 422 | Unprocessable Entity | Request body validation failed |
| 500 | Internal Server Error | Unexpected server error |

---

## TypeScript Types

Copy these types directly into your frontend project:

```typescript
// ── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  success: boolean;
  message: string;
  token: string | null;
  user: {
    id: string;
    name: string;
    email: string;
  } | null;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface GoogleAuthPayload {
  id_token: string;
}

// ── Chat ─────────────────────────────────────────────────────────────────────

export interface TableModel {
  column_headers: string[];
  columns_count: number;
  rows_count: number;
  rows: string[][];
}

export interface CanvasItem {
  text: string;
  table: TableModel | null;
  keypoints: string[] | null;
}

export interface OrbixaOutput {
  chat_response: string;
  canvas_text: CanvasItem[] | null;
}

export interface AgentRunResponse {
  run_id: string;
  session_id: string;
  agent_id: string;
  content: string;             // JSON string — parse to OrbixaOutput
  content_type: string;
  metrics: {
    time: number;
    input_tokens: number;
    output_tokens: number;
  } | null;
  created_at: string;
}

export interface SendMessagePayload {
  message: string;
  session_id?: string;
  stream?: boolean;
}

// ── Sessions ─────────────────────────────────────────────────────────────────

export interface SessionRun {
  run_id: string;
  message: string;
  content: string;             // JSON string — parse to OrbixaOutput
  created_at: string;
}

export interface ChatSession {
  id: string;
  agent_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  runs: SessionRun[];
  session_state: Record<string, unknown>;
}

// ── Knowledge Base ────────────────────────────────────────────────────────────

export interface BookEntry {
  name: string;
  chunk_count: number;
  parts: string[];
}

export interface ListBooksResponse {
  success: boolean;
  books: BookEntry[];
  total_books: number;
  total_chunks: number;
}
```

---

## Quick Start Code

### API Service (`src/lib/api.ts`)

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

function getHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const register = (payload: RegisterPayload) =>
  fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload),
  }).then(r => handleResponse<AuthResponse>(r));

export const login = (payload: LoginPayload) =>
  fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload),
  }).then(r => handleResponse<AuthResponse>(r));

export const forgotPassword = (email: string) =>
  fetch(`${BASE_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ email }),
  }).then(r => handleResponse<AuthResponse>(r));

export const resetPassword = (payload: ResetPasswordPayload) =>
  fetch(`${BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(payload),
  }).then(r => handleResponse<AuthResponse>(r));

export const googleAuth = (id_token: string) =>
  fetch(`${BASE_URL}/auth/google`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ id_token }),
  }).then(r => handleResponse<AuthResponse>(r));

export const getMe = (token: string) =>
  fetch(`${BASE_URL}/auth/me`, {
    headers: getHeaders(token),
  }).then(r => handleResponse<AuthResponse>(r));

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendMessage(
  token: string,
  message: string,
  sessionId?: string
): Promise<{ output: OrbixaOutput; sessionId: string; runId: string }> {
  const raw = await fetch(`${BASE_URL}/agents/orbixa-agent/runs`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify({
      message,
      ...(sessionId ? { session_id: sessionId } : {}),
      stream: false,
    }),
  }).then(r => handleResponse<AgentRunResponse>(r));

  return {
    output: JSON.parse(raw.content) as OrbixaOutput,
    sessionId: raw.session_id,
    runId: raw.run_id,
  };
}

export const getSessions = (token: string) =>
  fetch(`${BASE_URL}/agents/orbixa-agent/sessions`, {
    headers: getHeaders(token),
  }).then(r => handleResponse<ChatSession[]>(r));

export const getSession = (token: string, sessionId: string) =>
  fetch(`${BASE_URL}/agents/orbixa-agent/sessions/${sessionId}`, {
    headers: getHeaders(token),
  }).then(r => handleResponse<ChatSession>(r));

// ── Knowledge Base ────────────────────────────────────────────────────────────

export const listBooks = (token: string) =>
  fetch(`${BASE_URL}/knowledge/books`, {
    headers: getHeaders(token),
  }).then(r => handleResponse<ListBooksResponse>(r));

export async function uploadPDF(token: string, file: File) {
  const form = new FormData();
  form.append('file', file);
  return fetch(`${BASE_URL}/knowledge/ingest-pdf`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }, // no Content-Type — let browser set it
    body: form,
  }).then(r => handleResponse<{ success: boolean; message: string; chunks_added: number }>(r));
}

export const deleteBook = (token: string, bookName: string) =>
  fetch(`${BASE_URL}/knowledge/delete-book/${encodeURIComponent(bookName)}`, {
    method: 'DELETE',
    headers: getHeaders(token),
  }).then(r => handleResponse<{ success: boolean; message: string }>(r));
```

### Usage Example (React component)

```tsx
// Starting a new conversation
const result = await sendMessage(token, "What is machine learning?");
setSessionId(result.sessionId); // SAVE THIS

// Continuing the conversation
const followUp = await sendMessage(token, "Give me a Python example", sessionId);
console.log(followUp.output.chat_response); // main text reply
console.log(followUp.output.canvas_text);   // tables, keypoints, or null
```

---

> **Questions?** Contact Avik Modak or check the interactive Swagger UI at `http://localhost:8000/docs`
