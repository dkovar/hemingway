---
title: Handoff -- Hemingway / Cavendish 9/4/1935 Mapping Project
last_session_date: 2026-08-29
written_for: a new Claude session with no memory of the work below
---

# Handoff: Hemingway-in-Key-West data project

This file exists so a new session can pick this up cold. It covers what was
asked, what was decided, what was built, and what is still open. Read this
before touching any file in this folder.

## 1. The project, in one paragraph

David has a spreadsheet (`Sandbox Seven Thousand Hells - Document Master
List.csv`) built by a researcher referred to as "HKJ," cataloguing primary
sources (Hemingway's own letters and essays, Miami-area newspapers, Key West
Citizen) about Hemingway's time in Key West and specifically the September
1935 Labor Day hurricane, which devastated the Middle Florida Keys and killed
hundreds of WWI veterans working in FERA highway-construction camps.
Hemingway went out on his boat Pilar with a Key West rescue party and later
wrote "Who Murdered the Vets?" about it. The end goal (per the project's
Cowork instructions) is Python + Streamlit tooling to clean, analyze, and
visualize this data, eventually feeding an article. This session did the
first slice: mapping Hemingway's movements against Miami Herald reporter
Henry Cavendish's on 9/4/1935, the day after the hurricane hit.

## 2. Session-by-session narrative

### Turn 1 -- "Look at this data. Think about it but do not do anything."

David uploaded the master CSV and asked me to look at it and think, explicitly
without building anything yet (this matches a standing rule in his
`ursa-claude` preferences: design before doing, wait for explicit agreement).

What I found and reported back:
- 424 rows, each one a single granular fact/quote pulled from a source
  document, not one row per document. "Document ID" groups rows back to a
  source (Doc 1 = Hemingway's 9/7/1935 letter to Max Perkins; Doc 6 =
  his essay "Who Murdered the Vets?" i.e. WMtV; Doc 76 = Cavendish's Miami
  Herald dispatch). Other columns: Details (the actual quote/fact), Analysis
  (HKJ's own scholarly annotation/cross-referencing layer), Map Data? (a
  hand-flagged boolean, true on 69/424 rows, presumably HKJ's intended
  starting scope for mapping), Geographic Focus (Northern Axis / Southern
  Axis / Storm Area), and a loose Origin Point / Destination 1&2 / Departure
  / Arrival / Transport Mode set of columns that is only populated on a
  minority of rows.
- Found that Hemingway's and Cavendish's 9/4/1935 movements are both in the
  sheet and make a strong pair: Hemingway moving north from Key West,
  Cavendish moving south from Tavernier, both converging on "The Fill" (the
  washed-out highway crossing between Lower and Upper Matecumbe) the same
  afternoon.
- Flagged three caveats before building anything:
  1. Most "Event Date/Time" values are a synthetic ordering trick
     (incrementing seconds like 12:01:00, 12:01:01...) used purely to keep
     facts in reading order within a document -- not real clock times. This
     is stated explicitly in the sheet's own Analysis column (row 9,
     Document 1) and reinforced by literal researcher notes on Document 76
     ("***HKJ ADJUST EVENT TIMES TO KEEP CAVENDISH TOGETHER").
  2. Location data is split inconsistently across "Location/Origin Point"
     (often a comma-separated pile of places) and the more structured
     Origin/Destination columns (sparsely populated).
  3. Several named places (the veteran work camps, the Ferry Slip, the Fill,
     Caribbee Colony) no longer exist and need real historical geocoding,
     not a simple lookup.
- Asked one question: start narrow (gazetteer + this one 9/4 map as a proof
  of concept) or build the fuller Streamlit scaffolding first?

David answered: **"Save this to the workspace. We may want to write an
article about this work. Do just the 9/4."** -- i.e. narrow scope, but treat
it as durable/citable work product, not a throwaway.

### Turn 2 -- building the 9/4 slice

Did NOT touch the original CSV. Built, in `Hemingway/` on David's Google
Drive (this session works on his machine via a device-bridge shell, not by
uploading/downloading files):

- `working/document_master_list_working.csv` -- exact copy of the original
  (checksum-verified identical), everything else reads from this copy.
- Pulled the full, untruncated text of every 9/4/1935 row for Hemingway
  (Documents 1 and 6) and Cavendish (Document 76) to build an accurate,
  quote-cited waypoint list by hand (not auto-parsed -- the source columns
  are too inconsistent to parse mechanically and still be trustworthy).
- Did real web research (WebSearch/WebFetch) to site the historical/vanished
  locations: Keys Weekly's "Hurricane Disrupts Highway & Veteran Work Camps"
  article gave camp locations relative to each key (Camp 3 and the Ferry
  Slip both at the west/south end of Lower Matecumbe; Camp 5 at the
  east/north end; Camp 1 "just across Snake Creek from Plantation Key" on
  Windley Key). Wikipedia gave US-1 mile-marker ranges for each key. Modern
  coordinates for Key West, No Name Key, and Tavernier were confirmed via
  search (latitude.to).
- Because no reliable geocoding API/infobox coordinates were reachable from
  this environment, built a **linear mile-marker interpolation**: calibrated
  the lat/lon-per-mile rate on the confirmed No Name Key (MM30) -> Tavernier
  (MM91.5) segment, then placed every other point (confirmed island mile
  marker or inferred camp position) along that line. Every gazetteer row
  carries a `confidence` tag (`confirmed` / `approximate-interpolated` /
  `approximate-historical`) and a sourcing note -- see
  `data/gazetteer_09-04-1935.csv` and the Methodology file for the full
  rationale and citations.
- Built `scripts/generate_09_04_data.py`, a well-commented script that is the
  actual source of truth for the two derived tables (`data/gazetteer_09-04-1935.csv`,
  `data/movements_09-04-1935.csv`). Edit the script, re-run it, don't
  hand-edit the CSVs.
- Built a first-pass Streamlit app (`app/app.py`) plotting both routes on a
  pydeck map with a synced list of the underlying quotes.
- Verified: original CSV checksum unchanged; all 15 waypoints resolve to
  gazetteer coordinates with no missing joins; app starts headless with no
  errors.
- Wrote `notes/methodology_09-04-1935.md` (sourcing, the timestamp caveat,
  the geocoding confidence rubric, and an explicitly flagged **open research
  question**: whether Cavendish, standing at the Fill around 3 p.m. looking
  across at where Camp 5 had stood, could have seen Hemingway's Key West
  party -- HKJ's own notes on Document 76 raise this directly).
- Wrote `README.md` (how to run/regenerate) at the folder root.

### Turn 3 -- "OK, make a time slider that a) shows the current location of
each person and b) shows the current associated text."

Given the timestamp problem above, a literal time slider needed an explicit,
transparent time model rather than pretending the sheet's timestamps are
real. Built one:

- Every waypoint gets `time_confidence`: `reported` (a real time-of-day is
  stated in the source), `interpolated` (sequence-only stop between two
  reported anchors for the same person, placed at even intervals -- a
  constant-speed assumption, explicitly flagged as a display convenience,
  not a claim about actual pacing), or `extrapolated` (sequence-only stop
  with no later reported anchor -- only applies to Hemingway's last four 9/4
  stops after his 4:00 PM arrival -- fixed 30-minute steps forward, weakest
  confidence tier).
- Reported anchors used: Hemingway departs Key West 7:00 AM, arrives Lower
  Matecumbe 4:00 PM (Document 6); Cavendish at Tavernier ~6:10 AM, at the
  Fill ~3:00 PM, near Snake Creek ~4:00 PM (Document 76).
- Rewrote `app.py`: a slider (6:10 AM-6:00 PM, 5-minute steps) drives (a) a
  map showing each person's position linearly interpolated between their
  two surrounding waypoints (a straight-line approximation, not a real GPS
  track) and (b) a text panel showing the action/quote tied to whichever
  stop each person has actually reached, labeled with its
  reported/interpolated/extrapolated confidence.
- Regenerated the derived CSVs (`generate_09_04_data.py` now writes
  `est_minutes`, `est_time_display`, `time_confidence` columns), verified
  the merge has no missing coordinates, verified the interpolation logic
  standalone across the whole time range (no exceptions, sensible motion),
  and smoke-tested the Streamlit app headless (HTTP 200, no errors in logs).

**Mid-turn correction from David: "Hemingway was not there yet."** This
resolves the open near-miss question from the methodology notes: David
confirmed Hemingway's party had NOT yet arrived at the Fill/Camp 5 when
Cavendish stood on the opposite bank around 3 p.m. This was folded into both
`app.py` (the "near-miss" info panel now states this as fact, attributed,
rather than posing it as an open question) and
`notes/methodology_09-04-1935.md` (a new "RESOLVED (per David, 2026-08-29)"
section). Useful cross-check: the time model's own extrapolation, built
before this correction was given, already put Hemingway's arrival at the
Fill no earlier than ~6:00 PM -- three hours after Cavendish -- so the
correction is consistent with, not contradicted by, the estimated data.
Still open: the *exact* size of that gap is not pinned to any reported time
in the sources gathered so far; the "~6:00 PM" figure is an extrapolation,
not a fact, and the notes point at Document 62 (the Gilfond party's "early
evening" arrival) as a lead worth checking if a tighter number is wanted.

## 3. Current file layout (`Hemingway/` on David's Google Drive)

```
Hemingway/
  Sandbox Seven Thousand Hells - Document Master List.csv   <- ORIGINAL. Never modify.
  Claude-first pass.txt          <- David's own copy/paste of this session's first response. Not authored by tooling.
  README.md                      <- quick-start: how to run/regenerate
  HANDOFF.md                     <- this file
  working/
    document_master_list_working.csv   <- exact copy of the original; everything reads from here
  scripts/
    generate_09_04_data.py       <- SOURCE OF TRUTH for the two derived CSVs below. Edit this, not the CSVs.
  data/
    gazetteer_09-04-1935.csv     <- 14 places, lat/lon, mile marker, confidence tag, sourcing note
    movements_09-04-1935.csv     <- 15 ordered waypoints (6 Hemingway, 9 Cavendish), each with document_id,
                                     quote, time_type, time_label, est_minutes, est_time_display, time_confidence
  app/
    app.py                       <- Streamlit app: time slider + map + current-location/current-text panel
  notes/
    methodology_09-04-1935.md    <- full sourcing, caveats, the resolved near-miss question, open next steps
```

Nothing in `working/`, `data/`, `app/`, `notes/`, or `scripts/` should ever be
confused with the original CSV. If in doubt, `md5sum` the original against
`working/document_master_list_working.csv` -- they must always match.

## 4. How to run it

```
cd Hemingway/app
streamlit run app.py
```

streamlit and pydeck are already installed in this environment's Python (via
`pip3 install streamlit pydeck`, done in this session). If a new environment
doesn't have them: `pip3 install streamlit pydeck pandas`.

To regenerate the derived data after editing the waypoint lists or gazetteer
in `scripts/generate_09_04_data.py`:

```
cd Hemingway
python3 scripts/generate_09_04_data.py
```

## 5. Standing project context (not specific to this thread of work)

This Cowork project is titled "Hemingway" with the project instruction "Data
analysis of CSV data relating to Hemingway in Key West in 1935." Separately,
David's Cowork sessions in general (not just this project) run under his
`ursa-claude` repo's rules/preferences/context (candor, concise output, no em
dashes, design-before-doing, ask one question at a time, etc.) and a
standing instruction to check whether the `mini-cowork` MCP is connected at
session start. Those are account-wide, not project-specific -- a new session
should pick them up automatically via its own system prompt/instructions
rather than needing anything from this file, but they explain some of the
conventions in the files above (e.g. no em dashes anywhere, methodical
sourcing notes, the original-file-is-sacred discipline).

## 6. Open items for the next session

1. **Extend beyond 9/4.** The KWC (Key West Citizen) rows for 9/4 (Document
   9) describe other vessels leaving Key West that morning and may
   corroborate or complicate Hemingway's own timeline -- not yet folded in.
   Other days (9/2 storm night, 9/5 onward) are entirely unbuilt.
2. **Tighten Hemingway's afternoon/evening timing.** Document 62 (the
   Gilfond party's "early evening" Lower Matecumbe arrival) might supply a
   real reported time to replace part of the extrapolated tail (Camp 5, the
   Fill) -- worth a targeted look at that document's rows.
3. **Resolve Hemingway's overnight location** (night of 9/4 into 9/5,
   "sleeping on the deck of the run boat"). The sheet itself calls this a
   deduction between No Name Key and Lower Matecumbe. Deliberately left out
   of the plotted route for this reason.
4. **Get a local-historian sanity check on the approximate-historical
   coordinates** (Camp 5, Camp 1, the Ferry Slip, the Fill, Caribbee Colony)
   before anything with a precise dot on a map goes into a published
   article -- the sheet itself references a Keys historian, "Brad Bertelli,"
   in Document 76's analysis notes, who might be the right person to check
   against.
5. **If this becomes an article**, the honest framing is: the *route and
   sequence* of both men's 9/4 movements are well supported by primary
   sources; the *exact dot on the map* for anything tagged
   approximate-historical, and most of the *clock times* on the slider, are
   reasonable estimates, not verified facts. `notes/methodology_09-04-1935.md`
   has the full caveat language already drafted -- reuse it rather than
   re-deriving the caveats from scratch.
6. **Nothing has been pushed anywhere else** (no git repo, no article draft
   started). Everything referenced above lives only in this Drive folder.
