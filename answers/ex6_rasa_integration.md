# Ex6 — Rasa integration

## Prompt

How did you wire Rasa CALM into the sovereign-agent `StructuredHalf` protocol?
Describe specifically: (1) how your subclass translates an input `dict` into a
Rasa-compatible intent payload, (2) how your `ActionValidateBooking` custom
action surfaces validation failures back into a `HalfResult`, and (3) one thing
you would change about the integration if you were building this for production.

**Word count:** 200-400 words.

## Your answer

RasaStructuredHalf.run() takes the loop half's output dict and passes it through
normalise_booking_payload() before sending anything to Rasa. The normaliser converts messy
loop output into a clean Rasa webhook payload: "Haymarket Tap" becomes "haymarket_tap",
"25th April 2026" becomes "2026-04-25", "7:30pm" becomes "19:30", "£200" becomes 200.
The result is POSTed as JSON to localhost:5005 with message "/confirm_booking" and the
cleaned booking in metadata.

On the Rasa side, ActionValidateBooking reads the booking from
tracker.latest_message.metadata.booking and runs two checks. Party size above 8 triggers
SlotSet("validation_error", "party_too_large"). Deposit above 300 triggers
SlotSet("validation_error", "deposit_too_high"). The confirm_booking flow branches on
that slot: non-null goes to utter_booking_rejected, null goes to utter_booking_confirmed.
Back in Python, RasaStructuredHalf parses the response text for "can't accept" to set
next_action="escalate" or "booking confirmed" to set next_action="complete". In
sess_6fd0641628d8 party=6 deposit=200 passed validation and returned complete with ref
BK-7D401E9E. In sess_e0565858e727 party=12 failed with party_too_large and returned escalate.

For production I would replace the text-matching logic with structured custom events.
Right now rejection detection depends on parsing "can't accept" from Rasa's response string,
which breaks silently if the utterance template changes. A proper integration would have
ActionValidateBooking emit a custom JSON payload with a machine-readable action field
so the bridge never needs to parse human-readable text.

---

## Citations

- `evidence/ex6_real_sess_6fd0641628d8/session.json` (confirmed, party=6 deposit=200 ref BK-7D401E9E)
- `evidence/ex6_real_rejected_sess_e0565858e727/session.json` (rejected, party=12 party_too_large)
- `starter/rasa_half/validator.py:52` (normalise_booking_payload)
- `rasa_project/actions/actions.py:119` (party_too_large check)
