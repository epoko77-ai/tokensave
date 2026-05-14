# tokensave Pattern Taxonomy v1

생성: 2026-05-14 · 작성: token-pattern-taxonomist (opus)
출처: Anthropic 공식(Scout A·40 인용) + 커뮤니티 글로벌·한국(Scout B·32 소스) + 학술·실증(Scout C·9 소스) + 사용자 홈 카탈로그 실측(baseline.md)
채택 룰: **외부 독립 N ≥ 2 확증된 패턴만 본문 등록.** 사용자 baseline은 N=1이어도 hotspot 등록(외부 확증 마크).

---

## 0. 헤드라인 사실 (5줄)

1. **opus 99.0% (103/104 agents)** — Anthropic 공식 + community N≥5 + arXiv 2편 모두 backbone 다양화를 1순위 레버로 확증.
2. **멀티 에이전트 곱연산은 5개 패턴으로 정당화 가능** — 7×~15× per session 자체는 사실 [A003][S-B003] 그러나 (a) role-tier model mix, (b) common-context cache_control, (c) parallel/sequential 선언, (d) wall-clock cap, (e) file-based handoff 충족 시 비용·가치 균형. paper-maker v1.4·ainews-daily 같은 사용자 실측 패턴이 well-formed 사례. 26/28 하네스 5+ team — anti-pattern 아님, **missing-pattern** 여부가 핵심.
3. **HD-003 후보 20개** — 외부 N=3(Augment·Fowler·Zhang) + paper-maker 91분→30초 실측. Top3: `uap-case-parser`(10,840자), `pm-evidence-curator`(det_kw=3), `uap-source-fetcher`(det_kw=3).
4. **caching 0회 / 27 하네스** — ~660K자 반복 입력에 cache_control 0건. 공식 read=base의 10% + community N=3 실측(90% hit→80% 입력 절감). 미사용 레버 1순위.
5. **가격** — Opus $5/$25 vs Sonnet $3/$15 vs Haiku $1/$5 (per MTok). Opus→Sonnet -40%, Opus→Haiku -80%. Opus 4.7 토크나이저 +46% 인플레이션(Simon Willison).

---

## 1. 분류 체계 (10대 카테고리)

| ID | 카테고리 | 핵심 메커니즘 | 사용자 적용도 |
|----|---------|--------------|--------------|
| **C1** ★ | Model Tier Misallocation | 모든 역할에 균일 Opus | 🔴 99% (103/104) |
| **C2** ★ | Deterministic Work in LLM (HD-003) | regex·1:1·정규화 가능한 작업을 LLM | 🔴 20개 후보 |
| **C3** | Multi-Agent Team Composition (cost-optimized) | 5+ team의 5개 최적화 패턴(role-tier mix·caching·parallel·cap·file handoff) 누락 여부 | 🟡 26/28 multi-agent (정당 가능, missing-pattern 검사) |
| **C4** | Context Bloat | CLAUDE.md/로그/시스템 프롬프트 비대 | 🟡 SKILL.md 평균 8,693자 |
| **C5** | Prompt Caching Underuse | cache_control 부재, 동적 데이터 상단 | 🔴 27/27 (100%) |
| **C6** | Subagent Spawn Overhead | 작은 작업에 분기, 회수 불가 | 🟡 다수 |
| **C7** | Tool Call Inefficiency | 전체 Read, raw 로그, MCP 무제한 | 🟡 runtime |
| **C8** | Report/Artifact Loss (HD-010) | drafter가 보고 중 끊김 | 🔴 paper-maker |
| **C9** | Per-Call Content Cap Missing (HD-011) | 단일 호출 너무 큼 (58분/91분) | 🔴 paper-maker |
| **C10** | Architecture Pattern Mis-fit | 반사형 2.3× vs 계층형 1.4× Pareto | 🟡 다수 |

★ = 헤드라인.

---

## 2. 카테고리별 패턴 카드

### C1 — Model Tier Misallocation ★

**C1.1 All-Opus Anti-pattern · S1** — 트리거 `model: opus` ≥ 80%. 외부 [A001][A013][S-B017][S-B005][S-B018][S-B019][S-C02][S-C05] (Anthropic+community N=4+arXiv 2). 사용자 **103/104=99.0%**. 완화: Haiku=read-only·탐색·간단 요약·boilerplate / Sonnet=표준 집필·코드·번역 / Opus=아키텍처·high-stake. 절감 -40%(Sonnet)~-80%(Haiku). 메타 위반 ★★★

**C1.2 Opus 4.7 Drop-in Upgrade Without Measurement · S2** — 외부 [S-B008] Simon Willison 시스템 프롬프트 +1.46×; [S-B009] +46% 토큰. 완화: 업그레이드 전후 토큰 측정. 절감 -40%(보정 시)

**C1.3 Session Mid-stream Model Switch (Cache Bust) · S2** — 외부 [S-B007] 캐시 전체 무효화 그 턴 5×; [A004][A007]. 완화: 세션 모델 고정, 다른 모델은 새 세션

### C2 — Deterministic Work Routed Through LLM ★ (HD-003)

**C2.1 Verbatim 1:1 Mapping in LLM · S1** — 트리거 agent 본문 `verbatim`/`BibTeX`/`cross-reference` + code-phase 부재. 외부 [S-C07] Fowler "computational vs inferential"; [S-C08] Augment "probabilistic vs deterministic"; [S-C01] Zhang 2026; [S-C09] HD-003 91분→30초. 사용자 **20 RISKY**, Top3: uap-case-parser(10,840자), pm-evidence-curator(det_kw=3), uap-source-fetcher(det_kw=3). 완화: Python phase + LLM은 판단만. 절감 **-99%**. 메타 위반 ★★★

**C2.2 Format/Citation Normalization in LLM · S1** — 외부 [S-C07][S-C09]. 완화: csl-json/pybtex/dateutil. 절감 -99%

**C2.3 Data Parsing in LLM (CSV·HTML·PDF) · S1** — 외부 [S-B024] PDF 15p 45K→2K markdown (22×); [S-C09]. 완화: pandas/pypdf/BeautifulSoup. 절감 -90~-99%

**C2.4 Cross-reference / Dead Link Check in LLM · S2** — 외부 [S-C09][S-C07]. 완화: requests + linkchecker CLI

### C3 — Multi-Agent Team Composition (cost-optimized harness design)

**원칙:** 멀티에이전트 자체는 **정당**. paper-maker 16-agent v1.4·ainews-daily 7+ pipeline·policyblind 8-agent cross-verify·book-infographic-deck 9-agent mixed 등 사용자 실측이 hierarchical/pipeline 구조의 가치를 증명한다. 문제는 5+ team을 띄울 때 **5 cost-optimization 패턴**(role-tier mix · 공통 컨텍스트 캐싱 · 병렬·직렬 의도 선언 · wall-clock cap · file-based handoff)이 빠지면 곱연산(7×~15×)이 가치를 따라잡지 못한다는 점. C3 서브패턴은 **anti-pattern이 아니라 missing-pattern**으로 읽는다 — "여러 명이라 비싸다"가 아니라 "여러 명일 때 X 안 하면 비싸다".

채택 룰 3-tier: 5/5 충족 → PASS (well-formed) · 3~4/5 → WARN · 0~2/5 → FAIL (unjustified). audit.py R3 sub-rule 매핑 1:1.

**C3.1 5+ Team without Role-Tier Model Mix · S1** — orchestrator·worker·reviewer 모두 동일 model 선언(예: 전원 opus) → cost 곱연산의 1순위 원인. 외부 [A001] Anthropic "Sonnet for teammates, Opus for orchestrator"; [A013] Haiku for explore; [A002] Sonnet teammates; [S-B017][S-C02][S-C05]. 사용자 **103/104=99% opus (C1.1과 중첩)** — 5+ team 26/28 (93%) 중 role-tier 분기 보유 1건. 완화: orchestrator Opus / worker Sonnet 또는 Python / reviewer Opus(high-stake)·Sonnet(standard). 절감 -40% per Sonnet teammate, -80% per Haiku scout. audit.py R3a.

**C3.2 5+ Team without Common-Context Caching · S1** — 공통 system prompt / SKILL.md / reference에 `cache_control` breakpoint 부재. 5+ agent × N invocation = 공통 컨텍스트 매번 선불. 외부 [A004][A005] 공식 read=10% base; [S-B006] 90% hit→80% input 절감; [S-B028] 60~90% production. 사용자 **27/27 (100%) 0회**(R5와 부분 중첩, R3b는 5+ team 한정 — 단일 세션 스킬은 C5.1만 적용). 완화: SKILL.md + system block + 자주 호출 reference에 4 breakpoint. 절감 -90% input. audit.py R3b.

**C3.3 5+ Team without Parallel/Sequential Declaration · S2** — `병렬`/`순차`/`background`/`cascade`/`pipeline`/`하이브리드` 키워드 0회 — 의도적 실행 모드 선택의 부재. 잘못된 병렬 = rate-limit 폭주 [S-B003 49 병렬=887K tokens/min]; 잘못된 직렬 = wall-clock 폭증. 외부 [A003][S-B003][S-B004][S-C04] arXiv. 사용자 baseline: 28 하네스 중 의도 선언 명시 약 12개(paper-maker "Phase 3 백그라운드 병렬", busan-bukgu-research "에이전트 팀 병렬" 등 정상 패턴). 완화: 각 Phase에 "병렬 N / sequential cascade" 명시. audit.py R3c.

**C3.4 5+ Team without Wall-clock + Per-call Cap · S2** — 각 agent에 soft/hard wall-clock 한도, writer agent에 `per_call_cap: N자` 부재. runaway 차단 없으면 단일 agent가 91분 트랩(HD-003) 또는 7K자 단일 호출(C9.1)로 곱연산 폭발. 외부 [S-C05] 28.4% cost-of-pass; [S-C09] paper-maker 58분. 사용자 baseline: paper-maker v1.3.1·v1.4가 wall-clock 분기 명시(좋은 예) — 다른 5+ team은 대체로 미명시. 완화: agent 정의 frontmatter 또는 SKILL.md에 `wall_clock: 30min/50min`, `per_call_cap: 4000자`. audit.py R3d (C9.1과 중첩).

**C3.5 5+ Team without File-based Handoff · S2** — `_workspace/` · `산출물 트리` · `파일 기반` 컨벤션 부재. SendMessage 남용 시 cross-agent 토큰 누설 + 컨텍스트 분리 실패. 외부 [A023] subagent 컨텍스트 격리; [S-C03] tokenomics file-based. 사용자 baseline: paper-maker `_workspace/01_scope ~ 15_build/`, busan-bukgu-research `_workspace/01_plan ~ 05_report/`, policyblind `_workspace/01_architecture ~ 08_qa/` 등 다수 정상 패턴. 완화: 모든 5+ team SKILL.md에 산출물 트리 명문화, agent 간 통신은 파일 read/write로 강제. audit.py R3e.

**C3.6 Unjustified Hierarchy (Same-domain Reasoning Split) · S2** (외부 N=1+사용자 hotspot) — 같은 도메인 reasoning을 "더 철저하게 보이려고" 5인으로 분할 — 격리 가치 없음. 외부 [S-C04] reflexive 2.3× vs hierarchical 1.4×. 사용자 baseline: paper-maker strict + adversarial reviewer 독립 (격리 정당 — 좋은 예) vs 임의 분할 (anti-pattern). 정당 조건: (a) 독립 reasoning domain, (b) 컨텍스트 격리, (c) 진정한 병렬, (d) tool/permission 경계, (e) persona specialization. 완화: 분할 전 정당 조건 1개 이상 만족 자문. 자세히 → `references/optimal_team_composition.md`.

### C4 — Context Bloat

**C4.1 Bloated CLAUDE.md (>200 lines) · S1** — 외부 [A017][A024][A036] 공식; [S-B004][S-B005][S-B006] N=3 실측(400→150=-50%). 사용자 27 섹션 + 14.3 트리거/하네스. 완화: 운영만 본문, 이력 changelog, 워크플로 Skills, HTML 주석[A025]. 절감 **-50%**

**C4.2 Raw Log/Output in Main Context · S1** — 외부 [A016] 공식 10K줄→grep→수백 토큰; [S-B002][S-B010]. 완화: PreToolUse hook grep, `BASH_MAX_OUTPUT_LENGTH=20000`. 절감 -90~-99%

**C4.3 Dynamic Data Inside System Prompt (Cache Bust) · S2** — 외부 [S-B007] 20+ percentage point loss; [A007]. 완화: 동적 데이터 user message로, `<system-reminder>` 분리. 절감 -80%

**C4.4 Kitchen-sink Session · S2** — 외부 [A040]; [S-B006] 2hr=20min×3의 3배; [S-B016] 60%=저하. 완화: /clear, /compact 60% 전, `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70`. 절감 -67%

**C4.5 Non-actionable Body Content Bloat · S2** (외부 N=1, 사용자 hotspot) — 외부 [S-C02] SkillReducer "60% non-actionable" (55,315 skills). 사용자 평균 SKILL.md 8,693자, 최대 32,987자 (skill-creator). 32×8,693=278K자 상시 압력, 60% 적용 시 ~167K자 비실행. 완화: Phase·결정 트리·예시는 본문, 장식은 references/

### C5 — Prompt Caching Underuse

**C5.1 cache_control Breakpoint Absence · S1** — 외부 [A004][A005] 공식(read=10%, 90% 절감); [S-B006] 90% hit→80% 절감; [S-B028] 60~90% production. 사용자 **27/27 (100%) 0회**. 완화: system+SKILL.md+큰 reference에 breakpoint 4개, 최소 길이 Sonnet 1,024/Opus 4,096. 절감 **-80% 입력**

**C5.2 Tool/MCP Set Change Mid-session · S2** — 외부 [S-B007]; [A014]. 완화: 세션 툴 set 고정

**C5.3 Cache TTL Mismatch (5min vs 1hr) · S3** — 외부 [A010]; [S-B028]. 완화: 배치/장시간은 1hr. 절감 -50~-80%(배치)

### C6 — Subagent Spawn Overhead

**C6.1 Small Task in Subagent · S2** — 외부 [S-B003] spawn 20K~85K; [A019]. 완화: 절감치 > 30K일 때만

**C6.2 Idle Team Not Disbanded · S2** (외부 N=1, 공식) — 외부 [A023]. 완화: 작업 완료 후 즉시 해산

**C6.3 Skills Preload Without Need · S3** — 외부 [A015][A029]. 완화: 100% 사용 스킬만 preload

### C7 — Tool Call Inefficiency

**C7.1 Full File Read When Offset/Limit Possible · S2** — 외부 [A005][A039]; [S-B005]. 완화: grep으로 라인 찾고 주변 read

**C7.2 Write Instead of Edit · S2** (공식+합의, 개별 N=1) — 외부 [A005]. 완화: 기존 파일은 Edit 강제

**C7.3 MCP When CLI Available · S2** — 외부 [A020][A039]; [S-B002]. 완화: gh/aws/gcloud 우선, 미사용 MCP 끊기

**C7.4 Sequential When Parallel Possible · S3** (공식+합의, N=1) — 외부 [A035]. 완화: 독립 호출 묶어 병렬

### C8 — Report/Artifact Loss (HD-010)

**C8.1 Drafter Saves Artifact But Cuts Off in Report · S1** (외부 구조 N=1, 사용자 hotspot) — 외부 [S-C09] HD-010 paper-maker 1건; [S-C03] Tokenomics 구조 "59.4% 반복 리뷰" — 재실행 시 반복 통과. 완화: report-first — 산출물 경로 먼저, 보고 ≤200자

### C9 — Per-Call Content Cap Missing (HD-011)

**C9.1 Single Drafter Call Too Large · S1** — 외부 [S-C02] "수만 토큰/invocation"; [S-C05] 28.4% cost-of-pass 개선; [S-C09] 58분. 사용자 pm-section-drafter(7,018자) + 다른 drafter. 완화: per-call cap + 자동 분할(섹션>4K→2 sub-call). 절감 **-28.4% cost-of-pass**

### C10 — Architecture Pattern Mis-fit

**C10.1 Reflexive Architecture Without Pareto Check · S2** (외부 N=1, 사용자 hotspot) — 외부 [S-C04] Reflexive F1=0.943@2.3× vs Hierarchical F1=0.921@1.4×; Hybrid 89%@1.15×. 사용자 paper-maker editor-chief 3회 cap(좋은 예). 완화: 계층형 baseline + hybrid, 재시도 cap 3. 절감 -40%

**C10.2 Feedforward Without Feedback · S3** — 외부 [S-C07] Fowler "Guides + Sensors"; [S-C08] Augment "deterministic outer-harness". 완화: 두 루프 모두 정의

---

## 3. ★ Task → Model 매트릭스

가격: [A005] Anthropic 공식 per MTok base.

| # | 작업 유형 | 추천 | 근거 출처 | vs Opus |
|---|----------|------|-----------|---------|
| 1 | 결정적 변환(regex 가능) — citation·BibTeX·1:1·포맷 | **Python** | [S-C07][S-C08][S-C09] | free |
| 2 | 파일 탐색·grep·코드베이스 search | **Haiku** | [A013][S-B016][S-B031] | -80% |
| 3 | 패턴매칭·룰 분류(short input) | **Haiku** | [A013][S-B017][S-B031] | -80% |
| 4 | 짧은 정형 요약(≤1단락) | **Haiku** | [S-B031][S-B017] | -80% |
| 5 | 자연어 정형 출력(JSON·표) | **Sonnet** | [A001][S-B017][S-B018] | -40% |
| 6 | 표준 코드·디버깅 | **Sonnet** | [A001][S-B016][S-B017] | -40% |
| 7 | 멀티턴 코드 리뷰 | **Sonnet** | [A001][S-B017] | -40% |
| 8 | 문서 집필(≤5,000자) | **Sonnet** | [A001][S-B018] | -40% |
| 9 | 학술/정책 페이퍼(high-stake, 5K+자) | **Opus** | [S-C09] | 0% (정당) |
| 10 | 깊은 reasoning·아키텍처 결정 | **Opus** | [A001] | 0% (정당) |
| 11 | 창의적 자유 생성(5K+자, 톤 중요) | **Opus** | [A001] | 0% (정당) |
| 12 | 팩트체크(일반) | **Sonnet** | [A001][S-B017] | -40% |
| 13 | 팩트체크(학술 high-stake) | **Opus** | [S-C09] | 0% (정당) |
| 14 | 번역(실용 일상) | **Sonnet** | [A001][S-B018] | -40% |
| 15 | 번역(문학·격조) | **Opus** | [S-B016] | 0% |
| 16 | ESL/언어교육 콘텐츠 | **Sonnet** | [A001] | -40% |
| 17 | 시각·이미지 프롬프트 설계 | **Sonnet** | [A001] | -40% |
| 18 | 데이터 파싱(CSV→JSON, HTML, PDF 표) | **Python** | [S-B024][S-C07] | free |
| 19 | 카탈로그/메타 정합성 점검 | **Python** | [S-C07] | free |
| 20 | 짧은 FAQ 응답 | **Haiku** | [S-B031][S-B017] | -80% |
| 21 | 에이전트 팀 팀원(조정 작업) | **Sonnet** | [A002] | -40% |
| 22 | 코드베이스 탐색 서브에이전트 | **Haiku** | [A013] | -80% |
| 23 | 보일러플레이트·간단 수정 | **Haiku** | [S-B031] | -80% |
| 24 | log/output 압축(grep) | **Python/shell** | [A016] | free |

**핵심 규칙:** "결정적으로 표현 가능" → Python · "자연어 정형 출력·표준 코딩" → Sonnet · "복잡 reasoning·창의·high-stake"만 Opus.

---

## 4. 채택 vs 미채택 결정 표

| 출처 패턴 | 외부 N | 채택? | 카테고리 |
|----------|--------|------|---------|
| HD-003 결정적 LLM 라우팅 | 3+사용자 | ✅ ★ | C2 |
| HD-010 report-first | 0 직접/구조 1 | ✅ hotspot | C8 |
| HD-011 per-call cap | 2 | ✅ ★ | C9 |
| HD-020 uniform model | 2 | ✅ ★ | C1.1 |
| HD-007 parallel size | 1 부분 | 부분 | C3.2·C10.1 |
| HD-001 orchestration faults | 1 | 미채택 본문 (참고만) | — |
| HD-002·004·005·006·008·012·013·014·015·017 | 0 | 미채택 | — |
| HD-009 wall-clock budget | 0 | 미채택 (v2 후보, 사용자 6/27 언급) | — |
| HD-016 signal consumers | 1 | 부분 | C10.2 |
| HD-018 progress instrumentation | 1 구조 | 부분 (C8 인접) | — |
| HD-019 관찰 / HD-021 해결 | N/A | N/A | — |
| N1 라우팅 설명 부재 | 1 | v2 후보 (사용자 카탈로그 반대) | — |
| N2 비실행 콘텐츠 60%+ | 1 | ✅ hotspot | C4.5 |
| N3 계층형 Pareto | 1 | ✅ hotspot | C10.1 |
| N4 Plan-Execute-Verify | 1 | ✅ (Augment 합산 시 N=2) | C10.2 |
| N5 토큰 경제학 68× | 1 | 컨텍스트 메모(본문 미등록) | — |

**채택 확정 (외부 N≥2):** 24 패턴 (C1.1·1.2·1.3·C2.1·2.2·2.3·2.4·C3.1·3.2·3.3·C4.1·4.2·4.3·4.4·C5.1·5.2·5.3·C6.1·6.2·6.3·C7.1·7.2·7.3·7.4·C9.1·C10.2)
**사용자 hotspot 등록 (외부 N=1+사용자 baseline):** 4 패턴 (C4.5·C8.1·C10.1)
**총 29 서브패턴 / 10 카테고리.**

---

## 5. 사용자 실측 hotspot top 10

| # | 패턴 | 사용자 영향 | 권고 |
|---|------|-----------|------|
| 1 | **C1.1** All-Opus | 103/104 (99.0%) | structural-visual-designer·ainews-delivery-engineer 등 14개 5k+ 즉각 Sonnet; read-only는 Haiku |
| 2 | **C2.1** HD-003 RISKY | 20 agents | Top3 Python phase 분리: uap-case-parser(10,840자), pm-evidence-curator(det_kw=3), uap-source-fetcher(det_kw=3) |
| 3 | **C5.1** Caching 0회 | 27/27 (100%) | paper-maker SKILL.md(23,138자) 1순위로 cache_control 적용 |
| 4 | **C3.1~C3.5** 5+ team missing-patterns | 26/28 (93%) multi-agent · 15개 FAIL (0~2/5 패턴 충족) | `references/optimal_team_composition.md` 매트릭스 적용 — role-tier mix·cache_control·병렬 선언·wall-clock cap·file handoff |
| 5 | **C4.5** SKILL.md 비실행 | 32×8,693 = 278K자 | 본문 5K+자 스킬 references/ 분리 |
| 6 | **C4.1** CLAUDE.md bloat | 27 섹션 + 14.3 트리거/하네스 | 운영만 본문, 이력 changelog, 워크플로 Skills |
| 7 | **C9.1** Per-call cap | pm-section-drafter(7,018자) + 다른 drafter | per-call output cap + 자동 분할 |
| 8 | **C3.3** Spawn 오버헤드 | 14/27 = 8+ agents (52%) | Brief 룰: 절감 > 30K tokens일 때만 |
| 9 | **C10.1** Reflexive | 다수 재시도 루프 | hard cap 3회, 계층형 baseline + hybrid |
| 10 | **C8.1** Artifact loss | paper-maker 1건 + drafter 잠재 | 산출물 경로 먼저, 보고 200자 cap |

---

## 6. 운영 메모

**N≥2 룰 본문 등록 예외:**
- C8.1(HD-010) — 외부 동일 용어 0, Tokenomics 구조 일치 + paper-maker 실측 → hotspot.
- C4.5·C10.1 — Scout C 학술 1편씩 + 사용자 baseline 직접 적용 → 등록. 외부 N≥2 확보 시 정식.
- C6.2·C7.2·C7.4 — Anthropic 공식 + 커뮤니티 합의로 본문 등록.

**외부 미확증 HD 13개 미등록:** HD-002·004·005·006·008·009·012·013·014·015·017·018·019 — paper-maker 내부만 관찰, "참고만" 표시.

**v2 후보:** N1 라우팅 설명 부재(사용자 카탈로그는 반대 패턴), HD-009 wall-clock budget(사용자 6/27 언급, paper-maker만 본격).

**분류학 버전:** v1 (2026-05-14). **갱신 트리거:** 외부 N≥2 신규 / baseline 재측정 / 신규 메커니즘.
