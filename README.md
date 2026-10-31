# my-first-mcp

A learning project that builds a Model Context Protocol (MCP) server and client from scratch, plus a CLI chatbot where Claude uses the server through MCP.

## What it covers

- **Tools:** read_doc, update_doc, edit_doc, and list_docs, which let the model act on a small document store.
- **Resources:** a document list at docs://list and individual documents at docs://list/{doc_name}, read-only context the client can browse.
- **Prompts:** summarize_doc, review_doc, compare_docs, and rewrite_doc, which the chatbot exposes as slash commands.
- **Agent loop:** main.py sends the conversation to Claude, runs any tool calls through the MCP client, feeds the results back, and repeats until Claude answers.

## How the pieces connect

```
User  ->  main.py (CLI chatbot)  ->  Claude API
              |                        |
         MCP client             "use the read_doc tool"
              |
         MCP server (mcp_server.py, spawned as a subprocess)
              |
         core/documents.py (Pydantic models and mock data)
```

## Project structure

```
core/documents.py   mock document store with Pydantic models
mcp_server.py       MCP server: tools, resources, and prompts
mcp_client.py       MCP client: exercises all three primitives directly
main.py             CLI chatbot: Claude agent with slash commands
requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
pip install -r requirements.txt
```

Add your API key to a .env file (it is git-ignored):

```
ANTHROPIC_API_KEY=your-key-here
```

## Running

1. Inspect the server in the MCP Inspector (no code needed): `mcp dev mcp_server.py`
2. Exercise the client directly, without an AI model: `python mcp_client.py`
3. Run the chatbot: `python main.py`

## Limitations

This is a learning project, not production code. The document store is in-memory and mock, so changes do not persist between sessions. A production version would need persistent storage, authentication, error handling, rate limiting, and logging.
