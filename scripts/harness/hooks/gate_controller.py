"""
HITL Gate Controller & Progressive Relaxation Engine for Antigravity Runtime.
Provides runtime checks, status queries, and gate relaxation toggles.
"""

import sys
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, ".agents", "hitl_gate_config.json")


class HitlGateController:
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"HITL config not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def is_gate_active(self, gate_key: str) -> bool:
        """Returns True if the gate requires explicit user approval."""
        gate = self.config.get("gates", {}).get(gate_key)
        if not gate:
            return True
        return gate.get("enabled", True) and not gate.get("auto_approve", False)

    def relax_gate(self, gate_key: str, reason: str = "User trusted automated execution"):
        """Relaxes a gate so it executes autonomously without blocking."""
        if gate_key in self.config.get("gates", {}):
            self.config["gates"][gate_key]["auto_approve"] = True
            self.config["relaxation_history"].append({
                "gate": gate_key,
                "action": "RELAXED",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self._save_config()
            print(f"[RELAXED] Gate {gate_key} auto-approval enabled.")

    def activate_gate(self, gate_key: str, reason: str = "User requested strict review"):
        """Re-activates strict HITL review on a gate."""
        if gate_key in self.config.get("gates", {}):
            self.config["gates"][gate_key]["auto_approve"] = False
            self.config["relaxation_history"].append({
                "gate": gate_key,
                "action": "ACTIVATED",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            self._save_config()
            print(f"[STRICT] Gate {gate_key} is now strictly enforced with HITL.")

    def list_gates(self):
        print("\n" + "=" * 75)
        print(" ANTIGRAVITY NATIVE RUNTIME: HITL GATE PIPELINE STATUS")
        print("=" * 75)
        for key, g in self.config.get("gates", {}).items():
            status = "STRICT HITL" if not g.get("auto_approve") else "AUTO-RELAXED"
            print(f"[{status:12}] {key} ({g.get('stage')}): {g.get('name')}")
            print(f"               └─ {g.get('description')}")
        print("=" * 75 + "\n")


if __name__ == "__main__":
    controller = HitlGateController()
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "list":
            controller.list_gates()
        elif cmd == "relax" and len(sys.argv) > 2:
            controller.relax_gate(sys.argv[2])
        elif cmd == "activate" and len(sys.argv) > 2:
            controller.activate_gate(sys.argv[2])
    else:
        controller.list_gates()
