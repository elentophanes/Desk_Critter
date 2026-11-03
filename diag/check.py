# Desk_Critter — https://github.com/elentophanes/Desk_Critter
# Copyright (c) 2026 Elentophanes and contributors
# Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
# Commercial use requires a separate license — see COMMERCIAL.md.
# Required Notice: Copyright (c) 2026 Elentophanes (https://github.com/elentophanes/Desk_Critter)
"""
Quick check of the whole program, no screen needed:

    py diag\\check.py         (macOS: python3 diag/check.py)

  - fingerprints and compiles every .py / .pyw file in the repo (found automatically)
  - lists the critters and checks each one's sound files (SOUND, SOUND_DONE) exist
  - asks the Claude Desktop tool (tools/critter_mcp.py) for its tool list, without sending anything to the critter
  - renders all critters into critters_preview.svg (open it in a browser)
"""

__author__ = "Elentophanes"
__project_id__ = "6075ff8b1744"
import hashlib
import os
import py_compile
import runpy
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
sys.path.insert(0, root)
problems = []

files = sorted(os.path.relpath(os.path.join(d, f), root).replace("\\", "/")
               for d, dirs, names in os.walk(root)
               if not any(part.startswith(".") or part == "__pycache__" for part in os.path.relpath(d, root).split(os.sep))
               for f in names if f.endswith((".py", ".pyw")))
for f in files:
    print(hashlib.sha256(open(f, "rb").read().replace(b"\r\n", b"\n")).hexdigest()[:16], f)
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except py_compile.PyCompileError as e:
        problems.append(f"does not compile: {f}: {e.msg}")
print(f"compiled {len(files)} files")

import critters
found = critters.discover(print)
print("critters:", list(found))
for key, mod in found.items():
    for attr in ("SOUND", "SOUND_DONE"):
        name = getattr(mod, attr, None)
        if name and not os.path.isfile(os.path.join(root, "critters", name)):
            problems.append(f"critter '{key}': {attr} file critters/{name} is missing")

sys.path.insert(0, os.path.join(root, "tools"))
import critter_mcp
tools = critter_mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
print("Claude Desktop tools:", [t["name"] for t in tools])

runpy.run_path("tools/preview_critters.py", run_name="__main__")

if problems:
    print("\nPROBLEMS:\n  " + "\n  ".join(problems))
    sys.exit(1)
print("all OK")
