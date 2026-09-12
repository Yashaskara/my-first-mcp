"""
Mock document store.

This module simulates a document storage backend. In a real MCP server,
this would connect to a database, filesystem, or cloud storage API.

KEY CONCEPT: Your MCP server's tools need *something* to operate on.
This is that something — the "business logic" layer your tools wrap.
Pydantic models give you typed, validated data structures that MCP's
tool schema generation can leverage automatically.
"""

from pydantic import BaseModel


class Document(BaseModel):
    name: str
    content: str
    mime_type: str


# Our mock documents — each is a typed Pydantic model
DOCUMENTS: dict[str, Document] = {
    "document.pdf": Document(
        name="document.pdf",
        mime_type="application/pdf",
        content=(
            "Q3 2024 Performance Review\n"
            "The team exceeded targets by 15% in Q3.\n"
            "Action Items: Schedule Q4 planning, review hiring pipeline."
        ),
    ),
    "spreadsheet.xlsx": Document(
        name="spreadsheet.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=(
            "Monthly Revenue Data\n"
            "Jan: 120k | Feb: 135k | Mar: 128k\n"
            "Apr: 142k | May: 155k | Jun: 160k"
        ),
    ),
    "report.txt": Document(
        name="report.txt",
        mime_type="text/plain",
        content=(
            "Weekly Status Report - Week 37\n"
            "Completed: Auth migration, 3 bug fixes, monitoring dashboards\n"
            "Blocked: Waiting on security review for OAuth flow"
        ),
    ),
    "spec.md": Document(
        name="spec.md",
        mime_type="text/markdown",
        content=(
            "# API Specification v2\n"
            "## Endpoints\n"
            "- GET /api/users - List all users\n"
            "- POST /api/users - Create a new user\n"
            "- PUT /api/users/:id - Update user by ID"
        ),
    ),
}


def get_document(doc_name: str) -> Document:
    if doc_name not in DOCUMENTS:
        raise ValueError(f"Document '{doc_name}' not found. Available: {list(DOCUMENTS.keys())}")
    return DOCUMENTS[doc_name]


def read_document(doc_name: str) -> str:
    return get_document(doc_name).content


def update_document(doc_name: str, new_content: str) -> str:
    doc = get_document(doc_name)
    doc.content = new_content
    return f"Document '{doc_name}' updated successfully."

def edit_document(doc_name: str, old_content: str, new_content: str) -> str:
    doc = get_document(doc_name)
    if doc:
        doc.content = doc.content.replace(old_content, new_content)
        return f"Document '{doc_name}' edited successfully."

def list_documents() -> list[str]:
    return list(DOCUMENTS.keys())
