#!/usr/bin/env python3
"""record_timing.py <run-dir-relative-to-workspace> <tokens> <duration_ms> <tool_uses>"""
import json
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))
run, tokens, ms, tools = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
path = os.path.join(WS, run)
os.makedirs(path, exist_ok=True)
with open(os.path.join(path, "timing.json"), "w") as fh:
    json.dump({"total_tokens": tokens, "duration_ms": ms,
               "total_duration_seconds": round(ms / 1000, 1), "tool_uses": tools}, fh, indent=2)
print("timing:", run)
