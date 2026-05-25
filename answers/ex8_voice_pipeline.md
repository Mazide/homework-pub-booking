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

*(Write your answer below this line. Do not remove the heading.)*

---

## Citations

List at least TWO specific citations:

- `sessions/sess_<id>/logs/trace.jsonl:<line>` — `voice.utterance_in` or `voice.utterance_out` event
- `sessions/sess_<id>/...` — evidence of the persona staying in character
  (e.g. a specific LLM response with a clearly in-character phrase)
