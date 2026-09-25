"""
PreToolUse Hook Handler for Antigravity CLI.
Enforces safety guards on critical operations and prevents accidental destructive commands.
Reads JSON from stdin, outputs JSON to stdout.
"""

import sys
import json
import re

def handle_pre_tool():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        # Safety rule: Protect G:\ root and system drives from recursive deletion
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "")
            if re.search(r"Remove-Item.*[CG]:\\?\s*(-Recurse|-Force)", cmd, re.IGNORECASE) or \
               re.search(r"rmdir\s+/[sq]\s+[CG]:\\?", cmd, re.IGNORECASE):
                print(json.dumps({
                    "decision": "deny",
                    "reason": "Destructive deletion on root drive C: or G: is strictly forbidden by safety harness."
                }))
                return

        # Default: allow
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # Fallback to allow on unexpected hook exception
        print(json.dumps({"decision": "allow", "reason": f"Hook exception: {str(e)}"}))

if __name__ == "__main__":
    handle_pre_tool()
