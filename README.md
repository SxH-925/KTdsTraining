# 🧠 CodeEyes Assistant (v0.1)

SonarQube 정적 분석 위반 항목을 GPT 기반 AI로 분석하여  
정탐/오탐 여부를 판단하고, 정탐인 경우 **자동 수정 코드**를 제안하는 개발자용 AI Agent입니다.

---

## 📌 프로젝트 개요

- 위반 사항에 대한 빠른 정탐/오탐 판단
- 룰 설명 및 개선 코드 자동 제안
- AI 기반의 코드 품질 개선 지원

> ✅ CodeSmell 예방  
> ✅ 정적 분석 고도화 기반 데이터 확보  
> ✅ 개발자 룰 이해도 향상 및 대응 속도 향상

---

## ⚙️ 기술 스택

| 항목 | 내용 |
|------|------|
| 언어 | Python 3.10+ |
| 프레임워크 | [Streamlit](https://streamlit.io) |
| LLM | Azure OpenAI (GPT-4o-mini) |
| 분석 룰 | SonarQube 공식 문서 기반 (룰 DB JSON 형태로 관리) |

---

## 🧩 아키텍처
사용자 → Streamlit UI → Python 모듈 → Azure OpenAI API → 결과 반환 → 결과 출력
---

## 🚀 주요 기능

### ✅ 분석 기능

- 언어 선택 (Python / Java / JavaScript)
- 룰 선택 (자동 검색 포함)
- 코드 입력 (Ace 기반 코드 에디터)
- GPT 분석 결과 출력:
  - 룰 이름, 등급, 범주, 설명
  - 정탐 / 오탐 여부
  - 정탐일 경우 수정 코드 제안
  - 수정 난이도 표시
  - ⚠️ AI 코드에 대한 검토 주의 메시지

### 💬 후속 질문 기능

- AI에게 추가 질문을 던지고 응답을 실시간 확인

---

## 📁 프로젝트 구조

```bash
.
├── app.py (Streamlit 메인 실행 파일)
├── config.py (환경변수 로딩 및 설정값 관리)
├── parser.py (Markdown 응답 파싱 모듈)
├── llm.py (OpenAI 연동 및 RAG응답 처리)
├── prompt/
│   └── system_prompt.md (시스템 프롬프트 텍스트)
├── data/
│   └── rules_list.json (룰 목록 JSON)
│   └── logo.png (UI에 사용할 로고)
├── .env  # 환경변수 (OpenAI, Azure Search 키 등)

```
## .env 예시
- OPENAI_API_KEY=your-openai-key
- OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
- CHAT_MODEL=gpt-4o
- SEARCH_ENDPOINT=https://your-search-instance.search.windows.net/
- SEARCH_API_KEY=your-search-key
- INDEX_NAME=sonarqube-rules-index

## 향후 확장 고려 기능
- 소스코드정적분석 시스템 API 와 연결 (자동화)
- 룰 학습 모델 튜닝 (RAG 정규화)
- Token 최적화를 통한 비용관리
- 코드 리뷰 도구로 확장

## 테스트 데이터
Python - Docstrings should be defined def
    def normalize_verdict(text):
    if not text:
        return None
    lowered = text.lower()
    if "정탐" in lowered:
        return "정탐"
    elif "오탐" in lowered:
        return "오탐"
    return None

JS - switch statements should have default clauses
switch (param) {  //missing default clause
  case 0:
    doSomething();
    break;
  case 1:
    doSomethingElse();
    break;
}

## 라이선스
본 프로젝트는 사내 PoC / 교육 목적으로 활용되며 외부 배포 시 별도 라이선스 고려 필요

