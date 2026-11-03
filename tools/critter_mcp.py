# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Desk Critter tools for Claude Desktop: lets Claude make the critter wave (finished) or alert
(needs you) from a normal chat. Standard library only.

It is a tiny MCP server (the plug-in format Claude Desktop uses for tools). Claude Desktop starts
it in the background and talks to it over stdin/stdout. It offers exactly two tools:
    wave    green eyes and a happy wave   (same as: py tools\\critter_event.py done)
    alert   bounce, alert colours, sound  (same as: py tools\\critter_event.py help)
Nothing else is possible through it, so "Always allow" is safe.

Set up (see README, "Let Claude wave after every chat reply"):
  1. Claude Desktop -> Settings -> Developer -> Edit Config, add to "mcpServers":
        "desk-critter": {"command": "py",
                         "args": ["C:\\\\Users\\\\<you>\\\\Tools\\\\Desk_Critter\\\\tools\\\\critter_mcp.py"]}
  2. Restart Claude Desktop (quit it from the tray icon, then start it again).
  3. Add the instruction to Settings -> Profile -> personal preferences.

Check it by hand: py tools\\critter_mcp.py --selftest
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from critter_event import send          # writes the line the critter follows (same file as the hooks)

SERVER = {"name": "desk-critter", "version": "3.0"}
DEFAULT_PROTOCOL = "2025-06-18"
SESSION = "claude-chat"

TEXT_ARG = {"type": "object",
            "properties": {"text": {"type": "string",
                                    "description": "Optional short note, written to the critter's log"}},
            "additionalProperties": False}
SAFE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
TOOLS = [
    {"name": "wave",
     "title": "Critter: wave (finished)",
     "description": "Make the user's Desk Critter (a small desktop companion) show green eyes and wave, to signal that you have "
                    "finished your reply and nothing is needed from the user. Call it as the last step of a reply.",
     "inputSchema": TEXT_ARG, "annotations": {"title": "Critter: wave", **SAFE}},
    {"name": "alert",
     "title": "Critter: alert (needs you)",
     "description": "Make the user's Desk Critter bounce and play its alert sound, to signal that you "
                    "need the user's input, a decision or an approval. Use instead of wave in that case.",
     "inputSchema": TEXT_ARG, "annotations": {"title": "Critter: alert", **SAFE}},
]
KIND = {"wave": "done", "alert": "help"}
DEFAULT_TEXT = {"wave": "Claude finished", "alert": "Claude needs you"}


def serve(inp=sys.stdin.buffer, out=sys.stdout.buffer):
    """One JSON message per line in, one per line out. Only JSON may go to stdout."""
    for raw in inp:
        raw = raw.strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw.decode("utf-8"))
            reply = handle(msg) if isinstance(msg, dict) else \
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "batches not supported"}}
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        if reply is not None:
            out.write(json.dumps(reply).encode("utf-8") + b"\n")
            out.flush()


def handle(msg):
    """Answer one JSON-RPC message. Returns the reply dict, or None for notifications."""
    method, msg_id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if msg_id is None:                                   # a notification (e.g. "initialized")
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    if method == "initialize":
        return ok({"protocolVersion": params.get("protocolVersion") or DEFAULT_PROTOCOL,
                   "capabilities": {"tools": {}},
                   "serverInfo": SERVER,
                   "instructions": "Call 'wave' as the last step of each reply when you are done, or "
                                   "'alert' when you need the user's input or approval."})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        if name not in KIND:
            return {"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32602, "message": f"unknown tool: {name}"}}
        try:
            text = send(KIND[name], (params.get("arguments") or {}).get("text") or DEFAULT_TEXT[name], SESSION)
            return ok({"content": [{"type": "text", "text": f"Critter: {name} ({text})"}], "isError": False})
        except Exception as e:                           # e.g. the folder can't be written
            return ok({"content": [{"type": "text", "text": f"Critter {name} failed: {e}"}], "isError": True})
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"unknown method: {method}"}}


def selftest():
    """Pretend to be Claude Desktop: start up, list the tools, call wave."""
    for msg in ({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": DEFAULT_PROTOCOL, "capabilities": {}, "clientInfo": {"name": "selftest"}}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "wave", "arguments": {"text": "self-test"}}}):
        reply = handle(msg)
        print(f"{msg['method']:28s} -> {json.dumps(reply)[:150] if reply else '(no reply, notification)'}")
    print("If the critter is running it should now be waving.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        serve()
