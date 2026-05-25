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

In `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl` line 5, the executor called
`handoff_to_structured` with reason "loop half identified a candidate venue; passing to
structured half for confirmation under policy rules". The signal was the executor completing
`venue_search` at line 4 and finding haymarket_tap as a candidate. The executor script
treats any successful venue match as a trigger for handoff, because venue selection is a
loop-half task but booking confirmation against policy is a structured-half task.

The planner at line 3 produced one subgoal. That subgoal in the FakeExecutor script is
hardcoded to call `venue_search` then `handoff_to_structured` in sequence. In a real LLM
executor the decision would come from the planner's subgoal `assigned_half` field, but in
this scripted run the handoff is deterministic because the executor recognizes the subgoal
type and always delegates confirmation to the structured half. The key signal is that the
loop found a candidate but could not itself validate party size against business rules, so
it had no choice but to forward.

### Citation (required)

- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:5` — executor calls handoff_to_structured, includes reason and context fields

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

The integrity check never triggered in my offline run because the scripted executor called
every tool in correct order with valid arguments. But here is a specific scenario where it
would catch a failure that manual review would miss.

Suppose `get_weather` returns `{"condition": "sunny", "temperature_c": 12}` but the
executor passes `temperature_c=0` to `generate_flyer` (a copy-paste bug where the wrong
field is read from the return value). The flyer would say "Dress warm, 0C outside" which
looks plausible to a human reader checking only the flyer. The integrity check calls
`fact_appears_in_log("12", _TOOL_CALL_LOG)` and finds that 12 appears in the `get_weather`
return but not in the `generate_flyer` arguments. The check raises `AssertionError` with
"12 not found in tool call log", catching the silent data drop before the flyer is
accepted.

This failure would slip through code review because both tools succeed, no exception is
raised, and a reviewer checking the flyer output sees a plausible temperature rather than
an obviously wrong one.

### Citation (required)

- `evidence/ex5_offline/sess_e479b60eb81e/logs/trace.jsonl:4` — get_weather returns temperature_c=12
- `evidence/ex5_offline/sess_e479b60eb81e/logs/trace.jsonl:6` — generate_flyer receives temperature_c=12, integrity check passes

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

The first production failure would be a crash between Rasa accepting a booking and the
session reaching the "complete" state. In Ex7 round 2, line 13 of
`evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl` shows the session transition from loop
to structured, meaning Rasa has received the booking request. Line 14 shows structured to
complete, meaning the bridge wrote the final outcome. If the process dies between these two
events, Rasa has already confirmed the booking internally but the sovereign-agent session
never reaches "complete". The pub has a booking on their side. The customer receives no
confirmation. A retry would send a duplicate booking request to Rasa.

The primitive that surfaces this is the ticket state machine. A ticket stuck in the
"structured" state past a reasonable timeout is a detectable signal. The ticket state
machine enforces that every ticket must reach a terminal state (complete or failed) within
a bounded time. A monitoring job scanning for tickets older than, say, 60 seconds in a
non-terminal state would catch this crash before any human noticed the missing confirmation
email. Without this primitive the failure is invisible until a customer calls to complain.

### Citation (optional but encouraged)

- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:13` — session enters structured state, Rasa has accepted booking
- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:14` — session reaches complete; crash window is between these two lines
