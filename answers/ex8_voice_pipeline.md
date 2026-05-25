# Ex8 — Voice pipeline

## Prompt

Describe how your voice pipeline handles state across STT → LLM → TTS turns.
Where does the conversation history live? How does the Llama-3.3-70B manager
persona stay in character? If you ran in voice mode (not just text), describe
one failure mode you observed with real audio (latency, transcription errors,
audio quality) and how you'd address it.

If you only ran in text mode, answer the state question, the persona question,
and describe ONE plausible failure mode you'd expect from voice even without
having tested it. (Full credit still possible.)

**Word count:** 200-400 words.

## Your answer

The pipeline ran in text mode. Each turn follows the same path: user input is logged as a
voice.utterance_in trace event, passed to ManagerPersona.respond(), the LLM reply is logged
as voice.utterance_out, then printed. In voice mode the path is identical except input comes
from Speechmatics STT and output goes to Rime TTS before printing.

Conversation state lives inside ManagerPersona.history as a list of ManagerTurn objects.
Each call to respond() appends the new turn and rebuilds the full message list: system prompt,
then all prior turns as alternating user/assistant messages, then the new user message. This
gives Llama-3.3-70B complete context of every prior exchange so it can remember what was
already agreed (date, party size, deposit).

The persona stays in character through the system prompt which defines Alasdair MacLeod as a
gruff Edinburgh pub manager with explicit business rules: accept parties of 8 or fewer with
deposit under 300, decline otherwise. temperature=0 makes responses deterministic. In
sess_6f560a3bc542 when asked for 6 people on April 25th the manager replied "Aye, we can do
that. I'll pencil you in for April 25th at 7:30pm." and when the conversation ended replied
"Cheerio." Both responses are clearly in character and follow the rules.

This run was text mode only. The most plausible voice failure would be STT transcription
errors on Scottish venue names and amounts. "Haymarket Tap" could be transcribed as "Hey
market tap" and "deposit of £150" as "deposit of fifty". These errors would reach the LLM
as corrupted input, the manager would respond to wrong information, and the session trace
would log the corrupted text without any indication that transcription failed. The fix is
to add a confidence threshold check on the Speechmatics transcript and prompt the user to
repeat if confidence is below threshold before passing text to the persona.

---

## Citations

- `evidence/ex8_sess_6f560a3bc542/logs/trace.jsonl:1` (voice.utterance_in turn 0, booking request for 6 people)
- `evidence/ex8_sess_6f560a3bc542/logs/trace.jsonl:2` (voice.utterance_out turn 0, manager accepts in character "Aye, we can do that")
- `evidence/ex8_sess_6f560a3bc542/logs/trace.jsonl:6` (voice.utterance_out turn 2, manager ends with "Cheerio" staying in character)
