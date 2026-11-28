# 말씀 서재 v4.0 — Spatial Scriptorium & Polyglot Exegesis Engine

> **Zero-Cost ($0.00) · Offline-First · 66권 23개 역본 · 5대 공간 렌즈 · 성경 지식 성좌도 · 듀얼스크린 강단 텔레프롬프터**

## v4.0 대규모 아키텍처 & UI/UX 혁신 요약

### 1. 프론트엔드 무의존성 Reactive Micro-Kernel (`web/js/kernel/`)
- **`signals.js`**: Fine-grained 반응형 프리미티브(`signal`, `computed`, `effect`, `batch`) 및 Undo/Redo 히스토리 스택(`createHistory`) 도입.
- **`eventBus.js`**: 컴포넌트 간 콜백 스파게티를 제거하는 디커플링 Pub/Sub 이벤트 버스 + 진단 트레이스.
- **`commandRegistry.js`**: `⌘K` / `Ctrl+K` / `/` 통합 커맨드 팔레트 엔진 — 성경 구절 즉시 워프(`시 23:1`, `롬 8:28`), 66권, 645곡 새찬송가, 4대 테마, 5대 공간 렌즈 통합 퍼지 검색.
- **`pluginHost.js`**: 5대 공간 렌즈를 선언적으로 마운트/언마운트하는 플러그인 호스트.
- **`broadcastSync.js`**: `BroadcastChannel` 기반 무비용 듀얼스크린 강단 보조 화면(`?view=stage`) 실시간 동기화.

### 2. 기존 틀을 깨는 5대 공간 렌즈 (Spatial Lenses)
1. **몰입 서재 (Scriptorium)**: 66권 성경 본문 + 12대 주석 관점 + 원어 풀이 + **몰입 읽기(Zen Focus) 모드**.
2. **다중 역본 매트릭스 (Polyglot Synoptic Matrix)**: 23개 내장 역본 및 온라인 원문 중 **최대 4개 역본을 동시에 나란히 대조**, 추천 신학 프리셋(한·영 3역본, 한국어 4역본, 현대어·메시지, 직역·고전) 및 다중 역본 묶음 클리핑.
3. **성경 지식 성좌도 (Scripture Constellation Graph)**: 결정적 파이썬 그래프 엔진(`bible_station/graph.py`)이 생성한 `web/data/graph.json`(92개 노드 · 117개 관주/구속사 엣지 · 8개 인물 축)을 인터랙티브 SVG 성좌도로 시각화하고 클릭 시 본문으로 즉시 워프.
4. **예배 · 찬송 성소 (Worship Sanctuary)**: 예전 12종 · 새찬송가 645곡 · 교독문 137편 · 복음성가 95곡 · 예배 순서 8종.
5. **설교 공방 (Homiletics Studio)** + **차세대 강단 텔레프롬프터**:
   - 한국어 설교 발화 속도(분당 280자) 기반 **실시간 예상 설교 시간 예측기** 및 시각적 페이싱 바
   - 대지 블록 순서 재배치(`↑`/`↓`)
   - 강단 프롬프터 **자동 스크롤(S)**, **실시간 페이싱 게이지**, **암전(B)**, **보조 화면 동기화**

### 3. "Luminance Scriptorium" 4대 감각 테마 (`web/css/tokens.css`, `web/css/v4-spatial.css`)
- **한지 주간 (`hanji`)** · **양피지 고전 (`vellum`)** · **흑요석 서재 (`obsidian`)** · **강단 암전 OLED (`sanctuary`)** — 전 테마 WCAG AAA 고대비 유지 + 글래스모픽 탑바.

### 4. Python 백엔드 컴포저블 파이프라인 (`bible_station/pipeline/`, `graph.py`)
- 모놀리식 빌더를 `BuildContext` + `PipelineStage` + `BuildPipeline`의 8개 독립 스테이지로 분해.
- 신규 CLI 명령: `python3 -m bible_station.cli graph` (성좌도 그래프 빌드), `python3 -m bible_station.cli serve` (무의존성 로컬 웹 서버).

## 빠른 실행 및 테스트

```bash
# 1. 성경 지식 성좌도 그래프 생성
python3 -m bible_station.cli graph

# 2. v4.0 로컬 워크스테이션 실행
python3 -m bible_station.cli serve --port 8090
# 브라우저에서 http://127.0.0.1:8090 접속 (보조 강단 화면: ?view=stage)

# 3. 테스트 실행
python3 -m unittest discover -s tests -p 'test_v4_architecture.py' -v
npm --prefix web test
```
