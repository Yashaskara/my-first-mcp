"""
MCP Client — connects to an MCP server and exercises all three primitives.

=== HOW THE CLIENT-SERVER CONNECTION WORKS ===

There are 4 must-have steps for any MCP client:

STEP 1 — StdioServerParameters (Define how to find the server)
    You tell the client: "spawn this command as a subprocess."
    The client and server talk over stdin/stdout of that subprocess.
    This is the same thing you configured in the Inspector UI (command + arguments).

STEP 2 — stdio_client() (Open the connection)
    This actually spawns the server process and gives you raw read/write streams.
    Think of it like opening a TCP socket — a pipe in and a pipe out.
    The `async with` ensures the process gets cleaned up when done.

STEP 3 — ClientSession + initialize() (Handshake)
    ClientSession wraps the raw streams into a high-level API.
    initialize() is the handshake — client and server exchange:
      - Protocol version (so they agree on the same MCP spec)
      - Capabilities (what each side supports — tools? resources? prompts?)
    This is MANDATORY. Skip it and nothing works.

STEP 4 — list_tools() / call_tool() (Discover and use)
    Two methods — that's the entire tools API:
      - list_tools()  → "What tools do you have?" Returns names, descriptions, input schemas.
      - call_tool()   → "Run this one." Pass name + arguments dict, get result back.
    Same pattern for resources (list_resources / read_resource) and prompts (list_prompts / get_prompt).

=== THE MENTAL MODEL ===

    Client                          Server
      |                               |
      |--- initialize() ------------>|  (handshake)
      |<---- capabilities -----------|
      |                               |
      |--- list_tools() ------------>|  (discovery)
      |<---- [read_doc, update_doc] -|
      |                               |
      |--- call_tool("read_doc") --->|  (execution)
      |<---- "Weekly Status Report..."|

KEY INSIGHT: The client never imports your server code. It doesn't know what
read_document() is. It only knows what the server ADVERTISES through the MCP
protocol. The client and server are fully decoupled.
"""

import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # STEP 1: Define how to find the server
    # "Spawn `python mcp_server.py` as a subprocess, talk over its stdin/stdout"
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    # STEP 2: Open the connection — spawns the server process, gives us raw streams
    async with stdio_client(server_params) as (read_stream, write_stream):

        # STEP 3: Wrap streams in a session + handshake (exchanges protocol version & capabilities)
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # STEP 4: Discover and call — same pattern for tools, resources, and prompts

            # ---- TOOLS ----
            # list_tools() → returns name, description, inputSchema for each @mcp.tool()
            tools_result = await session.list_tools()
            print("=" * 50)
            print("TOOLS:")
            print("=" * 50)
            for tool in tools_result.tools:
                print(f"  {tool.name} — {tool.description[:60]}")
            print()

            # call_tool() invokes by name + arguments dict
            # Result is in result.content[0].text — MCP wraps everything in a content array
            result = await session.call_tool("read_doc", arguments={"doc_name": "report.txt"})
            print(f"read_doc('report.txt') → {result.content[0].text[:80]}...")
            print()

            # ---- RESOURCES ----
            # Same pattern: list_resources() to discover, read_resource(uri) to fetch
            # Resources are read-only data — no side effects, just context
            resources_result = await session.list_resources()
            print("=" * 50)
            print("RESOURCES:")
            print("=" * 50)
            for resource in resources_result.resources:
                print(f"  {resource.uri} — {resource.name}")
            print()
            
            content = await session.read_resource("docs://list")
            print(f"docs://list → {content}")
            print()

            content = await session.read_resource("docs://list/document.pdf")
            print(f"docs://list/document.pdf → {content}")
            print()

            content = await session.read_resource("docs://list/spreadsheet.xlsx")
            print(f"docs://list/spreadsheet.xlsx → {content}")
            print()

            # ---- PROMPTS ----
            # list_prompts() to discover, get_prompt() to fetch a filled-in template
            # get_prompt() returns a message structure (not a raw string) —
            # it's ready to be sent to an AI model as a user message
            prompts_result = await session.list_prompts()
            print("=" * 50)
            print("PROMPTS:")
            print("=" * 50)
            for prompt in prompts_result.prompts:
                print(f"  {prompt.name} — {prompt.description}")
            print()
            
            prompt = await session.get_prompt(
                "summarize_doc",
                arguments={"doc_name": "spec.md"},
            )
            print(f"summarize_doc('spec.md') → {prompt.messages[0].content.text}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
