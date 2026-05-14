# Python vs LLM 결정 트리 (C2 — HD-003 카테고리)

생성: 2026-05-14 · 출처: `taxonomy.md §C2` + 사용자 baseline §3 (20 RISKY agents)

본 문서는 **카테고리 C2 — Deterministic Work Routed Through LLM**의 결정 트리. 91분→30초 트랩(paper-maker pm-citation-formatter 사용자 실측)이 이 카테고리에서 발생.

## 핵심 메시지

> **"결정적으로 표현 가능한 작업은 Python으로 하라. LLM은 분리·우선순위 판단·재작성에만."**

근거 3축:
- [S-C07] Martin Fowler — "computational sensors vs inferential sensors" 구분이 LLM 시스템의 기본 설계.
- [S-C08] Augment Code — "deterministic outer-harness, probabilistic inner-loop".
- [S-C09] paper-maker HD-003 — citation-formatter v1.1 91분 LLM → v1.2 30초 Python (180× 시간 절감, -99% 토큰).

## 결정 트리

```
작업 설명에 다음 keyword 있는가?
├── verbatim·1:1 매핑·BibTeX·citation 정규화
│   └── YES → Python 분기 (pybtex, csl-json, re)
│
├── CSV·JSON·HTML·PDF 표 추출
│   └── YES → Python 분기 (pandas, pypdf, BeautifulSoup)
│
├── dead link·URL 유효성 확인
│   └── YES → Python 분기 (requests + linkchecker CLI)
│
├── cross-reference 매칭·번호 해결
│   └── YES → Python 분기 (dict lookup + JSON SSOT)
│
├── 날짜 포맷·시간 정규화
│   └── YES → Python 분기 (dateutil, strftime)
│
├── 파일 카운트·해시·grep·log 압축
│   └── YES → shell/python (wc, sha256sum, grep, awk)
│
└── 위 keyword 없음
    └── 자연어 reasoning·자유 생성 — LLM 사용 (model_selector로 모델 선택)
```

## 사용자 baseline 20 RISKY agent 매핑

`baseline.md §3` 에서 검출된 20개 agent. 우선순위 fix:

### 🔴 Top 3 (즉시 Python phase 분리 권고)

| Agent | det_kw | size | 작업 추정 | Python 권고 | 절감 |
|-------|-------:|-----:|----------|------------|------|
| `uap-case-parser.md` | 2 | 10,840자 | UAP case verbatim 파싱·구조화 | `re`로 케이스 분리, `dataclass` 매핑. LLM은 분류 모호 케이스만 | -99% |
| `pm-evidence-curator.md` | 3 | 3,297자 | evidence verbatim 추출·1차 출처 검증 | `requests` URL 검증, `re`로 정량 데이터 추출, LLM은 evidence 적합성 판단만 | -95% |
| `uap-source-fetcher.md` | 3 | 3,959자 | URL fetch + .mil/.gov 검증 + verbatim 보존 | `requests` + `urlparse` 도메인 화이트리스트, `BeautifulSoup` 본문 추출 | -90% |

### 🟡 Tier 2 (검토 후 분리)

| Agent | det_kw | size | 추정 트랩 |
|-------|-------:|-----:|-----------|
| `pm-editor-chief.md` | 2 | 7,933자 | 형식 검증·patch YAML 파싱 (이미 일부 코드 분리 진행 중) |
| `pm-section-drafter.md` | 2 | 7,018자 | drafter 본업은 LLM, 분량 cap 검증은 Python |
| `pm-argument-architect.md` | 1 | 6,792자 | CEW 트리플 구조 — Python으로 schema 검증 가능 |
| `pm-scope-architect.md` | 1 | 6,581자 | scope JSON schema 검증 — Python |
| `pm-pdf-composer.md` | 2 | 5,749자 | PDF 빌드는 Typst CLI, LLM은 빌드 실패 cascade 판단만 |
| `pm-prose-stylist.md` | 2 | 5,534자 | 윤문은 LLM, register 변경률·금지 패턴 검출은 Python |
| `uap-context-researcher.md` | 2 | 3,545자 | 1차 소스 매니페스트 정합성은 Python |
| `pm-coherence-editor.md` | 2 | 2,789자 | 흐름 봉합은 LLM, 섹션 transition 검출은 Python |
| `uap-fact-checker.md` | 1 | 4,133자 | 수치·연도 verbatim 매칭은 dict lookup |
| `uap-report-composer.md` | 1 | 5,176자 | Typst 빌드·차트 데이터 정합은 Python |
| `policyblind-architect.md` | 1 | 4,560자 | DB 스키마 검증 Python |
| `policyblind-source-collector.md` | 1 | 3,883자 | RSS 파싱 Python (feedparser) |
| `ainews-architect.md` | 1 | 3,605자 | 아키텍처는 LLM, schema 검증 Python |
| `ainews-source-clipper.md` | 1 | 3,280자 | RSS·HTML 클리핑 Python |
| `humanize-web-architect.md` | 1 | 3,631자 | API schema·deploy는 결정적 |
| `pm-academic-fact-checker.md` | 1 | 3,210자 | 인용 verbatim 매칭은 dict |
| `pm-literature-scout.md` | 1 | 3,826자 | DOI·publisher API 결정적 호출 |

### ✅ 1개 SAFE (이미 분리됨)

| Agent | code_split | 비고 |
|-------|-----------:|------|
| `pm-citation-formatter.md` | 1 | v1.2 — 91분→30초 사용자 실측. 이 패턴이 표준 |

## 분리 패턴 (pm-citation-formatter v1.2 참고)

```
agent 정의에 두 phase 명시:

## Phase 5C-1 (Deterministic Code Pass)

- 도구: Python 스크립트 (또는 Bash)
- 입력: 결정적 변환 대상 (citation list, evidence YAML, ...)
- 처리: re / pybtex / csl-json / requests 등 표준 라이브러리
- 출력: 변환 완료 JSON / Markdown + edge case list (≤ 10건)

## Phase 5C-2 (LLM Review Pass)

- 모델: Sonnet (정형 출력)
- 입력: Phase 5C-1의 edge case ≤ 10건 (전체 N건이 아니라!)
- 처리: 자연어 판단이 필요한 경우만 — 모호한 인용 형식·중복·미확정 출처
- 출력: edge case 처리 결과 + final list

게이트: edge case 0건이면 Phase 5C-2 skip
```

## Python 라이브러리 권고 (표준 + 결정적)

| 작업 | 라이브러리 | 비고 |
|------|-----------|------|
| regex | `re` (표준) | |
| 인용 BibTeX | `pybtex`, `bibtexparser` | |
| 인용 CSL-JSON | `csl-json` | |
| PDF 추출 | `pypdf`, `pdfplumber` | 표·이미지 분리 가능 |
| HTML 추출 | `BeautifulSoup`, `readability-lxml` | |
| CSV·JSON | `pandas`, `csv`, `json` (표준) | |
| HTTP | `requests`, `urllib.parse` | |
| concurrent | `concurrent.futures` (표준) | dead link 병렬 검증 |
| 날짜 | `dateutil`, `datetime` (표준) | |
| 해시 | `hashlib` (표준) | |
| linkchecker CLI | `linkchecker` (외부) | dead link 전수 |
| YAML | `pyyaml` | patch YAML 파싱 |
| schema 검증 | `jsonschema` | |

**원칙:** 표준 라이브러리 우선. 외부 의존 추가 시 `requirements.txt` 명시.

## 자기 체크 (agent 정의 작성 시)

새 agent를 만들 때 다음 자가 점검:

- [ ] agent 본문에 `verbatim` / `BibTeX` / `regex` / `정규화` / `verbatim` / `매핑` / `cross-reference` / `dead link` 키워드가 있는가?
- [ ] 있다면 → `Python 스크립트` / `code-phase` / `phase 5C-1` 등 분리 키워드 있는가?
- [ ] 없다면 → 두 phase로 분리 → 결정적 처리는 Python, LLM은 edge case 검토.
- [ ] phase 분리 정의에 입력·출력 데이터 형식 명시했는가? (JSON schema 권고)
- [ ] edge case 0건이면 LLM phase skip 게이트 명시했는가?

## audit.py 자동 검출

```bash
# 단일 하네스
python3 scripts/audit.py /path/to/your/harness --rules R2

# 전수 (홈 카탈로그)
python3 scripts/audit.py --rules R2
```

R2 룰 출력에 RISKY agent 리스트 + det_kw count + 권고 fix 자동 포함.

## 인접 참고

- `references/anti_patterns_atlas.md` — C2.1~C2.4 카드 4개.
- `scripts/model_selector.py` — DETERMINISTIC_KEYWORDS 18개 정규식이 본 결정 트리를 인코딩.
- `_workspace/02_audit/baseline.md §3` — 사용자 20 RISKY 원본 데이터.
