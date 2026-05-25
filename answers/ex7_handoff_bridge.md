# Ex7 — Handoff bridge

## Prompt

Walk through the bidirectional round-trip your handoff bridge performs. Start
with the initial task, describe each handoff event (forward and reverse), and
explain what session state the system is in at each transition. Identify the
exact line in your logs where the second research cycle begins after the
structured half's first rejection.

**Word count:** 200-400 words.

## Your answer

The bridge started with task "book for party of 12 in Haymarket". Round 1 began at trace
line 1 (bridge.round_start). The loop half ran: planner produced one subgoal, executor called
venue_search(near=Haymarket, party_size=12) at line 4 then handoff_to_structured at line 5
passing haymarket_tap with party=12 and deposit=0. The bridge packaged this into a forward
handoff and sent it to RasaStructuredHalf. Rasa ran ActionValidateBooking which detected
party_size=12 exceeds the cap of 8 and returned party_too_large. The session state changed
from loop to structured at line 6, then immediately back from structured to loop at line 7
with rejection_reason="sorry, we can't accept this booking. reason: party_too_large".

The second research cycle begins at line 8 (bridge.round_start round=2). The bridge called
build_reverse_task() which constructed a new task dict containing the rejection reason and
a retry flag, then passed it back into loop_half.run(). The planner replanned with the
rejection context. The executor called venue_search(near=Old Town, party_size=6) at line 11
then handoff_to_structured at line 12 with royal_oak and party=6. This time ActionValidateBooking
found party_size=6 within the cap and deposit=0 within the limit so it returned booking
confirmed with reference BK. The session state changed from loop to structured at line 13
then from structured to complete at line 14. The bridge returned outcome=completed rounds=2.

At each transition the bridge wrote a session.state_changed trace event so the full path
loop to structured to loop to structured to complete is visible without reading the full
payload of each message.

---

## Citations

- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:5` (forward handoff, executor calls handoff_to_structured round 1)
- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:7` (reverse handoff, structured rejects party_too_large, returns to loop)
- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:8` (second research cycle begins, bridge.round_start round=2)
- `evidence/ex7_sess_971ff4ccb044/logs/trace.jsonl:14` (session reaches complete state, round 2 confirmed)
