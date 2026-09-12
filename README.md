# My First MCP

A learning project to understand the Model Context Protocol (MCP) — tools, resources, and prompts — by building a CLI chatbot that talks to documents.

## Project Structure

```
├── core/
│   ├── __init__.py
│   └── documents.py    # Mock document store with Pydantic models
├── mcp_server.py       # MCP Server — tools, resources, and prompts
├── mcp_client.py       # MCP Client — test all three primitives directly
├── main.py             # CLI Chatbot — Claude agent with /commands
├── requirements.txt
├── .env                # Your API key (git-ignored, never committed)
├── .gitignore
└── README.md
```

## How the pieces connect

```
User  →  main.py (CLI Chatbot)  →  Claude API
              ↕                        ↕
         MCP Client             "Use read_doc tool"
              ↕
         MCP Server (mcp_server.py, spawned as subprocess)
              ↕
         core/documents.py (Pydantic models + mock data)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

Add your API key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running

**1. Test the server with MCP Inspector (no code needed):**
```bash
mcp dev mcp_server.py
```
Opens a browser UI where you can browse tools/resources/prompts and call them interactively.

**2. Test the client directly (no AI):**
```bash
python mcp_client.py
```

**3. Run the chatbot:**
```bash
python main.py
```

## Step-by-Step Development Roadmap

Work through these in order. Each step builds on the last.

### Phase 1: Understand the Server (mcp_server.py)

1. **Run the server in MCP Inspector** (`mcp dev mcp_server.py`). Click around the Tools tab. Call `read_doc` with different document names. Call it with a name that doesn't exist — observe the error format.

2. **Add the `list_docs` tool.** You have the function in `core/documents.py` already. Register it with `@mcp.tool()`. Restart the inspector and verify it appears.

3. **Uncomment and test resources** in `mcp_client.py`. Read the `docs://list` resource. Then add individual document resources using a URI template (`docs://{doc_name}`) on the server. Resources are the "browse" side of MCP vs tools being the "do" side.

4. **Uncomment and test prompts** in `mcp_client.py`. Call `get_prompt("summarize_doc", ...)` and look at what comes back — it's a message structure, not a raw string. Add a `compare_docs` prompt that takes two document names.

### Phase 2: Understand the Client (mcp_client.py)

5. **Trace the lifecycle.** Add print statements at each stage: connection, initialize handshake, list_tools, call_tool. Understand the `ClientSession` object — it's your handle to everything.

6. **Call update_doc then read_doc.** Verify state changes persist within a session. Think about why they DON'T persist across sessions (the server restarts).

7. **Try error cases.** Call a tool with wrong argument types. Call a non-existent tool. Read a non-existent resource URI. Understand how MCP surfaces errors.

### Phase 3: Build the Agent Loop (main.py)

8. **Study `agent_turn()`.** This is the heart of every AI agent. The loop is: send to Claude → check if it wants a tool → call the tool via MCP → feed result back → repeat. Trace through it with a simple prompt like "what's in report.txt?"

9. **Study `handle_slash_command()`.** See how MCP prompts become `/` commands. The server defines the templates, the client presents them. Try `/summarize_doc spec.md` and watch the prompt get fetched from the server, sent to Claude, which then calls the `read_doc` tool.

10. **Add multi-turn awareness.** Currently the chatbot maintains history. Try "what's in report.txt?" then "now update it with a new section" — observe how Claude uses context from prior turns.

### Phase 4: Extend It (your own features)

11. **Add a `compare_docs` prompt** on the server that takes two document names. Wire it into the chatbot as `/compare_docs`. Think about how to parse multiple arguments from one string.

12. **Add resource templates** for individual documents (`docs://{doc_name}`). Then in the chatbot, add a `/browse` command that lists resources and lets you read one.

13. **Add a `search_docs` tool** that takes a query string and searches document contents. This is a good exercise in writing tool descriptions that help Claude understand when to use it vs `read_doc`.

14. **Think about what's missing for production:** persistent storage, authentication, error handling, rate limiting, logging. You don't need to build these — just note where they'd go.

### Phase 5: Ship It

15. **Double-check `.gitignore`** — make sure `.env` and `.venv/` are listed. Run `git status` before committing to verify no secrets leak.

16. **Init the repo and push:**
```bash
git init
git add .
git commit -m "Initial commit: MCP learning project"
git remote add origin <your-github-url>
git push -u origin main
```
