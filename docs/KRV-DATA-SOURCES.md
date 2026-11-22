# KRV Data Sources

## Source and Transformation (v3.0)

- **Edition**: Korean Revised Version (1961, 개역한글판), published by the Korean Bible Society.
- **Canonical raw corpus**: `data/raw/bible_1961_krv.json` (66 books, 1,189 chapters, 31,102 verses; 0 empty verses, 0 replacement characters).
- **KRV 1961 versification notes**: `1SA` has 809 verses (`1SA 30:30` merges v.30–31) and `SNG` has 118 verses (`SNG 6:13–14` splits v.13), summing to exactly 31,102 verses matching `bible_station/canon.py`.
- **Acquired from**: <https://raw.githubusercontent.com/bluesaurel/Korean-Bible-1961-KRV/main/bible_1961_krv.json>.
- **Build & web export pipeline**: `python3 -m bible_station.cli build --export-web --export-bundle` ingests `data/raw/bible_1961_krv.json` into SQLite Dual-FTS5 (`bible_station/builder.py`) and exports deterministic per-book chunks (`web/data/krv/*.json`), compact offline search index (`web/data/search/krv.json`), and SHA-256 verified `web/data/manifest.json` (schema v3).

The Korean Bible Society's KRV FAQ states that the 1961 edition may be used without a copyright usage fee after expiration of its property-rights protection period, while author attribution and integrity rights must still be respected: <https://www.bskorea.or.kr/bbs/board.php?bo_table=copyright_faq&wr_id=5>. The Society's copyright notice identifies the edition as “Korean Revised Version © Korean Bible Society 1961”: <https://bible.bskorea.or.kr/copyright_notice>.

The application displays that attribution and links to the Society's notice. This provenance record does not claim that the mirror itself is an authorized distribution channel, or that every verse was independently compared with the Society's live text.

## Public Distribution Allowlist Policy (D-01 Option A)

Copyrighted Korean Bible Society editions (`개역개정` / `nkrv`, `새번역` / `rnksv`) and commercial translations are **excluded** from repository tracking and public GitHub Pages deployment. Both `.github/workflows/ci.yml` and `.github/workflows/deploy-pages.yml` enforce the `web/data/manifest.json` version allowlist before deployment. Pastors who own personal licensed translation text files may import them locally into browser IndexedDB only (never uploaded or redistributed).
