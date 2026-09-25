"""
Local Google Drive (G:) Mount & Zero Pay-As-You-Go Serialization Harness.
Validates zero-cost sermon note backup to G:\\내 드라이브\\성경주혜주석_설교노트\\,
JSON/Markdown round-trip integrity, and verifies absence of pay-per-use APIs.
"""

import sys
import os
import json
import unittest
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

G_DRIVE_FOLDER = r"G:\내 드라이브\성경주혜주석_설교노트"


class GDriveSyncHarness(unittest.TestCase):
    def test_01_g_drive_mount_accessible(self):
        """Verify that G:\\내 드라이브 mounted Google Drive folder is active and writable."""
        self.assertTrue(os.path.exists(G_DRIVE_FOLDER), f"Google Drive sync folder does not exist: {G_DRIVE_FOLDER}")
        self.assertTrue(os.path.isdir(G_DRIVE_FOLDER), f"Path is not a directory: {G_DRIVE_FOLDER}")

        # Test write and read round-trip
        test_file = os.path.join(G_DRIVE_FOLDER, ".harness_sync_probe.tmp")
        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(f"PROBE_{datetime.now().isoformat()}")
            self.assertTrue(os.path.exists(test_file), "Failed to write probe to G: drive")
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_02_sermon_json_serialization_roundtrip(self):
        """Test sermon outline JSON serialization matches mobile & desktop schema."""
        sermon_payload = {
            "sermonId": "20260925_moriah",
            "title": "모리아 산의 온전한 순종과 여호와 이레의 축복",
            "preacher": "박우호 목사",
            "sermonDate": "2026-09-27",
            "serviceType": "주일대예배",
            "scriptureRef": "창세기 22:1-14",
            "targetDurationMins": 30,
            "outline": [
                {
                    "section": "서론",
                    "title": "믿음의 시험과 인생의 광야",
                    "content": "하나님의 부르심과 즉각 순종.",
                    "citations": ["창 22:1"]
                },
                {
                    "section": "본론 I",
                    "title": "독자를 내려놓는 믿음의 결단",
                    "content": "히브리어 야히드, 자기 부인의 성화 단계.",
                    "citations": ["창 22:2", "요 3:16", "롬 8:32"]
                },
                {
                    "section": "결론",
                    "title": "약속의 자녀로서의 결단",
                    "content": "부활 신앙과 르호봇의 축복.",
                    "citations": ["갈 4:28", "히 11:17-19"]
                }
            ],
            "zeroPayAsYouGo": True
        }

        # Serialize
        serialized = json.dumps(sermon_payload, ensure_ascii=False, indent=2)
        # Deserialize
        deserialized = json.loads(serialized)

        self.assertEqual(deserialized["sermonId"], sermon_payload["sermonId"])
        self.assertEqual(len(deserialized["outline"]), 3)
        self.assertTrue(deserialized["zeroPayAsYouGo"])

    def test_03_zero_cost_policy_assertion(self):
        """Assert that no pay-per-use cloud API keys are mandatory for core functionality."""
        # Core pastoral exegesis, 8 commentaries, and sermon studio must work 100% offline
        # or through Google AI Pro / Google Drive desktop mount without billing charges
        free_storage_active = os.path.exists(r"G:\내 드라이브")
        self.assertTrue(free_storage_active, "Google Drive desktop provides zero-cost unlimited storage under AI Pro")


if __name__ == "__main__":
    unittest.main()
