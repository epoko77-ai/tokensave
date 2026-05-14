# Prompt Caching Checklist (C5 카테고리)

생성: 2026-05-14 · 출처: `taxonomy.md §C5` + Scout A (Anthropic 공식) + Scout B (커뮤니티 실측)

## 헤드라인 (메타 원칙 강화)

> **사용자 baseline: 27/27 하네스 (100%) cache_control 언급 0회.** 평균 SKILL.md 8,693자 × 32개 + 평균 agent 정의 3,200자 × 104개 = **~660K자 반복 입력**이 캐싱 미적용 상태. 단일 레버로 가장 큰 즉각 절감 — input tokens -80% (hit rate 90% 시).

## 가격 메커니즘 [A005]

| 항목 | 가격 (base의 배수) |
|------|-------------------:|
| 정상 input | 1.00× |
| cache write 5min | 1.25× (한 번 적재) |
| cache write 1hr | 2.00× (한 번 적재) |
| **cache read** | **0.10×** |

**예시 — Opus + 50K input tokens 반복 호출 10회:**

| 시나리오 | 1회 비용 | 10회 비용 | 합계 |
|---------|---------|----------|------|
| 캐싱 없음 | $0.25 (50K × $5/M) | $2.50 | $2.50 |
| 5min 캐싱 (1st write + 9 reads) | $0.3125 (write) + $0.0225 × 9 (read) | $0.5150 | -79% |
| 1hr 캐싱 (1st write + 9 reads) | $0.50 (write) + $0.0225 × 9 (read) | $0.7025 | -72% |

## 5단계 도입 체크리스트

### 1. 우선순위 — 어디부터?

사용자 baseline 기준 1순위 후보:

| # | 대상 | 크기 | 추정 절감 |
|---|------|------|----------|
| 1 | `paper-maker/SKILL.md` | 23,138자 (~5,800 토큰) | 호출당 입력의 큰 부분이 캐시 hit → -80% input cost |
| 2 | `skill-creator/SKILL.md` | 32,987자 (~8,250 토큰) | 호출 횟수 × 80% 절감 |
| 3 | 8+ agent 하네스 14개 SKILL.md | 평균 8,693자 | 호출 빈도 높을수록 ROI 큼 |
| 4 | system prompt + 토큰 큰 reference 파일 | 변동 | 4 breakpoint 분산 적용 |

### 2. 적용 위치 4 breakpoint (Anthropic 공식 [A004][A005])

API 호출에서 cache_control breakpoint 최대 4개 지정 가능. 분배 권고:

```
breakpoint 1: system prompt (정적·반복) → 5min 캐시
breakpoint 2: SKILL.md (스킬 본문) → 5min
breakpoint 3: 큰 reference 파일 (예: task_to_model_matrix.md) → 5min
breakpoint 4: 누적 컨텍스트 (이전 turn) → 5min
```

API 호출 예 (Anthropic SDK):

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": system_prompt,
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": skill_md_body,
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": reference_doc,
             "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": user_query},  # 동적, 캐시 안 함
        ],
    }
]
```

### 3. 최소 길이 — 캐싱 작동 조건

| 모델 | 최소 토큰 | 비고 |
|------|---------:|------|
| Opus | 4,096 | 미만이면 캐싱 무시 |
| Sonnet | 1,024 | |
| Haiku | 2,048 | |

너무 짧으면 캐싱 자체가 발동 안 함. 평균 SKILL.md 8,693자 ≈ 2,200 토큰 → Sonnet은 OK, Opus는 단독으론 부족. system + skill + reference 묶어 캐싱하면 한계 돌파.

### 4. TTL 선택 — 5min vs 1hr [A010][S-B028]

```
세션 내 반복 호출 < 5분 간격 → 5min (write 1.25×)
세션 간 / 배치 작업 > 30분 간격 → 1hr (write 2.00×)
일일 1회 배치 → 1hr 무의미 (어차피 캐시 만료)
```

paper-maker처럼 phase 별 길어지는 작업 = 1hr. 즉시 단발은 5min.

### 5. 캐시 무효화 회피 [S-B007]

캐시 자동 무효화 발생 시 그 턴 5× 비용 (왜냐면 write 1.25× × miss 전체). 사용자 baseline에 위험 패턴 3개:

**(a) 세션 중 모델 교체 — `/model` 명령**
→ 캐시 전체 무효화. 정책: 세션 시작 시 모델 고정, 다른 모델은 새 세션 또는 서브에이전트.

**(b) 시스템 프롬프트 상단 동적 데이터** [A007]
→ timestamp·랜덤 ID·세션 변동 정보가 system prompt 상단에 있으면 매 turn cache miss.
→ 정책: 동적 데이터는 user message로, system prompt 정적 유지, `<system-reminder>` 분리.

**(c) MCP / 도구 set 변경** [A014]
→ 세션 중 MCP 추가/제거 시 tool 정의 변경 = 캐시 무효화.
→ 정책: 세션 시작 시 tool set 고정. 추가 필요 시 새 세션.

## audit.py 자동 검출

```bash
python3 scripts/audit.py --rules R5
```

R5 룰: `cache_control` / `prompt caching` / `캐싱` 키워드 검색 → 27/27 0회 검출 시 FAIL + 1순위 후보 자동 추천 (가장 큰 SKILL.md).

## 메타 원칙 셀프 체크 (Skill builder 자신)

본 plz-save-token 스킬 자체도 캐싱 적용:

- [ ] SKILL.md (현재 ~13K chars) → 호출 시 cache_control 적용?
- [ ] task_to_model_matrix.md (~6K chars) → reference로 함께 캐싱?
- [ ] 매번 모든 references/ 파일을 컨텍스트에 로드하지 않고 필요 시만 Skill tool로 호출?

## 인접 참고

- `references/anti_patterns_atlas.md` — C5.1~C5.3 카드 3개.
- `scripts/audit.py R5` — 자동 검출.
- `scripts/estimate_cost.py --cache-hit-ratio 0.9` — 캐싱 적용 시 비용 시뮬레이션.
- Anthropic 공식 문서: `docs.anthropic.com/en/docs/build-with-claude/prompt-caching`
