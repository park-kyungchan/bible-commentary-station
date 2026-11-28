"""Unit tests for Bible Commentary Station v4.0 Pipeline & Knowledge Graph Engine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bible_station import __version__
from bible_station.graph import build_scripture_graph, export_scripture_graph
from bible_station.pipeline import BuildContext, BuildPipeline


class _DummyStage:
    def __init__(self, name: str, run: bool = True):
        self.name = name
        self._run = run

    def should_run(self, ctx: BuildContext) -> bool:
        return self._run

    def execute(self, ctx: BuildContext):
        return {"ran": True, "stage": self.name}


class TestV4Architecture(unittest.TestCase):
    def test_version_is_v4(self):
        self.assertEqual(__version__, "4.0.0")

    def test_pipeline_executes_and_skips_cleanly(self):
        events = []
        pipeline = BuildPipeline(
            [_DummyStage("alpha", True), _DummyStage("beta", False), _DummyStage("gamma", True)],
            on_stage_complete=lambda r: events.append((r.name, r.status)),
        )
        ctx = BuildContext(
            db_path=Path("x.db"),
            krv_json=Path("krv.json"),
            web_data_dir=Path("web/data"),
            bundle_dir=Path("dist"),
        )
        results = pipeline.run(ctx)
        self.assertEqual([(r.name, r.status) for r in results], [("alpha", "ok"), ("beta", "skipped"), ("gamma", "ok")])
        self.assertEqual(events, [("alpha", "ok"), ("beta", "skipped"), ("gamma", "ok")])
        self.assertIn("alpha", ctx.metrics)
        self.assertNotIn("beta", ctx.metrics)

    def test_knowledge_graph_deterministic_export(self):
        repo_root = Path(__file__).resolve().parent.parent
        exegesis_path = repo_root / "web" / "data" / "exegesis.json"
        exegesis = json.loads(exegesis_path.read_text(encoding="utf-8"))
        g1 = build_scripture_graph(exegesis)
        g2 = build_scripture_graph(exegesis)
        self.assertEqual(g1, g2)
        self.assertEqual(g1["schemaVersion"], 4)
        self.assertGreater(g1["stats"]["nodeCount"], 50)
        self.assertGreater(g1["stats"]["edgeCount"], 80)
        self.assertGreaterEqual(len(g1["topHubs"]), 5)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "exegesis.json").write_text(exegesis_path.read_text(encoding="utf-8"), encoding="utf-8")
            stats = export_scripture_graph(tmp_dir)
            self.assertTrue((tmp_dir / "graph.json").exists())
            self.assertEqual(stats["nodeCount"], g1["stats"]["nodeCount"])


if __name__ == "__main__":
    unittest.main()
