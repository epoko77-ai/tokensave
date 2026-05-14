---
name: plz-save-token
description: Claude Code 하네스의 토큰 낭비를 사전·사후 점검·재작성 가이드로 차단하는 메타 스킬. 모델 티어 오배분(Opus 99%)·결정적 작업의 LLM 위임(HD-003 트랩)·멀티에이전트 팀 구성 미최적화(role-tier mix·common cache·parallel/serial 선언·wall-clock cap·file-based handoff 5 missing-patterns)·프롬프트 캐싱 0회·SKILL.md 비대화 등 10대 카테고리·31 서브패턴을 카탈로그하고, 4가지 모드(PRE-FLIGHT 사전 점검·AUTHORING 신규 스킬/에이전트 설계·AUDIT 기존 하네스 감사·HOOK 런타임 자동 가드) + 3 headline matrix(task→model · model_selector CLI · optimal team composition)로 활용한다. 멀티에이전트 자체는 정당, 단 비용 최적화된 멀티에이전트를 빌드하는 가드. 트리거 — "토큰 절감", "plz-save-token", "이 작업 모델 뭐가 적절해", "이거 LLM 안 쓰고 파이썬으로 되나", "내 하네스 감사해줘", "오퍼스 남용 점검", "프롬프트 캐싱 어떻게", "에이전트 병렬 vs 순차", "스킬 만들 때 토큰 절약", "모델 선택", "Sonnet vs Opus", "Haiku로 충분", "결정적 작업 분리", "비용 추정", "5+ 팀 정당화", "멀티에이전트 비용 최적화", "감사 다시", "캐싱 도입", "context bloat", "SKILL.md 너무 크다". 후속 작업 — "패턴 추가", "감사 재실행", "모델 재추천", "비용 비교", "팀 구성 검토" 도 동일 스킬.
version: 1.0
meta_skill: true
---

# plz-save-token — Claude Code 토큰 낭비 사전·사후 차단 메타 스킬

> **메타 스킬 예외 선언.** 본 스킬은 4모드 + 3 headline matrix + 분류학 카탈로그를 한 번에 활성화해야 즉시 가치가 나오는 메타 카테고리다. 따라서 자기 자신의 R4(컨텍스트 비대)·R9(SKILL.md 비실행 비대) 룰은 예외 적용 — `audit.py`가 `meta_skill: true` frontmatter 인식 시 R4·R9 WARN 자동 제외. 다만 발동 ROI는 명시: 1회 발동 ≈ 10K input(≈ $0.15 Opus) vs 하네스 1개 비용 최적화 적용 -60~75% (수십\$ 절감) = 수백배 ROI. 매 세션 자동 부담은 frontmatter description ~200자만, 본문은 사용자 명시 발동 시에만 주입.

## Mandatory Activation Rules (Zero Tolerance)

**아래 조건 중 하나라도 해당하면 이 스킬이 즉시 활성화된다. 우회·연기 금지.**

1. 사용자가 "토큰 절감 / plz-save-token / 모델 선택 / 캐싱 / 하네스 감사 / 오퍼스 남용" 키워드 중 하나를 입력한다.
2. 사용자가 **신규 스킬·에이전트·하네스 설계를 시작**한다. 트리거: "스킬 만들어줘", "에이전트 추가", "하네스 구성", "팀 구성", "5인 팀" 등.
3. 사용자가 **에이전트를 spawn하기 직전**(Task tool 호출 직전) — `MODE 1 PRE-FLIGHT` 자동 실행.
4. 사용자가 **결정적으로 표현 가능한 작업**(verbatim·1:1 매핑·BibTeX·regex·CSV·JSON 정규화·dead link·해시·grep·카운트)을 LLM에 시키려 한다 — `Python 권고 게이트` 발동.
5. 사용자가 **5+ agent 팀**을 띄우려 한다 — `optimal team composition gate` 발동 (MODE 1 Step 3, 5 cost-optimization 패턴 자가 체크).

**기본 행동:** 사용자가 이 스킬을 명시적으로 부르지 않아도, Agent tool 호출 직전 또는 SKILL.md/에이전트 정의 편집 직전에 결정 트리(§MODE 1·2)를 따라 self-check를 거친다.

---

## 4대 메타 원칙 (제일 중요)

1. **결정적 작업은 Python, LLM은 판단·재작성·우선순위에만.** HD-003 패턴 위반은 91분→30초(180×) 절감 실측이 존재한다 [S-C09]. 이 스킬 자체의 결정 트리·룰 매칭·검출 로직은 모두 코드(`scripts/audit.py`, `scripts/model_selector.py`)로 짠다. LLM은 코드가 만든 후보 목록을 보고 우선순위·완화책만 판단한다.
2. **모델 티어 분기 필수.** 모든 작업에 Opus는 토큰 낭비. Haiku = read-only·탐색·룰 분류. Sonnet = 표준 집필·코드·정형 출력·번역. Opus = 아키텍처·high-stake reasoning·창의 5K+자만. 사용자 baseline 99.0% opus는 **anti-pattern 확정** [Anthropic A001·A013, S-C02, S-C05].
3. **멀티에이전트는 정당, 단 비용 최적화된 멀티에이전트.** 5+ team 곱연산(7×~15×) [A003]은 사실이고 paper-maker·ainews-daily·policyblind 같은 well-formed 사례가 가치를 증명한다. 진입 전 게이트는 "팀 띄우지 마"가 아니라 **5 cost-optimization 패턴 자가 체크** — role-tier mix, cache_control, parallel/serial 선언, wall-clock cap, file-based handoff. 자세히 → `references/optimal_team_composition.md`.
4. **메타 위반은 즉각 보고.** 이 스킬을 사용하는 과정 자체가 위반(예: opus로 결정적 grep 작업)을 하면 사용자에게 **shame token** 출력 — "본 스킬 메타 원칙 위반 발생, 다음 호출에서 수정 권고".

---

## 실측 baseline 예시 (one operator's catalog — 메타 원칙 강화)

> The numbers below come from **one operator's** Claude Code setup (27 harnesses, 104 agents, 32 skills),
> audited on 2026-05-14. Run `python3 scripts/audit.py` against your own catalog to get your numbers.
> Full data → `examples/personal_baseline.md`.

`<your-plz-save-token-dir>/_workspace/02_audit/baseline.md` — static measurement from one operator's catalog (2026-05-14).
See `examples/personal_baseline.md` for the full data.

| # | 사실 | 출처 |
|---|------|------|
| H1 | **opus 99.0%** (103/104 agents) — 단일 모델 전략 | baseline §1 + [A001][A013][S-C02][S-C05] |
| H2 | **prompt caching 언급 0회** / 27 하네스 (100%) | baseline §4 + [A004][A005][S-B028] |
| H3 | **5+ agent 하네스 93%** (25/27), 8+ 52%, Paper Maker 15인 — 멀티에이전트 자체는 정당, 5 cost-optimization 패턴 충족 여부가 핵심 | baseline §4 + [A003][S-B003] + `references/optimal_team_composition.md` |
| H4 | **HD-003 RISKY 20 agents** — uap-case-parser(10,840자), pm-evidence-curator(det_kw=3), uap-source-fetcher(det_kw=3) | baseline §3 + [S-C07][S-C08][S-C09] |
| H5 | **SKILL.md 평균 8,693자**, 최대 32,987자 (skill-creator), 32개 합 278K자 상시 컨텍스트 압력 | baseline §6 + [S-C02] |

이 5개 사실이 본 스킬 활성화·우선순위·재작성 권고의 근간이다. 새 작업을 시작할 때 항상 이 수치를 떠올려라 — "내가 지금 또 99% opus를 만들고 있는가?"

> **Note for contributors:** These numbers are from one operator's catalog. Run `audit.py` on your own setup — your baseline will differ. Contribute your findings to help grow the catalog.

---

## MODE 1: PRE-FLIGHT (작업 시작 전 사전 점검) ★

사용자가 새 작업을 요청했을 때 LLM 첫 응답 전 self-check 3단계.

### Step 1 — 이거 LLM 정말 필요한가?

작업 설명에 다음 결정적 keyword가 보이면 **Python 권고 게이트** 발동:

| 결정적 keyword | 대안 Python 도구 | 절감 |
|---------------|-----------------|------|
| regex·verbatim·1:1 매핑 | `re` 모듈 | -99% |
| BibTeX·citation 정규화 | `pybtex`·`csl-json` | -99% |
| CSV→JSON·HTML→JSON·PDF 표 | `pandas`·`pypdf`·`BeautifulSoup` | -90~-99% |
| dead link·HTTP 200 체크 | `requests` + `linkchecker` | -95% |
| 파일 grep·카운트·해시 | `grep`·`wc`·`sha256sum` | free |
| 날짜·포맷 정규화 | `dateutil`·`strftime` | -99% |
| cross-reference 매칭 | `dict` lookup + JSON | -99% |

**실행:** `python scripts/model_selector.py --task "<자연어 작업 설명>"` 호출 → Python 우선 분기 자동 추천.

**근거:** [S-C07] Fowler "computational vs inferential sensors" / [S-C08] Augment "deterministic outer-harness" / [S-C09] paper-maker pm-citation-formatter 91분→30초 사용자 실측 / [S-B024] PDF 15p 45K→2K tokens(22×) 절감.

### Step 2 — 모델 티어 무엇이 적절한가?

`scripts/model_selector.py`가 결정 트리(LLM 호출 0회) 적용:

- **Haiku** (-80% vs Opus): read-only 탐색·grep·짧은 정형 분류·룰 기반·짧은 정형 요약·boilerplate. 가격 $1/MTok input.
- **Sonnet** (-40% vs Opus): 자연어 정형 출력·JSON/표 생성·표준 코드·디버깅·코드 리뷰·실용 번역·문서 ≤ 5,000자·팩트체크 일반·에이전트 팀원·시각/이미지 프롬프트. 가격 $3/MTok.
- **Opus** (정당 0%): 깊은 reasoning·아키텍처 결정·창의 5,000자+ 톤 중요·학술/정책 페이퍼 high-stake·문학 번역·high-stake 팩트체크. 가격 $5/MTok input · $25 output.

상세 24행 매트릭스 → `references/task_to_model_matrix.md`.

### Step 3 — 멀티 에이전트 구성이 비용 최적화됐는가?

5+ team을 띄우려 한다면 다음 5개 자가 체크. **이건 멀티에이전트를 막는 게 아니라 곱연산을 정당화하는 가드.** paper-maker 16-agent v1.4·ainews-daily 7+ pipeline·policyblind 8-agent cross-verify 등 사용자 실측 패턴이 hierarchical/pipeline 구조의 가치를 증명한다. 문제는 5 최적화가 빠질 때 곱연산이 가치를 따라잡지 못한다는 점.

| # | 자가 체크 | 충족 시 효과 |
|---|----------|------------|
| 1 | orchestrator만 Opus, worker는 Sonnet, reviewer는 high-stake만 Opus — role-tier 분기? | -40% per Sonnet teammate, -80% per Haiku scout |
| 2 | 공통 system/SKILL block에 cache_control 4 breakpoint? | -90% input (hit rate 90%) |
| 3 | 병렬·직렬 의도적 선언? (background N / sequential cascade / 하이브리드) | wall-clock + retry 곱연산 회피 |
| 4 | per-agent wall-clock + per-call output cap? | runaway 차단, -28.4% cost-of-pass |
| 5 | file-based handoff (`_workspace/` 산출물 트리)? SendMessage 남용 회피? | 컨텍스트 격리 보존, 토큰 누설 방지 |

**3-tier 판정 (audit.py R3 sub-rules R3a~R3e 1:1 매핑):**

- 체크 5/5 → 5+ team **PASS (well-formed)**. `references/optimal_team_composition.md` 매트릭스 검증만.
- 체크 3~4/5 → **WARN — 누락 항목 우선 보강.** 같은 매트릭스에서 missing 패턴 적용.
- 체크 0~2/5 → 5+ team **FAIL (unjustified multiplier)**. 7×~15× 곱연산 [A003][S-B003]을 5개 패턴 없이 지불 중 — `optimal_team_composition.md` 처음부터 적용 권고.

**근거:** 멀티에이전트 자체는 정당. 사용자 28 하네스 중 26 (93%)이 5+ team이고, paper-maker·ainews-daily·policyblind 같은 well-formed 사례가 가치를 증명한다. C3 검출은 anti-pattern이 아니라 **missing-pattern** — "여러 명이라 비싸다"가 아니라 "여러 명일 때 X 안 하면 비싸다" [A001·A002·A004·S-B003·S-C04].

**비용 비교:** `python scripts/estimate_cost.py --scenario harness=<name>` 로 정량. `python scripts/audit.py /path/to/harness --rules R3` 로 5 sub-rule별 현재 상태 즉시 확인.

---

## MODE 2: AUTHORING (신규 스킬·에이전트 설계 가이드) ★

### 9대 금지 패턴 체크리스트 (스킬·에이전트 작성 직전 self-review)

신규 SKILL.md / agent.md 파일을 Write/Edit 하기 전 다음 9가지 self-check. 하나라도 ✗이면 **수정 후 재제출.**

| # | 금지 패턴 | 카테고리 | 자가 체크 질문 |
|---|----------|---------|---------------|
| 1 | 모든 agent `model: opus` 고정 | C1.1 | 이 agent가 정말 reasoning·창의·high-stake 인가? read-only/탐색이면 Haiku, 정형 출력이면 Sonnet 강제 |
| 2 | Opus 4.7 업그레이드 후 토큰 측정 누락 | C1.2 | Opus 4.7 토크나이저 +46% 인플레이션 [S-B008][S-B009] — 업그레이드 전후 동일 prompt 토큰 카운트 비교 했는가? |
| 3 | 결정적 키워드(verbatim·BibTeX·CSV·dead link) + code-phase 0 | C2.x | agent 본문에 결정적 작업 있으면 `Python 스크립트`·`code-phase` 키워드 필수 |
| 4 | 5+ agent 팀에 role-tier 분기 + cache_control + file-based handoff 부재 | C3.1·C3.2·C3.5 | 멀티에이전트는 정당 — 단, 5 최적화 패턴 충족 자문 (`references/optimal_team_composition.md`). audit.py R3 sub-rule 5/5 met? |
| 5 | 5+ team에 병렬/직렬 의도 선언 + wall-clock cap 미선언 | C3.3·C3.4 | `Phase 3 백그라운드 병렬 N` / `sequential cascade` 명시. agent에 `wall_clock: 30min` + writer `per_call_cap: 4000자` [S-B003 49 병렬=887K tokens/min 위험] |
| 6 | CLAUDE.md/SKILL.md > 200 lines without changelog 분리 | C4.1 | 운영 정보만 본문, 이력은 `~/CLAUDE-changelog.md` |
| 7 | cache_control breakpoint 0회 | C5.1 | system prompt + SKILL.md + 큰 reference 파일에 cache_control 4 breakpoint? 최소 Sonnet 1024 / Opus 4096 토큰 [A004][A005] |
| 8 | writer/drafter agent에 per-call output cap 부재 | C9.1 | `cap: 4000자/call` 또는 `> 4K → 2 sub-call 자동 분할` 룰 명시? [S-C05] 28.4% cost-of-pass 개선 |
| 9 | 재시도 hard cap 0 | C10.1 | `iter ≤ 3` 또는 `재시도 max N` 선언? [S-C04] hierarchical+hybrid 89%@1.15× vs reflexive 94%@2.3× |

### 권장 패턴 매트릭스 (도입 효과 큰 순서)

| 우선순위 | 패턴 | 적용 | 절감 |
|--------|------|------|------|
| 🥇 1 | Sonnet 팀원, Opus orchestrator만 | 5+ agent 하네스 25개 모두 | -40% per teammate |
| 🥇 2 | HD-003 Python phase 분리 | agent 본문에 결정적 keyword 있는 모든 agent | -99% per agent |
| 🥇 3 | cache_control 4 breakpoint | SKILL.md > 4K + 자주 호출 system prompt | -80% input tokens |
| 🥈 4 | per-call output cap | writer/drafter agent | -28.4% cost-of-pass |
| 🥈 5 | Optimal team composition matrix | 5+ team 설계 전 — role-tier mix + caching + parallel/serial 선언 + wall-clock cap + file-based handoff | -40~-90% per pattern, well-formed multi-agent 보장 |
| 🥉 6 | report-first convention | drafter / composer | 재실행 비용 0 |
| 🥉 7 | wall-clock budget table | 8+ agent 하네스 | runaway 차단 |

상세 → `references/anti_patterns_atlas.md` (29개 서브패턴 빠른 카드).

### 모델 분기 룰 (단순)

```
역할이 [탐색·grep·읽기·짧은 분류·boilerplate] 이면 → Haiku
역할이 [정형 출력·코드·번역·일반 집필·팀원·일반 팩트체크] 이면 → Sonnet
역할이 [아키텍처·창의 5K+자·학술 페이퍼·high-stake 판단·orchestrator] 이면 → Opus
역할이 [verbatim·BibTeX·regex·정규화·dead link·CSV·grep·hash] 이면 → Python (LLM 0회)
```

---

## MODE 3: AUDIT (기존 하네스 감사)

### 명령어

```bash
# 단일 하네스 감사 (절대 경로 또는 상대 경로 모두 가능)
python scripts/audit.py /path/to/your/harness
python scripts/audit.py /path/to/your/harness --json

# 전수 감사 (~/.claude/agents + skills + CLAUDE.md 27 하네스)
python scripts/audit.py
python scripts/audit.py --top 10        # 우선순위 hotspot top 10
python scripts/audit.py --json | jq ...
```

### 검출 룰 9개 (정적 grep + section presence)

audit.py는 `taxonomy.json`을 로드해 다음 9개 룰을 적용한다. 각 결과는 PASS/FAIL/WARN/N/A + evidence(file:line) + 권고 fix + 출처 ID.

| 룰 | 카테고리 | 검출 | 사용자 baseline hit |
|----|---------|------|---------------------|
| R1 | C1.1 All-Opus | `model: opus` 비율 ≥ 80% | 99.0% (103/104) FAIL |
| R2 | C2.x HD-003 | 결정적 keyword + code-split 0 | 20 RISKY FAIL |
| R3 | C3.1~C3.5 team composition | 5+ team 마다 5 sub-rule (R3a~R3e) 체크 — 3-tier 판정 PASS/WARN/FAIL | 5+ team 26/28; 5/5 met=1, 3-4/5=10, 0-2/5=15 → FAIL |
| R4 | C4.1 bloat | CLAUDE.md/SKILL.md > 200 lines | SKILL 평균 8,693자 WARN |
| R5 | C5.1 caching | cache_control / "prompt caching" 언급 | 27/27 0회 FAIL |
| R6 | C7.1 read pattern | 동일 파일 반복 Read 의심 | runtime |
| R7 | C8.1 HD-010 | `.checkpoints/` / "output-first" 부재 | paper-maker 1건 |
| R8 | C9.1 HD-011 | writer/drafter agent에 cap 부재 | pm-section-drafter(7,018자) FAIL |
| R9 | C4.5 비실행 콘텐츠 | SKILL.md 본문 Phase·결정 트리 비율 60%+ 의심 | skill-creator 32,987자 WARN |

### 출력 해석

- **FAIL** = 외부 N≥2 확증 + 사용자 baseline 위반 → 즉시 fix 권고
- **WARN** = 외부 N=1 또는 패턴 일치만 → 검토 후 결정
- **PASS** = 룰 충족
- **N/A** = 룰 적용 대상 아님 (예: 1~2 agent 하네스에 R3 적용 안 함)

전수 모드 출력에 **hotspot top 10** 자동 포함 — 사용자 baseline §5의 10대 hotspot 매핑.

### 우선순위 fix (전수 모드 권고 순서)

1. R1 FAIL → `structural-visual-designer`·`ainews-delivery-engineer` 등 14개 5K+ opus 에이전트 Sonnet 다운그레이드 (절감 -40%/agent)
2. R2 FAIL → Top3 (uap-case-parser·pm-evidence-curator·uap-source-fetcher) Python phase 분리 (절감 -99%/agent)
3. R5 FAIL → paper-maker SKILL.md(23,138자) 1순위 cache_control 적용 (절감 -80% input)
4. R3 FAIL → 5+ team 하네스에 5 cost-optimization 패턴 적용 (`references/optimal_team_composition.md`): role-tier mix · cache_control · parallel/serial 선언 · wall-clock cap · file-based handoff. 절감: -40% per Sonnet teammate + -90% input via caching.
5. R8 FAIL → writer/drafter agent에 per-call cap + 자동 분할 룰 (절감 -28.4% cost-of-pass)

---

## MODE 4: HOOK (런타임 자동 가드)

`~/.claude/settings.json` 의 PreToolUse(Task matcher) + UserPromptSubmit 두 hook에 `scripts/hook_check.py` 등록 → 매번 자각 없이 가드. 출력은 stderr 경고만(exit 0, 블로킹 ❌).

**상세 설정·JSON 예제·트리거 keyword 전체 → `references/hook_examples.md`**

---

## ★ Headline 1: Task → Model Quick Lookup (10대 작업 유형)

전체 24행은 `references/task_to_model_matrix.md` 참조. 가장 자주 쓰는 10개만 본문 발췌.

| # | 작업 유형 | 추천 모델 | 근거 출처 | vs Opus |
|---|----------|----------|-----------|---------|
| 1 | 결정적 변환 (regex·1:1·BibTeX·포맷 정규화) | **Python** | [S-C07][S-C08][S-C09] | free |
| 2 | 파일 탐색·grep·코드베이스 search | **Haiku** | [A013][S-B016][S-B031] | -80% |
| 3 | 패턴매칭·룰 기반 분류 (short input) | **Haiku** | [A013][S-B017] | -80% |
| 4 | 짧은 정형 요약 (≤ 1 단락) | **Haiku** | [S-B031][S-B017] | -80% |
| 5 | 자연어 정형 출력 (JSON·표) | **Sonnet** | [A001][S-B017][S-B018] | -40% |
| 6 | 표준 코드·디버깅 | **Sonnet** | [A001][S-B016][S-B017] | -40% |
| 7 | 문서 집필 (≤ 5,000자) | **Sonnet** | [A001][S-B018] | -40% |
| 8 | 학술/정책 페이퍼 (5K+자 high-stake) | **Opus** | [S-C09] | 0% 정당 |
| 9 | 깊은 reasoning·아키텍처 결정 | **Opus** | [A001] | 0% 정당 |
| 10 | 데이터 파싱 (CSV·HTML·PDF) | **Python** | [S-B024][S-C07] | free |

**핵심 규칙:** "결정적으로 표현 가능" → Python · "자연어 정형 출력·표준 코딩" → Sonnet · "복잡 reasoning·창의·high-stake"만 Opus.

---

## ★ Headline 2: scripts/model_selector.py 사용법

매 작업 시작 시 호출. LLM 호출 0회(완전 결정적 결정 트리).

```bash
# 자연어 작업 설명 → 모델 추천 + 근거 + 예상 비용
python scripts/model_selector.py --task "PDF에서 표 추출하고 CSV로 정규화"
# → 추천: Python (LLM 0회)
#   근거: 결정적 keyword "PDF·CSV·정규화" 탐지 [S-B024][S-C07]
#   참고: task_to_model_matrix.md #18 행
#   예상 비용 (LLM 시): Opus $0.06/1K tokens 입력 ≈ $0.72 (12K tokens) → Python 사용 시 $0

python scripts/model_selector.py --task "주간 IT 칼럼 5000자 집필" --tokens 8000 --quality high
# → 추천: Sonnet
#   근거: 자연어 정형 출력·문서 집필 ≤ 5K자 [A001][S-B018]
#   참고: task_to_model_matrix.md #8 행
#   예상 비용: Sonnet $3/MTok input × 8K + $15/MTok output × 6K = $0.114
#   vs Opus: $5/MTok × 8K + $25 × 6K = $0.190 (40% saved)

python scripts/model_selector.py --task "agent 정의 grep으로 결정적 키워드 탐지" --tokens 200
# → 추천: Python (LLM 0회)
#   근거: grep · 결정적 keyword 탐지 [S-C07]
#   참고: task_to_model_matrix.md #24 행
```

`--quality low|medium|high` 플래그로 품질 요구 수준 명시. high면 마지막 단계에서 Sonnet→Opus 상향 검토.

---

## 10대 카테고리 × 29 서브패턴 (요약)

| ID | 카테고리 | 헤드라인 서브패턴 (S1만) | 사용자 hit |
|----|---------|--------------------------|-----------|
| C1 ★ | Model Tier Misallocation | C1.1 All-Opus | 99.0% 🔴 |
| C2 ★ | Deterministic in LLM (HD-003) | C2.1 verbatim·BibTeX, C2.2 format, C2.3 parsing | 20 RISKY 🔴 |
| C3 | Multi-Agent Team Composition (cost-optimized) | C3.1 role-tier mix, C3.2 cache_control, C3.3 parallel/serial, C3.4 wall-clock cap, C3.5 file-based handoff | 26/28 multi-agent 🟡 (missing-patterns 검사) |
| C4 | Context Bloat | C4.1 >200 lines, C4.2 raw log | 평균 8,693자 🟡 |
| C5 | Prompt Caching Underuse | C5.1 cache_control 부재 | 100% 🔴 |
| C6 | Subagent Spawn Overhead | (S2만) | 14/27 8+ |
| C7 | Tool Call Inefficiency | (S2만) | runtime |
| C8 | Report/Artifact Loss (HD-010) | C8.1 report-first 부재 | paper-maker |
| C9 | Per-Call Cap Missing (HD-011) | C9.1 drafter 분량 cap 부재 | pm-section-drafter |
| C10 | Architecture Mis-fit | (S2만 — 반사형 2.3× vs 계층 1.4×) | 다수 재시도 |

**31 서브패턴 전체 카드 + 출처 ID 모두 → `references/anti_patterns_atlas.md`** (C3 재포지셔닝 후 6 cards). 멀티에이전트 최적 팀 구성 매트릭스 → `references/optimal_team_composition.md` (★ headline #3).

---

## 참고 자료 트리

```
references/
├── task_to_model_matrix.md           ★ headline 1 — 24행 매트릭스 + 근거 + 예상 비용
├── optimal_team_composition.md       ★ headline 3 — 멀티에이전트 well-formed 매트릭스 (C3 1:1 매핑)
├── python_vs_llm_tree.md             C2 결정 트리 + 사용자 20 RISKY 사례
├── prompt_caching_checklist.md       C5 breakpoint·5min/1hr·사용자 paper-maker 1순위
├── parallel_patterns.md              C3/C6 7×~15× 곱연산·계층 vs 반사·spawn cap
├── anti_patterns_atlas.md            31 서브패턴 빠른 카드 (C3 reframed)
└── hook_examples.md                  settings.json 등록 예제

scripts/
├── audit.py                      MODE 3 (전수 모드 default, 9개 룰)
├── estimate_cost.py              가격 SSOT (모듈 상단 상수)
├── model_selector.py             ★ MODE 1 호출 (결정 트리, LLM 0회)
└── hook_check.py                 MODE 4 (PreToolUse·UserPromptSubmit)
```

---

## 가격 데이터 SSOT (Anthropic 공식 [A005])

| 모델 | Input $/MTok | Output $/MTok | Cache write 5min | Cache read |
|------|-------------:|--------------:|----------------:|----------:|
| Opus | 5.00 | 25.00 | base × 1.25 | base × 0.1 |
| Sonnet | 3.00 | 15.00 | base × 1.25 | base × 0.1 |
| Haiku | 1.00 | 5.00 | base × 1.25 | base × 0.1 |

상세·1hr 캐시·MTok 환산 → `scripts/estimate_cost.py` 모듈 상단 상수 + `references/prompt_caching_checklist.md`.

**주의:** 가격은 Anthropic 정책 변경 가능. v1 작성 시점(2026-05-14) 기준. 변경 시 `scripts/estimate_cost.py` 상단 한 곳만 수정하면 audit.py·model_selector.py·hook_check.py 모두 자동 반영.

---

## 출처 키 (taxonomy.json sources_external 매핑)

- **A###** = Anthropic 공식 (docs·blog·cookbook). 40 인용 수집(Scout A).
- **S-B###** = 커뮤니티 (X·Reddit·블로그·GitHub). 32 인용(Scout B).
- **S-C##** = 학술·실증 (arXiv·Augment·Fowler·OpenAI·HD 카탈로그). 9 인용(Scout C).
- **HD-###** = 사용자 본인 `_reference/harness-diagnostic/` 21갭 카탈로그. 4개 채택(HD-003·010·011·020).

---

## 메타 원칙 셀프 체크

본 스킬을 사용할 때 자기 자신도 메타 원칙을 지키는지 9 step 체크리스트가 있다. **체크 ≤ 6/9이면 shame token 출력 — "본 스킬 메타 원칙 위반. 다음 호출 수정 권고."**

**9 step 체크리스트 전체 → `references/meta_self_check.md`**

---

## 현재 버전

- **v1.0** (2026-05-14) — **C3 reframed**: "Multi-Agent Cost Multiplier" anti-pattern → "Multi-Agent Team Composition (cost-optimized harness design)" missing-pattern. R3 단순 5+ team FAIL → R3a~R3e 5 sub-rule 3-tier 판정. 신규 headline #3 `references/optimal_team_composition.md`. 31 서브패턴(28→31, C3 3→6). 메시지: 멀티에이전트는 정당, 단 비용 최적화된 멀티에이전트.
- **v1.0.0** (2026-05-14) — 초기 빌드. taxonomy v1 + Scout A·B·C + baseline 정적 측정 기반.

**갱신 트리거:** 외부 N≥2 신규 패턴 / Anthropic 가격 변동 / 사용자 baseline 재측정(audit.py 전수 재실행).
