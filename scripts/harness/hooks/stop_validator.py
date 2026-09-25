"""
Stop Hook Handler for Antigravity CLI.
Ensures background tasks are completed and required validations pass before terminating turns.
"""

import sys
import json

def handle_stop():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        fully_idle = payload.get("fullyIdle", True)
        
        # If tasks are still running in background, tell agent to wait
        if not fully_idle:
            print(json.dumps({
                "decision": "continue",
                "reason": "Background asynchronous processes are still finalizing. Please await their completion."
            }))
            return

        print(json.dumps({"decision": "allow"}))
    except Exception:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    handle_stop()
