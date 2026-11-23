# 말씀 서재 v3.0 (Bible Commentary Station)

> **시니어 목회자를 위한 오프라인-퍼스트 성경 66권 3대 역본(개역개정 기본 · 개역한글 · 새번역, 각 31,102절) · 12대 주석 관점 참고 요약 · 예배·예전(사도신경/주기도문/성찬/축도/137교독문/645찬송가) · 설교 스튜디오 · 강단 프롬프터 워크스테이션**  
> **Zero-Cost ($0.00) 아키텍처**: 외부 종량제 클라우드 없이 Python 표준 라이브러리(의존성 0) + 로컬 SQLite Dual-FTS5 + 정적 PWA로 동작합니다.

## 주요 아키텍처 (v3.0)

1. **Zero-Dependency SSOT 코어 패키지 (`bible_station/`)**
   - `canon.py`: 성경 66권 정경 메타데이터(개역한글 1961 기준 1,189장 31,102절, 장별 절 수 SSOT), 12대 주석 관점 카탈로그(교파 중립적 설명), 구절 ID 공식.
   - `schema.py`: **External-Content Dual FTS5 (`unicode61` + `trigram`) + SQLite 자동 동기화 트리거** 및 Flutter Drift 스키마 자동 생성기(`sync-drift`).
   - `parsers.py` & `search.py`: 시니어 목회자 친화 관대 검색(`여호와는나의목자`, `복있는 사람`, `시 23편 1절`, `계시록 21:4`, `사랑?`) + 3단계 폴백(Trigram → Unicode61 → 공백제거) + 구절 자동 이동 + FTS5 인젝션 차단.
   - `builder.py` & `cli.py`: 100% 멱등·결정적(Deterministic) 빌더, 3대 역본(`nkrv` 개역개정 기본 · `krv` 개역한글 · `rnksv` 새번역 각 66권 청크 + 각주 구조 분리 + 3종 오프라인 검색 인덱스 `web/data/search/{nkrv,krv,rnksv}.json`), SHA-256 매니페스트(`schemaVersion: 3`, 203개 체크섬), SQLite Online Backup API 기반 WAL-free `VACUUM` 읽기 전용 안전 번들(`.db.gz`), 엄격 코퍼스 검증기(`validate`).
   - `catalog_worship.py` & JSON 카탈로그: 새찬송가 645곡(중복 없는 통일찬송가 번호, 공식 제목 일치), 21세기 새교독문 137편 전편 오프라인 본문 지원(#88–#137 구조화 성경구절 시퀀스 포함), 예배 예전(사도신경·주기도문 새번역/전통번역, 성찬 예식, 축도 3종), PII 없는 예배 순서 템플릿 5종.
   - `health_check.py`: 주간 운영 상태 점검 CLI (HelloAO API, 주석 공식 URL, Drive 예배 링크, 라이브 Pages SHA-256 무결성).
2. **모듈형 오프라인 PWA (`web/`)**
   - Sanctuary Hanji & Sumi Ink 디자인 시스템(WCAG AAA `>= 7.0:1`), 모바일 본문 영역 80%+, 48px 시니어 터치 타깃, 무눈부심 강단 프롬프터, IndexedDB 자동저장 + JSON 전체 백업/복원, 개인 소장 번역본 로컬 가져오기(BYOT).
3. **자동화 검증 및 배포 게이트 (`.github/workflows/`)**
   - `ci.yml`: Zero-dependency Python 3.12 빌드/패키징/결정적 출력/WAL-free `.db.gz` + 5-table FTS5/코퍼스·예배 불변성/PII·라이선스 허용목록/Node v24 웹 모듈 테스트.
   - `deploy-pages.yml`: `verify`(`ci.yml`) 통과 필수, `package.json` 제외 및 `.nojekyll` 포함 스테이징, 라이선스 허용목록 검증 후 GitHub Pages 배포.
   - `scheduled-health.yml`: 매주 월요일 11:00 KST 자동 운영 상태 점검 및 중복 방지 `ops-health` 이슈 알림.
4. **Flutter 클라이언트 (`lib/`)**
   - Drift 스키마 SSOT 동기화 유지(Wave 2 별도 PR에서 부트스트랩 및 태블릿 UI 패리티 진행).

## 빠른 시작 (Quick Start)

```bash
# 1. SQLite Dual-FTS5 마스터 DB + 결정적 웹 데이터(66권 청크·검색 인덱스·주석·예배) + WAL-free 번들 빌드
python3 -m bible_station.cli build --export-web --export-bundle
python3 -m bible_station.cli validate

# 2. 단위 테스트 및 비파괴 엔지니어링 하네스 실행 (리포트 갱신 시 --write-report 지정)
python3 -m unittest discover -s tests -p 'test_suite.py' -v
python3 tests/run_harness.py

# 3. 오프라인-퍼스트 웹 워크스테이션 로컬 실행
python3 -m http.server 8090 --directory web
# 브라우저에서 http://localhost:8090 접속
```
