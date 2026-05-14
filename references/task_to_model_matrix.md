# Task → Model 매트릭스 (24행 전체) ★ HEADLINE

생성: 2026-05-14 · 출처: `taxonomy.md §3` (token-pattern-taxonomist v1) + Scout A·B·C 인용 + 사용자 baseline 교차검증

본 매트릭스는 `model_selector.py`의 결정 트리가 직접 인코딩하는 24행이다. CLI가 자동으로 매칭하므로 사용자는 매번 본 문서를 통독할 필요 없다. 다만 모델 분기 근거가 의심스러울 때, 새 패턴을 추가할 때, 학습 목적일 때 이 매트릭스를 참조한다.

## 가격 기준 (Anthropic 공식 [A005], 2026-05-14 기준)

| 모델 | Input $/MTok | Output $/MTok | vs Opus input |
|------|-------------:|--------------:|---------------|
| Opus | 5.00 | 25.00 | 100% (기준) |
| Sonnet | 3.00 | 15.00 | -40% |
| Haiku | 1.00 | 5.00 | -80% |
| Python | 0 | 0 | free |

가격 SSOT는 `scripts/estimate_cost.py` PRICING 상수. 변경 시 한 곳만 수정.

---

## 24행 매트릭스

### 그룹 A — Python 분기 (LLM 호출 0회) · 5행

| # | 작업 유형 | 추천 | 근거 | 출처 | vs Opus |
|---|----------|------|------|------|---------|
| 1 | 결정적 변환 (regex 가능) — citation·BibTeX·1:1·포맷 정규화 | **Python** | Fowler "computational sensors", Augment "deterministic outer-harness", HD-003 91분→30초 사용자 실측 | [S-C07][S-C08][S-C09] | free |
| 18 | 데이터 파싱 (CSV→JSON, HTML, PDF 표) | **Python** | PDF 15p 45K→2K tokens(22×), pandas/pypdf/BeautifulSoup | [S-B024][S-C07] | free |
| 19 | 카탈로그/메타 정합성 점검 | **Python** | Fowler "computational sensors" — JSON schema·해시·count는 결정적 | [S-C07] | free |
| 24 | log/output 압축 (grep 가능) | **Python/shell** | Anthropic hook 예제: 10000줄→grep→수백 토큰 | [A016] | free |
| (보조) | 모든 정형 검사·count·hash·dedup·sort | **Python** | 표준 라이브러리 | [S-C07] | free |

**작업 keyword 자동 매칭 (model_selector.py DETERMINISTIC_KEYWORDS):**
- `regex`, `정규 표현`, `verbatim`, `1:1 매핑`, `BibTeX`, `citation 정규화`
- `CSV→JSON`, `JSON 정규화`, `PDF 표 추출`, `HTML 파싱`
- `dead link`, `sha256`, `해시`, `파일 카운트`, `grep`, `날짜 포맷`, `cross-reference 매칭`

**라이브러리 권고:**
- regex → `re` (표준)
- 인용 → `pybtex`, `csl-json`
- 데이터 → `pandas`, `pypdf`, `BeautifulSoup`, `readability-lxml`
- 링크 → `requests` + `linkchecker` CLI
- 날짜 → `dateutil`
- HTTP → `requests` + `concurrent.futures`

### 그룹 B — Haiku 분기 · 6행 (-80% vs Opus)

| # | 작업 유형 | 추천 | 근거 | 출처 | vs Opus |
|---|----------|------|------|------|---------|
| 2 | 파일 탐색·grep·코드베이스 search | **Haiku** | Anthropic Explore agent 빌트인 = Haiku | [A013][S-B016][S-B031] | -80% |
| 3 | 패턴매칭·룰 분류 (short input) | **Haiku** | morphllm "Haiku 20× cheaper for mechanical" | [A013][S-B017][S-B031] | -80% |
| 4 | 짧은 정형 요약 (≤ 1 단락) | **Haiku** | tech-insider routing 60% Haiku | [S-B031][S-B017] | -80% |
| 20 | 짧은 FAQ 응답 | **Haiku** | tech-insider Haiku 60% | [S-B031][S-B017] | -80% |
| 22 | 코드베이스 탐색 서브에이전트 | **Haiku** | Anthropic Explore 빌트인 = Haiku | [A013] | -80% |
| 23 | 보일러플레이트·간단 수정 | **Haiku** | morphllm Sonnet vs Haiku 비교 | [S-B031] | -80% |

**작업 keyword 자동 매칭 (model_selector.py HAIKU_KEYWORDS):**
- `탐색`, `explore`, `파일 찾`, `read-only`, `읽기 전용`
- `짧은 분류`, `룰 분류`, `short classification`, `boilerplate`
- `짧은 요약`, `1 단락`, `one paragraph`, `FAQ`, `짧은 응답`

### 그룹 C — Sonnet 분기 · 8행 (-40% vs Opus, 일반 작업의 기본값)

| # | 작업 유형 | 추천 | 근거 | 출처 | vs Opus |
|---|----------|------|------|------|---------|
| 5 | 자연어 정형 출력 (JSON·표 생성) | **Sonnet** | Sonnet handles most coding tasks (Anthropic 공식) | [A001][S-B017][S-B018] | -40% |
| 6 | 표준 코드·디버깅 | **Sonnet** | Anthropic 공식 권고 | [A001][S-B016][S-B017] | -40% |
| 7 | 멀티턴 코드 리뷰 | **Sonnet** | Anthropic + tech-insider | [A001][S-B017] | -40% |
| 8 | 문서 집필 (≤ 5,000자) | **Sonnet** | Anthropic + velog 한국 커뮤니티 | [A001][S-B018] | -40% |
| 12 | 팩트체크 (일반) | **Sonnet** | Anthropic + tech-insider | [A001][S-B017] | -40% |
| 14 | 번역 (실용 일상) | **Sonnet** | Anthropic + velog | [A001][S-B018] | -40% |
| 16 | ESL / 언어 교육 콘텐츠 | **Sonnet** | 표준 조정 작업 | [A001] | -40% |
| 17 | 시각 / 이미지 프롬프트 설계 | **Sonnet** | Anthropic 공식 | [A001] | -40% |
| 21 | 에이전트 팀 팀원 (조정 작업) | **Sonnet** | Anthropic "Use Sonnet for teammates" — orchestrator는 Opus, 팀원은 Sonnet | [A002] | -40% |

**작업 keyword 자동 매칭 (model_selector.py SONNET_KEYWORDS):**
- `JSON 생성`, `정형 출력`, `표 생성`
- `코드 작성`, `디버깅`, `code review`
- `번역` (문학·격조 제외)
- `팩트체크` (학술·high-stake 제외)
- `팀원`, `조정 작업`, `teammate`, `ESL`, `언어 교육`
- `이미지 프롬프트`, `시각 프롬프트`, `image prompt`

### 그룹 D — Opus 분기 (정당화 필요) · 5행

| # | 작업 유형 | 추천 | 근거 | 출처 | vs Opus |
|---|----------|------|------|------|---------|
| 9 | 학술 / 정책 페이퍼 (5K+자, high-stake) | **Opus** | paper-maker 사용자 실측 — reviewer 통과 필수 | [S-C09] | 0% 정당 |
| 10 | 깊은 reasoning · 아키텍처 결정 | **Opus** | Anthropic 공식 "reserve Opus for architectural" | [A001] | 0% 정당 |
| 11 | 창의 자유 생성 (5K+자, 톤 중요) | **Opus** | Anthropic 공식 multi-step reasoning | [A001] | 0% 정당 |
| 13 | 팩트체크 (학술 high-stake) | **Opus** | paper-maker fact-checker 채택 | [S-C09] | 0% 정당 |
| 15 | 번역 (문학·격조) | **Opus** | bearblog 1.5M 조회 가이드 권고 | [S-B016] | 0% 정당 |

**작업 keyword 자동 매칭 (model_selector.py OPUS_KEYWORDS):**
- `아키텍처`, `architecture`, `설계 결정`
- `학술 페이퍼`, `정책 페이퍼`, `paper NeurIPS/ACL/CHI/KCI`
- `창의 자유 생성`, `5000자+ 톤 중요`
- `high-stake 팩트체크`, `학술 팩트체크`
- `문학 번역`, `격조 번역`
- `orchestrator`, `오케스트레이터`

---

## 결정 룰 (model_selector.py가 구현하는 결정 트리)

```
1. 결정적 keyword 매칭? → Python 권고 (LLM 0회)
2. Opus keyword (high-stake) 매칭? → Opus (정당화 필요)
3. Haiku keyword 매칭? → Haiku (-80% vs Opus)
4. Sonnet keyword 매칭? → Sonnet (-40% vs Opus)
5. 매칭 0 → Sonnet (기본값, 대다수 작업)

quality 플래그 조정:
  - low + Sonnet/Opus → Haiku 검토 신호
  - high + Sonnet → Opus 검토 신호
  - high + Haiku → Sonnet 검토 신호
```

**핵심 원칙:** "결정적으로 표현 가능" → Python · "자연어 정형 출력·표준 코딩" → Sonnet · "복잡 reasoning·창의·high-stake"만 Opus.

---

## 사용자 baseline 교차검증 (2026-05-14)

- **현재 사용자 분포:** opus 99.0% (103/104). 0% Sonnet · 0% Haiku.
- **이 매트릭스 적용 시 예상 재분배:**
  - 5K+ 비결정적·비-writer opus 14개 중 약 10개 → Sonnet (5K+ chars, 단순 정형/디자인/조립 역할)
  - read-only 탐색 류 (정확한 카운트는 audit.py 재실행 필요) → Haiku
  - HD-003 RISKY 20개 → Python phase 추가 + LLM 검토만 Sonnet/Haiku
- **예상 절감:** 단순 산술 — 14 agent × -40% (Sonnet) + 20 agent × -99% (Python phase) ≈ 전체 토큰 비용 -45% 잠재.

---

## 갱신 트리거

본 매트릭스는 다음 조건에서 갱신:

1. **외부 신규 N≥2 패턴 확증** — 새 모델/도구/모범사례 (예: Claude 5 출시 시).
2. **Anthropic 가격 변동** — `scripts/estimate_cost.py` PRICING 수정 → 본 표 vs Opus % 갱신.
3. **사용자 baseline 재측정** — `python scripts/audit.py` 재실행 후 패턴 hit pct 갱신.
4. **새 carpet 작업 유형 등장** — 24행에 없는 작업이 반복되면 신규 행 추가.

---

## 인접 참고

- `references/python_vs_llm_tree.md` — 그룹 A (Python 분기) 상세 결정 트리.
- `references/anti_patterns_atlas.md` — 29개 서브패턴 빠른 카드.
- `references/prompt_caching_checklist.md` — Sonnet/Opus 응답 시 caching으로 -80% 추가 절감.
- `scripts/model_selector.py` — 본 매트릭스를 코드로 인코딩한 결정적 CLI.
- `scripts/estimate_cost.py` — 가격 SSOT + 시나리오 비교.
