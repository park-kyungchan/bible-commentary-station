# Korean Bible Data Sources (v3.0)

## Built-In Full Korean Bible Translations (Personal Pastoral Edition)

Per the owner's binding directive, this personal pastoral workstation bundles **all three full 66-book Korean translations** in the unified v3.0 compact schema (`web/data/<ver>/<OSIS>.json`, `web/data/search/<ver>.json`, SHA-256 verified in `web/data/manifest.json`):

1. **`nkrv` — 개역개정 (Default)**: 66 books, 1,189 chapters, 31,102 verses (0 empty verses; previously dropped `GEN 29:28` and `DAN 3:19` repaired). Personal pastoral study use.
2. **`krv` — 개역한글 (1961)**: 66 books, 1,189 chapters, 31,102 verses, generated deterministically from `data/raw/bible_1961_krv.json`.
   - KRV 1961 versification notes: `1SA` has 809 verses (`1SA 30:30` merges v.30–31) and `SNG` has 118 verses (`SNG 6:13–14` splits v.13), summing to 31,102 verses matching `bible_station/canon.py`.
   - Acquired from: <https://raw.githubusercontent.com/bluesaurel/Korean-Bible-1961-KRV/main/bible_1961_krv.json>.
   - Korean Bible Society KRV notice: “Korean Revised Version © Korean Bible Society 1961” (<https://bible.bskorea.or.kr/copyright_notice>, <https://www.bskorea.or.kr/bbs/board.php?bo_table=copyright_faq&wr_id=5>).
3. **`rnksv` — 새번역**: 66 books, 1,189 chapters, 31,102 verses, cleanly migrated from legacy mislabeled `web/data/nrsv/` (which is retired and blocked in CI/deploy).
   - All 3,234 inline `" / ㉠..."` footnote annotations (3,651 entries) are separated cleanly into structured top-level `footnotes` maps so verse prose stays clean for pulpit reading.
   - The 12 genuine Nestle-Aland/UBS critical-text variant omissions (`MAT 17:21`, `MAT 18:11`, `MAT 23:14`, `MRK 9:44`, `MRK 9:46`, `MRK 11:26`, `MRK 15:28`, `LUK 23:17`, `ACT 8:37`, `ACT 15:34`, `ACT 24:7`, `ACT 28:29`) are preserved explicitly as `""` and documented in `builder.DOCUMENTED_VARIANT_OMISSIONS`.

## Build, Validation & Allowlist Enforcement

`python3 -m bible_station.cli build --export-web --export-bundle` and `python3 -m bible_station.cli validate` generate and verify all 3 translations (`nkrv`, `krv`, `rnksv`), all 3 single-fetch search indices (`web/data/search/{nkrv,krv,rnksv}.json`), and all 203 SHA-256 checksums in `web/data/manifest.json`. Pastors may additionally import personal custom translation files locally into browser IndexedDB.
