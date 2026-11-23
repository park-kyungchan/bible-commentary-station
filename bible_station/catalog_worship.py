"""
Korean Worship, Liturgy & Responsive Reading Catalog (v3.0):
- All 645 21st-Century New Hymns (새찬송가) reconciled 100% with hymns_645.json,
  deduplicated legacy Unified Hymnal (old) numbers, and validated Drive IDs.
- All 137 21st-Century Responsive Readings (21세기 새교독문, #1~#137) with exact
  KRV chapter-bounds clamping and structured verse-reference segments (including #2
  Psalm 2 backfill and #88~#137 seasonal/liturgical readings extracted from Drive PPTs).
- Verified Korean Liturgies (사도신경 새번역/전통, 주기도문 새번역/전통, 성찬 예식, 축도 3종).
- 5 PII-free Korean Protestant Worship Order Templates.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .canon import BOOKS_BY_OSIS, get_chapter_verse_count

_DRIVE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,64}$")
_VALID_ROLES = frozenset({"leader", "congregation", "unison"})

_BOOK_PREFIX_OSIS = {
    "시편": "PSA",
    "잠언": "PRO",
    "이사야": "ISA",
    "마태복음": "MAT",
    "요한복음": "JHN",
    "고린도후서": "2CO",
    "에베소서": "EPH",
    "빌립보서": "PHP",
    "히브리서": "HEB",
    "요한1서": "1JN",
    "요한계시록": "REV",
}


def _require_json(filename: str) -> Any:
    path = Path(__file__).resolve().parent / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required worship catalog asset missing from package: {path} "
            "(ensure [tool.setuptools.package-data] bundles bible_station/*.json)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_drive_id(drive_id: str, context: str) -> str:
    if not drive_id:
        return ""
    if not _DRIVE_ID_RE.match(drive_id):
        raise ValueError(f"Invalid Google Drive ID {drive_id!r} for {context}")
    return drive_id


def _drive_urls(drive_id: str, context: str) -> Tuple[str, str, str]:
    valid_id = _validate_drive_id(drive_id, context)
    if not valid_id:
        return "", "", ""
    return (
        valid_id,
        f"https://drive.google.com/file/d/{valid_id}/preview",
        f"https://drive.google.com/file/d/{valid_id}/view?usp=drivesdk",
    )


def _h(num: int, old: int, group: str, osis: str, ch: int, vs: int, label: str) -> Dict[str, Any]:
    return {
        "num": num,
        "old": old,
        "category": group,
        "ref": {"osis": osis, "ch": ch, "vs": vs, "label": label},
    }


def _classify_hymn_21c(num: int) -> Tuple[str, str, Dict[str, Any]]:
    """Map 21st-Century New Hymnal (1~645) number to official section, theme group, and default scripture."""
    if 1 <= num <= 7:
        return ("송영", "주일경배", {"osis": "PSA", "ch": 100, "vs": 1, "label": "시편 100:1"})
    if 8 <= num <= 41:
        return ("경배·찬양", "주일경배", {"osis": "PSA", "ch": 95, "vs": 1, "label": "시편 95:1"})
    if 42 <= num <= 62:
        return ("주일·예배", "주일경배", {"osis": "PSA", "ch": 118, "vs": 24, "label": "시편 118:24"})
    if 63 <= num <= 79:
        return ("창조주 하나님", "주일경배", {"osis": "GEN", "ch": 1, "vs": 1, "label": "창세기 1:1"})
    if 80 <= num <= 100:
        return ("예수 그리스도", "은혜·사랑", {"osis": "JHN", "ch": 1, "vs": 14, "label": "요한복음 1:14"})
    if 101 <= num <= 129:
        return ("대림·성탄", "절기·특별", {"osis": "LUK", "ch": 2, "vs": 14, "label": "누가복음 2:14"})
    if 130 <= num <= 158:
        return ("고난·십자가", "절기·특별", {"osis": "ISA", "ch": 53, "vs": 5, "label": "이사야 53:5"})
    if 159 <= num <= 181:
        return ("부활·재림", "절기·특별", {"osis": "1CO", "ch": 15, "vs": 20, "label": "고린도전서 15:20"})
    if 182 <= num <= 198:
        return ("성령", "절기·특별", {"osis": "ACT", "ch": 2, "vs": 4, "label": "사도행전 2:4"})
    if 199 <= num <= 206:
        return ("성경", "은혜·사랑", {"osis": "PSA", "ch": 119, "vs": 105, "label": "시편 119:105"})
    if 207 <= num <= 249:
        return ("교회·성례·헌신", "감사·헌신", {"osis": "EPH", "ch": 2, "vs": 20, "label": "에베소서 2:20"})
    if 250 <= num <= 300:
        return ("회개·속죄·구원", "은혜·사랑", {"osis": "ROM", "ch": 8, "vs": 1, "label": "로마서 8:1"})
    if 301 <= num <= 335:
        return ("은혜·감사·소명", "은혜·사랑", {"osis": "EPH", "ch": 2, "vs": 8, "label": "에베소서 2:8"})
    if 336 <= num <= 369:
        return ("기도·간구·시련", "기도·위로", {"osis": "PHP", "ch": 4, "vs": 6, "label": "빌립보서 4:6"})
    if 370 <= num <= 450:
        return ("위로·인도·평안", "기도·위로", {"osis": "PSA", "ch": 23, "vs": 1, "label": "시편 23:1"})
    if 451 <= num <= 519:
        return ("제자도·전도·사명", "감사·헌신", {"osis": "MAT", "ch": 28, "vs": 19, "label": "마태복음 28:19"})
    if 520 <= num <= 549:
        return ("믿음·소망·천국", "장례·파송", {"osis": "HEB", "ch": 11, "vs": 1, "label": "히브리서 11:1"})
    if 550 <= num <= 599:
        return ("절기·가정·감사", "절기·특별", {"osis": "PSA", "ch": 100, "vs": 4, "label": "시편 100:4"})
    if 600 <= num <= 619:
        return ("장례·추도·파송", "장례·파송", {"osis": "REV", "ch": 21, "vs": 4, "label": "요한계시록 21:4"})
    return ("예전·기도송·아멘", "주일경배", {"osis": "PSA", "ch": 150, "vs": 6, "label": "시편 150:6"})


# Curated scripture ranges aligned to official 21st-Century Responsive Reading numbers (#1..#87)
_CURATED_RR_META: Dict[int, Tuple[str, str, int, int]] = {
    1: ("주일예배", "주일예배", 1, 6),       # 시편 1편
    2: ("주일예배", "주일예배", 1, 12),      # 시편 2편 (backfill)
    5: ("주일예배", "주일예배", 1, 9),       # 시편 8편
    10: ("주일·위로", "위로·기도", 1, 11),   # 시편 16편
    12: ("주일예배", "주일예배", 1, 14),     # 시편 19편
    13: ("주일·위로", "위로·기도", 1, 6),    # 시편 23편
    14: ("주일예배", "주일예배", 1, 10),     # 시편 24편
    15: ("주일·위로", "위로·기도", 1, 14),   # 시편 27편
    21: ("감사·찬양", "감사·찬양", 1, 10),   # 시편 34편
    22: ("주일·위로", "위로·기도", 1, 9),    # 시편 37편
    24: ("주일·위로", "위로·기도", 1, 11),   # 시편 46편
    27: ("참회·사순절", "절기·특별", 1, 12), # 시편 51편
    28: ("기도·묵상", "위로·기도", 1, 8),    # 시편 63편
    29: ("추수·감사", "감사·찬양", 1, 13),   # 시편 65편
    30: ("선교·감사", "감사·찬양", 1, 7),    # 시편 67편
    35: ("주일예배", "주일예배", 1, 12),     # 시편 84편
    36: ("송구영신·장례", "절기·특별", 1, 12), # 시편 90편
    37: ("주일·위로", "위로·기도", 1, 12),   # 시편 91편
    39: ("주일예배", "주일예배", 1, 7),      # 시편 95편
    40: ("감사·찬양", "감사·찬양", 1, 9),    # 시편 96편
    44: ("추수감사·주일", "감사·찬양", 1, 5), # 시편 100편
    45: ("감사·찬양", "감사·찬양", 1, 12),   # 시편 103편
    46: ("창조·찬양", "감사·찬양", 1, 12),   # 시편 104편
    51: ("감사·부활", "감사·찬양", 1, 14),   # 시편 118편
    52: ("말씀·주일", "주일예배", 105, 112), # 시편 119편
    53: ("주일·위로", "위로·기도", 1, 8),    # 시편 121편
    54: ("추수감사·위로", "감사·찬양", 1, 6), # 시편 126편
    55: ("가정·어린이주일", "절기·특별", 1, 5), # 시편 127편
    57: ("기도·참회", "위로·기도", 1, 8),    # 시편 130편
    58: ("성도의 교제", "주일예배", 1, 3),   # 시편 133편
    60: ("주일예배", "주일예배", 1, 12),     # 시편 139편
    63: ("감사·찬양", "감사·찬양", 1, 13),   # 시편 145편
    66: ("감사·찬양", "감사·찬양", 1, 6),    # 시편 150편
    67: ("지혜·신뢰", "주일예배", 1, 12),    # 잠언 3장
    68: ("신년·위로", "위로·기도", 1, 11),   # 이사야 40장(1)
    69: ("신년·위로", "위로·기도", 27, 31),  # 이사야 40장(2)
    74: ("팔복·주일", "주일예배", 1, 12),    # 마태복음 5장
    77: ("복음·구원", "주일예배", 1, 16),    # 요한복음 3장
    78: ("위로·소망", "위로·기도", 1, 14),   # 요한복음 14장
    82: ("고난·헌신", "절기·특별", 5, 11),   # 빌립보서 2장
    83: ("기도·평안", "위로·기도", 4, 13),   # 빌립보서 4장
    84: ("믿음·소망", "주일예배", 1, 10),    # 히브리서 11장
    85: ("사랑·교제", "주일예배", 7, 16),    # 요한1서 4장
    87: ("장례·천국소망", "절기·특별", 1, 7), # 요한계시록 21장
}


def _build_chapter_segments(osis: str, ch: int, start_vs: int, end_vs: int) -> List[Dict[str, Any]]:
    """Build alternating Leader / Congregation / final Unison segments for a chapter range."""
    segments: List[Dict[str, Any]] = []
    verses = list(range(start_vs, end_vs + 1))
    for idx, vs in enumerate(verses):
        if len(verses) > 1 and idx == len(verses) - 1:
            role = "unison"
        else:
            role = "leader" if idx % 2 == 0 else "congregation"
        segments.append({
            "role": role,
            "osis": osis,
            "ch": ch,
            "start_vs": vs,
            "end_vs": vs,
        })
    return segments


def _validate_segments(num: int, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not segments:
        raise ValueError(f"Responsive reading #{num} has empty segments[]")
    cleaned: List[Dict[str, Any]] = []
    for idx, seg in enumerate(segments):
        role = seg.get("role")
        osis = seg.get("osis")
        ch = int(seg.get("ch", 0))
        s_vs = int(seg.get("start_vs", 0))
        e_vs = int(seg.get("end_vs", 0))
        if role not in _VALID_ROLES:
            raise ValueError(f"RR #{num} seg[{idx}] invalid role: {role!r}")
        if osis not in BOOKS_BY_OSIS:
            raise ValueError(f"RR #{num} seg[{idx}] invalid osis: {osis!r}")
        max_vs = get_chapter_verse_count(osis, ch)
        if max_vs is None or not (1 <= s_vs <= e_vs <= max_vs):
            raise ValueError(
                f"RR #{num} seg[{idx}] out-of-bounds coordinate {osis} {ch}:{s_vs}-{e_vs} (max={max_vs})"
            )
        entry: Dict[str, Any] = {
            "role": role,
            "osis": osis,
            "ch": ch,
            "start_vs": s_vs,
            "end_vs": e_vs,
        }
        if seg.get("customText"):
            entry["customText"] = str(seg["customText"])
        cleaned.append(entry)
    return cleaned


def _merge_137_responsive_readings() -> List[Dict[str, Any]]:
    drive_map: Dict[str, Dict[str, str]] = _require_json("responsive_drive_ppts.json")
    sequences_map: Dict[str, List[Dict[str, Any]]] = _require_json("responsive_sequences.json")

    out: List[Dict[str, Any]] = []
    for num in range(1, 138):
        d = drive_map.get(str(num))
        if d:
            raw_name = re.sub(r"\.pptx?$", "", d["file"], flags=re.I)
            raw_title = re.sub(r"^\d+번\s*-\s*", "", raw_name).replace("_", " ").strip()
            drive_id, ppt_preview, ppt_view = _drive_urls(d["id"], f"responsive #{num}")
        else:
            raw_title = "시편 2편" if num == 2 else f"교독문 {num}번"
            drive_id, ppt_preview, ppt_view = "", "", ""

        osis, ch, start_vs, end_vs = "", 0, 0, 0
        m = re.match(
            r"^(시편|잠언|이사야|마태복음|요한복음|고린도후서|에베소서|빌립보서|히브리서|요한1서|요한계시록)\s*(\d+)",
            raw_title,
        )
        if m:
            osis = _BOOK_PREFIX_OSIS[m.group(1)]
            ch = int(m.group(2))
            max_vs = get_chapter_verse_count(osis, ch)
            assert max_vs is not None, f"Invalid chapter {osis} {ch} for RR #{num}"
            if "(2)" in raw_title:
                start_vs, end_vs = min(13, max_vs), min(31, max_vs)
            else:
                start_vs, end_vs = 1, min(12, max_vs)

        # Classify season & group cleanly
        if num <= 66:
            season, group = "시편 교독", "주일예배"
            if any(k in raw_title for k in ("23편", "27편", "37편", "46편", "63편", "91편", "121편", "130편")):
                group = "위로·기도"
            elif any(
                k in raw_title
                for k in (
                    "34편", "65편", "67편", "96편", "98편", "100편", "103편",
                    "104편", "118편", "136편", "145편", "148편", "149편", "150편",
                )
            ):
                group = "감사·찬양"
        elif num <= 87:
            season, group = "구·신약 교독", "주일예배"
        else:
            season, group = "절기·예식", "절기·특별"
            if "감사" in raw_title:
                group = "감사·찬양"

        # Apply curated metadata aligned to official numbering, clamped strictly to actual chapter bounds
        if num in _CURATED_RR_META and osis:
            cur_season, cur_group, cur_s, cur_e = _CURATED_RR_META[num]
            max_vs = get_chapter_verse_count(osis, ch)
            assert max_vs is not None
            season, group = cur_season, cur_group
            start_vs = max(1, min(cur_s, max_vs))
            end_vs = max(start_vs, min(cur_e, max_vs))

        # Build / validate structured segments (R-WR-03: 0 offline-empty readings across #1..#137)
        if str(num) in sequences_map:
            segments = _validate_segments(num, sequences_map[str(num)])
        elif osis and ch > 0:
            segments = _validate_segments(num, _build_chapter_segments(osis, ch, start_vs, end_vs))
        else:
            raise ValueError(f"Responsive reading #{num} ({raw_title}) missing both osis/ch and responsive_sequences entry")

        out.append({
            "num": num,
            "title": raw_title,
            "season": season,
            "group": group,
            "osis": osis,
            "ch": ch,
            "start_vs": start_vs,
            "end_vs": end_vs,
            "segments": segments,
            "driveId": drive_id,
            "pptPreviewUrl": ppt_preview,
            "pptViewUrl": ppt_view,
        })
    return out


def build_expanded_worship_catalog() -> Dict[str, Any]:
    # 100 curated scripture-linked hymns (titles resolved from hymns_645.json SSOT; zero duplicate old IDs)
    curated_hymns: List[Dict[str, Any]] = [
        # 주일경배 (20)
        _h(1, 1, "주일경배", "PSA", 100, 1, "시편 100:1"),
        _h(2, 2, "주일경배", "MAT", 28, 19, "마태복음 28:19"),
        _h(8, 9, "주일경배", "ISA", 6, 3, "이사야 6:3"),
        _h(9, 53, "주일경배", "PSA", 19, 1, "시편 19:1"),
        _h(10, 34, "주일경배", "PSA", 95, 1, "시편 95:1"),
        _h(15, 15, "주일경배", "PSA", 36, 5, "시편 36:5"),
        _h(20, 41, "주일경배", "PSA", 24, 7, "시편 24:7"),
        _h(21, 21, "주일경배", "PSA", 103, 1, "시편 103:1"),
        _h(23, 23, "주일경배", "PSA", 51, 15, "시편 51:15"),
        _h(25, 25, "주일경배", "REV", 4, 10, "요한계시록 4:10"),
        _h(27, 27, "주일경배", "REV", 5, 12, "요한계시록 5:12"),
        _h(29, 29, "주일경배", "PSA", 150, 1, "시편 150:1"),
        _h(31, 10, "주일경배", "PSA", 96, 1, "시편 96:1"),
        _h(32, 32, "주일경배", "COL", 1, 16, "골로새서 1:16"),
        _h(35, 35, "주일경배", "PSA", 145, 1, "시편 145:1"),
        _h(43, 43, "주일경배", "PSA", 118, 24, "시편 118:24"),
        _h(64, 13, "주일경배", "PSA", 100, 2, "시편 100:2"),
        _h(67, 31, "주일경배", "PSA", 104, 1, "시편 104:1"),
        _h(70, 38, "주일경배", "PSA", 46, 1, "시편 46:1"),
        _h(79, 40, "주일경배", "GEN", 1, 1, "창세기 1:1"),

        # 은혜·사랑 (22)
        _h(28, 28, "은혜·사랑", "1SA", 7, 12, "사무엘상 7:12"),
        _h(85, 85, "은혜·사랑", "PHP", 3, 8, "빌립보서 3:8"),
        _h(88, 88, "은혜·사랑", "SNG", 2, 1, "아가 2:1"),
        _h(90, 90, "은혜·사랑", "1JN", 4, 19, "요한일서 4:19"),
        _h(91, 91, "은혜·사랑", "ACT", 4, 12, "사도행전 4:12"),
        _h(93, 93, "은혜·사랑", "PHP", 4, 13, "빌립보서 4:13"),
        _h(95, 82, "은혜·사랑", "PSA", 16, 11, "시편 16:11"),
        _h(96, 94, "은혜·사랑", "MAT", 16, 16, "마태복음 16:16"),
        _h(191, 427, "은혜·사랑", "GAL", 5, 22, "갈라디아서 5:22"),
        _h(200, 235, "은혜·사랑", "PSA", 119, 103, "시편 119:103"),
        _h(204, 379, "은혜·사랑", "MAT", 7, 24, "마태복음 7:24"),
        _h(252, 184, "은혜·사랑", "1JN", 1, 7, "요한일서 1:7"),
        _h(258, 190, "은혜·사랑", "ZEC", 13, 1, "스가랴 13:1"),
        _h(268, 202, "은혜·사랑", "ROM", 8, 2, "로마서 8:2"),
        _h(288, 204, "은혜·사랑", "JHN", 3, 16, "요한복음 3:16"),
        _h(301, 460, "은혜·사랑", "1CO", 15, 10, "고린도전서 15:10"),
        _h(304, 404, "은혜·사랑", "ROM", 8, 39, "로마서 8:39"),
        _h(305, 405, "은혜·사랑", "EPH", 2, 8, "에베소서 2:8"),
        _h(310, 410, "은혜·사랑", "2TI", 1, 12, "디모데후서 1:12"),
        _h(410, 467, "은혜·사랑", "PSA", 40, 3, "시편 40:3"),
        _h(412, 469, "은혜·사랑", "JHN", 14, 27, "요한복음 14:27"),
        _h(542, 340, "은혜·사랑", "HEB", 11, 1, "히브리서 11:1"),

        # 기도·위로 (20)
        _h(336, 383, "기도·위로", "ROM", 8, 35, "로마서 8:35"),
        _h(337, 363, "기도·위로", "1PE", 5, 7, "베드로전서 5:7"),
        _h(338, 364, "기도·위로", "GEN", 28, 11, "창세기 28:11"),
        _h(342, 395, "기도·위로", "1CO", 10, 13, "고린도전서 10:13"),
        _h(361, 480, "기도·위로", "1TH", 5, 17, "데살로니가전서 5:17"),
        _h(363, 484, "기도·위로", "PSA", 130, 1, "시편 130:1"),
        _h(364, 482, "기도·위로", "PHP", 4, 6, "빌립보서 4:6"),
        _h(365, 485, "기도·위로", "JHN", 14, 1, "요한복음 14:1"),
        _h(369, 487, "기도·위로", "MAT", 11, 28, "마태복음 11:28"),
        _h(370, 455, "기도·위로", "ROM", 8, 28, "로마서 8:28"),
        _h(380, 424, "기도·위로", "GAL", 2, 20, "갈라디아서 2:20"),
        _h(382, 432, "기도·위로", "ISA", 41, 10, "이사야 41:10"),
        _h(384, 434, "기도·위로", "PSA", 23, 1, "시편 23:1"),
        _h(390, 446, "기도·위로", "PSA", 23, 3, "시편 23:3"),
        _h(391, 447, "기도·위로", "PSA", 18, 2, "시편 18:2"),
        _h(405, 458, "기도·위로", "DEU", 33, 27, "신명기 33:27"),
        _h(413, 470, "기도·위로", "PSA", 23, 4, "시편 23:4"),
        _h(430, 456, "기도·위로", "GEN", 22, 2, "창세기 22:2"),
        _h(435, 492, "기도·위로", "PSA", 73, 26, "시편 73:26"),
        _h(438, 495, "기도·위로", "PSA", 121, 1, "시편 121:1"),

        # 감사·헌신 (16)
        _h(94, 102, "감사·헌신", "PHP", 3, 8, "빌립보서 3:8"),
        _h(212, 347, "감사·헌신", "JHN", 12, 26, "요한복음 12:26"),
        _h(213, 348, "감사·헌신", "ROM", 12, 1, "로마서 12:1"),
        _h(214, 349, "감사·헌신", "PSA", 121, 2, "시편 121:2"),
        _h(311, 341, "감사·헌신", "2CO", 5, 15, "고린도후서 5:15"),
        _h(314, 511, "감사·헌신", "JHN", 21, 15, "요한복음 21:15"),
        _h(320, 350, "감사·헌신", "PSA", 51, 10, "시편 51:10"),
        _h(323, 355, "감사·헌신", "ISA", 6, 8, "이사야 6:8"),
        _h(325, 359, "감사·헌신", "JOS", 1, 9, "여호수아 1:9"),
        _h(429, 489, "감사·헌신", "1TH", 5, 18, "데살로니가전서 5:18"),
        _h(449, 377, "감사·헌신", "JHN", 14, 6, "요한복음 14:6"),
        _h(455, 507, "감사·헌신", "PHP", 2, 5, "빌립보서 2:5"),
        _h(569, 453, "감사·헌신", "JHN", 10, 11, "요한복음 10:11"),
        _h(587, 306, "감사·헌신", "PSA", 100, 4, "시편 100:4"),
        _h(589, 308, "감사·헌신", "PSA", 126, 5, "시편 126:5"),
        _h(592, 309, "감사·헌신", "PSA", 65, 11, "시편 65:11"),

        # 절기·특별 (14)
        _h(104, 104, "절기·특별", "MAT", 1, 23, "마태복음 1:23"),
        _h(109, 109, "절기·특별", "LUK", 2, 7, "누가복음 2:7"),
        _h(115, 115, "절기·특별", "PSA", 98, 4, "시편 98:4"),
        _h(122, 122, "절기·특별", "LUK", 2, 15, "누가복음 2:15"),
        _h(126, 126, "절기·특별", "LUK", 2, 14, "누가복음 2:14"),
        _h(144, 144, "절기·특별", "ISA", 53, 5, "이사야 53:5"),
        _h(147, 136, "절기·특별", "LUK", 23, 33, "누가복음 23:33"),
        _h(150, 135, "절기·특별", "GAL", 6, 14, "갈라디아서 6:14"),
        _h(151, 138, "절기·특별", "ISA", 53, 5, "이사야 53:5"),
        _h(160, 150, "절기·특별", "MAT", 28, 6, "마태복음 28:6"),
        _h(165, 151, "절기·특별", "1CO", 15, 20, "고린도전서 15:20"),
        _h(184, 173, "절기·특별", "ACT", 2, 3, "사도행전 2:3"),
        _h(552, 358, "절기·특별", "PSA", 90, 12, "시편 90:12"),
        _h(559, 305, "절기·특별", "PSA", 127, 1, "시편 127:1"),

        # 장례·파송 (8)
        _h(480, 531, "장례·파송", "REV", 21, 1, "요한계시록 21:1"),
        _h(491, 543, "장례·파송", "PHP", 3, 14, "빌립보서 3:14"),
        _h(493, 544, "장례·파송", "JHN", 14, 2, "요한복음 14:2"),
        _h(505, 268, "장례·파송", "MAT", 28, 19, "마태복음 28:19"),
        _h(606, 532, "장례·파송", "REV", 22, 5, "요한계시록 22:5"),
        _h(608, 534, "장례·파송", "REV", 21, 4, "요한계시록 21:4"),
        _h(619, 419, "장례·파송", "NUM", 6, 24, "민수기 6:24"),
        _h(620, 420, "장례·파송", "1TH", 5, 23, "데살로니가전서 5:23"),
    ]

    titles_map: Dict[str, str] = _require_json("hymns_645.json")
    hymns_ppt_map: Dict[str, Dict[str, str]] = _require_json("hymns_drive_ppts.json")
    liturgies: List[Dict[str, Any]] = _require_json("catalog_liturgy.json")
    templates: List[Dict[str, Any]] = _require_json("worship_templates.json")
    ccm_raw: List[Dict[str, Any]] = _require_json("ccm_drive_ppts.json")

    ccm_items: List[Dict[str, Any]] = []
    for entry in ccm_raw:
        cid = str(entry["id"])
        drive_id, ppt_preview, ppt_view = _drive_urls(str(entry.get("driveId", "")), f"ccm {cid}")
        ccm_items.append({
            "id": cid,
            "title": str(entry["title"]),
            "category": str(entry.get("category", "경배·찬양")),
            "driveId": drive_id,
            "pptPreviewUrl": ppt_preview,
            "pptViewUrl": ppt_view,
        })

    curated_by_num = {h["num"]: h for h in curated_hymns}
    seen_old: set[int] = set()
    full_hymns: List[Dict[str, Any]] = []

    for num in range(1, 646):
        title = titles_map.get(str(num))
        if not title:
            raise ValueError(f"Missing hymn title for #{num} in hymns_645.json")
        section, default_group, default_ref = _classify_hymn_21c(num)
        hp = hymns_ppt_map.get(str(num))
        drive_id, ppt_preview, ppt_view = _drive_urls(hp["id"] if hp else "", f"hymn #{num}")

        if num in curated_by_num:
            cur = curated_by_num[num]
            old_num = cur["old"]
            if old_num > 0:
                if old_num in seen_old:
                    raise ValueError(f"Duplicate legacy Unified Hymnal number old={old_num} on hymn #{num}")
                seen_old.add(old_num)
            full_hymns.append({
                "num": num,
                "old": old_num,
                "title": title,
                "category": cur["category"],
                "section": section,
                "featured": True,
                "ref": cur["ref"],
                "driveId": drive_id,
                "pptPreviewUrl": ppt_preview,
                "pptViewUrl": ppt_view,
            })
        else:
            full_hymns.append({
                "num": num,
                "old": 0,
                "title": title,
                "category": default_group,
                "section": section,
                "featured": False,
                "ref": default_ref,
                "driveId": drive_id,
                "pptPreviewUrl": ppt_preview,
                "pptViewUrl": ppt_view,
            })

    return {
        "hymnGroups": ["전체", "주일경배", "은혜·사랑", "기도·위로", "감사·헌신", "절기·특별", "장례·파송"],
        "responsiveGroups": ["전체", "주일예배", "위로·기도", "감사·찬양", "절기·특별"],
        "ccmGroups": ["전체", "경배·찬양", "은혜·사랑", "기도·위로", "헌신·결단", "절기·파송"],
        "hymns": full_hymns,
        "responsiveReadings": _merge_137_responsive_readings(),
        "liturgies": liturgies,
        "templates": templates,
        "ccm": ccm_items,
    }


get_worship_catalog = build_expanded_worship_catalog
