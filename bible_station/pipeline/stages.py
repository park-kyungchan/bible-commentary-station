"""Discrete, Testable Build Pipeline Stages for Bible Commentary Station v4.0."""

from __future__ import annotations

from typing import Any, Dict, List

from ..builder import export_zero_cost_bundle
from ..graph import export_scripture_graph
from .base import BuildContext, PipelineStage


class SchemaInitStage:
    name = "schema_init"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        ctx.builder.initialize_schema()
        return {"initialized": True}


class MasterSeedStage:
    name = "master_seed"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        ctx.builder.seed_master_data()
        return {"seeded": True}


class KrvIngestStage:
    name = "krv_ingest"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None and ctx.krv_json.exists()

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        count = ctx.builder.ingest_full_krv(ctx.krv_json)
        return {"verses_ingested": count}


class ExegesisIngestStage:
    name = "exegesis_ingest"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        return dict(ctx.builder.ingest_curated_exegesis())


class OptimizeDbStage:
    name = "optimize_db"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        ctx.builder.optimize()
        return dict(ctx.builder.get_table_counts())


class WebExportStage:
    name = "web_export"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.builder is not None and ctx.export_web

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        return dict(
            ctx.builder.export_web_chunks(
                ctx.web_data_dir,
                source_date_epoch=ctx.source_date_epoch,
            )
        )


class KnowledgeGraphStage:
    name = "knowledge_graph"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.export_graph and (ctx.web_data_dir / "exegesis.json").exists()

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        return export_scripture_graph(ctx.web_data_dir)


class ZeroCostBundleStage:
    name = "zero_cost_bundle"

    def should_run(self, ctx: BuildContext) -> bool:
        return ctx.export_bundle and ctx.db_path.exists()

    def execute(self, ctx: BuildContext) -> Dict[str, Any]:
        return dict(export_zero_cost_bundle(ctx.db_path, ctx.bundle_dir, version=ctx.version))


def default_db_stages() -> List[PipelineStage]:
    return [
        SchemaInitStage(),
        MasterSeedStage(),
        KrvIngestStage(),
        ExegesisIngestStage(),
        OptimizeDbStage(),
        WebExportStage(),
        KnowledgeGraphStage(),
    ]
