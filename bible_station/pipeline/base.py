"""Composable, Observable Build Pipeline Core (Zero-Dependency)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol


@dataclass
class BuildContext:
    """Shared immutable-intent configuration and mutable artifact metrics across stages."""

    db_path: Path
    krv_json: Path
    web_data_dir: Path
    bundle_dir: Path
    export_web: bool = False
    export_bundle: bool = False
    export_graph: bool = True
    source_date_epoch: Optional[int] = None
    version: str = "4.0.0"
    builder: Any = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StageResult:
    name: str
    status: str  # "ok" | "skipped"
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)


class PipelineStage(Protocol):
    name: str

    def should_run(self, ctx: BuildContext) -> bool:
        ...

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        ...


HookFn = Callable[[StageResult], None]


class BuildPipeline:
    """Executes ordered PipelineStages with timing telemetry and lifecycle hooks."""

    def __init__(self, stages: List[PipelineStage], on_stage_complete: Optional[HookFn] = None) -> None:
        self.stages = list(stages)
        self.on_stage_complete = on_stage_complete

    def run(self, ctx: BuildContext) -> List[StageResult]:
        results: List[StageResult] = []
        for stage in self.stages:
            t0 = time.perf_counter()
            if not stage.should_run(ctx):
                res = StageResult(name=stage.name, status="skipped", duration_ms=0.0)
            else:
                details = stage.execute(ctx) or {}
                elapsed = round((time.perf_counter() - t0) * 1000.0, 2)
                ctx.metrics[stage.name] = details
                res = StageResult(name=stage.name, status="ok", duration_ms=elapsed, details=details)
            results.append(res)
            if self.on_stage_complete:
                self.on_stage_complete(res)
        return results
