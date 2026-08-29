# Hemingway / Cavendish, 9/4/1935

Streamlit app mapping Ernest Hemingway's and Miami Herald reporter Henry
Cavendish's movements on September 4, 1935, the day after the Labor Day
hurricane hit the Middle Florida Keys -- built from primary-source quotes
cataloged in HKJ's research spreadsheet.

This is the deployable slice of a larger research project. It does **not**
include the original master-list spreadsheet or the working copy derived
from it -- only the two derived tables the app actually reads
(`data/gazetteer_09-04-1935.csv`, `data/movements_09-04-1935.csv`), the
script that built them, and the methodology notes. The full project
(original CSV, this session's narrative) lives in the Hemingway Drive folder,
not in this repo.

## Layout

- `app.py` -- Streamlit app: map of both routes plus the underlying quotes.
- `data/gazetteer_09-04-1935.csv` -- every place on the two routes, with lat/lon and a confidence rating.
- `data/movements_09-04-1935.csv` -- ordered waypoints per person, each tied to a document ID and quote.
- `scripts/generate_09_04_data.py` -- regenerates the two tables above from hand-curated, source-cited waypoint lists. Edit this, not the CSVs.
- `notes/methodology_09-04-1935.md` -- sourcing, caveats (especially the synthetic-timestamp issue), and the resolved "near-miss" question.
- `HANDOFF.md` -- full narrative of how this data and app were built.

## Running locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Regenerating the derived data

```
python3 scripts/generate_09_04_data.py
```
