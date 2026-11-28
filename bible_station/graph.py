"""Deterministic Scripture Knowledge Graph Builder (Zero-Dependency).

Transforms cross-references, thematic character chains, commentary coverage,
and Strong's lexical entries into a pre-computed spatial constellation graph
(`web/data/graph.json`) for instant offline rendering in the Constellation Lens.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .canon import BOOKS_BY_ID, BOOKS_BY_OSIS

CLUSTER_PALETTE = {
    "OT": "#D97706",
    "NT": "#2563EB",
    "CHAIN": "#059669",
    "LEXICON": "#9333EA",
}


def _decode_verse_id(vid: int) -> Tuple[int, int, int]:
    book_id = vid // 1_000_000
    rem = vid % 1_000_000
    chapter = rem // 1_000
    verse = rem % 1_000
    return book_id, chapter, verse


def build_scripture_graph(exegesis: Dict[str, Any]) -> Dict[str, Any]:
    """Build a deterministic, normalized spatial knowledge graph from exegesis data."""
    nodes_map: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    edge_seen: set[Tuple[str, str, str]] = set()
    degree: Dict[str, int] = defaultdict(int)

    def ensure_verse_node(
        osis: str,
        chapter: int,
        verse: int,
        *,
        verse_id: int | None = None,
        text: str = "",
        stage: str = "",
    ) -> str:
        book = BOOKS_BY_OSIS.get(osis)
        book_id = book.book_id if book else 1
        vid = verse_id or (book_id * 1_000_000 + chapter * 1_000 + verse)
        nid = f"v:{vid}"
        if nid not in nodes_map:
            testament = book.testament if book else "OT"
            nodes_map[nid] = {
                "id": nid,
                "kind": "verse",
                "verseId": vid,
                "osis": osis,
                "bookId": book_id,
                "bookName": book.name_kr if book else osis,
                "abbr": book.name_kr_abbr if book else osis,
                "chapter": chapter,
                "verse": verse,
                "label": f"{book.name_kr_abbr if book else osis} {chapter}:{verse}",
                "fullLabel": f"{book.name_kr if book else osis} {chapter}:{verse}",
                "testament": testament,
                "category": book.category if book else "",
                "cluster": testament,
                "excerpt": text[:160] if text else "",
                "stage": stage,
                "commentaryCount": 0,
            }
        else:
            if text and not nodes_map[nid]["excerpt"]:
                nodes_map[nid]["excerpt"] = text[:160]
            if stage and not nodes_map[nid]["stage"]:
                nodes_map[nid]["stage"] = stage
        return nid

    def add_edge(src: str, dst: str, rel: str, weight: float = 0.85, note: str = "") -> None:
        if src == dst:
            return
        key = (src, dst, rel)
        if key in edge_seen:
            return
        edge_seen.add(key)
        edges.append({
            "source": src,
            "target": dst,
            "relation": rel,
            "weight": round(float(weight), 3),
            "note": note[:180] if note else "",
        })
        degree[src] += 1
        degree[dst] += 1

    # 1. Count commentary density per verse
    comm_counts: Dict[int, int] = defaultdict(int)
    for c in exegesis.get("commentaries", []):
        vid = int(c.get("verse_start_id") or 0)
        if vid:
            comm_counts[vid] += 1

    # 2. Ingest cross-references
    cross_refs = exegesis.get("crossReferences", {})
    for from_vid_str, ref_list in sorted(cross_refs.items()):
        from_vid = int(from_vid_str)
        b_id, ch, vs = _decode_verse_id(from_vid)
        book = BOOKS_BY_ID.get(b_id)
        if not book:
            continue
        src_id = ensure_verse_node(book.osis_code, ch, vs, verse_id=from_vid)
        for ref in ref_list:
            to_osis = ref.get("to_osis")
            to_ch = int(ref.get("to_chapter") or 1)
            to_vs = int(ref.get("to_verse") or 1)
            to_vid = int(ref.get("to_verse_id") or 0) or None
            if not to_osis:
                continue
            dst_id = ensure_verse_node(
                to_osis,
                to_ch,
                to_vs,
                verse_id=to_vid,
                text=str(ref.get("to_text") or ""),
            )
            add_edge(
                src_id,
                dst_id,
                str(ref.get("relationship_type") or "THEMATIC"),
                float(ref.get("score") or 0.9),
                str(ref.get("note") or ""),
            )

    # 3. Ingest thematic chains as orbital constellations
    chains = exegesis.get("chains", {})
    chain_keys = sorted(chains.keys())
    for topic_key in chain_keys:
        chain = chains[topic_key]
        cid = f"c:{topic_key}"
        nodes_map[cid] = {
            "id": cid,
            "kind": "chain",
            "topicKey": topic_key,
            "label": chain.get("title", topic_key).split("(")[0].strip(),
            "fullLabel": chain.get("title", topic_key),
            "meaning": chain.get("meaning", ""),
            "excerpt": str(chain.get("summary") or "")[:200],
            "cluster": "CHAIN",
            "testament": "BOTH",
            "commentaryCount": 0,
        }
        prev_vnode = None
        for link in chain.get("links", []):
            osis = link.get("osis_code")
            ch = int(link.get("chapter") or 1)
            vs = int(link.get("verse") or 1)
            if not osis:
                continue
            vnid = ensure_verse_node(
                osis,
                ch,
                vs,
                text=str(link.get("verse_text") or ""),
                stage=str(link.get("stage_label") or ""),
            )
            add_edge(cid, vnid, "CHAIN_MEMBER", 0.95, str(link.get("sermon_point") or ""))
            if prev_vnode:
                add_edge(prev_vnode, vnid, "CHAIN_STEP", 0.78, str(link.get("stage_label") or ""))
            prev_vnode = vnid

    # 4. Compute deterministic radial constellation layout [0..1000, 0..700]
    cx, cy = 500.0, 350.0
    chain_nodes = sorted([n for n in nodes_map.values() if n["kind"] == "chain"], key=lambda x: x["id"])
    ot_nodes = sorted(
        [n for n in nodes_map.values() if n["kind"] == "verse" and n["testament"] == "OT"],
        key=lambda x: (x["bookId"], x["chapter"], x["verse"]),
    )
    nt_nodes = sorted(
        [n for n in nodes_map.values() if n["kind"] == "verse" and n["testament"] == "NT"],
        key=lambda x: (x["bookId"], x["chapter"], x["verse"]),
    )

    for i, node in enumerate(chain_nodes):
        angle = (2.0 * math.pi * i) / max(len(chain_nodes), 1) - math.pi / 2.0
        node["x"] = round(cx + 128.0 * math.cos(angle), 2)
        node["y"] = round(cy + 108.0 * math.sin(angle), 2)

    for i, node in enumerate(ot_nodes):
        t = (i + 0.5) / max(len(ot_nodes), 1)
        angle = math.pi * 0.62 + t * math.pi * 0.76
        radius_x = 340.0 + (i % 3) * 44.0
        radius_y = 240.0 + ((i + 1) % 3) * 32.0
        node["x"] = round(cx + radius_x * math.cos(angle), 2)
        node["y"] = round(cy + radius_y * math.sin(angle), 2)

    for i, node in enumerate(nt_nodes):
        t = (i + 0.5) / max(len(nt_nodes), 1)
        angle = -math.pi * 0.38 + t * math.pi * 0.76
        radius_x = 340.0 + (i % 3) * 44.0
        radius_y = 240.0 + ((i + 1) % 3) * 32.0
        node["x"] = round(cx + radius_x * math.cos(angle), 2)
        node["y"] = round(cy + radius_y * math.sin(angle), 2)

    max_deg = max(degree.values(), default=1)
    nodes_list = sorted(nodes_map.values(), key=lambda x: x["id"])
    for node in nodes_list:
        deg = degree.get(node["id"], 0)
        node["degree"] = deg
        node["centrality"] = round(deg / max_deg, 3) if max_deg else 0.0
        if node["kind"] == "verse":
            node["commentaryCount"] = comm_counts.get(node["verseId"], 0)

    top_hubs = sorted(
        [n for n in nodes_list if n["kind"] == "verse"],
        key=lambda n: (-n["degree"], -n["commentaryCount"], n["verseId"]),
    )[:10]

    return {
        "schemaVersion": 4,
        "viewport": {"width": 1000, "height": 700, "centerX": cx, "centerY": cy},
        "clusters": [
            {"id": "CHAIN", "label": "성경 인물·주제 축", "color": CLUSTER_PALETTE["CHAIN"]},
            {"id": "OT", "label": "구약 성경", "color": CLUSTER_PALETTE["OT"]},
            {"id": "NT", "label": "신약 성경", "color": CLUSTER_PALETTE["NT"]},
        ],
        "nodes": nodes_list,
        "edges": edges,
        "topHubs": [
            {"id": n["id"], "label": n["fullLabel"], "osis": n["osis"], "chapter": n["chapter"], "verse": n["verse"], "degree": n["degree"]}
            for n in top_hubs
        ],
        "stats": {
            "nodeCount": len(nodes_list),
            "verseNodeCount": len(ot_nodes) + len(nt_nodes),
            "chainNodeCount": len(chain_nodes),
            "edgeCount": len(edges),
        },
    }


def export_scripture_graph(web_data_dir: Path) -> Dict[str, Any]:
    """Read `exegesis.json` from web_data_dir and write deterministic `graph.json`."""
    exegesis_path = web_data_dir / "exegesis.json"
    if not exegesis_path.exists():
        raise FileNotFoundError(f"exegesis.json not found at {exegesis_path}")
    exegesis = json.loads(exegesis_path.read_text(encoding="utf-8"))
    graph = build_scripture_graph(exegesis)
    out_path = web_data_dir / "graph.json"
    out_path.write_text(
        json.dumps(graph, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    return graph["stats"]
