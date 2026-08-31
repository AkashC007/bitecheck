# Privacy and ethics

## Active principles

- Never commit credentials or expose server secrets to the browser.
- Do not scrape restricted platforms.
- Clearly label synthetic data.
- Do not retain precise user location or voice transcripts by default.
- Preserve source attribution when external data is introduced.
- Do not describe review confidence as proof of truthfulness.

No user data, location, transcript, restaurant data, or review data is stored in
Milestone 0.

Milestone 1 stores only generated records. Restaurant names use generated word
combinations, addresses use obvious demo street names, and every record includes
`data_provenance: synthetic`. Coordinates and travel times are for testing only.

## Browser voice privacy

Milestone 12 voice input starts only after the user presses the visible
push-to-talk control and the browser grants microphone access. BiteCheck does
not record, upload, or store audio. The recognized transcript is placed in an
editable text box and is sent to the local conversation endpoint only when the
user submits it.

Browser speech-recognition implementations may process audio through services
controlled by the browser vendor. That behavior is outside BiteCheck and can
vary by browser, so text input remains the complete privacy-preserving fallback.
Spoken replies are disabled by default, use browser speech synthesis, and can be
stopped immediately. BiteCheck does not create a transcript history or attach
voice data to an identity.
