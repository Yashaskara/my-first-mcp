"""
MCP Server — exposes tools, resources, and prompts.

=== THE THREE PRIMITIVES OF MCP ===

1. TOOLS   → Functions the AI model can *call* (like API endpoints)
             Registered with @mcp.tool()
             The model decides when to use them based on the user's request.

2. RESOURCES → Data the AI model can *read* (like GET endpoints)
               Registered with @mcp.resource("uri://pattern")
               Think of these as "context" the model can pull in.
               URIs follow a scheme like "docs://document.pdf"

3. PROMPTS → Reusable prompt templates the client can offer to the user
             Registered with @mcp.prompt()
             These are NOT system prompts — they're user-facing templates
             that a client (like our chatbot) can list and fill in.

=== TOOLS vs RESOURCES ===
- Tools DO something (read, write, compute) — they have side effects
- Resources ARE something (data, context) — they're read-only views
- A tool might call read_document(); a resource exposes the document directly

=== YOUR TASK ===
1. Study the three decorator patterns: @mcp.tool(), @mcp.resource(), @mcp.prompt()
2. Add a list_docs tool
3. Add a resource for each document
4. Create a prompt template for document comparison
5. Test everything with: mcp dev mcp_server.py
"""

from mcp.server.mcpserver import MCPServer

from core.documents import read_document, update_document, list_documents, get_document, edit_document

mcp = MCPServer("Document Server")


# =========================================================================
# TOOLS — actions the model can perform
# =========================================================================

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

# TODO: Add a list_docs tool here
# Hint: @mcp.tool() + a function that returns list_documents()

@mcp.tool()
def list_docs() -> list[str]:
    """List all available documents."""
    return list_documents()


# =========================================================================
# RESOURCES — read-only data the model can pull into its context
# =========================================================================
# Resources use URI patterns. The client can list them and read them.
# Unlike tools, these don't "do" anything — they just provide data.
#
# KEY QUESTION: Why would you use a resource instead of a tool?
# Answer: Resources are declarative. The client/model can browse them
# without needing to know the right function call or arguments.
# They're like a file browser vs a command line.
# =========================================================================

@mcp.resource("docs://list")
def resource_list_docs() -> str:
    """List all available documents."""
    return "\n".join(list_documents())


# TODO: Add a resource for individual documents.
# Hint: Use a URI template with a parameter:
@mcp.resource("docs://list/{doc_name}")
def resource_get_doc(doc_name: str) -> str:
    """Get the contents of a document by its filename.
    Available documents: document.pdf, spreadsheet.xlsx, report.txt, spec.md
    """
    return get_document(doc_name)
      
# Then test it in MCP Inspector — you'll see it in the Resources tab.


# =========================================================================
# PROMPTS — reusable prompt templates the client can offer to users
# =========================================================================
# Prompts are NOT system prompts. They're templates that a client
# (like our chatbot) can list and present to the user as slash commands.
# The server defines them; the client decides how to expose them.
#
# KEY QUESTION: Why define prompts on the server instead of the client?
# Answer: The server knows its domain. A document server knows useful
# document operations; the client just needs to present them.
# =========================================================================

@mcp.prompt()
def summarize_doc(doc_name: str) -> str:
    """Create a concise summary of a document."""
    return f"Please read the document '{doc_name}' and provide a concise summary highlighting the key points."


@mcp.prompt()
def review_doc(doc_name: str) -> str:
    """Review a document for issues and suggest improvements."""
    return f"Please read '{doc_name}' and review it for clarity, completeness, and any issues. Suggest specific improvements."


# TODO: Add a compare_docs prompt that takes two doc names
@mcp.prompt()
def compare_docs(doc_name1: str, doc_name2: str) -> str:
    """Compare two documents and provide a summary of the differences."""
    return f"Please compare the documents '{doc_name1}' and '{doc_name2}' and provide a summary of the differences."
# TODO: Add a rewrite_doc prompt that takes a doc name and a target style
@mcp.prompt()
def rewrite_doc(doc_name: str, target_style: str) -> str:
    """Rewrite a document in a target style."""
    return f"Please rewrite the document '{doc_name}' in the target style '{target_style}'."

if __name__ == "__main__":
    mcp.run()
