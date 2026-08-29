# Methodology: Hemingway / Cavendish, September 4, 1935

Working notes for the first slice of the Hemingway-in-Key-West mapping project:
the two men's movements on 9/4/1935, the day after the Labor Day hurricane hit
the Middle Keys. Written to be reusable if this becomes an article.

## Files

- `Sandbox Seven Thousand Hells - Document Master List.csv` -- original source. Never modified.
- `working/document_master_list_working.csv` -- exact working copy of the original. All scripts read from here, never the original.
- `scripts/generate_09_04_data.py` -- builds the two derived tables below from hand-curated waypoint lists (see script docstring/comments for per-waypoint sourcing and the time model, below).
- `data/gazetteer_09-04-1935.csv` -- every place named on the two 9/4 routes, with lat/lon, an explicit confidence rating, and a one-line rationale.
- `data/movements_09-04-1935.csv` -- ordered waypoints for each person, each tied to a document ID, a direct quote, and now an estimated clock time (see Time model below).
- `app/app.py` -- Streamlit app: a time slider drives a map showing each person's current (interpolated) position and the text tied to their most recently reached stop.

## Why 9/4 only, and why hand-curated

The full master list has 424 rows spanning dozens of documents and both weeks
after the storm. Rather than try to auto-parse the "Origin Point" / "Destination"
columns for the whole sheet (they are inconsistently populated -- see Data
quality below), this first pass hand-built the two 9/4 routes directly from the
underlying Details/Analysis text, so every waypoint is traceable to a specific
document ID and quote. That is slower but auditable. If this expands to more
days, the same waypoint schema (person, seq, location, time_type, time_label,
document_id, action, quote) should still hold.

## The timestamp problem

Most "Event Date/Time" values in the master sheet are **not real clock times**.
The compiler used incrementing seconds (`12:01:00`, `12:01:01`, `12:01:02`...)
purely to keep facts in the order they appear within a source document -- this
is stated explicitly in the Analysis column of row 9 (Document 1). Cavendish's
article (Document 76) does the same thing, and several of its rows are flagged
directly by the researcher: "***HKJ ADJUST EVENT TIMES TO KEEP CAVENDISH
TOGETHER" -- i.e. those times are provisional placeholders, not reported times.

Only a few stops on each 9/4 route have an actual reported time of day:
- Hemingway: departs Key West 7:00 AM, arrives Lower Matecumbe 4:00 PM (Document 6).
- Cavendish: at Tavernier ~6:00-6:20 AM, at the Fill ~3:00 PM, tied to a body count near Snake Creek ~4:00 PM (Document 76).

## Time model (added for the time-slider view)

To drive a continuous slider that shows "where was each person at time T"
without pretending to precision the sources don't support, every waypoint in
`movements_09-04-1935.csv` now carries:

- `time_type` -- the original categorical flag: **reported** (real time of
  day stated) or **sequence** (order known, clock time not).
- `est_minutes` / `est_time_display` -- a clock-time estimate usable by a
  slider, computed as follows:
  - **reported** waypoints keep the stated time verbatim.
  - **sequence** waypoints between two reported anchors for the same person
    are placed at even intervals between those two anchor times (`time_confidence = interpolated`).
  - **sequence** waypoints with no later reported anchor (Hemingway's last
    four 9/4 stops, after his 4:00 PM arrival) are extrapolated forward in
    fixed 30-minute steps from the last reported time (`time_confidence = extrapolated`).
- `time_confidence` -- `reported` / `interpolated` / `extrapolated`, in
  descending order of trust. The app labels every time with this tag and
  explains it in the "How to read this" expander. Do not strip these labels
  if this data is reused elsewhere -- an extrapolated 6:00 PM at the Fill is
  a display convenience, not a fact.

This is a deliberate simplification (constant speed between two known points),
chosen because it is transparent and reproducible, not because it is
accurate. If this project continues, the extrapolated tail of Hemingway's
route (Camp 5, the Fill) is the best candidate for real research to replace
guesswork -- e.g. estimating walking/boat time from known distances, or
finding a corroborating source with an actual time.

## Geocoding approach and confidence levels

None of the historic camps, the Ferry Slip, the Fill, or Caribbee Colony exist
on a modern map. Three confidence levels are used in the gazetteer:

- **confirmed** -- a real modern coordinate for a place that still exists
  (Key West, No Name Key, Tavernier), checked against public sources.
- **approximate-interpolated** -- the modern key/crossing exists and its US-1
  mile-marker range is documented, but the exact coordinate is linearly
  interpolated along the highway corridor between the three confirmed points
  above, calibrated on the No Name Key -> Tavernier segment. Good enough to
  show relative position and sequence; not a survey point.
- **approximate-historical** -- the site itself is gone. Placed at a mile
  marker inferred from a secondary source's description of "which end of the
  key" the site was on (see per-row notes), then interpolated the same way.
  This is the least certain tier. Camp 5, the Ferry Slip/Camp 3, Camp 1, and
  the Fill fall here.

Key sources for siting:
- Keys Weekly, "Keys History: Hurricane Disrupts Highway & Veteran Work Camps" -- <https://keysweekly.com/42/keys-history-hurricane-disrupts-highway-veteran-work-camps/> (camp locations relative to each key)
- Wikipedia: Lower Matecumbe Key, Upper Matecumbe Key, Windley Key, Craig Key, Snake Creek Bridge (mile-marker ranges)
- latitude.to (No Name Key, Tavernier confirmed coordinates)

If this becomes an article, the honest caveat is: the *route and sequence* are
well supported by the primary sources; the *exact dot on the map* for anything
tagged approximate-historical is a reasonable placement, not a verified site.
Worth a pass with a Keys local historian (the sheet references a "Brad
Bertelli" already, in Document 76's analysis notes) before publishing precise
coordinates as fact.

## The near-miss question -- RESOLVED (per David, 2026-08-29)

Cavendish reaches the Fill on the Upper Matecumbe side around 3 p.m. and
reports seeing across the gap to where Camp 5 had stood -- no sign of the camp,
no sign of survivors. The researcher's own working notes on Document 76 raised
the obvious question: if Cavendish had seen the Hemingway/Key West party at
Camp 5, would he not have mentioned it?

David confirmed directly: **Hemingway was not there yet.** This app's time
model is consistent with that: even on its most generous (extrapolated)
reading, Hemingway's party does not reach the Fill until roughly 6:00 PM,
three hours after Cavendish stood on the opposite bank. So this was not a
missed sighting -- the two accounts describe the same washed-out crossing from
opposite sides, hours apart, not a shared moment. The app's "near-miss" panel
has been updated to state this rather than pose it as an open question.

What is still open: exactly how much later Hemingway arrived is not pinned to
a reported time anywhere in the sources gathered so far -- the "roughly 6:00
PM" figure is the extrapolated estimate described above, not a fact. If a
source surfaces a real reported time for the Camp 5 / Fill leg (the sheet
mentions a Document 62, the Gilfond party account, arriving Lower Matecumbe
"early evening" -- worth checking against this), replace the extrapolation
with it.

## Known gaps / next steps if this project continues

- Hemingway's overnight location the night of 9/4 into 9/5 ("sleeping on the
  deck of the run boat") is itself a deduction in the source sheet (No Name Key
  or Lower Matecumbe, "places are deductions xref southern axis summaries").
  Left out of the plotted route for this reason; worth its own resolution pass.
- The KWC (Key West Citizen) rows for 9/4 (Document 9) describe several other
  vessels leaving Key West that morning and may corroborate or complicate
  Hemingway's own timeline -- not yet folded into this dataset.
- Document 62 (Gilfond party, "early evening" arrival Lower Matecumbe) could
  supply a real reported time to replace part of Hemingway's extrapolated tail.
- This whole approach (hand-curated waypoints keyed to document ID + quote,
  now with a time-estimation layer) should scale to additional days, but each
  new day will need its own pass through the raw Details text and its own
  reported-time anchors; it is not a mechanical extraction from the existing
  spreadsheet columns.

## Geocoding correction -- CORRECTED (2026-08-29)

David reported (after deploying the app to Streamlit Cloud) that all of
Hemingway's waypoints appeared to plot in open water rather than on land.

Root cause: `scripts/generate_09_04_data.py` placed every interpolated point
along a single straight line between just two confirmed reference points 61
miles apart (No Name Key, MM30, and Tavernier, MM91.5). The real Overseas
Highway corridor curves noticeably between those two points, so a straight
line cuts across Florida Bay rather than following the keys -- every
interpolated point came out 2-5 miles north of the real island it was meant
to represent, worst in the middle of the range (Craig Key, Lower Matecumbe)
and smallest near the two original anchors.

Fixed by looking up four more confirmed modern reference points along the
corridor and interpolating piecewise between whichever two anchors bracket
each mile marker, instead of one line end to end:

- Craig Key (MM72): 24.8383, -80.7595 (latitude.to)
- Lower Matecumbe Key centroid (MM75.5): 24.8635, -80.7160 (latitude.to)
- Upper Matecumbe Key centroid (MM81.5): 24.9180, -80.6351 (latitude.to)
- Snake Creek Hwy 1 bridge (MM86): 24.9517, -80.5883 (tidespro)

Four gazetteer rows that happen to sit exactly on these new anchors --
Craig Key, Lower Matecumbe (interior), Upper Matecumbe (Matecumbe Hotel /
King's Inn), and Snake Creek -- were upgraded from `approximate-interpolated`
to `confirmed` accordingly. The remaining interpolated rows (the ferry
slip/Camp 3 end, Camp 5, the Fill, Caribbee Colony, Islamorada, Whale
Harbor, Windley Key/Camp 1) are still interpolated, just now within a much
shorter bracket (a few miles instead of 61), so they should track the real
coastline far more closely -- but they are still estimates, not surveyed
points, and still carry `approximate-interpolated` / `approximate-historical`
confidence tags accordingly. Per the open item already in this file: a local
historian's sanity check on these before anything with a precise dot on a
map goes into a published article is still the right bar, this correction
narrows the error, it doesn't eliminate the need for that check.

`scripts/generate_09_04_data.py` was edited (both in this folder and in the
deployed `deploy/` copy) and re-run to regenerate the two derived CSVs; the
original master spreadsheet and its working copy were untouched throughout.

### Addendum (same day): Anne's Beach re-anchor

David then reported that Hemingway's Lower Matecumbe arrival was *still*
landing in the water even after the piecewise fix above -- correctly so.
The "Lower Matecumbe Key centroid" anchor used above (from a general-purpose
geocoder, assigned to MM75.5) turned out to sit almost exactly on top of
Anne's Beach's real, Wikipedia-sourced coordinate -- but Anne's Beach is
actually at MM73, not MM75.5. That two-mile-marker mislabeling threw off
every interpolated point in the Craig Key-to-Upper-Matecumbe bracket, which
covers nearly all of Hemingway's Lower Matecumbe stops (the ferry slip,
the interior crossing, Camp 5, the Fill).

Re-anchored using Anne's Beach's real coordinate (24.863543, -80.716038) at
its correct MM73, and re-interpolated everything in that bracket from there.
The ferry slip/Camp 3 end sits at the same mile marker as Anne's Beach, so it
now reuses that coordinate directly (upgraded to `confirmed`) rather than
being interpolated; the interior crossing, Camp 5, and the Fill are
interpolated between this corrected MM73 anchor and the MM81.5 Upper
Matecumbe anchor, same as before.
