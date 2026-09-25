# 성경주혜주석 (Biblical Exegesis & Commentary Pastoral Workstation)

> 박우호 목사님의 성경 연구, 주석 비교, 심층 관주 탐색, 설교 준비를 위한 전용 워크스테이션 (차후 다수 목회자 확장형 아키텍처)

---

## 📌 주요 기능 요약

1. **8종 대표 성경 주석 비교**:
   - 옥스포드 원어성경대전, 웨슬리 주석, 호크마 종합주석, 그랜드 종합주석, 카리스마 주석, 매튜 헨리 주석, 베이커 성경배경주석, ESV 성경해설주석
2. **성경 관주(串珠, Cross-References) & 인물 연쇄 관주(Chain-Ref)**:
   - 본문 구절과 짝을 이루는 관주 성구의 **실제 성경 본문 전문(Full Text)** 즉시 확인
   - **이삭(Isaac)**, 아브라함 등 인물 클릭 시 성경 전체를 관통하는 생애 구속사 사슬망 및 설교 포인트 제공
3. **원어 형태론 분해 & 스트롱코드**:
   - 히브리어/헬라어 스트롱 번호 칩 및 렉시콘 팝업
4. **설교 스튜디오 & 원클릭 인용**:
   - 주석 및 관주 구절에서 클릭 한 번으로 설교 대지 카드로 스크랩 및 편집
5. **강단 설교 프롬프터 모드 (Pulpit Mode)**:
   - 성구대 거치 전용 대형 폰트, 실시간 타이머, 무소음 75%/25% 터치 탭 페이징
6. **디바이스 최적화**:
   - Galaxy Z Fold 6 (접힘 1열 & 펼침 3패널), iPad (11인치), PC 데스크톱 반응형 지원

---

## 🚀 빠른 시작 (Quick Start)

### 1. 인터랙티브 웹 프로토타입 실행
```powershell
python -m http.server 8080 --directory "C:\Users\packr\Desktop\성경주혜주석\prototype"
# 브라우저에서 http://localhost:8080 접속
```

### 2. SQLite FTS5 데이터베이스 빌드 및 GCP 패키징
```powershell
python "C:\Users\packr\Desktop\성경주혜주석\scripts\data_pipeline\build_bible_db.py" --sample --export-gcp
```
