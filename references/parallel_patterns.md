# Parallel Patterns (C3 / C6 / C10 카테고리)

생성: 2026-05-14 · 출처: `taxonomy.md §C3·C6·C10` + Scout A·B·C

## 헤드라인 (메타 원칙 강화)

> **사용자 baseline: 25/27 하네스 (93%) 5+ agent 팀, 14/27 (52%) 8+ agent, Paper Maker 15인.** 7×~15× cost multiplier — 단일 세션이 가능한데도 팀을 띄우면 그만큼 토큰이 곱연산된다.

## 1. 멀티에이전트 cost multiplier [A003][S-B003]

| 패턴 | multiplier | 출처 |
|------|-----------:|------|
| 표준 세션 (baseline) | 1× | — |
| Plan-mode agent team | 7× | [A003] Anthropic 공식 |
| 49 병렬 fanout (실측) | 887K tokens/min | [S-B003] aicosts.ai |
| 5 병렬 = Pro 15분 소진 | 15× | [S-B004] 실측 |

**즉시 적용 룰:**
- 5+ agent 팀 띄우기 전 자문: "이거 단일 세션으로 안 되나?"
- 팀원은 Sonnet (Anthropic "use Sonnet for teammates" [A002]), orchestrator만 Opus.
- spawn 오버헤드 20K~85K [S-B003] — 작업 절감 추정치 < 30K이면 단일 세션이 이득.

## 2. 단일 세션 vs 에이전트 팀 결정 트리

```
질문 1: 작업 phase 수 ≥ 3 인가?
   NO → 단일 세션 ✅
   YES → 질문 2로

질문 2: 각 phase가 독립적으로 병렬 가능한가? (입력 충돌 0, 출력 머지 가능)
   NO → 단일 세션 ✅ (순차 phase는 팀이 무의미)
   YES → 질문 3으로

질문 3: 병렬 phase의 작업 절감 추정치 > 30K tokens × N agent ?
   NO → 단일 세션 ✅ (spawn 오버헤드 회수 불가)
   YES → 팀 검토 — 단, 다음 4가지 확인

   [3-1] 팀원 모델은 Sonnet인가? (Anthropic 공식 [A002])
   [3-2] 병렬 fanout cap ≤ 5 명시했는가? (49 동시 = 887K/min 위험 [S-B003])
   [3-3] orchestrator는 명시적 종료 명령 있는가? (Idle team 비용 [A023])
   [3-4] spawn 후 24K~ 토큰 회수 가능한 작업인가?
```

## 3. 병렬 fanout cap [S-B003][S-B004]

**무제한 fanout 위험:**
- 49 병렬 = 분당 887K tokens (aicosts.ai 실측)
- 5 병렬 = 15분 만에 Pro $20 한도 소진
- 사용자 30개 하네스 중 "병렬" / "parallel" / "fanout" 30회 언급 — 거의 모든 하네스가 병렬 의존, but cap 명시 부재.

**권고:**
```
병렬 hard cap: 3 ~ 5 (wave 실행 권고)
wave 1: agent[0..4] 병렬 → 완료 대기 → wave 2: agent[5..9] 병렬
```

agent 정의에 명시:
```yaml
parallel:
  max_concurrent: 5
  wave_size: 3
  on_wave_completion: gate_check
```

## 4. 계층 vs 반사형 아키텍처 [S-C04]

arXiv:2603.22651 (Benchmarking Multi-Agent) Pareto frontier:

| 아키텍처 | 정확도 | 비용 배수 | 권고 |
|---------|------:|---------:|------|
| 반사형 (Reflexive) | F1=0.943 | 2.3× | 마지막 단계 정밀 검수에만 |
| 계층형 (Hierarchical) | F1=0.921 | 1.4× | **baseline 권고** |
| Hybrid (계층 + 한정 반사) | 89% | 1.15× | **Pareto 최적** |

**적용:**
- 계층형 baseline + 마지막 단계만 hybrid 재시도 (max 3회).
- 사용자 paper-maker editor-chief 3회 cap = 좋은 예. 다른 하네스 검증 필요.
- 재시도 hard cap ≤ 3: `for i in range(MAX_ITER):` 명시.

## 5. spawn 오버헤드 [S-B003][A023]

**Sub-agent spawn 비용:**
- spawn 자체 = 20K ~ 85K tokens (Anthropic + community)
- 사용자 8+ agent 하네스 14개 — spawn 누적 280K~1,190K tokens
- "Idle team not disbanded" — 작업 끝났는데 팀 살아 있으면 background token $0.04/session

**Rule of thumb:**
```
작업 절감 추정치 > 30K tokens × N spawn → 팀 OK
< 30K → 단일 세션
```

**명시적 종료 (A023):**
```
phase 종료 후 orchestrator가 SendMessage("team_disband")
또는 agent 정의에 max_idle_time: 60s
```

## 6. Subagent skills preload [A015][A029]

**위험 패턴:**
- agent frontmatter에 skills 다수 나열 → 사용 안 해도 startup에 모두 로드
- 사용자 평균 트리거 phrase 14.3개/하네스 — 트리거 중복·과잉으로 잘못된 스킬 활성화 가능

**권고:**
- 100% 사용 스킬만 frontmatter preload.
- 나머지는 Skill tool로 on-demand 호출.

## 7. Sequential vs Parallel 도구 호출 [A035]

**Anthropic 공식:** "독립 도구 호출은 한 메시지에 묶어 병렬화."

위험:
- 메시지 N개 = 컨텍스트 누적 N번 → 토큰 비용 누적
- 사용자 카탈로그 runtime — 측정 필요

**권고 (이미 단일 세션 내):**
```
같은 메시지에서 grep + Read + ls 동시 호출 → 1 turn
순차 호출 → 3 turn (캐시 무효화 위험 + 컨텍스트 누적)
```

## audit.py 자동 검출

```bash
python3 scripts/audit.py --rules R3      # 5+ agent 하네스 검출
```

R3 룰: CLAUDE.md 하네스 메타에서 팀 카운트 → 5+ 비율 ≥ 50% 시 WARN, 80% 시 FAIL.

R3 출력 예시:
```
| `paper-maker` | 15 agents |
| `policyblind` | 8 agents  |
| `busan-policy-pledges` | 8 agents |
...
권고: 진입 전 게이트 '이거 단일 세션 가능?', Sonnet 팀원 재배정
```

## 메타 원칙 셀프 체크

본 tokensave 스킬 자체:

- [x] 5인 팀 — sonnet 3 + opus 2 (메타 원칙 적용)
- [x] Phase 1만 백그라운드 병렬 — 이후는 순차 (병렬 무의미)
- [x] 별도 QA 에이전트 없음 — 오케스트레이터 직접 (작은 검증은 별도 spawn 토큰 낭비)

## 인접 참고

- `references/anti_patterns_atlas.md` — C3.1~3.3, C6.1~6.3, C10.1~10.2 카드 8개.
- `scripts/audit.py R3` — 5+ 팀 검출.
- `scripts/estimate_cost.py --scenario harness=paper-maker` — 15인 팀 시나리오 vs 단일 세션 비교.
