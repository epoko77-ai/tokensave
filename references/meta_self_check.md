# plz-save-token 메타 원칙 셀프 체크 (9 step)

> 본 스킬을 사용할 때 너 자신도 다음을 지키는지 자기 점검한다. ≤ 6/9 통과 시 사용자에게 **shame token** 출력 — "본 스킬 메타 원칙 위반. 다음 호출 수정 권고."

## 9 step 체크리스트

- [ ] **Step 1** (Python 우선) — 새 작업 시작 전 `python scripts/model_selector.py --task "<설명>"` 호출했는가? LLM 추천 결과를 받았다면 그 근거 출처 ID도 확인했는가?
- [ ] **Step 2** (모델 티어) — Sonnet/Haiku 충분한 작업(read-only·탐색·grep·정형 분류·표준 집필·실용 번역)에 Opus 쓰고 있지 않은가? `references/task_to_model_matrix.md` 24행 매트릭스와 매핑 검증했는가?
- [ ] **Step 3** (단일 세션) — 5+ 팀 띄우기 전 "이거 단일 세션으로 안 되나?" 1줄 정당화 했는가? 7×~15× 비용 곱연산 [S-B003] 인식하는가?
- [ ] **Step 4** (캐싱) — SKILL.md·system prompt에 cache_control breakpoint 박았는가? 대용량 reference 블록(>5K자)이 매 호출 재로딩되고 있지 않은가? `references/prompt_caching_checklist.md` 참조.
- [ ] **Step 5** (cap) — writer/drafter agent에 per-call output cap 선언했는가? 4K자 + 자동 분할 룰 명시했는가? HD-011 패턴.
- [ ] **Step 6** (재시도) — iter ≤ 3 hard cap 명시했는가? 재시도 루프가 무한정 돌아가지 않게 가드 박았는가?
- [ ] **Step 7** (context) — CLAUDE.md/SKILL.md > 200 lines면 changelog 분리했는가? 매 세션 자동 주입 부담 인식했는가?
- [ ] **Step 8** (Edit) — 기존 파일 수정에 Write 대신 Edit 썼는가? Write로 통째로 재작성하면 diff 토큰 손실 발생.
- [ ] **Step 9** (메타 위반 보고) — 본 스킬 사용 중 메타 원칙 위반 발생 시 사용자에게 즉시 보고했는가? 위반을 숨기지 않았는가?

## 채점

| 통과 step | 판정 |
|----------|------|
| 9/9 | ✅ 모범 |
| 7~8/9 | 🟡 합격 — 미흡 step 다음 호출 보강 |
| ≤ 6/9 | 🔴 **shame token** 발동 — 사용자에게 즉시 보고 + 다음 호출 수정 권고 |

## Shame token 출력 포맷

```
⚠️  plz-save-token 메타 원칙 위반 (X/9 통과)
  - 미흡: Step N(이름), Step M(이름), ...
  - 다음 호출 수정 권고: <구체 액션>
```

## 자기 사용 사례

본 스킬 v1 빌드 자체가 이 체크리스트의 모범 사례 (Step 1·2·3·6·7·8 모두 통과). 다만 SKILL.md 21K(슬림화 후 ~15K)는 Step 7에 부분 위반 — `meta_skill: true` frontmatter로 예외 처리됨.
