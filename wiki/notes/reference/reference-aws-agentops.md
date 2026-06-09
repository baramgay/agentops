---
name: reference-aws-agentops
type: reference
domain: agents시스템
updated: 2026-06-09
---
# AWS Summit 2026 - AgentOps 실전 운영 전략

## 핵심 메시지

AI 프로젝트의 성공은

- 좋은 모델
- 좋은 프롬프트

보다

- 평가(Evaluation)
- 모니터링(Observability)
- 최적화(Optimization)

체계를 구축하는 것이 중요하다.

---

# AgentOps란?

## 정의

AI Agent를

```text
개발
→ 평가
→ 배포
→ 모니터링
→ 개선
```

하는 운영 체계

---

## 기존 DevOps와 비교

### DevOps

```text
Code
→ Test
→ Deploy
→ Monitor
```

### AgentOps

```text
Prompt
→ Evaluate
→ Deploy
→ Observe
→ Improve
```

---

# Agent 평가(Evaluation)

## 왜 필요한가?

LLM은 동일 입력에도

- 답변이 달라질 수 있음
- 품질이 변할 수 있음
- Tool 사용이 실패할 수 있음

따라서 지속적인 평가가 필요

---

# 모든 곳에 평가를 추가하라

## 1. 모델 성능 평가

### 품질 지표

- 정확성
- 충실도(Faithfulness)
- 유용성
- 관련성
- 완전성
- 유해성
- 환각(Hallucination)
- 논리적 일관성

---

### 코드/텍스트 평가

- 코드 생성 품질
- 지시 준수 여부
- 포맷 준수 여부

---

## 2. Tool 사용 평가

### 평가 대상

- Tool 선택 정확도
- 함수 호출 정확도
- 파라미터 전달 정확도

---

## 3. 대화 평가

### Turn 단위 평가

- 응답 관련성
- 응답 품질
- 정확성
- 충실도
- 간결성
- 일관성

---

## 4. 세션 평가

### 목표 달성 여부

예시

- 예약 성공
- 민원 해결
- 문서 생성 완료

---

## 5. 시스템 평가

### 운영 지표

- Latency
- TTFT(Time To First Token)
- 비용
- 처리량

---

# 평가 및 최적화 라이프사이클

## Step1

목표와 메트릭 정의

### 정의 항목

- 에이전트 목적
- 핵심 KPI
- 성공 기준

---

## Step2

평가 데이터 구축

### 구성

#### 레이블 데이터

실제 정답 데이터

#### 합성 데이터

AI 생성 테스트 데이터

---

## Step3

테스트

### 평가 대상

- Agent
- Tool 호출
- Multi-Agent
- RAG

---

### 평가 방법

#### Rule Based

규칙 기반

#### LLM-as-a-Judge

AI가 AI를 평가

#### Human Evaluation

사람 평가

---

## Step4

최적화

### 개선 대상

- 모델
- 프롬프트
- Tool
- 파이프라인
- 컨텍스트

---

# PoC → Production 전환 전략

## PoC 단계

### Agent 개발

- 목표 정의
- 성공지표 정의

### Evaluation

- Baseline 확보
- 성능 검증

### Runtime

- 실행환경 구성

### Observability

- 로그 수집
- 추적

---

## Production 이후

### Offline Evaluation

사전 검증

---

### Shadow Mode

실사용 데이터 관찰

실제 사용자 영향 없음

---

### A/B Test

모델 비교

Prompt 비교

---

### Full Rollout

전체 서비스 배포

---

## 핵심

```text
배포
≠ 완료

배포
→ 모니터링
→ 평가
→ 최적화
→ 재배포
```

---

# Agent 패턴

## Single Agent

단일 Agent

```text
User
 ↓
LLM
 ↓
Response
```

---

## Tool-Augmented Agent

도구 사용 Agent

```text
Agent
 ├ DB
 ├ API
 └ Search
```

---

## RAG Agent

검색 기반 Agent

```text
User
 ↓
Retriever
 ↓
LLM
```

---

## ReAct

Reason + Act

```text
생각
→ 행동
→ 관찰
→ 반복
```

---

## Sequential

순차 실행

```text
Agent A
 ↓
Agent B
 ↓
Agent C
```

---

## Parallel

병렬 실행

```text
Agent A
 ├ Agent B
 ├ Agent C
 └ Agent D
```

---

## Hierarchical

Manager + Worker

```text
Manager
 ├ Worker1
 ├ Worker2
 └ Worker3
```

---

## Graph Agent

그래프 기반

복잡한 워크플로우

---

## Swarm

분산 협업

다수 Agent 협업

---

## Federated A2A

Agent to Agent

도메인별 전문 Agent 협력

---

# AgentOps Lifecycle

## 1. Prototype

### 수행

- 모델 선정
- 프레임워크 선정
- Prompt 실험

---

## 2. Development

### 수행

- Agent 구현
- Tool 연결
- Gateway 구축
- 테스트 데이터 생성

---

## 3. Test

### 수행

- QA
- 통합 테스트
- Offline Eval
- Human Eval

---

## 4. Production

### 수행

- 실시간 모니터링
- Online Eval
- 사용자 피드백 수집
- 거버넌스

---

# Observability

## 왜 필요한가?

Agent는 내부 추론 과정을 숨긴다.

따라서

- Prompt
- Tool Call
- Context
- Output

모든 과정을 추적해야 함

---

## Trace 예시

```text
질문
 ↓
Prompt 생성
 ↓
Tool 호출
 ↓
Tool 결과
 ↓
LLM 응답
 ↓
최종 답변
```

---

# 운영 시 필수 대시보드

## 품질

- 정확도
- 충실도
- 성공률

---

## 비용

- Token 사용량
- 모델 비용

---

## 성능

- Latency
- TTFT

---

## Tool

- 호출 성공률
- 오류율

---

## 사용자

- 만족도
- 재질문율

---

# 발표 핵심 인사이트

## Insight 1

에이전트 개발보다

에이전트 평가가 중요하다.

---

## Insight 2

LLM 성능보다

Ground Truth 품질이 중요하다.

---

## Insight 3

RAG만으로는 부족하다.

AgentOps 체계가 필요하다.

---

## Insight 4

미래 아키텍처는

Single Agent가 아니라

Multi-Agent 구조다.

---

## Insight 5

AI 서비스도 결국

```text
CI/CD
+
Evaluation
+
Observability
```

가 필요하다.

---

# Your Organization 적용 아이디어

## 데이터허브

### Data Search Agent

데이터 검색

---

### Metadata Agent

메타데이터 생성

---

### Quality Agent

품질 진단

---

## AI 행정지원

### 민원 Agent

민원 응답

---

### 정책 Agent

정책 검색

---

### 보고서 Agent

보고서 작성

---

## AgentOps 플랫폼

### Evaluation

평가 자동화

### Observability

Trace 관리

### Dashboard

품질 모니터링

### Feedback

사용자 피드백 반영

---

# 최종 결론

AI 프로젝트의 성공 공식

```text
Agent
+
Evaluation
+
Observability
+
Optimization
+
Governance
=
Production AI
```

좋은 모델을 만드는 시대에서

좋은 Agent 운영 체계를 만드는 시대로 이동하고 있다.