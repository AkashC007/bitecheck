# Public inspection explorer

The primary BiteCheck experience queries the official City of Chicago Food
Inspections dataset at request time. It does not use the synthetic review,
rating, cuisine, cost, dietary, hours, travel-time, theme, confidence, or ranking
fields from the Analytics Lab.

## Data flow

1. The user chooses a preset Chicago area, enters a restaurant/address/ZIP, or
   explicitly grants current-location permission.
2. The browser sends a typed POST request to the same-origin Next.js route.
3. FastAPI builds a bounded SODA query for restaurant facility records with
   coordinates. Geographic searches use `within_circle`.
4. The provider validates each untrusted external row and skips malformed rows.
5. The service groups records by City license number, selects the newest
   inspection, groups result labels, and calculates straight-line distance.
6. The browser validates the response again before rendering factual cards.

## Card fields

- City license number and establishment names
- Address and exact OpenStreetMap coordinate link
- Facility type and City risk category
- Latest inspection date, result, and inspection type
- Counts for inspection rows included in that bounded live query
- Straight-line distance when a geographic center was supplied

## Interpretation boundaries

- An inspection result describes what inspectors observed on its recorded date.
- A Pass is not a guarantee of current safety or current operation.
- A Fail is not a permanent label; users should consult the linked official
  dataset for later inspections and full details.
- “City risk category” is a source field, not a BiteCheck prediction.
- History counts cover only records returned by the bounded query and are not
  claimed as a complete lifetime history.
- Current-location distance is straight-line distance, not walking, transit, or
  driving time.
- The explorer covers Chicago inspection records, not every restaurant outside
  Chicago and not menu, price, rating, or opening-hours data.

## Reliability behavior

The City provider has an eight-second timeout and returns a safe HTTP 503 when
the source cannot be reached or parsed. There is no hidden fallback to synthetic
restaurant facts. Tests replace the live provider with deterministic fakes; a
separate live smoke check confirms the real source contract.
