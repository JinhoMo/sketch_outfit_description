# Sketch — Identity Consulting Report 자동화

Sketch Branding Shop의 "Identity Consulting Report" 제작을 자동화하는 프로젝트. 고객 정보(나이·직업·추구미)와 전신 사진을 받아 Gemini로 분석 리포트와 스타일링 룩북 이미지를 생성하고, 잡지형 2단 레이아웃의 HTML/PNG/PDF 리포트로 내보낸다.

## 구조

```
sketch/
├── automation/              # 메인 앱 (uv 워크스페이스 멤버)
│   ├── main.py              # Streamlit UI 엔트리
│   ├── modules/
│   │   ├── ai_engine.py     # Gemini 클라이언트 (텍스트 + 이미지)
│   │   ├── prompts.py       # 리포트 JSON 스키마 + 이미지 프롬프트
│   │   ├── renderer.py      # Jinja2 HTML 템플릿 (잡지형 2단)
│   │   ├── exporter.py      # HTML → PNG/PDF (subprocess로 playwright 호출)
│   │   └── exporter_worker.py  # playwright 실행용 독립 스크립트
│   ├── logs/                # 일일 로그 (app_YYYYMMDD.log)
│   ├── requirements.txt
│   └── .streamlit/config.toml  # runOnSave=true
├── original_image/          # 입력 전신샷
├── generated_image/         # 생성된 룩북 이미지
├── sample.png               # 리포트 레이아웃 레퍼런스
└── .env                     # GOOGLE_API_KEY (Google AI Studio 키)
```

## 실행

```bash
cd automation
pip install -r requirements.txt
playwright install chromium   # 최초 1회
streamlit run main.py
```

`.env`에 `GOOGLE_API_KEY=AIzaSy...` (따옴표·공백 없이). Google AI Studio(https://aistudio.google.com/apikey)에서 발급된 키만 작동 — Vertex AI 키는 불가.

## 사용 모델

- 텍스트: `gemini-3-flash-preview` → `gemini-3.1-pro-preview` → 2.5 폴백 (`ai_engine.py:TEXT_MODELS`). 503 시 지수백오프 3회
- 이미지: `gemini-3.1-flash-image-preview` (Nano Banana). 원본 얼굴·체형 유지 image-to-image

## 워크플로우

1. **입력**: 전신샷 모드(사진 + 추구미 이미지 2장) 또는 텍스트 폼 모드(외형 상세 텍스트)
2. **리포트 생성**: Gemini가 고정 JSON 스키마로 응답 (`prompts.REPORT_SCHEMA_INSTRUCTION`)
3. **룩북 생성**: `ThreadPoolExecutor`로 3장 병렬 생성, 각 룩마다 다른 컨셉 (`prompts.LOOK_VARIATIONS`)
4. **렌더**: `renderer.render_html()` → Playfair Display + EB Garamond + Noto Sans KR 베이지 레이아웃
5. **수정하기** expander: 텍스트 필드 인라인 수정, BEFORE 교체, 룩북 프롬프트 기반 개별 재생성
6. **내보내기**: HTML 다운로드, PNG/PDF는 Playwright subprocess로 렌더

## 주요 설계 결정

- **미리캔버스 자동화 안 함**: 공식 API 없음. 대신 HTML 템플릿으로 직접 렌더 → PDF 저장
- **Playwright를 subprocess로 분리**: Windows에서 Streamlit의 SelectorEventLoop와 Playwright subprocess가 충돌(`NotImplementedError`). `exporter_worker.py`를 별도 Python 프로세스로 실행해 우회
- **`load_dotenv(override=True)`**: OS 환경변수의 구식 키가 `.env`를 가리는 사고 방지
- **JSON 스키마 강제**: Gemini `response_mime_type="application/json"` + 스키마 프롬프트로 파싱 안정화. 코드펜스·주변 텍스트 방어용 `_parse_json` 포함
- **session_state 기반 상태 관리**: Streamlit 재실행에도 HTML/이미지/캐시된 PNG·PDF 유지. 다운로드 버튼이 다시 누르면 사라지는 문제 방지
- **HTML 변경 감지로 캐시 무효화**: 동일 HTML이면 PNG/PDF 캐시 유지, 바뀌면 자동 폐기

## 디버깅

- 로그: `automation/logs/app_YYYYMMDD.log` + stdout 동시 기록
- 모델 ID 404: `python -c "..."` 로 `ListModels` 호출해 실제 지원 모델 확인
- 키 이슈: 실제로 로드된 키 확인 `python -c "from dotenv import load_dotenv,find_dotenv; print(find_dotenv())"` — `.env` 파일 위치 확인

## 안 하는 것

- 루트에 `main.py` 두지 말 것 (과거 OpenAI 스캐폴드 잔재, 삭제됨)
- `automation/.env` 따로 두지 말 것 (루트 `.env`만 사용, `find_dotenv()`가 상위로 탐색)
- 이미지 생성에 fallback 모델 자동 폴백 넣지 말 것 (과금·품질 차이 커서 명시적 ID 유지)
