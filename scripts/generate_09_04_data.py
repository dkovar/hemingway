#!/usr/bin/env python3
"""
Build the 9/4/1935 movement + gazetteer tables for the Hemingway/Cavendish
map, from the master document list (working copy only -- original untouched).

Every waypoint below is hand-curated from working/document_master_list_working.csv
(Document IDs 1, 6 for Hemingway; 76 for Cavendish), cross-checked against public
secondary sources for place location (see notes/methodology_09-04-1935.md for
citations). Nothing here is invented: where the source data does not support a
precise time or a precise coordinate, that is marked explicitly rather than
guessed silently.

Coordinates for the Overseas Highway corridor (Lower Matecumbe through Snake
Creek) are not independently surveyed -- they are linearly interpolated along
US-1 mile markers between three confirmed reference points (Key West MM0,
No Name Key MM30, Tavernier MM91.5). See notes/methodology_09-04-1935.md.

TIME MODEL (added for the time-slider view)
---------------------------------------------
Most of the master sheet's "Event Date/Time" values are a synthetic ordering
key (incrementing seconds), not real clock times -- see the methodology notes.
Only a handful of stops on each route have an actual reported time of day. To
drive a continuous time slider anyway, every waypoint gets an `est_minutes`
value (minutes after midnight, local time, 9/4/1935) computed like this:

  - REPORTED waypoints keep the time stated in the source, verbatim.
  - SEQUENCE-ONLY waypoints that fall between two reported anchors for the
    same person are placed at even intervals between those two anchor times.
    This is a display convenience, not a claim about pacing -- it assumes
    constant speed between two known points in time, which is almost
    certainly wrong in detail (a boat crossing and a survivor interview do
    not take equally long) but is a defensible default absent better
    information.
  - SEQUENCE-ONLY waypoints with no later reported anchor for that person
    (Hemingway's last four 9/4 stops) are extrapolated forward at a fixed
    30-minute step from the last reported time. This is clearly the
    weakest part of the time model and is labeled "extrapolated" in the
    output, distinct from "interpolated".

Every row's `time_confidence` column says which of the three applies. The app
must not present interpolated/extrapolated times with the same confidence as
reported ones.
"""
import csv
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ---------------------------------------------------------------------------
# Reference points confirmed via web search against modern sources
# ---------------------------------------------------------------------------
KEY_WEST = (0.0, 24.5551, -81.7800)      # confirmed modern coordinate
NO_NAME_KEY = (30.0, 24.6926, -81.3260)  # confirmed modern coordinate (latitude.to)
TAVERNIER = (91.5, 25.0092, -80.5082)    # confirmed modern coordinate (latitude.to)

_mm0, _lat0, _lon0 = NO_NAME_KEY
_mm1, _lat1, _lon1 = TAVERNIER
LAT_PER_MI = (_lat1 - _lat0) / (_mm1 - _mm0)
LON_PER_MI = (_lon1 - _lon0) / (_mm1 - _mm0)


def interp_coord(mile_marker):
    lat = _lat0 + (mile_marker - _mm0) * LAT_PER_MI
    lon = _lon0 + (mile_marker - _mm0) * LON_PER_MI
    return round(lat, 4), round(lon, 4)


CONFIRMED_COORDS = {
    "Key West": (KEY_WEST[1], KEY_WEST[2]),
    "No Name Key": (NO_NAME_KEY[1], NO_NAME_KEY[2]),
    "Tavernier": (TAVERNIER[1], TAVERNIER[2]),
}

# ---------------------------------------------------------------------------
# Gazetteer: every place named on the two 9/4/1935 routes
# mile_marker source: Keys Weekly "Hurricane Disrupts Highway & Veteran Work
# Camps" (camps), Wikipedia Lower/Upper Matecumbe Key & Windley Key & Craig Key
# (island mile-marker ranges), Snake Creek Bridge Wikipedia page (MM86).
# ---------------------------------------------------------------------------
GAZETTEER = [
    # name, aliases, mile_marker, confidence, method, notes
    ("Key West", "Key West", 0.0, "confirmed", "known modern coordinate",
     "Hemingway's home port; departure point 9/4 per WMtV (Doc 6)."),
    ("No Name Key", "No Name Key", 30.0, "confirmed", "known modern coordinate",
     "KWC (Doc 9) reports a highway route Key West -> No Name Key 9/4; also the "
     "ambiguous overnight location in Hemingway's letter to Perkins (Doc 1)."),
    ("Craig Key", "Craig Key", 72.0, "approximate-interpolated", "mile-marker interpolation",
     "Not named directly in the 9/4 rows; included for the map's highway line only."),
    ("Lower Matecumbe (Ferry Slip / Camp 3 end)", "Lower Matecumbe, Ferry Slip, Camp 3",
     73.0, "approximate-historical",
     "mile-marker interpolation + secondary-source siting",
     "Ferry slip and Camp 3 both sited at the west/south end of Lower Matecumbe "
     "(Keys Weekly: 'Camp 3 was located at the west (south) end of the island, "
     "which aligns with the ferry landing area'). This is where Hemingway's "
     "boat lands and where he re-boards to reach Camp 5."),
    ("Lower Matecumbe (interior)", "Lower Matecumbe", 75.5, "approximate-interpolated",
     "mile-marker interpolation",
     "General midpoint of the key, used for Hemingway's on-foot passage past "
     "the railroad embankment and mangroves; exact spot not recoverable."),
    ("Camp 5", "Camp 5", 78.0, "approximate-historical",
     "mile-marker interpolation + secondary-source siting",
     "Sited at the east/north end of Lower Matecumbe per Keys Weekly. Hemingway: "
     "'We were the first in to camp five... Out of 187 only 8 survived' (Doc 1)."),
    ("The Fill", "The Fill", 79.0, "approximate-historical",
     "mile-marker interpolation + inference from both accounts",
     "The washed-out highway/bridge crossing between Lower and Upper Matecumbe. "
     "Hemingway reaches it walking north from Camp 5 (Doc 6: 'The Fill is as far "
     "north as the Hemingway part of this expedition gets'); Cavendish reaches "
     "it walking south down Upper Matecumbe and looks across the gap toward "
     "Camp 5 (Doc 76). Placed at MM79, the seam between the two islands."),
    ("Caribbee Colony", "Caribbee Colony", 80.0, "approximate-interpolated",
     "mile-marker interpolation",
     "Small settlement near the south end of Upper Matecumbe; swept clean per "
     "Cavendish (Doc 76)."),
    ("Upper Matecumbe (Matecumbe Hotel / King's Inn)", "Upper Matecumbe",
     81.5, "approximate-interpolated", "mile-marker interpolation",
     "Cavendish passes the ruined Matecumbe Hotel and O.W. King's Inn & "
     "Sandwich Shop here (Doc 76)."),
    ("Islamorada (post office / train wreck)", "Islamorada, Islamorada (PO; Train)",
     82.5, "approximate-interpolated", "mile-marker interpolation",
     "Site of the derailed FEC relief train and the ruined post office where "
     "Cavendish meets county solicitor Fred Pine (Doc 76)."),
    ("Whale Harbor", "Whale Harbor", 83.5, "approximate-interpolated",
     "mile-marker interpolation",
     "Crossing point between Upper Matecumbe and Windley Key; American Legion "
     "volunteers ran an outboard rowboat shuttle here (Doc 76)."),
    ("Windley Key (Camp 1)", "Windley Key, Camp 1", 85.0, "approximate-historical",
     "mile-marker interpolation + secondary-source siting",
     "Camp 1 sited 'just across Snake Creek from Plantation Key' per Keys "
     "Weekly, i.e. the Snake Creek end of Windley Key."),
    ("Snake Creek", "Snake Creek", 86.0, "approximate-interpolated",
     "mile-marker interpolation (Wikipedia: Snake Creek Bridge, MM86)",
     "Crossing between Plantation Key and Windley Key; Cavendish crosses here "
     "by small boat against strong current (Doc 76)."),
    ("Tavernier", "Tavernier", 91.5, "confirmed", "known modern coordinate",
     "Cavendish's starting point the morning of 9/4 (Doc 76)."),
]

# ---------------------------------------------------------------------------
# Ordered waypoints for the two 9/4/1935 routes.
# reported_minutes: minutes after midnight if the source states a real clock
#   time, else None (time gets interpolated/extrapolated -- see module docstring).
# time_type: "reported" (real time stated) or "sequence" (order known, time not).
# ---------------------------------------------------------------------------
HEMINGWAY_ROUTE = [
    dict(seq=1, location="Key West", time_type="reported", reported_minutes=7 * 60,
         time_label="7:00 AM (reported departure)", doc="6",
         action="Departs Key West by highway (to No Name Key) then boat.",
         quote="\"It was not until late the next day that a boat got through to Matecumbe Key from Key West.\""),
    dict(seq=2, location="Lower Matecumbe (Ferry Slip / Camp 3 end)", time_type="reported",
         reported_minutes=16 * 60, time_label="4:00 PM (reported arrival)", doc="6",
         action="Boat lands at the Lower Matecumbe ferry slip.",
         quote="\"When we reached Lower Matecumbe there were bodies floating in the ferry slip.\""),
    dict(seq=3, location="Lower Matecumbe (interior)", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="6",
         action="Walks the island on foot past the wrecked railroad embankment and mangroves.",
         quote="\"The biggest bunch of the dead were in the tangled... mangroves behind the tank cars and the water towers.\""),
    dict(seq=4, location="Lower Matecumbe (Ferry Slip / Camp 3 end)", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="6",
         action="Returns to the slip to get a boat north to Camp 5.",
         quote="\"...we have to go back [to the slip] and get in a boat before we can check up on Camp Five.\""),
    dict(seq=5, location="Camp 5", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="1 / 6",
         action="First rescue party into Camp 5; finds 8 survivors of 187.",
         quote="\"We were the first in to camp five of the veterans who were working on the Highway construction. Out of 187 only 8 survived.\""),
    dict(seq=6, location="The Fill", time_type="sequence", reported_minutes=None,
         time_label="narrative order only -- Hemingway's furthest point north on 9/4", doc="6",
         action="Walks from Camp 5 to the Fill; finds 69 bodies total between the camp and the fill.",
         quote="\"...we only find sixty-seven of those plus two more along the fill makes sixty-nine... The Fill is as far north as the Hemingway part of this expedition gets.\""),
]

CAVENDISH_ROUTE = [
    dict(seq=1, location="Tavernier", time_type="reported", reported_minutes=6 * 60 + 10,
         time_label="~6:00-6:20 AM (reported)", doc="76",
         action="Gathers survivor accounts at Tavernier; watches a Coast Guard amphibian pass south.",
         quote="\"Reporter notes comms established only as far south as Camp 1; nothing then known about Camp 3 and Camp 5.\""),
    dict(seq=2, location="Snake Creek", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Crosses Snake Creek by small boat against a strong current.",
         quote="\"Snake Creek currents still very strong -- 'swirling like a millrace.'\""),
    dict(seq=3, location="Windley Key (Camp 1)", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Arrives Camp 1; walks the broken highway; interviews the FEC train crew and Russell family survivors.",
         quote="\"[Camp 1] leveled to the ground and bodies littered the jumbled masses of wreckage round about.\""),
    dict(seq=4, location="Whale Harbor", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Crosses Whale Harbor by rowboat with outboard, run by American Legion volunteers.",
         quote="\"...it was necessary to make a wide arc in order to avoid the treacherous current. As a result it was only possible to make a round trip about once every hour.\""),
    dict(seq=5, location="Islamorada (post office / train wreck)", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Reaches the derailed FEC relief train and ruined post office; meets county solicitor Fred Pine.",
         quote="\"...came upon Fred Pine, county solicitor, standing in the remains of the post office, near where the missing rescue train lay on its side.\""),
    dict(seq=6, location="Upper Matecumbe (Matecumbe Hotel / King's Inn)", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Passes the ruined Matecumbe Hotel and O.W. King's Inn & Sandwich Shop.",
         quote="\"[Matecumbe Hotel] in ruins, with the roof blown away and the second story of the building in complete wreckage.\""),
    dict(seq=7, location="Caribbee Colony", time_type="sequence", reported_minutes=None,
         time_label="narrative order only", doc="76",
         action="Passes the site of Caribbee Colony, swept clean.",
         quote="\"...swept away as though a mowing machine had passed over it... The body of George Henderson... was flattened against a telegraph pole.\""),
    dict(seq=8, location="The Fill", time_type="reported", reported_minutes=15 * 60,
         time_label="~3:00 PM (reported)", doc="76",
         action="Reaches the end of the road at the Fill; looks across the gap toward Lower Matecumbe and Camp 5.",
         quote="\"...reaches 'the end of the road' at about 3 p.m. and looks across 2 miles of water toward Lower Matecumbe. The Overseas highway bridge between Upper Matecumbe key and Lower Matecumbe key is gone.\""),
    dict(seq=9, location="Snake Creek", time_type="reported", reported_minutes=16 * 60,
         time_label="~4:00 PM (reported, tied to body count)", doc="76",
         action="National Guard orders all persons off Upper Matecumbe; returns toward Snake Creek as body recovery continues.",
         quote="\"...25 removed by 4 p.m. 30 additional waiting @ Snake Creek.\""),
]

EXTRAPOLATION_STEP_MIN = 30  # used only when a trailing run has no later reported anchor


def assign_times(route):
    """Fill in est_minutes + time_confidence for every waypoint in a route,
    honoring reported times and interpolating/extrapolating the rest."""
    route = [dict(r) for r in route]  # copy
    n = len(route)

    # reported anchors, by index
    anchors = [i for i, r in enumerate(route) if r["reported_minutes"] is not None]
    for i in anchors:
        route[i]["est_minutes"] = route[i]["reported_minutes"]
        route[i]["time_confidence"] = "reported"

    # interpolate between consecutive anchors
    for a, b in zip(anchors, anchors[1:]):
        t0, t1 = route[a]["est_minutes"], route[b]["est_minutes"]
        gap = b - a
        for k, i in enumerate(range(a + 1, b), start=1):
            route[i]["est_minutes"] = t0 + (t1 - t0) * k / gap
            route[i]["time_confidence"] = "interpolated"

    # extrapolate forward past the last anchor (fixed step)
    if anchors:
        last_anchor = anchors[-1]
        t = route[last_anchor]["est_minutes"]
        for i in range(last_anchor + 1, n):
            t += EXTRAPOLATION_STEP_MIN
            route[i]["est_minutes"] = t
            route[i]["time_confidence"] = "extrapolated"
        # extrapolate backward before the first anchor, if any (not needed for
        # these two routes -- both start on a reported anchor -- but handled
        # for completeness/future days)
        first_anchor = anchors[0]
        t = route[first_anchor]["est_minutes"]
        for i in range(first_anchor - 1, -1, -1):
            t -= EXTRAPOLATION_STEP_MIN
            route[i]["est_minutes"] = t
            route[i]["time_confidence"] = "extrapolated"
    else:
        # no reported anchors at all in this route: fall back to a bare
        # sequence index so the slider still has something to work with
        for i, r in enumerate(route):
            r["est_minutes"] = i * EXTRAPOLATION_STEP_MIN
            r["time_confidence"] = "no anchor -- sequence index only"

    return route


def minutes_to_clock(m):
    m = round(m) % (24 * 60)
    h, mm = divmod(m, 60)
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{mm:02d} {suffix}"


def write_gazetteer():
    path = os.path.join(OUT_DIR, "gazetteer_09-04-1935.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["canonical_name", "aliases", "mile_marker", "lat", "lon",
                    "confidence", "method", "notes"])
        for name, aliases, mm, conf, method, notes in GAZETTEER:
            if name in CONFIRMED_COORDS:
                lat, lon = CONFIRMED_COORDS[name]
            else:
                lat, lon = interp_coord(mm)
            w.writerow([name, aliases, mm, lat, lon, conf, method, notes])
    print("wrote", path)


def write_movements():
    path = os.path.join(OUT_DIR, "movements_09-04-1935.csv")
    hem = assign_times(HEMINGWAY_ROUTE)
    cav = assign_times(CAVENDISH_ROUTE)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["person", "seq", "location_canonical", "time_type", "time_label",
                    "document_id", "action", "quote", "est_minutes", "est_time_display",
                    "time_confidence"])
        for person, route in (("Hemingway", hem), ("Cavendish", cav)):
            for r in route:
                w.writerow([person, r["seq"], r["location"], r["time_type"], r["time_label"],
                            r["doc"], r["action"], r["quote"], round(r["est_minutes"], 1),
                            minutes_to_clock(r["est_minutes"]), r["time_confidence"]])
    print("wrote", path)


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    write_gazetteer()
    write_movements()
