"""
Strong's Concordance Dictionary Parser for Hebrew (OT) and Greek (NT).
"""

import json
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser

class StrongParser(BaseParser):
    """
    Parser for Strong's Hebrew and Greek dictionary data.
    """

    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parses JSON format Strong dictionary."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        entries = []
        raw_list = data if isinstance(data, list) else data.get("words", [])
        for item in raw_list:
            parsed = self.normalize_entry(item)
            if parsed:
                entries.append(parsed)
        return entries

    def normalize_entry(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalizes strong lexicon entry."""
        s_id = item.get("strong_id") or item.get("id") or item.get("strongs")
        if not s_id:
            return None
            
        s_id = s_id.upper().strip()
        lang = "HEBREW" if s_id.startswith("H") else ("GREEK" if s_id.startswith("G") else "HEBREW")

        lemma = item.get("lemma") or item.get("word") or ""
        translit = item.get("transliteration") or item.get("xlit") or ""
        pronunc = item.get("pronunciation") or item.get("pron") or ""
        pos = item.get("part_of_speech") or item.get("pos") or ""
        def_kr = item.get("definition_kr") or item.get("def_kr") or item.get("definition") or ""
        def_en = item.get("definition_en") or item.get("def_en") or ""
        root_id = item.get("root_id") or item.get("root")
        derivation = item.get("derivation") or ""
        occurrences = int(item.get("occurrence_count") or item.get("occurrences", 0))

        return {
            "strong_id": s_id,
            "language": lang,
            "lemma": lemma,
            "transliteration": translit,
            "pronunciation": pronunc,
            "part_of_speech": pos,
            "definition_kr": def_kr,
            "definition_en": def_en,
            "root_id": root_id,
            "derivation": derivation,
            "occurrence_count": occurrences
        }
