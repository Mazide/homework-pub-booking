# Ex5 — Edinburgh research loop scenario

## Prompt

Describe the trajectory your Ex5 scenario takes through the loop half. Which
subgoals did the planner produce? Which tools were called? Were there any
tool calls that the dataflow integrity check would have flagged if you had
left them uncorrected?

**Word count:** 150-300 words.

## Your answer

In the offline run (sess_e479b60eb81e), the planner produced two subgoals: sg_1 to research
Edinburgh venues near Haymarket for a party of 6, and sg_2 to produce a Markdown flyer with
venue, weather, and cost data. The executor ran all four tools in order. venue_search returned
haymarket_tap as the only match. get_weather and calculate_cost were called in parallel and
returned cloudy/12C and total £540/deposit £0 respectively. generate_flyer wrote flyer.md to
the session workspace. complete_task closed the session. The dataflow integrity check verified
four facts from the flyer (£540, £0, 12C, cloudy) against _TOOL_CALL_LOG and all matched tool
outputs, so ok=True.

Three real Nebius runs (Qwen3-32B) showed different failure modes. In sess_6cb421723557 (the
first attempt, original prompt), the model called no research tools at all. It called
handoff_to_structured immediately, claiming it needed party size and area from a structured half
despite both being explicitly stated in the task. In sess_f3f276307594, the
model made a single venue_search call with self-invented arguments (near='Edinburgh', party_size=10)
instead of the explicitly specified near='Haymarket', party_size=6. It received 0 results, then
immediately called complete_task with an empty result and handoff_to_structured without
attempting any other tools. In sess_7d723426b7b7 (run after updating the task prompt to
explicitly forbid handoff_to_structured and repeat the correct arguments), the model spiralled:
three consecutive venue_search calls with invented parameters (Edinburgh Old Town party=10,
Edinburgh City Center party=20, Edinburgh party=5), all returning 0 results, followed by
handoff_to_structured. In both cases generate_flyer was never called and the dataflow integrity
check never ran because the scenario failed before reaching the flyer stage.

No tool calls in the offline run would have been flagged because the scripted trajectory produced
correct data end-to-end. Hypothetically, if the LLM had written £560 in the flyer instead of
the £540 returned by calculate_cost, verify_dataflow would have caught it since 560 appears in no
tool output. However, if it had used hire_fee_gbp=110 from venue_search output as the total,
the check would have passed because 110 is present in the log even though it is semantically wrong
as a total cost. This is a known limitation: the check verifies existence in the log, not
which field the value came from.

---

## Citations

- `evidence/ex5_offline/sess_e479b60eb81e/logs/trace.jsonl:3` (venue_search called with correct args, near=Haymarket party_size=6)
- `evidence/ex5_offline/sess_e479b60eb81e/logs/trace.jsonl:4-5` (get_weather and calculate_cost called in parallel, sg_1 executor)
- `evidence/ex5_real_sess_6cb421723557/logs/trace.jsonl:3` (handoff_to_structured called with no prior tool calls, original prompt)
- `evidence/ex5_real_sess_f3f276307594/logs/trace.jsonl:3` (single venue_search with wrong args Edinburgh party=10, then immediate complete_task)
- `evidence/ex5_real_sess_7d723426b7b7/logs/trace.jsonl:3-5` (three venue_search calls with wrong args after prompt fix, spiral failure)
- `evidence/ex5_offline/sess_e479b60eb81e/logs/tickets/tk_be68a595` (planner ticket showing two subgoals)
