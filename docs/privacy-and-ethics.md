# Privacy and ethics

## Active principles

- Never commit credentials or expose server secrets to the browser.
- Do not scrape restricted platforms.
- Clearly label synthetic data.
- Do not retain precise user location or voice transcripts by default.
- Preserve source attribution when external data is introduced.
- Do not describe review confidence as proof of truthfulness.

No user location, transcript, account, or personal profile is stored.

## Browser location privacy

Current location is optional and requested only after the user presses “Use my
location” and grants browser permission. The coordinates live only in React
state in that browser tab: they are not placed in a URL, sent to the Next.js or
FastAPI services, logged, or persisted. They are used to calculate straight-line
distance to the fixed 24-record snapshot and optionally reorder visible results.

Straight-line distance is labeled separately from the synthetic travel-time
estimates. It is not a routing estimate and does not mean that these are all of
the restaurants near the user. Exact establishment addresses link to
OpenStreetMap using the public City coordinates.

The current restaurant snapshot contains public establishment identity,
address, coordinate, license, and inspection fields from the City of Chicago
Food Inspections dataset. BiteCheck records the source, snapshot date,
transformations, and disclaimer. Inspection records describe conditions at the
time of inspection and are not presented as a current safety guarantee.

Cuisine, price, dietary availability, ratings, reviews, opening hours, travel
times, themes, confidence, and ranking labels are synthetic. They are kept
separate through field-level provenance and must not be interpreted as factual
claims about the named businesses.

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
