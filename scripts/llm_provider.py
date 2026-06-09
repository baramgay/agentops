"""
LLM Provider — 에이전트 반응 생성 추상화

- MockLLMProvider   : API 키 불필요, role.md 기반 rule-based 응답
- OpenAILLMProvider : 실제 GPT-4o-mini API 호출 (API 키 필요)

환경변수:
    LLM_PROVIDER=mock|openai   (기본: mock)
    OPENAI_API_KEY=sk-...      (openai 사용 시 필요)
    OPENAI_MODEL=gpt-4o-mini   (선택, 기본: gpt-4o-mini)
"""

from __future__ import annotations

import os
import random
from abc import ABC, abstractmethod

from persona_loader import PersonaContext

# .env 파일 로드 (존재 시)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class LLMProvider(ABC):
    """반응 생성 provider 추상 클래스"""

    @abstractmethod
    def generate_reaction(
        self,
        agent_id: str,
        instruction: str,
        persona: PersonaContext | None,
        action: str,
    ) -> str:
        """지시와 페르소나를 받아 에이전트 반응 텍스트를 생성한다."""
        ...


# ── Mock (rule-based persona) ───────────────────────────

_AGENT_KEYWORDS: dict[str, list[str]] = {
    # 빅데이터팀
    "data-collector": ["데이터 수집", "공공데이터포털", "지자체 API"],
    "data-cleaner": ["데이터 전처리", "품질 검증", "결측치 처리"],
    "eda-analyst": ["탐색적 데이터 분석", "데이터 프로파일링", "인사이트 도출"],
    "statistician": ["통계 분석", "가설 검정", "회귀 분석"],
    "ml-engineer": ["머신러닝 모델", "예측 모델 개발", "교차검증"],
    "deep-learning": ["딥러닝", "신경망 모델", "CNN/RNN"],
    "gis-specialist": ["GIS 분석", "공간 데이터", "지도 시각화"],
    "text-analyst": ["텍스트 분석", "자연어 처리", "키워드 추출"],
    "visualizer": ["데이터 시각화", "차트 및 그래프", "대시보드 구성"],
    "reporter": ["분석 보고서", "결과 문서화", "PPT 작성 지원"],
    # 개발팀
    "requirements": ["요구사항 분석", "명세서 작성", "범위 관리"],
    "ux-designer": ["UX 설계", "와이어프레임", "사용자 흐름"],
    "frontend": ["프론트엔드 개발", "화면 구현", "React/Streamlit"],
    "backend": ["백엔드 개발", "API 설계", "서버 구축"],
    "dba": ["DB 설계", "쿼리 최적화", "데이터베이스 관리"],
    "security": ["보안", "취약점 분석", "OWASP 점검"],
    "tester-unit": ["단위 테스트", "테스트 코드", "커버리지 확보"],
    "tester-qa": ["QA 테스트", "통합 테스트", "품질 검증"],
    "devops": ["CI/CD", "인프라 구축", "배포 자동화"],
    "tech-writer": ["기술 문서", "가이드 작성", "문서화"],
    # PPTX팀
    "pptx-planner": ["PPTX 기획", "발표 구성", "스토리라인 설계"],
    "pptx-content": ["PPTX 내용 작성", "카피라이팅", "메시지 설계"],
    "pptx-designer": ["PPTX 디자인", "슬라이드 디자인", "시각 디자인"],
    "pptx-builder": ["PPTX 제작", "python-pptx", "자동화 구현"],
    "pptx-reviewer": ["PPTX 검토", "품질 체크", "피드백"],
    "realty-analyst": ["부동산 동향", "월보 작성", "경남 부동산시장", "가격지수", "미분양", "인허가", "분양"],
    # 리드 / 오케스트레이터
    "lead-data": ["데이터 분석 총괄", "분석 파이프라인", "팀 조율"],
    "lead-dev": ["개발 총괄", "개발 파이프라인", "기술 검토"],
    "lead-pptx": ["PPTX 총괄", "발표 자료 기획", "디자인 감독"],
    "orchestrator": ["전체 조율", "팀장 보고", "작업 분배"],
}

_ACTION_TEMPLATES: dict[str, list[str]] = {
    "work": [
        "{keyword} 작업을 시작하겠습니다.",
        "{keyword} 업무에 집중하겠습니다.",
        "{keyword} 업무에 들어가겠습니다.",
        "{keyword} 지시 확인했습니다. 바로 시작하겠습니다.",
        "{keyword} 업무, 즉시 진행합니다.",
        "알겠습니다. {keyword} 최선을 다하겠습니다.",
    ],
    "gather": [
        "회의실로 이동하겠습니다.",
        "라운지로 집합하겠습니다.",
        "팀 회의에 참석하겠습니다.",
        "지금 바로 이동합니다.",
        "합류하겠습니다.",
    ],
    "return": [
        "데스크로 복귀하겠습니다.",
        "{keyword} 업무를 재개하겠습니다.",
        "복귀하여 {keyword} 업무를 계속하겠습니다.",
        "자리로 돌아가겠습니다.",
    ],
    "break": [
        "잠깐 휴식하겠습니다.",
        "휴식 후 {keyword} 업무에 복귀하겠습니다.",
        "커피 브레이크 후 {keyword} 업무를 재개하겠습니다.",
        "잠시 쉬겠습니다.",
    ],
    "review": [
        "{keyword} 검토를 시작하겠습니다.",
        "{keyword} 점검에 들어가겠습니다.",
        "{keyword} 품질을 확인하겠습니다.",
        "검토 중입니다. 잠시 기다려 주세요.",
        "확인 후 보고드리겠습니다.",
    ],
    "done": [
        "작업 완료했습니다. 검토 요청드립니다.",
        "처리 완료. 결과물 확인 부탁드립니다.",
        "완료했습니다. 다음 지시를 기다리겠습니다.",
        "{keyword} 작업을 마쳤습니다.",
    ],
    "wait": [
        "대기하겠습니다.",
        "추가 지시를 기다리겠습니다.",
        "{keyword} 업무 대기 중입니다.",
        "준비 완료, 대기 중입니다.",
    ],
    "none": [
        "지시 확인했습니다.",
        "{keyword} 관련 지시를 접수했습니다.",
        "{keyword} 담당으로 지시를 확인했습니다.",
        "알겠습니다.",
    ],
}

# 에이전트별 개성 있는 말투 접두어
_AGENT_STYLE_PREFIX: dict[str, str] = {
    "orchestrator": "전체 조율 관점에서 — ",
    "lead-data": "데이터팀 총괄로서 — ",
    "lead-dev": "개발팀 총괄로서 — ",
    "lead-pptx": "PPTX팀 총괄로서 — ",
    "data-collector": "[수집] ",
    "data-cleaner": "[전처리] ",
    "eda-analyst": "[EDA] ",
    "statistician": "[통계] ",
    "ml-engineer": "[ML] ",
    "gis-specialist": "[GIS] ",
    "security": "[보안] ",
    "tester-unit": "[단위테스트] ",
    "tester-qa": "[QA] ",
    "devops": "[CI/CD] ",
    "tech-writer": "[문서] ",
}


class MockLLMProvider(LLMProvider):
    """API 키 없이 role.md 기반 rule-based 반응 생성."""

    def generate_reaction(
        self,
        agent_id: str,
        instruction: str,
        persona: PersonaContext | None,
        action: str,
    ) -> str:
        # 키워드 선정 (설정 없으면 "작업" fallback)
        keywords = _AGENT_KEYWORDS.get(agent_id, ["작업"])
        # 다양성을 위해 키워드 목록에서 랜덤 선택
        keyword = random.choice(keywords) if len(keywords) > 1 else keywords[0]

        # 템플릿 선택
        templates = _ACTION_TEMPLATES.get(action, _ACTION_TEMPLATES["none"])
        template = random.choice(templates)

        reaction = template.format(keyword=keyword)

        # 에이전트별 개성 있는 접두어 적용 (work/review/done 액션만)
        if action in ("work", "review", "done"):
            prefix = _AGENT_STYLE_PREFIX.get(agent_id, "")
            if prefix:
                reaction = prefix + reaction

        # max 60자 제한 (말풍선 가독성)
        if len(reaction) > 60:
            reaction = reaction[:57] + "..."

        return reaction


# ── OpenAI (real) ───────────────────────────────────────

class OpenAILLMProvider(LLMProvider):
    """실제 OpenAI API 호출 (API 키 없으면 Mock으로 폴트백)."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None
        if self.api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"[OpenAI] 클라이언트 초기화 실패: {e}")

    def generate_reaction(
        self,
        agent_id: str,
        instruction: str,
        persona: PersonaContext | None,
        action: str,
    ) -> str:
        if not self._client:
            return MockLLMProvider().generate_reaction(agent_id, instruction, persona, action)

        system = _build_system_prompt(persona)
        user = (
            f"사용자 지시: {instruction}\n"
            f"action 분류: {action}\n\n"
            "위 지시에 대해 짧게(1~2문장, 최대 60자) 반응하세요."
        )

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
                max_tokens=150,
                timeout=10,
            )
            text = (resp.choices[0].message.content or "").strip()
            if len(text) > 60:
                text = text[:57] + "..."
            return text
        except Exception as e:
            print(f"[OpenAI] API 호출 실패: {e}")
            return MockLLMProvider().generate_reaction(agent_id, instruction, persona, action)


def _build_system_prompt(persona: PersonaContext | None) -> str:
    """OpenAI system prompt 템플릿"""
    if not persona:
        return "당신은 AI 에이전트입니다. 사용자 지시에 짧게(1~2문장, 최대 60자) 반응하세요."
    expertise_text = "\n".join((persona.expertise or [])[:3])
    principles_text = "\n".join(f"- {p}" for p in (persona.principles or [])[:5])
    return (
        f"당신은 {persona.name}입니다.\n\n"
        f"정체성:\n{persona.identity}\n\n"
        f"전문 역량:\n{expertise_text}\n\n"
        f"원칙:\n{principles_text}\n\n"
        "사용자의 지시에 대해 짧게(1~2문장, 최대 60자) 반응하세요."
    )


# ── 팩토리 ──────────────────────────────────────────────

def get_provider() -> LLMProvider:
    """환경변수 LLM_PROVIDER 에 따라 provider 인스턴스 반환.

    LLM_PROVIDER=openai 이지만 OPENAI_API_KEY가 없으면
    경고 출력 후 MockLLMProvider로 폴트백한다.
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider_name == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and api_key.startswith("sk-"):
            return OpenAILLMProvider()
        print("[WARN] LLM_PROVIDER=openai 이지만 OPENAI_API_KEY가 유효하지 않습니다. MockLLMProvider로 폴트백합니다.")
    return MockLLMProvider()


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    from persona_loader import load_persona

    provider = get_provider()
    test_cases = [
        ("data-collector", "공공데이터 수집 시작", "work"),
        ("frontend", "화면 구현 시작", "work"),
        ("security", "보안 검토해줘", "review"),
        ("orchestrator", "전체 회의 소집", "gather"),
        ("pptx-designer", "슬라이드 디자인 시작", "work"),
    ]

    for aid, instr, act in test_cases:
        persona = load_persona(aid)
        reaction = provider.generate_reaction(aid, instr, persona, act)
        print(f"[{aid:20}] ({act:6}) → {reaction}")
