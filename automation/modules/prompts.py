"""Prompt builders for Identity Consulting Report."""

REPORT_SCHEMA_INSTRUCTION = """
너는 Sketch Branding Shop의 수석 이미지 컨설턴트이자 편집 디자이너다.
아래 조건에 맞춰 "Identity Consulting Report"를 작성한다.

⚠️ 섹션 순서 변경 금지.
⚠️ 오타 없는 정제된 문장으로 작성한다.
⚠️ 감성적인 문장 금지, 실무 컨설팅 톤 유지.
⚠️ 모든 항목은 간결한 한국어 구/문장으로 작성 (각 항목 1~2줄).

반드시 아래 JSON 스키마에 맞춰 **JSON만** 반환한다. 다른 텍스트, 마크다운, 코드펜스 금지.

{
  "before": {
    "impression": "인상 한 줄",
    "mood": "분위기 한 줄",
    "presence": "존재감 한 줄"
  },
  "client_info": {
    "age": "나이",
    "job": "직업",
    "goal_image": "목표 이미지",
    "current_impression": "현재 이미지 인상"
  },
  "body_style_analysis": {
    "body": "체형 분석",
    "face": "얼굴 인상 분석",
    "current_issue": "현재 스타일 문제점",
    "direction": "이미지 보완 방향"
  },
  "key_recommendations": {
    "top": "상의 전략",
    "bottom": "하의 전략",
    "silhouette": "실루엣 전략",
    "detail": "디테일 전략"
  },
  "avoid": {
    "fit": "피해야 할 핏",
    "color": "피해야 할 컬러",
    "mood": "피해야 할 무드",
    "ratio": "비율을 무너뜨리는 요소"
  },
  "colors": {
    "recommended": [
      {"name": "컬러1 한글명", "hex": "#RRGGBB"},
      {"name": "컬러2 한글명", "hex": "#RRGGBB"},
      {"name": "컬러3 한글명", "hex": "#RRGGBB"},
      {"name": "컬러4 한글명", "hex": "#RRGGBB"}
    ],
    "avoid": [
      {"name": "컬러1 한글명", "hex": "#RRGGBB"},
      {"name": "컬러2 한글명", "hex": "#RRGGBB"},
      {"name": "컬러3 한글명", "hex": "#RRGGBB"}
    ]
  },
  "lookbook": [
    "LOOK 1 스타일링 해석 (1~2문장)",
    "LOOK 2 스타일링 해석 (1~2문장)",
    "LOOK 3 스타일링 해석 (1~2문장)"
  ],
  "summary": {
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4"],
    "strategy": "Less but Stronger 전략 한 문단"
  },
  "final_comment": "Soft Face + Structured Styling = (해당 인물 이미지 정의 문장)"
}
"""


def build_text_report_prompt(age: str, job: str, desired_keywords: str,
                             extra_text: str = "", has_image: bool = True) -> str:
    input_block = f"""
[입력 자료]
- 나이 : {age}
- 직업 : {job}
- 추구미 키워드 : {desired_keywords}
"""
    if has_image:
        input_block += "- 원본 이미지 1장 (BEFORE) 첨부\n- 추구미 이미지 2장 첨부 가능\n"
    else:
        input_block += "- 위 이미지 첨부가 어려워 텍스트로 외형 전달함.\n"
        if extra_text:
            input_block += f"\n{extra_text}\n"

    return REPORT_SCHEMA_INSTRUCTION + "\n" + input_block


LOOK_VARIATIONS = [
    "데일리 캐주얼 무드. 가볍고 편안하면서도 정돈된 실루엣. 자연스러운 레이어드.",
    "세미 포멀 무드. 구조감 있는 아우터 또는 셋업. 디테일로 포인트.",
    "시그니처 스타일링. 컬러/소재 대비를 활용한 감각적 조합. 액세서리로 마무리.",
]


def build_before_image_prompt(age: str, job: str, desired_keywords: str, extra_text: str) -> str:
    return f"""아래 외형 묘사를 기반으로 실제 인물 전신 사진을 생성한다.

[인물 정보]
- 나이: {age}
- 직업: {job}
- 추구 이미지(참고용): {desired_keywords}

[외형 묘사]
{extra_text}

요구사항:
 • 머리부터 발끝까지 전신이 모두 보이는 자연스러운 서 있는 포즈
 • 인물이 프레임 중앙에 크게 잡히도록 타이트한 구도 (이미지 높이의 85% 이상)
 • 세로 구도(portrait), 배경 여백 최소화
 • 평범한 일상 복장 (브랜딩 이전의 BEFORE 상태)
 • 과장되지 않은 현실적인 체형과 얼굴
 • 중립적이고 깔끔한 실내 또는 스튜디오 배경
 • 사실적이고 자연광, 고해상도

복장 가이드 (반드시 준수):
 • 상의는 속옷이 비치지 않는 충분히 두껍고 불투명한 소재
 • 몸에 과도하게 밀착되지 않는 편안한 핏 (속옷 라인이 드러나지 않음)
 • 단정하고 무난한 평상복 (티셔츠/셔츠/니트 + 바지 또는 긴 스커트)
 • 노출이 적고 보수적인 실루엣
 • 얇은 니트·블라우스 등 속옷 실루엣이 드러날 수 있는 아이템 금지"""


def build_image_prompt(age: str, desired_keywords: str, look_index: int = 0) -> str:
    variation = LOOK_VARIATIONS[look_index % len(LOOK_VARIATIONS)]
    return f"""원본 이미지를 기반으로 얼굴, 체형, 키, 분위기를 그대로 유지한다.
인물의 정체성과 자연스러운 비율을 절대 변경하지 않는다.

아래 고객 정보를 기반으로 스타일을 재구성한다.
나이: {age}
추구 이미지: {desired_keywords}

해당 나이와 라이프스타일에 맞는 현실적이고 세련된 스타일을 구현한다.
단순한 옷 변경이 아니라 이미지 브랜딩 관점에서 스타일링한다.

스타일링 핵심 방향:
 • 체형 보완
 • 비율 개선
 • 강점 강조
 • 트렌디한 이미지 구축

이번 룩 컨셉:
 • {variation}

액세서리, 헤어, 메이크업까지 추구 이미지와 나이에 맞게 설계한다.

촬영 프레이밍 (중요):
 • 인물이 프레임의 중심에 크게 잡히도록 타이트한 구도
 • 머리부터 발끝까지 전신이 모두 보이되, 인물이 이미지 높이의 85% 이상 차지
 • 배경 여백은 최소화 — 인물이 주인공, 배경은 보조
 • 세로 구도(portrait orientation), 클로즈업된 풀바디 샷

배경:
 • 미니멀하고 깔끔한 환경, 인물을 방해하지 않는 단순한 배경

패션 에디토리얼, 고퀄리티, 사실적인 이미지."""
