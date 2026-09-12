"""
CLI Chatbot — a command-line agent with "/" commands powered by MCP prompts.

=== HOW THE AGENT CONNECTS EVERYTHING ===

This file is mcp_client.py + Claude API glued together.
The agent IS an MCP client that also talks to an AI model.

    User types "What's in report.txt?"
            ↓
       main.py (run_chatbot)
            ↓
       Sends message to Claude API (with tool definitions from MCP)
            ↓
       Claude responds: "I need to call read_doc"  (stop_reason == "tool_use")
            ↓
       main.py calls session.call_tool() ← THIS IS THE MCP CLIENT PART
            ↓
       MCP Server runs read_doc() → returns content
            ↓
       main.py sends tool result BACK to Claude as a "tool_result" message
            ↓
       Claude responds: "Here's what's in report.txt..."
            ↓
       Printed to user

=== THE THREE KEY PIECES ===

PIECE 1 — mcp_tools_to_claude_format() (The Bridge)
    MCP and Claude use slightly different schemas for tools.
    MCP calls it `inputSchema`, Claude expects `input_schema`.
    This function translates between the two protocols.
    Without it, Claude wouldn't know what tools exist.

PIECE 2 — agent_turn() (The Agent Loop)
    The heart of every AI agent. A while True loop with two branches:
    - Claude wants a tool (stop_reason == "tool_use"):
        Extract tool name + args → call via MCP → send result back → loop again
    - Claude gives a text response (any other stop_reason):
        We're done, return the text.
    Claude can call MULTIPLE tools in one turn and may need MULTIPLE rounds
    before giving a final answer. The while True handles both.

PIECE 3 — handle_slash_command() (Prompts Become Commands)
    This is where MCP prompts shine:
    1. On startup, chatbot fetches all prompts from server (list_prompts)
    2. User types "/summarize_doc spec.md" → matches against prompts map
    3. Calls session.get_prompt() → server returns filled-in template
    4. That text gets sent to Claude as if the user typed it
    5. Claude then uses tools (read_doc) to fulfill the request
    The server defines WHAT prompts exist. The client decides HOW to present them.

=== HOW IT ALL CONNECTS ===

    main.py
    ├── Anthropic() client ← talks to Claude API
    ├── MCP ClientSession  ← talks to mcp_server.py (same 4 steps as mcp_client.py)
    │   ├── list_tools()   → converted to Claude format → passed to Claude API
    │   ├── call_tool()    → called when Claude requests a tool
    │   └── get_prompt()   → called when user types a /command
    └── Chat loop          ← ties it all together with message history

=== YOUR TASK ===
Set ANTHROPIC_API_KEY in .env, then run: python main.py
Try:
  - "What's in report.txt?"                          (natural language → tool call)
  - /summarize_doc spec.md                            (prompt → tool call → summary)
  - /review_doc report.txt                            (prompt → tool call → review)
  - "What's in report.txt?" then "Now add a section"  (multi-turn with context)
  - /tools                                            (local command, no server)
  - /help                                             (see all commands)
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SYSTEM_PROMPT = """You are a helpful document assistant. You have access to tools
that let you read and update documents. Use them when the user asks about
document contents. Be concise in your responses."""


def mcp_tools_to_claude_format(mcp_tools) -> list[dict]:
    """Convert MCP tool schemas → Claude API format.
    MCP uses `inputSchema`, Claude expects `input_schema` — this bridges the two.
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        }
        for tool in mcp_tools
    ]


async def agent_turn(client, model, messages, claude_tools, session):
    """
    Run one full agent turn: send messages to Claude, handle any tool calls,
    return the final text response.

    This is the core loop you'll find in every MCP-based agent.
    The while True handles Claude needing multiple rounds of tool calls.
    """
    while True:
        # Send conversation + available tools to Claude
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=claude_tools,       # Tools discovered from MCP, converted to Claude format
            messages=messages,
        )

        # BRANCH A: Claude wants to call one or more tools
        if response.stop_reason == "tool_use":
            # Add Claude's response (which includes tool_use blocks) to history
            messages.append({"role": "assistant", "content": response.content})

            # Process each tool call — Claude may request multiple in one turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  ↳ calling {block.name}({json.dumps(block.input)})")
                    # HERE is where MCP client calls the MCP server
                    result = await session.call_tool(block.name, arguments=block.input)
                    # Package the result in Claude's expected tool_result format
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,       # Must match the tool_use block's id
                        "content": result.content[0].text,
                    })

            # Send tool results back to Claude — it needs them to formulate its answer
            messages.append({"role": "user", "content": tool_results})
            # Loop continues — Claude may call more tools or give a final response

        # BRANCH B: Claude gave a final text response — we're done
        else:
            final_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            messages.append({"role": "assistant", "content": final_text})
            return final_text


async def handle_slash_command(command: str, session, prompts_map) -> str | None:
    """
    Handle "/" commands. Returns the prompt text to send to Claude,
    or None for local-only commands (that print their own output).

    TODO: This is where you wire up MCP prompts as slash commands.
    The pattern: parse the command → call session.get_prompt() → return the text.
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lstrip("/")
    args_str = parts[1] if len(parts) > 1 else ""

    # --- Local commands (no server round-trip) ---
    if cmd == "help":
        print("\n  Local commands:")
        print("    /help        — Show this help")
        print("    /tools       — List available tools")
        print("    /prompts     — List available prompt templates")
        print("    /quit        — Exit the chatbot")
        print("\n  Prompt commands (from MCP server):")
        for name, prompt in prompts_map.items():
            print(f"    /{name} <args> — {prompt.description}")
        print()
        return None

    if cmd == "quit":
        return "QUIT"

    if cmd == "tools":
        tools_result = await session.list_tools()
        print("\n  Available tools:")
        for tool in tools_result.tools:
            print(f"    {tool.name} — {tool.description[:70]}")
        print()
        return None

    if cmd == "prompts":
        print("\n  Available prompts:")
        for name, prompt in prompts_map.items():
            print(f"    /{name} — {prompt.description}")
        print()
        return None

    # --- MCP prompt commands (fetched from server at startup) ---
    if cmd in prompts_map:
        # Get the prompt template from the MCP server, filled in with user's args.
        # The returned text gets sent to Claude as if the user typed it.
        prompt_info = prompts_map[cmd]
        prompt_args = {}
        if prompt_info.arguments and args_str:
            prompt_args[prompt_info.arguments[0].name] = args_str

        result = await session.get_prompt(cmd, arguments=prompt_args)
        return result.messages[0].content.text

    print(f"  Unknown command: /{cmd}. Type /help for available commands.")
    return None


async def run_chatbot():
    # Claude API client — talks to the AI model
    client = Anthropic()
    model = "claude-sonnet-4-20250514"

    # MCP connection — same 4 steps as mcp_client.py
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Discover tools from MCP server → convert to Claude's format
            tools_result = await session.list_tools()
            claude_tools = mcp_tools_to_claude_format(tools_result.tools)

            # Discover prompts from MCP server → these become our "/" commands
            # The server defines domain-specific templates; we present them as CLI commands
            prompts_result = await session.list_prompts()
            prompts_map = {p.name: p for p in prompts_result.prompts}

            print("╔══════════════════════════════════════╗")
            print("║     Document Assistant Chatbot       ║")
            print("╠══════════════════════════════════════╣")
            print("║  Type a message or use /commands     ║")
            print("║  /help for available commands        ║")
            print("╚══════════════════════════════════════╝")
            print()

            messages = []

            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    result = await handle_slash_command(user_input, session, prompts_map)
                    if result == "QUIT":
                        print("Goodbye!")
                        break
                    if result is None:
                        continue
                    # Prompt template returned text → send it to Claude
                    user_input = result

                messages.append({"role": "user", "content": user_input})

                response_text = await agent_turn(
                    client, model, messages, claude_tools, session
                )
                print(f"\nAssistant: {response_text}\n")


if __name__ == "__main__":
    asyncio.run(run_chatbot())
