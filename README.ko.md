# plz-save-token

[![Version](https://img.shields.io/badge/version-1.0-blue)](https://github.com/epoko77-ai/plz-save-token/releases/tag/v1.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Dependencies](https://img.shields.io/badge/deps-stdlib_only-green.svg)](#)
[![English README](https://img.shields.io/badge/README-English-lightgrey)](README.md)

> **멀티에이전트 Claude Code 하네스를 위한 토큰 비용 lint 도구.**
> 멀티에이전트를 막는 게 아니라, **잘 형성된(well-formed)** 멀티에이전트를 짓도록 돕는다.
> 자매 저장소: [harness-diagnostic](https://github.com/epoko77-ai/harness-diagnostic) — 구조적 진단 / plz-save-token — 비용 최적화.

> 🌏 **영어 README:** [README.md](README.md) — 더 상세한 설명, 사례, 인용 정보.
> 📚 **한국어 참고:** [`references/taxonomy.md`](references/taxonomy.md) — 220줄, 분류학 전체. 본 README와 함께 보면 도구 한국어로 깊이 이해 가능.

---

## TL;DR

사용자(작성자) 본인의 27개 하네스 Claude Code 카탈로그를 직접 감사한 결과:

- 에이전트 **99%가 Opus 사용** (103/104)
- **프롬프트 캐싱 0/27** (모든 하네스가 미사용)
- **20개 에이전트가 결정적 작업(regex·verbatim 매핑)을 LLM에 위임** — 한 사례는 91분 Opus 호출 후 산출물 0
- **5+ agent 팀이 93%** (25/27)

팀 자체는 대부분 정당하다 — paper-maker, ainews-daily, policyblind 같은 사례는 well-formed hierarchical/pipeline 구조. 문제는 **7×~15× 곱연산을 5개 비용 최적화 패턴 없이 지불**하는 것.

`plz-save-token`은 (1) 분류학(10 카테고리 × 31 sub-patterns), (2) 정적 감사 스크립트 `audit.py`, (3) LLM 호출 0회 결정 트리 `model_selector.py`, (4) 24행 작업→모델 매트릭스, (5) 멀티에이전트 최적 팀 구성 매트릭스를 묶은 메타 스킬. **표준 라이브러리만 사용 (외부 의존 0).**

5초 안에 본인 카탈로그 감사: `python3 scripts/audit.py`

---

## 80/20 원칙 (도구의 심장)

> **작업 복잡도를 모델 티어와 먼저 매칭하라** — 결정적 작업은 Python, 탐색은 Haiku, 표준 출력은 Sonnet, high-stake reasoning은 Opus. **이 단일 레버가 절감의 ~70-80%.**
> 5개 팀 구성 패턴(cache_control, role-tier mix, 병렬/직렬 의도 선언, wall-clock cap, file-based handoff)은 그 위에 ~30% multiplier로 얹힌다. **단 올바른 tier 매칭 위에서만.**
> **tier 먼저, team 다음.** base tier가 틀린 상태에서 team 최적화는 fractions of nothing이다.

---

## 문제 (1줄씩)

- **모델 티어 오배정** — orchestrator·worker·reviewer 모두 Opus 기본값. read-only scout, regex classifier, boilerplate writer가 Sonnet/Haiku 가격으로 40-80% 더 싸게 끝낼 일을 Opus 가격으로 지불.
- **결정적 작업이 LLM에 묶임 (HD-003 트랩)** — verbatim 1:1 매핑, BibTeX, CSV→JSON 파싱은 regex+dictionary 작업. Python 30초가 Opus 91분 + 산출물 0과 같은 일을 한다.
- **공통 컨텍스트 매번 재지불** — cached input은 base의 10%. 23KB SKILL.md × 5 agents × 10 호출 = 같은 SKILL.md 50번 지불. `cache_control` 누락 시 보이지 않는다.
- **병렬/직렬 의도 없음, cap 없음, file-based handoff 없음** — 실행 모드가 우연. runaway risk 무한. SendMessage 남발로 토큰 누설.
- **SKILL.md/CLAUDE.md 비대** — 본인 카탈로그 평균 8,693자, 최대 32,987자. 대부분 장식(changelog, roadmap, philosophy) — 런타임에 필요한 phase 정의 아님.

위 모두 file-level linter(agnix 등)는 못 잡는다. 시스템 단위로 측정해야 보인다.

---

## 무엇이 들어있나

**4가지 모드:**

| 모드 | 무엇을 하나 | 비용 |
|------|------------|------|
| **Pre-flight** | `model_selector.py` — 자연어 작업 설명 → 추천 모델 + 근거 + 비용 추정 | LLM 0회 |
| **Authoring** | 9대 금지 패턴 체크리스트 + 24행 task→model 매트릭스 | passive |
| **Audit** | `audit.py` — `~/.claude` 전체에 9개 정적 룰 적용 | 약 5초, LLM 0회 |
| **Hook** | `settings.json` 런타임 가드 (`PreToolUse:Task` + `UserPromptSubmit`) — 블로킹 안 함 | 0 blocking |

**3개 헤드라인 산출물:**

1. **[`references/task_to_model_matrix.md`](references/task_to_model_matrix.md)** — 작업 유형 24행 × 추천 모델 × 근거 + 출처 인용 (**Primary lever — 80/20에서 80**)
2. **[`scripts/model_selector.py`](scripts/model_selector.py)** — 위 매트릭스를 코드로 인코딩한 CLI 결정 트리. 1초 응답
3. **[`references/optimal_team_composition.md`](references/optimal_team_composition.md)** — 8개 workload 패턴 × 5개 비용 최적화 패턴 매트릭스 (Secondary optimization — 80/20에서 20)

---

## 빠른 시작 (3분)

```bash
git clone https://github.com/epoko77-ai/plz-save-token
cd plz-save-token

# 전체 ~/.claude 카탈로그 감사 (9개 룰, 약 5초)
python3 scripts/audit.py
python3 scripts/audit.py --top 10                       # 우선순위 hotspot top 10
python3 scripts/audit.py /path/to/harness/root          # 단일 하네스
python3 scripts/audit.py --json | jq .

# 결정 트리에 작업 던지기
python3 scripts/model_selector.py --task "PDF에서 표 추출하고 CSV로 정규화"
python3 scripts/model_selector.py --task "주간 칼럼 5000자 집필" --tokens 8000 --quality high

# 모델별 비용 비교
python3 scripts/estimate_cost.py --compare --input-tokens 30000 --output-tokens 5000
```

표준 라이브러리만. `pip install` 필요 없음. Python 3.10+.

### Claude Code 스킬로 배포 (자동 발동)

모든 새 Claude Code 세션에서 자동 활성화하려면 — "내 하네스 감사해줘" 또는 "이 작업 모델 뭐가 적절해" 입력 시 자동 발동 — self-contained 스킬로 설치:

```bash
mkdir -p ~/.claude/skills/plz-save-token
cp -r SKILL.md scripts references ~/.claude/skills/plz-save-token/
```

스킬은 self-contained: SKILL.md + scripts/ + references/ 모두 `~/.claude/skills/plz-save-token/` 아래. 이후 `git pull` 후 같은 `cp -r` 한 번이면 sync. SKILL.md frontmatter에 20+ 한국어/영어 트리거 키워드 박혀있음.

---

## 분류학(catalog)이 도구만큼 가치 있다

`audit.py`와 `model_selector.py`는 더 오래 가는 자산 위에 얹힌 얇은 껍데기 — **분류학 그 자체**.

- **[`references/taxonomy.md`](references/taxonomy.md)** — 10 카테고리 × 31 sub-patterns. 각 카드는 트리거 키워드·검출 방법·완화책·예상 절감률·**2개 이상 독립 외부 인용**(Anthropic 공식 + 커뮤니티 + 학술) 포함. 220줄 19KB, 30분에 통독 가능. **이미 한국어**.
- **[`references/taxonomy.json`](references/taxonomy.json)** — 같은 내용을 머신 파싱 가능 JSON으로. 외부 대시보드·도구 정의·downstream lint로 import 가능.
- **[`references/task_to_model_matrix.md`](references/task_to_model_matrix.md)** — 24행 primary lever 매트릭스. 설계 문서, RFC, 온보딩 가이드에 그대로 가져다 쓰기.

reference 문서들은 **도구와 분리해서도 의미 있도록** 의도적으로 설계됨 — 설계 리뷰, 페이퍼 인용, 새 멀티에이전트 하네스 팀 온보딩, 또는 신규 SKILL.md 작성 시 체크리스트로. [`taxonomy.md`](references/taxonomy.md)를 한 번 읽고 [task-to-model 매트릭스](references/task_to_model_matrix.md)를 북마크하는 것만 해도 이 repo는 본전.

---

## 실측 사례 — paper-maker (16-agent 학술 페이퍼 하네스)

상세는 [`examples/case_studies/A_paper_maker_retrospective.md`](examples/case_studies/A_paper_maker_retrospective.md). 핵심:

| | plz-save-token 미사용 | plz-save-token 적용 |
|---|---------------------|---------------------|
| 1회 실행 비용 추정 (480K input / 160K output) | $6.40 (Opus, 캐시 없음, 모두 LLM) | ~$1.80 (Sonnet + 90% 캐시 + 3 Python phase 분리) |
| 최악 케이스 (`pm-citation-formatter`) | **91분 Opus 호출, 산출물 0** (HD-003 트랩, 실측) | ~30초 Python phase → **180× 단축** |
| R3 판정 | FAIL (0/5 met) | PASS (5/5 met, well-formed) |
| **누적** | — | **-72% 비용, 적용 시간 3시간** |

WARN tier 사례(PolicyBlind, 2시간 작업 → -56%, 연 $1,099 절감)는 [`examples/case_studies/B_policyblind_warn_to_pass.md`](examples/case_studies/B_policyblind_warn_to_pass.md).

---

## 정직한 한계

- **단일 운영자 baseline** — 본 README의 충격 수치(99% Opus 등)는 작성자 본인 27 하네스 카탈로그. taxonomy는 N≥2 외부 출처 채택 룰을 따르지만 baseline은 N=1. 다른 운영자 감사 결과 환영.
- **Claude Code 한정** — `~/.claude/agents/` 레이아웃과 SKILL.md 컨벤션 기반 검출. LangChain, CrewAI, AutoGen은 어댑터 필요 (v1.1 로드맵).
- **가격은 시점 데이터** — Anthropic 공식 per-MTok 가격(2026-05-14 기준). `scripts/estimate_cost.py`의 PRICING 상수 한 곳만 갱신하면 모든 스크립트에 반영.
- **품질 저하 risk 미측정** — 매트릭스의 "Sonnet 다운그레이드 -40%"는 작업이 Sonnet으로 충분하다는 전제. 다운그레이드 후 재시도 발생 시 saved tokens ≠ saved cost. v1.2 measurement framework 로드맵. **이 점이 채택 시 가장 큰 risk** — 영어 README "Quality regression risk" 섹션 + [`references/quality_measurement.md`](references/quality_measurement.md) (계획) 참조.
- **메타 스킬** — `SKILL.md` 자체가 비대 룰(R4/R9)에 걸릴 수 있지만 `meta_skill: true` frontmatter로 예외. 도구가 자기 자신 audit 100% 통과.

---

## 자매 저장소 — harness-diagnostic

`plz-save-token`과 [`harness-diagnostic`](https://github.com/epoko77-ai/harness-diagnostic)은 같은 작성자가 만든 보완재:

| 도구 | 답하는 질문 | 산출물 |
|------|------------|-------|
| harness-diagnostic | "내 하네스에 구조적으로 무엇이 빠졌나?" | 21갭 × PASS/FAIL, 5층 모델 |
| plz-save-token | "내 하네스가 어디서 토큰이 새고, 무엇을 어떻게 고치나?" | 31 sub-patterns × 비용 영향, 모델 결정 트리, 비용 추정기 |

함께 쓰는 워크플로: harness-diagnostic 먼저 구조적 갭 진단 → plz-save-token 비용 갭 감사. 4개 룰이 겹친다(HD-003 ↔ R2, HD-010 ↔ R7, HD-011 ↔ R8, HD-020 ↔ R1) — 두 도구 모두 FAIL이면 fix 우선순위 최상위.

상세: [`docs/hybrid_workflow.md`](docs/hybrid_workflow.md).

---

## 로드맵

- **v1.1** — LangChain/LangGraph, CrewAI YAML, Python-class 하네스 어댑터. 외부 검증(2026-05-14)에서 R2/R3/R8 패턴이 외부 프레임워크에서도 실재함 확인.
- **v1.2** — 품질 측정 도구 (`quality_delta.py`, golden-task harness, retry-cost calculator). `task_to_model_matrix.md`의 가장 중요한 간격 해소.
- **v1.3** — `audit.py --json` hotspot 키 버그 fix. SKILL.md 추가 슬림화.
- **v2.0** — 프레임워크 전체 커버리지, 커뮤니티 baseline 누적, case study converging 시 매트릭스 행 revision.

### v2.0 promotion 조건

v1.0은 사용 가능한 첫 버전. v2.0(커뮤니티 검증)까지 3가지 게이트:

1. **N ≥ 3 외부 운영자 baseline** — [`baseline_submission` issue](https://github.com/epoko77-ai/plz-save-token/issues/new?template=baseline_submission.md)
2. **≥ 1 measured 품질 저하 case study** — [quality regression issue](https://github.com/epoko77-ai/plz-save-token/issues/new?template=quality_regression_report.md)
3. **≥ 1 프레임워크 어댑터 출시** (CrewAI YAML이 가장 단순한 첫 타깃)

**느린 길이 정직한 길.**

---

## 기여

catalog는 inbound evidence로 자란다. 본인 하네스에 `audit.py` 돌려서:

- **분류학에 없는 새 패턴** (외부 출처 2개 이상 확보) — [pattern proposal issue](https://github.com/epoko77-ai/plz-save-token/issues/new?template=pattern_proposal.md)
- **본인 하네스 baseline 제출** — N=1 → N=2 → N=3 진행
- **품질 저하 measured 사례** — 가장 부족한 evidence

PR 환영. `references/meta_self_check.md` 9-step 자가 점검 통과 후 제출 권고.

---

## 라이선스

MIT. 2026 Lee Seung-hyun (epoko77-ai).

## 인사

- [`harness-diagnostic`](https://github.com/epoko77-ai/harness-diagnostic) — 5층 모델과 HD-003/010/011/020 갭 정의.
- Anthropic Claude Code docs, API docs, engineering blog — Scout A 40 인용의 원천.
- Augment Code, Martin Fowler, OpenAI harness engineering — "deterministic vs inferential work" 경계가 HD-003을 codify.
- Zhang et al. 2026 (arXiv:2604.08906) — 409 agentic bug 분석.

영어 README와 더 상세한 인용: [README.md](README.md).
