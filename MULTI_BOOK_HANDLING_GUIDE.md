# Multi-Book Handling & Agent State Management Guide

## Overview

When a user queries multiple medical textbooks (e.g., "Compare Preeclampsia treatment in Harrison's and Williams Obstetrics"), the system uses a sophisticated combination of:

1. **Agentic Knowledge Filters** - AI determines what to search
2. **Sequential Search Execution** - One book per search, not parallel
3. **Session State Tracking** - Maintains context across requests
4. **Agent Memory** - Learns about user preferences

---

## 1. How Multi-Book Queries Are Handled

### Architecture Flow

```
User Request: "Compare Preeclampsia in Harrison's and Williams"
        │
        ▼
┌─────────────────────────────────────┐
│  1. SYSTEM PROMPT INSTRUCTION       │
│  "Search individually and           │
│   sequentially, never multiple      │
│   books in one search"              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  2. AGENT DECISION MAKING           │
│  (Gemini LLM with agentic filters)  │
│  ├─ Detect multiple books           │
│  ├─ Plan search strategy            │
│  └─ Queue books_to_search state     │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  3. SEQUENTIAL SEARCH EXECUTION     │
│  Search 1: book_name="Harrison's"   │
│  ├─ Query Qdrant (vector search)    │
│  ├─ Apply filter validator          │
│  └─ Retrieve results                │
│                                     │
│  Search 2: book_name="Williams"     │
│  ├─ Query Qdrant (vector search)    │
│  ├─ Apply filter validator          │
│  └─ Retrieve results                │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  4. SYNTHESIS & RESPONSE            │
│  ├─ Combine results from both       │
│  ├─ Comparative analysis            │
│  ├─ Update session state            │
│  └─ Return unified JSON response    │
└────────────┬────────────────────────┘
             │
             ▼
        Response to User
```

### Key Configuration for Multi-Book Support

In `agents/medical_agent.py`:

```python
agent = Agent(
    # ... other config ...
    
    # CRITICAL SETTINGS FOR MULTI-BOOK HANDLING:
    enable_agentic_knowledge_filters=True,  # ← AI decides what to search
    search_knowledge=True,                   # ← Enable knowledge base search
    add_session_state_to_context=True,       # ← Pass state to AI
    enable_agentic_state=True,               # ← AI can modify state
    
    # Session state tracking
    session_state=get_session_state_schema(),
    
    # ... rest of config ...
)
```

---

## 2. Agent State Management - Session State Schema

### What is Session State?

Session state is a **persistent dictionary** stored in MongoDB that tracks:

```python
session_state = {
    "topics_to_write": [],      # Topics user wants written/generated
    "books_to_search": [],      # Queue of books to search
    "preferred_books": [],      # Books user has explicitly validated
    "writing_progress": {}      # Progress tracking for content generation
}
```

### Example: Multi-Book Query

**User Request**: "I want to compare Preeclampsia treatment. First search Harrison's, then Williams, then compare."

**Session State Evolution**:

```
Initial State:
{
  "topics_to_write": [],
  "books_to_search": [],
  "preferred_books": [],
  "writing_progress": {}
}

After User Input (Agent updates state):
{
  "topics_to_write": ["Preeclampsia treatment comparison"],
  "books_to_search": ["Harrison's Principles.pdf", "Williams Obstetrics.pdf"],
  "preferred_books": [],
  "writing_progress": {
    "Preeclampsia treatment comparison": {
      "searched_books": ["Harrison's Principles.pdf"],
      "pending_books": ["Williams Obstetrics.pdf"],
      "status": "in_progress"
    }
  }
}

After Search 1 (Harrison's):
{
  "topics_to_write": ["Preeclampsia treatment comparison"],
  "books_to_search": ["Williams Obstetrics.pdf"],
  "preferred_books": ["Harrison's Principles.pdf"],
  "writing_progress": {
    "Preeclampsia treatment comparison": {
      "searched_books": ["Harrison's Principles.pdf"],
      "pending_books": ["Williams Obstetrics.pdf"],
      "status": "in_progress",
      "harrison_findings": {
        "key_points": ["...", "..."],
        "search_timestamp": "2025-01-12T10:30:00Z"
      }
    }
  }
}

After Search 2 (Williams):
{
  "topics_to_write": [],
  "books_to_search": [],
  "preferred_books": ["Harrison's Principles.pdf", "Williams Obstetrics.pdf"],
  "writing_progress": {
    "Preeclampsia treatment comparison": {
      "searched_books": ["Harrison's Principles.pdf", "Williams Obstetrics.pdf"],
      "pending_books": [],
      "status": "completed",
      "comparison_done": true
    }
  }
}

After Response (State Reset):
{
  "topics_to_write": [],
  "books_to_search": [],
  "preferred_books": ["Harrison's Principles.pdf", "Williams Obstetrics.pdf"],  # ← Retained
  "writing_progress": {}  # ← Reset after completion
}
```

### How Agent Uses Session State

The session state is passed to Gemini in the system context. The agent can:

✅ **Read State**:
```python
# Agent reads current state
if session_state["books_to_search"]:
    # Execute next search
    next_book = session_state["books_to_search"][0]
    search(book_name=next_book)
```

✅ **Modify State**:
```python
# Agent tracks progress
session_state["writing_progress"]["topic"]["status"] = "in_progress"
session_state["books_to_search"].append("New Book.pdf")
```

✅ **Reset State**:
```python
# After completing a task
session_state["topics_to_write"] = []
session_state["writing_progress"] = {}
session_state["books_to_search"] = []
```

---

## 3. The "One Book Per Search" Rule - Implementation

### Why This Rule Exists

The Qdrant knowledge base **only accepts ONE book_name in metadata filters**:

```python
# VALID - Single book
search(filters={"book_name": "Harrison's Principles.pdf"}, query="treatment")

# INVALID - Multiple books (causes error)
search(filters={"book_name": ["Harrison's.pdf", "Williams.pdf"]}, query="treatment")
# ❌ Error: book_name must be a string, not list
```

### Filter Validator Enforcement

In `knowledge/filter_validator.py`:

```python
def validate_filters(filters: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Validates filters according to medical bot rules.
    
    Rule: Only ONE book_name per search (no lists of books)
    """
    
    if 'book_name' in filters:
        book_name = filters['book_name']
        
        # Check if it's a list (INVALID)
        if isinstance(book_name, list):
            return False, "Multiple books in one search are not allowed. Search each book individually."
        
        # Must be a string (VALID)
        if not isinstance(book_name, str):
            return False, "book_name must be a string"
    
    return True, None
```

### How Agent Handles Multiple Books

**User**: "Search both Harrison's and Williams"

**Agent Logic** (from system prompt):
```markdown
### The "One Book Per Search" Rule
* Technical Constraint: The search tool only accepts ONE `book_name` per query.
* Multi-Book Requests: If a user asks: "Search Harrison's and Williams," you must execute TWO separate searches.
    * Search 1: filters: {"book_name": "Harrison's Principles.pdf"}
    * Search 2: filters: {"book_name": "Williams Obstetrics.pdf"}
* Never refuse a multi-book search. Execute them sequentially and synthesize the results.
```

**Agent Execution**:

1. **Search 1 Execution**:
   ```python
   knowledge.search(
       query="preeclampsia treatment",
       filters={"book_name": "Harrison's Principles.pdf"}
   )
   # Returns: ~1000 word chunks from Harrison's
   ```

2. **Search 2 Execution**:
   ```python
   knowledge.search(
       query="preeclampsia treatment",
       filters={"book_name": "Williams Obstetrics.pdf"}
   )
   # Returns: ~1000 word chunks from Williams
   ```

3. **Synthesis**:
   ```python
   # Combine results in JSON response
   combined_findings = {
       "harrison_approach": "...",
       "williams_approach": "...",
       "key_differences": "...",
       "clinical_consensus": "..."
   }
   ```

---

## 4. System Prompt Instructions for Multi-Book

The system prompt in `Prompts.md` explicitly instructs the agent:

### Core Multi-Book Directives

```markdown
## 🧠 AGENTIC SESSION STATE MANAGEMENT:
You must utilize the session state to track the conversation context automatically.
*   **topics_to_write**: Track subjects requested for content generation.
*   **books_to_search**: Queue specific books mentioned by the user or discovered via search.
*   **preferred_books**: Store books the user has validated or requested explicitly.
*   **writing_progress**: Track completion of chapters/sections to ensure continuity.

## 📚 KNOWLEDGE BASE SEARCH GUIDELINES:

### The "One Book Per Search" Rule
*   **Technical Constraint**: The search tool only accepts **ONE** `book_name` per query.
*   **Multi-Book Requests**: If a user asks: "Search Harrison's and Williams," you must execute **two separate searches**.
    *   Search 1: `filters: {"book_name": "Harrison's Principles.pdf"}`
    *   Search 2: `filters: {"book_name": "Williams Obstetrics.pdf"}`
*   **Never refuse** a multi-book search. Execute them sequentially and synthesize the results.
```

### Search Strategy Hierarchy

The prompt defines how to handle different search scenarios:

```markdown
### Search Hierarchy
1. **Book Name + Query**: filters: {"book_name": "Name.pdf"}, query: "topic"
   → Best for general context
   → Returns: ~1000 word chunks

2. **Part Filter**: filters: {"book_name": "Name.pdf", "part": "Part_1"}, query: "topic"
   → Use if you know the general section
   → Returns: ~50 pages of context

3. **Page Filter**: filters: {"book_name": "Name.pdf", "page": 125}, query: "topic"
   → Last resort only
   → Returns: Single page only
```

---

## 5. Real-World Example: Multi-Book Comparison

### Scenario
**User**: "Compare the management of gestational diabetes between Williams Obstetrics and Gabbe's Obstetrics"

### Step-by-Step Execution

#### Initial State
```python
session_state = {
    "topics_to_write": [],
    "books_to_search": [],
    "preferred_books": [],
    "writing_progress": {}
}
```

#### Step 1: User Message Processed by Agent
- Agent recognizes multi-book comparison request
- Updates session state:
  ```python
  session_state["topics_to_write"] = ["gestational diabetes management comparison"]
  session_state["books_to_search"] = [
    "Williams Obstetrics.pdf",
    "9th_ed_Gabbe_s_Obstetrics.pdf"
  ]
  ```

#### Step 2: First Search (Williams)
```python
# Agent executes
knowledge.search(
    query="gestational diabetes management screening diagnostic criteria treatment",
    filters={"book_name": "Williams Obstetrics.pdf"}
)

# Qdrant returns:
# - Screening recommendations
# - Diagnostic thresholds (75g OGTT)
# - Management protocols
# - Delivery planning
```

#### Step 3: State Update After First Search
```python
session_state["writing_progress"] = {
    "gestational diabetes management comparison": {
        "williams_findings": {
            "screening": "28-32 weeks",
            "thresholds": ["95 mg/dL", "180 mg/dL", "155 mg/dL"],
            "management": "Lifestyle + insulin if needed",
            "delivery": "Check glucose at delivery"
        },
        "searched_books": ["Williams Obstetrics.pdf"],
        "pending_books": ["9th_ed_Gabbe_s_Obstetrics.pdf"]
    }
}
```

#### Step 4: Second Search (Gabbe's)
```python
# Agent executes
knowledge.search(
    query="gestational diabetes management screening diagnostic criteria treatment",
    filters={"book_name": "9th_ed_Gabbe_s_Obstetrics.pdf"}
)

# Qdrant returns:
# - Screening approach
# - Diagnostic thresholds
# - Management protocols
# - Delivery considerations
```

#### Step 5: Synthesis & Response
```python
# Agent combines findings
response = {
    "query_response": "Comparison of gestational diabetes management between two leading obstetric references...",
    "prescriptionText": [
        {
            "text": "## Williams Obstetrics Approach\n..."
        },
        {
            "text": "## Gabbe's Obstetrics Approach\n..."
        },
        {
            "text": "## Key Differences\n..."
        },
        {
            "table": {
                "column_headers": ["Aspect", "Williams", "Gabbe's"],
                "rows": [
                    ["Screening Time", "28-32 weeks", "24-28 weeks"],
                    ["Glucose Threshold", "140 mg/dL", "135 mg/dL"],
                    ...
                ]
            }
        }
    ]
}
```

#### Step 6: Final State
```python
session_state["books_to_search"] = []  # All books searched
session_state["preferred_books"] = [
    "Williams Obstetrics.pdf",
    "9th_ed_Gabbe_s_Obstetrics.pdf"
]
session_state["writing_progress"] = {}  # Cleared after completion
```

---

## 6. Agno Framework's Role in Multi-Book Handling

### Key Agno Features Used

| Feature | Purpose | Config |
|---------|---------|--------|
| `enable_agentic_knowledge_filters=True` | AI decides what/how to search | Agent config |
| `enable_agentic_state=True` | AI can modify session state | Agent config |
| `add_session_state_to_context=True` | Pass state to LLM | Agent config |
| `search_knowledge=True` | Enable knowledge base | Agent config |
| `Knowledge` class | Manage knowledge base | Qdrant integration |
| `Qdrant` class | Vector search | Metadata filtering |
| `MongoDb` class | Persist sessions | State storage |

### How Agno Orchestrates Multi-Book Queries

```python
class Agent:
    def run(self, message: str, session_id: str):
        # 1. Load session state from MongoDB
        session_state = load_session_state(session_id)
        
        # 2. Add to context
        context = build_context(
            message=message,
            session_state=session_state,  # ← Added here
            history=load_history(session_id),
            system_prompt=SYSTEM_PROMPT
        )
        
        # 3. Call LLM with full context
        response = llm.call(context)
        
        # 4. LLM may call knowledge.search() multiple times
        while knowledge_search_needed(response):
            results = knowledge.search(
                query=response.extracted_query,
                filters=validate_filters(response.extracted_filters)
            )
            response = llm.continue_with_context(results)
        
        # 5. Save updated session state
        save_session_state(session_id, session_state)
        
        # 6. Return response
        return response
```

---

## 7. Flow Diagram: Multi-Book Query Handling

```
┌─────────────────────────────────────────────────────────────┐
│                    User Sends Message                       │
│        "Compare treatment in Harrison's and Williams"      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  JWT Middleware      │
        │  ✓ Validate token    │
        │  ✓ Extract user_id   │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │  Load Session from MongoDB       │
        │  - History                       │
        │  - State (books_to_search, etc)  │
        │  - Memories                      │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌────────────────────────────────────────────┐
        │  Build Agent Context                       │
        │  ├─ System Prompt (multi-book rules)      │
        │  ├─ User Message                          │
        │  ├─ Session State                         │
        │  ├─ Chat History (5 runs)                 │
        │  ├─ User Memories                         │
        │  └─ Few-shot Examples                     │
        └──────────┬─────────────────────────────────┘
                   │
                   ▼
        ┌────────────────────────────────────────────┐
        │  Gemini LLM Processing                     │
        │  ├─ Recognizes multi-book request         │
        │  ├─ Updates session state                 │
        │  └─ Decides to search                     │
        └──────────┬─────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    Search 1              Search 2
    (Harrison's)          (Williams)
        │                     │
        ▼                     ▼
    Validate                Validate
    Filters                 Filters
    ✓ Valid                 ✓ Valid
        │                     │
        ▼                     ▼
    Qdrant                  Qdrant
    Vector Search           Vector Search
    + metadata              + metadata
    filter                  filter
        │                     │
        ▼                     ▼
    Results 1               Results 2
    (~1000 words)           (~1000 words)
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────────────────┐
        │  LLM Synthesis                  │
        │  ├─ Combine results             │
        │  ├─ Comparative analysis        │
        │  ├─ Update session state        │
        │  └─ Format JSON response        │
        └──────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │  Save Session to MongoDB         │
        │  ├─ Updated state                │
        │  ├─ New history entry            │
        │  └─ Memories                     │
        └──────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────────────────┐
        │  Return Response to User         │
        │  {                               │
        │    "query_response": "...",      │
        │    "prescriptionText": [...]     │
        │  }                               │
        └──────────────────────────────────┘
```

---

## 8. Summary: Multi-Book Handling Architecture

| Component | Role | Implementation |
|-----------|------|-----------------|
| **System Prompt** | Instructs AI to search sequentially | `Prompts.md` |
| **Agent Config** | Enables agentic filtering & state | `agents/medical_agent.py` |
| **Session State** | Tracks books_to_search & progress | MongoDB storage |
| **Filter Validator** | Enforces one book per search | `knowledge/filter_validator.py` |
| **Qdrant** | Stores & searches documents | Metadata filtering |
| **Gemini LLM** | Makes search decisions | Agentic knowledge filters |
| **Agno Framework** | Orchestrates everything | FastAPI + Agent class |

---

## 9. Key Takeaways

✅ **Yes, Agent State is Used**: Session state tracks `books_to_search`, `preferred_books`, `writing_progress`

✅ **Sequential Execution**: Multiple books are searched one at a time, NOT in parallel

✅ **Agentic Control**: The LLM (Gemini) decides what to search based on:
- System prompt instructions
- Session state
- User message
- Chat history

✅ **Filter Validation**: "One book per search" rule is enforced at the Qdrant level

✅ **Synthesis**: Results from multiple searches are combined in a single JSON response

✅ **State Persistence**: Progress is saved across requests in MongoDB

✅ **Scalable**: Can handle 2, 3, or more books in a single query (agent executes sequentially)

---

## Questions This Answers

**Q1: How are multiple books handled?**  
A: User provides multiple books → Agent updates session state → Executes searches sequentially (one book at a time) → Synthesizes results

**Q2: Is agent state used?**  
A: YES! Session state tracks `books_to_search` (queue), `preferred_books` (learned preferences), `topics_to_write`, and `writing_progress`

**Q3: Why sequential and not parallel?**  
A: Filter validator enforces "one book_name per search" (technical constraint). Sequential execution allows the LLM to synthesize findings from search 1 before executing search 2.

**Q4: How does the system know which books to search?**  
A: The system prompt tells the LLM to recognize multi-book requests and update session state. The LLM controls what's searched based on the user request.

---
