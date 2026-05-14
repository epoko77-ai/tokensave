# Anti-Patterns Atlas (29 서브패턴 빠른 참조)

생성: 2026-05-14 · 출처: `taxonomy.md §2` + Scout A·B·C + 사용자 baseline

본 문서는 10대 카테고리 × 29 서브패턴 카드. 각 카드 1~2문장 + 출처 ID + 사용자 hit + 완화.

## 심각도 범례

- **S1** = 즉시 fix 필요 (외부 N≥2 + 사용자 baseline 위반)
- **S2** = 검토 필요 (외부 N≥1 또는 패턴 일치)
- **S3** = 모니터링 (사후 측정 시 등록)

## ★ = 헤드라인 카테고리

---

## C1 — Model Tier Misallocation ★

### C1.1 — All-Opus Anti-pattern (S1) ★★★

모든 agent에 `model: opus` 균일 할당. 단순 탐색·정형 출력에 Opus 사용은 -40%(Sonnet)~-80%(Haiku) 절감 기회 상실. 출처: [A001][A013][S-B017][S-B005][S-C02][S-C05]. **One operator's baseline: 103/104 = 99.0% 🔴** (see `examples/personal_baseline.md`).

**완화:** Haiku=read-only·탐색·간단 요약·boilerplate / Sonnet=표준 집필·코드·번역·정형 출력 / Opus=아키텍처·high-stake reasoning. `task_to_model_matrix.md` 24행 참조.

### C1.2 — Opus 4.7 Drop-in Upgrade Without Measurement (S2)

Claude Opus 4.7 업그레이드 후 토크나이저 +46% 인플레이션 [S-B008][S-B009] (Simon Willison). 측정 안 하면 체감 40% 가격 인상. **완화:** 업그레이드 전후 동일 prompt 토큰 카운트 비교.

### C1.3 — Session Mid-stream Model Switch (Cache Bust) (S2)

세션 중 `/model` 명령으로 모델 교체 시 캐시 전체 무효화 = 그 턴 5× 비용 [S-B007][A004][A007]. **완화:** 세션 시작 시 모델 고정. 다른 모델 필요 시 새 세션 또는 서브에이전트.

---

## C2 — Deterministic Work Routed Through LLM ★ (HD-003)

### C2.1 — Verbatim 1:1 Mapping in LLM (S1) ★★★

agent 본문에 `verbatim` / `BibTeX` / `cross-reference` / `regex 변환` 키워드 있는데 code-phase 부재. paper-maker pm-citation-formatter 91분→30초 (180×) 실측. 출처: [S-C07][S-C08][S-C01][S-C09]. **One operator's baseline: 20 RISKY agents 🔴** (see `examples/personal_baseline.md`). Top3: `uap-case-parser`(10,840자), `pm-evidence-curator`(det_kw=3), `uap-source-fetcher`(det_kw=3).

**완화:** Python phase 분리 + LLM은 edge case 판단만. 절감 -99% per agent. → `references/python_vs_llm_tree.md`

### C2.2 — Format/Citation Normalization in LLM (S1)

BibTeX 생성, 인용 스타일 변환, 날짜 포맷 정규화를 LLM에 위임. 출처: [S-C07][S-C09]. **완화:** `pybtex`·`csl-json`·`dateutil` 라이브러리. 절감 -99%.

### C2.3 — Data Parsing in LLM (CSV·HTML·PDF) (S1)

CSV→JSON, HTML 스크래핑, PDF 표 추출을 LLM이 처리. PDF 15p 45K→2K 토큰 (22×) 절감 가능 [S-B024][S-C09]. **완화:** `pandas`·`pypdf`·`BeautifulSoup`·`readability-lxml` 선처리. 절감 -90~-99%.

### C2.4 — Cross-reference / Dead Link Check in LLM (S2)

링크 유효성·참조 번호 매칭을 LLM에 위임. [S-C09][S-C07]. **완화:** `requests` + `concurrent.futures`, `linkchecker` CLI. 절감 -95%.

---

## C3 — Multi-Agent Team Composition (cost-optimized harness design)

> **C3 reframed (v1.0).** Multi-agent is justified — when 5 cost-optimization patterns are applied. C3 cards detect **missing patterns**, not the team itself. paper-maker 16-agent v1.4, ainews-daily 7+ pipeline, policyblind 8-agent cross-verify are operator examples of justified hierarchical/pipeline harnesses. audit.py R3 maps each card to a sub-rule (R3a~R3e). 3-tier decision: 5/5 met = PASS (well-formed) · 3-4/5 = WARN · 0-2/5 = FAIL (unjustified multiplier).
>
> Full matrix → `references/optimal_team_composition.md` (headline #3).

### C3.1 — 5+ Team without Role-Tier Model Mix (S1) ★★★ — audit.py R3a

5+ team에서 orchestrator·worker·reviewer 모두 동일 model 선언 → cost 곱연산의 1순위 원인. Anthropic 공식 [A001][A002] "Sonnet for teammates, Opus for orchestrator"; [A013] Haiku for explore; [S-B017][S-C02][S-C05]. **One operator's baseline: 103/104 = 99% opus; 5+ team 26/28 (93%) 중 role-tier 분기 보유 1건 🔴** (see `examples/personal_baseline.md`).

**완화:** orchestrator: Opus / worker: Sonnet 또는 Python / reviewer: Opus(high-stake)·Sonnet(standard). 절감 -40% per Sonnet teammate, -80% per Haiku scout. → `references/optimal_team_composition.md` P1.

### C3.2 — 5+ Team without Common-Context Caching (S1) ★★★ — audit.py R3b

5+ agent × N invocation = 공통 컨텍스트(SKILL.md, system prompt) 매번 선불. cache_control 4 breakpoint 부재 시 90% hit→80% input 절감 기회 상실. 출처: [A004][A005][S-B006][S-B028]. **사용자: 27/27 = 100% 0회 🔴** (R5와 부분 중첩, R3b는 5+ team 한정).

**완화:** 공통 system prompt + SKILL.md + 자주 호출 reference에 4 breakpoint. Sonnet 1024 / Opus 4096 최소 토큰. 절감 -90% input. → `references/prompt_caching_checklist.md`.

### C3.3 — 5+ Team without Parallel/Sequential Declaration (S2) — audit.py R3c

`병렬`/`순차`/`background`/`cascade`/`pipeline`/`하이브리드` 키워드 0회 — 의도적 실행 모드 선택의 부재. 잘못된 병렬 = rate-limit 폭주 [S-B003 49 병렬=887K tokens/min]; 잘못된 직렬 = wall-clock 폭증. 출처: [A003][S-B003][S-B004][S-C04].

**완화:** 각 Phase에 "병렬 N / sequential cascade / 하이브리드" 명시. background_tasks: N, wave 실행, fan-out/fan-in 정의. paper-maker "Phase 3 백그라운드 병렬" = 좋은 예. → `references/parallel_patterns.md`.

### C3.4 — 5+ Team without Wall-clock + Per-call Cap (S2) — audit.py R3d

각 agent에 wall-clock 한도, writer에 `per_call_cap: N자` 부재. runaway 차단 없으면 단일 agent 91분 트랩(HD-003) 또는 7K자 단일 호출(C9.1) 곱연산 폭발. 출처: [S-C05] 28.4% cost-of-pass; [S-C09] 58분. 

**완화:** agent 정의 또는 SKILL.md에 `wall_clock: 30min/50min`, `per_call_cap: 4000자`, `retry_count: ≤ 3`. paper-maker v1.3.1 wall-clock 분기 = 좋은 예 (C9.1과 중첩).

### C3.5 — 5+ Team without File-based Handoff (S2) — audit.py R3e

`_workspace/` · `산출물 트리` · `파일 기반` 컨벤션 부재 → SendMessage 남용 → cross-agent 토큰 누설 + 컨텍스트 격리 실패. 출처: [A023][S-C03].

**완화:** 모든 5+ team SKILL.md에 산출물 트리 명문화, agent 간 통신은 file read/write로. paper-maker `_workspace/01_scope ~ 15_build/`, busan-bukgu-research `_workspace/01_plan ~ 05_report/`, policyblind `_workspace/01_architecture ~ 08_qa/` = 좋은 예.

### C3.6 — Unjustified Hierarchy (Same-domain Reasoning Split) (S2)

같은 도메인 reasoning을 "더 철저하게 보이려고" 5인으로 분할 — 격리 가치 없음. 정당 조건: (a) 독립 reasoning domain, (b) 컨텍스트 격리, (c) 진정한 병렬, (d) tool/permission 경계, (e) persona specialization. 출처: [S-C04] reflexive 2.3× vs hierarchical 1.4×.

**완화:** 분할 전 정당 조건 1+ 만족 자문. paper-maker strict + adversarial reviewer 독립(정당) vs 임의 분할(anti-pattern). → `references/optimal_team_composition.md` "When 5+ team is/isn't justified".

---

## C4 — Context Bloat

### C4.1 — Bloated CLAUDE.md (>200 lines) (S1)

CLAUDE.md > 200 lines는 매 세션 고정 비용. 사용자 baseline 27 하네스 섹션 + 14.3 트리거/하네스. 출처: [A017][A024][A036][S-B004][S-B005][S-B006]. **완화:** 운영만 본문, 이력 changelog 분리, 워크플로 Skills 이전, HTML 주석 활용 [A025]. 절감 -50% (실측 N=2).

### C4.2 — Raw Log/Output in Main Context (S1)

10K줄 raw 로그를 컨텍스트에 붙여넣기. Anthropic hook 예시: grep으로 수백 토큰 [A016][S-B002][S-B010]. **완화:** PreToolUse hook grep, `BASH_MAX_OUTPUT_LENGTH=20000`, `2>&1 | grep -A5 ERROR | head -120`. 절감 -90~-99%.

### C4.3 — Dynamic Data Inside System Prompt (Cache Bust) (S2)

timestamp·세션 변동 데이터를 system prompt 상단에 두면 매 turn cache miss. [S-B007][A007]. **완화:** 동적 데이터를 user message로, `<system-reminder>` 분리. 절감 -80% (캐시 회복).

### C4.4 — Kitchen-sink Session (S2)

1시간+ 연속 세션에 여러 주제 누적. 2hr = 20min×3의 3배 비용 [S-B006]. 60% 도달 시 저하 [S-B016]. **완화:** `/clear` 무관 작업 사이, 60% 도달 전 `/compact`, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70`. 절감 -67%.

### C4.5 — Non-actionable Body Content Bloat (S2)

SKILL.md 본문에 장식·역사·메타 60%+. SkillReducer "55,315 skills 분석" [S-C02]. **사용자: 평균 8,693자 × 32 = 278K자 상시 압력, 60% 적용 시 ~167K자 비실행 🟡**. **완화:** 본문은 Phase·결정 트리·예시만. 장식 references/로.

---

## C5 — Prompt Caching Underuse

### C5.1 — cache_control Breakpoint Absence (S1) ★★★

system prompt + SKILL.md + 큰 reference에 `cache_control` 4 breakpoint 미적용. 출처: [A004][A005][S-B006][S-B028]. **사용자: 27/27 = 100% 0회 🔴**. **완화:** 4 breakpoint 적용 (system, skill, reference, accumulated). Sonnet 1024 / Opus 4096 최소 토큰. 절감 -80% input (90% hit rate). → `references/prompt_caching_checklist.md`

### C5.2 — Tool/MCP Set Change Mid-session (S2)

세션 중 MCP 추가/제거 시 캐시 무효화. [S-B007][A014]. **완화:** 세션 시작 시 tool set 고정.

### C5.3 — Cache TTL Mismatch (5min vs 1hr) (S3)

배치 / 1hr 파이프라인에 5min 캐시 사용 → 매번 만료. [A010][S-B028]. **완화:** 배치 / 장시간 작업은 1hr. 절감 -50~-80%.

---

## C6 — Subagent Spawn Overhead

### C6.1 — Small Task in Subagent (S2)

짧은 grep / 카운트에 Task tool 분기 = spawn 20K~85K 회수 불가. [S-B003][A019]. **완화:** rule of thumb: 절감치 > 30K tokens일 때만.

### C6.2 — Idle Team Not Disbanded (S2)

작업 완료 후 팀 미해산 시 background $0.04/session 누적 [A023]. **완화:** orchestrator 명시적 종료 명령, `max_idle_time` 설정.

### C6.3 — Skills Preload Without Need (S3)

agent frontmatter에 skills 다수 나열 → startup 시 모두 로드. [A015][A029]. **완화:** 100% 사용 스킬만 preload, 나머지 Skill tool on-demand.

---

## C7 — Tool Call Inefficiency

### C7.1 — Full File Read When Offset/Limit Possible (S2)

대형 파일 전체 Read. [A005][A039][S-B005]. **완화:** grep으로 라인 찾고 주변 read (offset/limit). 절감 수천 토큰/호출.

### C7.2 — Write Instead of Edit (S2)

기존 파일 수정에 Write 사용. Edit = diff만 전송. [A005]. **완화:** 기존 파일은 Edit 강제. 전송량 -90%+.

### C7.3 — MCP When CLI Available (S2)

`gh` / `aws` / `gcloud` CLI 대신 MCP 서버 사용. [A020][A039][S-B002]. **완화:** CLI 우선, 미사용 MCP 끊기. tool 정의 오버헤드 제거.

### C7.4 — Sequential When Parallel Possible (S3)

독립 도구 호출 순차 처리 → 메시지 N개 = 컨텍스트 누적 N번. [A035]. **완화:** 같은 메시지에 묶어 병렬화.

---

## C8 — Report/Artifact Loss (HD-010)

### C8.1 — Drafter Saves Artifact But Cuts Off in Report (S1)

drafter가 산출물은 디스크에 저장했지만 보고 텍스트가 끊김 → 사용자가 산출물 위치 모름 → 재실행. paper-maker 사용자 실측 1건. [S-C09][S-C03]. **완화:** output-first 컨벤션 — 산출물 경로 먼저 1줄 출력, 보고는 ≤200자.

---

## C9 — Per-Call Content Cap Missing (HD-011)

### C9.1 — Single Drafter Call Too Large (S1)

한 호출 출력 분량 미선언. pm-section-drafter 7,018자 정의 + per-call cap 0. Efficient Agents 28.4% cost-of-pass 개선 [S-C05]. 출처: [S-C02][S-C05][S-C09]. **완화:** per-call output cap + 자동 분할 (섹션 > 4K → 2 sub-call). 절감 -28.4% cost-of-pass.

---

## C10 — Architecture Pattern Mis-fit

### C10.1 — Reflexive Architecture Without Pareto Check (S2)

무한 재실행 루프 / iter cap 부재. 반사형 F1=0.943@2.3× vs 계층형 F1=0.921@1.4×; Hybrid 89%@1.15× = Pareto 최적 [S-C04]. **완화:** 계층형 baseline + 마지막 단계만 hybrid 재시도 (hard cap 3회). 절감 -40%. paper-maker editor-chief 3회 cap = 좋은 예.

### C10.2 — Feedforward Without Feedback (S3)

prompt 가이드만, linter/test/review 없음. Fowler "Guides + Sensors" 양쪽 필요 [S-C07][S-C08]. **완화:** guides (사전 prompt) + sensors (사후 검증) 두 루프 모두 정의.

---

## 우선순위 fix 순서 (사용자 baseline 기준)

1. **C5.1** caching 적용 — `paper-maker/SKILL.md` 23,138자 1순위 (즉시 -80% input)
2. **C1.1** opus 다운그레이드 — 14개 5K+ 비결정적 agent → Sonnet (각 -40%)
3. **C2.1** HD-003 Python 분리 — Top3 (uap-case-parser·pm-evidence-curator·uap-source-fetcher) (각 -99%)
4. **C3.1~C3.5** 5+ team missing-patterns — 26 multi-agent 하네스에 5개 최적화 패턴 적용 (`references/optimal_team_composition.md` 매트릭스). 절감: role-tier mix -40% per Sonnet teammate, cache_control -90% input, file-based handoff 컨텍스트 격리 보존.
5. **C9.1** per-call cap — writer/drafter agent 자동 분할 (-28.4% cost-of-pass)
6. **C4.1** CLAUDE.md changelog 분리 — 이미 부분 적용, 추가 -50%
7. **C8.1** report-first 컨벤션 — drafter / composer (재실행 비용 0)
8. **C4.5** SKILL.md references/ 분리 — 5K+자 스킬 (-60% non-actionable 추정)
9. **C10.1** 재시도 hard cap 3 — 다수 하네스 (-40%)
10. **C7.1/2/3/4** 도구 효율 — runtime 측정 후 적용

## 출처 키

- **A###** Anthropic 공식 — 40 인용 (Scout A)
- **S-B###** 커뮤니티 — 32 인용 (Scout B)
- **S-C##** 학술·실증 — 9 인용 (Scout C)
- **HD-###** 사용자 본인 harness-diagnostic 21갭 카탈로그 — 4개 채택

## 인접 참고

- `references/task_to_model_matrix.md` — C1 대응
- `references/python_vs_llm_tree.md` — C2 상세
- `references/prompt_caching_checklist.md` — C5 상세
- `references/parallel_patterns.md` — C3·C6·C10 상세
- `references/hook_examples.md` — 런타임 가드 (전 패턴 자동 경고)
- `scripts/audit.py` — 9 룰 자동 검출
