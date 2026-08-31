# Browser voice methodology (Milestone 12 in progress)

Voice is optional progressive enhancement around the existing follow-up text
contract. Push-to-talk requests browser speech recognition, writes the result
into the same editable input, and never submits automatically. Typed input
remains the complete fallback.

Spoken replies are off by default. When enabled, the browser cancels older
speech before reading a concise transition and top-result summary. A visible
stop control cancels speech immediately. No audio is stored by BiteCheck and no
paid API key is used.

The interface handles unsupported recognition, denied microphone access, no
speech, capture failure, network failure, and unexpected errors with text
guidance. Recognition is configured for one push-to-talk turn, interim
transcripts, and `en-US`; the transcript stays editable before submission.

Automated adapter tests cover standard and prefixed browser support, transcript
handoff, error normalization, speech cancellation, and stop behavior. Final
Milestone 12 completion still requires a user-authorized live microphone
permission check because Codex will not grant microphone access on the user's
behalf.

Live checks not requiring microphone permission verified the visible and
accessible push-to-talk, spoken-reply, and stop controls; editable transcript
handoff through a suggestion; successful text fallback; off/on/off spoken-reply
state; a narrow layout without horizontal overflow; and zero browser console
errors or warnings.
