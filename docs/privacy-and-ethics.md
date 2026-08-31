# Privacy and ethics

## Active principles

- Never commit credentials or expose server secrets to the browser.
- Do not scrape restricted platforms.
- Clearly label synthetic data.
- Do not retain precise user location or voice transcripts by default.
- Preserve source attribution when external data is introduced.
- Do not describe review confidence as proof of truthfulness.

No user location, transcript, account, or personal profile is stored.

## Location privacy

Current location is optional and requested only after the user presses the
visible control and grants browser permission. Preset Chicago-area searches do
not use or share a personal location.

The public explorer sends the chosen coordinates in a POST body to the
same-origin Next.js route and FastAPI. FastAPI uses them in an HTTPS geographic
query to the City of Chicago open-data service. BiteCheck does not store them in
a database, cookie, file, browser storage, or application log. The external City
service necessarily receives the coordinates as part of its query and operates
under its own logging and privacy practices.

The separate synthetic Analytics Lab keeps current coordinates only in React
state. It calculates straight-line distance locally against the fixed 24-record
snapshot and never sends those coordinates to FastAPI.

Straight-line distance is labeled separately from the synthetic travel-time
estimates. It is not a routing estimate and does not mean that these are all of
the restaurants near the user. Exact establishment addresses link to
OpenStreetMap using the public City coordinates.

The public explorer returns live public establishment identity, address,
coordinate, license, facility, City risk-category, and inspection-result fields.
The Analytics Lab snapshot contains public establishment identity,
address, coordinate, license, and inspection fields from the City of Chicago
Food Inspections dataset. BiteCheck records the source, snapshot date,
transformations, and disclaimer. Inspection records describe conditions at the
time of inspection and are not presented as a current safety guarantee.

Cuisine, price, dietary availability, ratings, reviews, opening hours, travel
times, themes, confidence, and ranking labels are synthetic. They are kept
inside the explicitly labeled Analytics Lab, separated through field-level
provenance, and must not be interpreted as factual claims about the named
businesses.

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
