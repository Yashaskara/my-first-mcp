"""
MCP server that exposes a small document store through the three MCP primitives.

1. Tools: functions the model can call (read, update, edit, and list documents).
2. Resources: read-only data the client can browse (docs://list, docs://list/{doc_name}).
3. Prompts: reusable templates a client can offer to users, for example as slash commands.

Tools perform actions and may have side effects. Resources are read-only views of
data. Prompts are user-facing templates, not system prompts.

Run it in the MCP Inspector with: mcp dev mcp_server.py
"""

from mcp.server.mcpserver import MCPServer

from core.documents import read_document, update_document, list_documents, get_document, edit_document

mcp = MCPServer("Document Server")

# ---------------------------------------------------------------------------
# Tools: actions the model can perform
# ---------------------------------------------------------------------------

@mcp.tool()
def read_doc(doc_name: str) -> str:
    """Read the contents of a document by its filename.
    Available documents: document.pdf, spreadsheet.xlsx, report.txt, spec.md
    """
    return read_document(doc_name)

@mcp.tool()
def update_doc(doc_name: str, new_content: str) -> str:
    """Update the contents of a document.
    Provide the document filename and the new content to write.
    Available documents: document.pdf, spreadsheet.xlsx, report.txt, spec.md
    """
    return update_document(doc_name, new_content)

@mcp.tool()
def edit_doc(doc_name: str, old_content: str, new_content: str) -> str:
    """Edit the contents of a document.
    Provide the document filename, the old content to replace, and the new content to write.
    Available documents: document.pdf, spreadsheet.xlsx, report.txt, spec.md
    """
    return edit_document(doc_name, old_content, new_content)

@mcp.tool()
def list_docs() -> list[str]:
    """List all available documents."""
    return list_documents()

# ---------------------------------------------------------------------------
# Resources: read-only data the model can pull into its context
# ---------------------------------------------------------------------------
# Resources are declarative: a client can browse them without knowing which
# function to call, like a file browser instead of a command line.

@mcp.resource("docs://list")
def resource_list_docs() -> str:
    """List all available documents."""
    return "\n".join(list_documents())

@mcp.resource("docs://list/{doc_name}")
def resource_get_doc(doc_name: str) -> str:
    """Get the contents of a document by its filename.
    Available documents: document.pdf, spreadsheet.xlsx, report.txt, spec.md
    """
    return get_document(doc_name)

# ---------------------------------------------------------------------------
# Prompts: reusable templates the client can offer to users
# ---------------------------------------------------------------------------
# The server defines the prompts because it knows its domain; the client only
# decides how to present them (the chatbot exposes them as slash commands).

@mcp.prompt()
def summarize_doc(doc_name: str) -> str:
    """Create a concise summary of a document."""
    return f"Please read the document '{doc_name}' and provide a concise summary highlighting the key points."

@mcp.prompt()
def review_doc(doc_name: str) -> str:
    """Review a document for issues and suggest improvements."""
    return f"Please read '{doc_name}' and review it for clarity, completeness, and any issues. Suggest specific improvements."

@mcp.prompt()
def compare_docs(doc_name1: str, doc_name2: str) -> str:
    """Compare two documents and provide a summary of the differences."""
    return f"Please compare the documents '{doc_name1}' and '{doc_name2}' and provide a summary of the differences."

@mcp.prompt()
def rewrite_doc(doc_name: str, target_style: str) -> str:
    """Rewrite a document in a target style."""
    return f"Please rewrite the document '{doc_name}' in the target style '{target_style}'."

if __name__ == "__main__":
    mcp.run()
