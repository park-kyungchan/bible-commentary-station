"""
Cross Reference (관주) Parser based on Treasury of Scripture Knowledge (TSK).
Maps related scripture passages for pastoral cross-study.
"""

import json
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser, ScriptureRefNormalizer
try:
    from ..schema import calculate_verse_id
except (ImportError, ValueError):
    from schema import calculate_verse_id

class CrossRefParser(BaseParser):
    """
    Parser for Cross References (Treasury of Scripture Knowledge).
    """

    def __init__(self):
        self.ref_normalizer = ScriptureRefNormalizer()

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parses JSON, CSV, or TSV cross reference file."""
        if file_path.endswith('.json'):
            return self.parse_json(file_path)
        else:
            return self.parse_tsv(file_path)

    def parse_tsv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses TSV/CSV format:
        from_ref \t to_ref \t score \t type
        or
        from_verse_id \t to_verse_id \t score
        """
        refs = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t') if '\t' in line else line.split(',')
                if len(parts) >= 2:
                    from_raw = parts[0].strip()
                    to_raw = parts[1].strip()
                    score = float(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else 1.0
                    rel_type = parts[3].strip() if len(parts) > 3 and parts[3].strip() else "THEMATIC"
                    
                    from_id = int(from_raw) if from_raw.isdigit() else None
                    to_id = int(to_raw) if to_raw.isdigit() else None

                    if from_id is None:
                        f_res = self.ref_normalizer.parse_reference(from_raw)
                        if f_res:
                            from_id = f_res[3]
                            
                    if to_id is None:
                        t_res = self.ref_normalizer.parse_reference(to_raw)
                        if t_res:
                            to_id = t_res[3]

                    if from_id and to_id:
                        refs.append({
                            "from_verse_id": from_id,
                            "to_verse_id": to_id,
                            "score": score,
                            "relationship_type": rel_type,
                            "note": None
                        })
        return refs

    def parse_json(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        refs = []
        raw_list = data if isinstance(data, list) else data.get("cross_references", [])
        for item in raw_list:
            from_v = item.get("from_verse_id")
            to_v = item.get("to_verse_id")
            if not from_v or not to_v:
                if "from_ref" in item and "to_ref" in item:
                    f_res = self.ref_normalizer.parse_reference(item["from_ref"])
                    t_res = self.ref_normalizer.parse_reference(item["to_ref"])
                    if f_res and t_res:
                        from_v = f_res[3]
                        to_v = t_res[3]

            if from_v and to_v:
                refs.append({
                    "from_verse_id": int(from_v),
                    "to_verse_id": int(to_v),
                    "score": float(item.get("score", 1.0)),
                    "relationship_type": item.get("relationship_type", "THEMATIC"),
                    "note": item.get("note")
                })
        return refs
