# Ex9 — Reflection

Answer all three questions. The grader expects every question to be answered;
blank answers are zero.

---

## Наблюдения из реальных запусков (для справки при написании ответов)

**Ex5 offline** (детерминированный, правильный):
- Сессия: `evidence/ex5_offline/sess_e479b60eb81e`
- Инструменты: venue_search → get_weather → calculate_cost → generate_flyer → complete_task
- Flyer: Haymarket Tap, £540 total, £0 deposit, cloudy 12C
- Integrity check: verified 4 facts ✓

**Ex5 real (Qwen3-32B)** — пример сбоя LLM:
- Сессия: `evidence/ex5_real_sess_f3f276307594`
- venue_search вызван с неверными аргументами (Edinburgh, party=10 вместо Haymarket, party=6)
- 0 результатов → модель сдалась, вызвала complete_task + handoff_to_structured
- flyer.md не создан — integrity check не нужен, сценарий провалился раньше

---

## Q1 — Planner handoff decision

### Prompt

Find a point in your Ex7 logs where the planner decided to hand off to the
structured half. Quote the planner's reasoning or the specific subgoal's
`assigned_half` field. What signal caused the decision?

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

### Citation (required)

- `sessions/sess_<id>/logs/tickets/tk_<id>/raw_output.json` — planner output showing the subgoal with `assigned_half`
- OR `sessions/sess_<id>/logs/trace.jsonl:<line>` — trace event showing the decision

---

## Q2 — Dataflow integrity catch

### Prompt

Describe one instance where your Ex5 dataflow integrity check caught something
manual inspection would have missed, OR (if the check never triggered in your
runs) describe a plausible scenario where it WOULD catch a failure. Your
scenario must be specific enough that someone else could construct the test
case.

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

### Citation (required)

If you observed it trigger:

- `sessions/sess_<id>/logs/trace.jsonl:<line>` — event where the integrity check fired
- `sessions/sess_<id>/workspace/flyer.md` — the problematic output

If you're describing a hypothetical:

- Describe exactly what the malformed tool output would look like, and
  what the flyer would say, such that a human reviewer would miss it
  but the check would not.

---

## Q3 — First production failure + primitive

### Prompt

If you were shipping this agent to a real pub-booking business next week,
what's the first production failure you'd expect, and which sovereign-agent
primitive (ticket state machine, manifest discipline, IPC atomic rename,
SessionQueue retry, drift-corrected scheduler, mount allowlist, HITL approval,
etc.) would surface it?

Name EXACTLY ONE primitive and EXACTLY ONE failure mode. Vague answers that
name multiple primitives or generic "something will break" failures lose
points.

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

### Citation (optional but encouraged)

- Link to the sovereign-agent docs section describing the primitive you named,
  OR a trace line from your own logs showing that primitive in action.
