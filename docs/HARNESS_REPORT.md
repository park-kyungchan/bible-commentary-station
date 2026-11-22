# 성경주혜주석 v2.0 Engineering Harness 실측 검증 보고서

> **생성 일시 (UTC)**: 2026-11-22 01:24:58  
> **실제 결과**: **13/13 통과 (100.0%)** | 실패: 0 | 오류: 0 | 소요 시간: 0.102초

## 1. 테스트 스위트별 실제 실행 결과

| 검증 영역 | 테스트 스위트 | 통과/전체 | 상태 |
| :--- | :--- | :---: | :---: |
| Canon & DB Integrity (31,102 KRV) | `TestCanonAndDatabaseIntegrity` | 4/4 | **PASS** |
| Hybrid Korean FTS5 & Idempotency | `TestHybridKoreanFts5AndIdempotency` | 4/4 | **PASS** |
| Web PWA & Flutter Static Audit | `TestWebAndFlutterStaticAudit` | 5/5 | **PASS** |

## 2. 실측 성능 및 아티팩트 지표 (31,102절 KRV 완본 기준)

| 지표 | 실측값 |
| :--- | :--- |
| 구절 단건 조회 (`verse_id` 인덱스, p50) | **0.0029 ms** |
| 한국어 3글자 FTS5 Trigram 검색 (31,102절, p50) | **0.1683 ms** |
| 8대 주석 조인 (`창세기 22:2`, 8종 매칭) | **0.0847 ms** |
| SQLite FTS5 마스터 DB 크기 (비압축 -> Gzip) | **21.77 MB -> 8.91 MB (59.07% 절감)** |
| 웹 PWA 권별 지연 로딩 평균 청크 크기 (66권 분할) | **66.7 KB** (기존 4.3MB 대비 98.4% 초기 로딩 절감) |
