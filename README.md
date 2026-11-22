# 성경주혜주석 v2.0 (Bible Commentary Station)

> **오프라인-퍼스트(Offline-First) 성경 66권(31,102절) · 8대 주석 비교 · 심층/연쇄 관주 · 다중 설교 스튜디오 · 강단 프롬프터 워크스테이션**  
> **Zero-Cost ($0.00) 아키텍처**: 유료 종량제 클라우드 없이 로컬 SQLite Dual-FTS5 + 정적 PWA + GitHub Releases/Google Drive 연동으로 동작합니다.

## 주요 아키텍처 (v2.0 전면 개편)

1. **SSOT(단일 진실 원천) 코어 패키지 (`bible_station/`)**
   - `canon.py`: 성경 66권 정경 메타데이터(구약 39 + 신약 27 = 31,102절), 8대 주석(교파 중립적 학술 설명), 구절 ID 공식.
   - `schema.py`: **External-Content Dual FTS5 (`unicode61` + `trigram`) + SQLite 자동 동기화 트리거** 및 Flutter Drift 스키마 자동 생성기(`sync-drift`).
   - `search.py`: 2글자 한글 어근(`사랑`)과 3글자 이상 부분 문자열(`독생자`, `모리아`)을 모두 0.1~5ms 이내로 검색하고 FTS5 구문 인젝션을 차단하는 하이브리드 검색 엔진.
   - `builder.py` & `cli.py`: 100% 멱등(Idempotent) DB 빌더, 66권 지연 로딩 웹 청크 생성기(초기 로딩 4.3MB -> 평균 68KB, 98.4% 절감), 실측 통계 기반 SHA-256 Zero-Cost 번들러.
2. **모듈형 오프라인 PWA (`web/`)**
   - 2,798줄 단일 `index.html` 모놀리스를 `index.html` + `css/workstation.css` + ES Modules(`storage.js`, `bibleService.js`, `app.js`) + 오프라인-퍼스트 `sw.js`로 완전 분해.
   - IndexedDB 다중 설교 아카이브(기존 `localStorage` 자동 마이그레이션, Markdown/JSON 백업), 8대 주석 **2종 나란히 비교 모드**, XSS-safe DOM 렌더링, 설교 스튜디오와 **실시간 연동되는 WCAG AAA 21:1 강단 프롬프터**.
3. **Flutter Clean Architecture (`lib/`)**
   - `Colors.emerald` 컴파일 오류 및 `gdrive_service.dart` UTF-8 바이트 길이 버그 수정.
   - `BibleRepository` 인터페이스 + `SqliteBibleRepository` 실구현 + `WorkstationController` 상태관리 + 스트리밍·SHA-256·원자적 교체(Atomic Swap) `ArtifactSyncService`.
4. **실측 기반 검증 하네스 (`tests/`) & CI (`.github/workflows/ci.yml`)**
   - 하드코딩 `PASS`와 동어반복 테스트를 제거하고 31,102절 DB·FTS5 멱등성·웹 청크·Flutter 정적 회귀를 실제 검증합니다.

## 빠른 시작 (Quick Start)

```bash
# 1. SQLite Dual-FTS5 마스터 DB + 66권 웹 청크 + Zero-Cost 번들 일괄 빌드
python3 -m bible_station.cli build --export-web --export-bundle
python3 -m bible_station.cli sync-drift

# 2. 전체 엔지니어링 하네스 실행 (docs/HARNESS_REPORT.md 실측 갱신)
python3 tests/run_harness.py

# 3. 오프라인-퍼스트 웹 워크스테이션 로컬 실행
python3 -m http.server 8090 --directory web
# 브라우저에서 http://localhost:8090 접속
```
