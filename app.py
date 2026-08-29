import math
import os

import pandas as pd
import pydeck as pdk
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")

st.set_page_config(page_title="9/4/1935: Hemingway and Cavendish on the Keys", layout="wide")

COLORS = {
    "Hemingway": [200, 60, 40],   # brick red, moving north from Key West
    "Cavendish": [40, 90, 170],   # blue, moving south from Tavernier
}

CONF_LABEL = {
    "reported": "reported time",
    "interpolated": "estimated -- interpolated between two reported times",
    "extrapolated": "estimated -- extrapolated, weakest confidence",
}


def minutes_to_clock(m):
    m = round(m) % (24 * 60)
    h, mm = divmod(m, 60)
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{mm:02d} {suffix}"


@st.cache_data
def load_data():
    gaz = pd.read_csv(os.path.join(DATA_DIR, "gazetteer_09-04-1935.csv"))
    mov = pd.read_csv(os.path.join(DATA_DIR, "movements_09-04-1935.csv"))
    mov = mov.merge(
        gaz[["canonical_name", "lat", "lon", "mile_marker", "confidence"]],
        left_on="location_canonical", right_on="canonical_name", how="left",
    )
    return gaz, mov


gaz, mov = load_data()

missing = mov[mov["lat"].isna()]
if len(missing):
    st.error(
        "These waypoints have no matching gazetteer entry and will not plot: "
        + ", ".join(missing["location_canonical"].unique())
    )

st.title("September 4, 1935: two reporters walk into the storm")
st.caption(
    "Ernest Hemingway (Key West Citizen letters and \"Who Murdered the Vets?\") and "
    "Miami Herald reporter Henry Cavendish, moving toward each other across the "
    "wrecked Florida Keys the day after the Labor Day hurricane."
)

with st.expander("How to read this map and slider -- please read before drawing conclusions", expanded=False):
    st.markdown(
        "- **Most clock times here are estimates, not reported facts.** Only a few "
        "stops on each route have an actual time of day stated in the source "
        "(marked **reported** below). The rest are placed on the clock by "
        "interpolating evenly between the reported times on either side "
        "(**interpolated**), or, for Hemingway's last four stops, extrapolated "
        "forward in fixed 30-minute steps because no later reported time exists "
        "for that leg (**extrapolated** -- the least certain). The slider and the "
        "moving dots use these estimates; the text panel always tells you which "
        "kind of time you're looking at.\n"
        "- **The dot moves at constant speed between two known points.** That is a "
        "display convenience, not a claim that Hemingway or Cavendish moved at an "
        "even pace -- a boat crossing and a survivor interview don't take the same "
        "amount of time. Treat the moving dot as an approximation of *where they "
        "generally were*, not a GPS track.\n"
        "- **Coordinates for the Keys corridor are interpolated**, not surveyed -- "
        "several 1935 sites (the veteran work camps, the Ferry Slip, the Fill, "
        "Caribbee Colony) no longer exist. See the Data quality tab for the "
        "confidence rating behind every dot.\n"
        "- Both routes converge at **The Fill**, the washed-out highway crossing "
        "between Lower and Upper Matecumbe -- Hemingway reaching it from the "
        "south, Cavendish from the north, on the same afternoon (but not at the "
        "same time -- see the note below the slider).\n"
        "- Use **Prev event / Next event** to jump straight to the previous or next "
        "reported/estimated stop for whichever person(s) you have selected above, "
        "instead of dragging by hand."
    )

people = st.multiselect("Show route for", ["Hemingway", "Cavendish"], default=["Hemingway", "Cavendish"])

# ---------------------------------------------------------------------------
# Time slider
# ---------------------------------------------------------------------------
t_min = float(mov["est_minutes"].min() // 10 * 10)
t_max = float(-(-mov["est_minutes"].max() // 10) * 10)  # round up to next 10

if "slider_minutes" not in st.session_state:
    st.session_state.slider_minutes = t_min


def _event_times():
    """Sorted, de-duplicated waypoint times for whichever people are shown."""
    sub = mov[mov["person"].isin(people)] if people else mov
    return sorted(sub["est_minutes"].unique().tolist())


def _event_label(t):
    """Who/what happens at waypoint time t, for button tooltips and captions."""
    hits = mov[mov["est_minutes"] == t]
    if hits.empty:
        return minutes_to_clock(t)
    bits = [f"{r['person']} at {r['location_canonical']}" for _, r in hits.iterrows()]
    return f"{minutes_to_clock(t)} -- " + "; ".join(bits)


def _jump(direction):
    times = _event_times()
    cur = st.session_state.slider_minutes
    if direction == "next":
        later = [t for t in times if t > cur]
        if later:
            st.session_state.slider_minutes = float(later[0])
    else:
        earlier = [t for t in times if t < cur]
        if earlier:
            st.session_state.slider_minutes = float(earlier[-1])


_times = _event_times()
_cur = st.session_state.slider_minutes
_earlier = [t for t in _times if t < _cur]
_later = [t for t in _times if t > _cur]

col_prev, col_slider, col_next = st.columns([1.1, 5, 1.1])
with col_prev:
    st.button(
        "\u25c0 Prev event", use_container_width=True, disabled=not _earlier,
        on_click=_jump, args=("prev",),
        help=_event_label(_earlier[-1]) if _earlier else "No earlier event",
    )
with col_next:
    st.button(
        "Next event \u25b6", use_container_width=True, disabled=not _later,
        on_click=_jump, args=("next",),
        help=_event_label(_later[0]) if _later else "No later event",
    )
with col_slider:
    st.slider(
        "Time of day, September 4, 1935 (minutes shown; clock time rendered below)",
        min_value=t_min, max_value=t_max, step=5.0,
        key="slider_minutes",
    )

slider_minutes = st.session_state.slider_minutes
st.markdown(f"### {minutes_to_clock(slider_minutes)}")
if _later:
    st.caption(f"Next: {_event_label(_later[0])}")


def person_state(df_person, t):
    """Where a person is, and what they're doing, at slider time t."""
    df_person = df_person.sort_values("seq").reset_index(drop=True)
    before = df_person[df_person["est_minutes"] <= t]
    after = df_person[df_person["est_minutes"] > t]

    if len(before) == 0:
        cur = df_person.iloc[0]
        nxt = df_person.iloc[1] if len(df_person) > 1 else None
        frac, status = 0.0, "not yet departed"
    else:
        cur = before.iloc[-1]
        if len(after):
            nxt = after.iloc[0]
            span = nxt["est_minutes"] - cur["est_minutes"]
            frac = 0.0 if span <= 0 else min(1.0, (t - cur["est_minutes"]) / span)
            status = "en route" if frac > 1e-6 else "at this stop"
        else:
            nxt = None
            frac, status = 0.0, "final 9/4 stop reached"

    if nxt is not None and frac > 0:
        lat = cur["lat"] + (nxt["lat"] - cur["lat"]) * frac
        lon = cur["lon"] + (nxt["lon"] - cur["lon"]) * frac
    else:
        lat, lon = cur["lat"], cur["lon"]

    traveled = df_person[df_person["est_minutes"] <= cur["est_minutes"]]
    return dict(cur=cur, nxt=nxt, frac=frac, lat=lat, lon=lon, status=status, traveled=traveled)


states = {}
for person in people:
    sub = mov[mov["person"] == person]
    if len(sub):
        states[person] = person_state(sub, slider_minutes)

col_map, col_text = st.columns([2, 1])

with col_map:
    layers = []
    for person, st_ in states.items():
        color = COLORS.get(person, [120, 120, 120])
        traveled = st_["traveled"]
        if len(traveled) >= 2:
            layers.append(pdk.Layer(
                "PathLayer",
                data=[{"path": traveled[["lon", "lat"]].values.tolist(), "color": color}],
                get_path="path", get_color="color",
                width_min_pixels=3, get_width=4,
            ))
        # faint full route for context
        full = mov[mov["person"] == person].sort_values("seq")
        layers.append(pdk.Layer(
            "PathLayer",
            data=[{"path": full[["lon", "lat"]].values.tolist(), "color": color + [60]}],
            get_path="path", get_color="color",
            width_min_pixels=1, get_width=1,
        ))
        # stop markers (small)
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=full.assign(r=60),
            get_position="[lon, lat]", get_fill_color=color + [140],
            get_radius="r", pickable=False,
        ))
        # current position (large, outlined)
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=[{"lat": st_["lat"], "lon": st_["lon"], "color": color,
                   "person": person, "status": st_["status"],
                   "location": st_["cur"]["location_canonical"]}],
            get_position="[lon, lat]", get_fill_color="color",
            get_radius=260, pickable=True, stroked=True,
            get_line_color=[255, 255, 255], line_width_min_pixels=2,
        ))

    if layers:
        # Fit the camera to whoever is currently on screen: each selected
        # person's current position plus their very next stop. Fixes two
        # problems with the old fixed mean-centered zoom=10.2 view: (a) Key
        # West, at the far southwest end of the whole corridor, was getting
        # cut out of frame whenever it was the current or a recent position,
        # so it looked like the event "didn't show up on the map"; and (b)
        # the destination of the next "Next event" click wasn't visible yet,
        # so arriving there looked like an unexplained jump. Falls back to
        # the full route extent if nothing is selected.
        relevant_lats, relevant_lons = [], []
        for _person, _st in states.items():
            relevant_lats.append(float(_st["lat"]))
            relevant_lons.append(float(_st["lon"]))
            if _st["nxt"] is not None:
                relevant_lats.append(float(_st["nxt"]["lat"]))
                relevant_lons.append(float(_st["nxt"]["lon"]))
        if not relevant_lats:
            relevant_lats = mov["lat"].tolist()
            relevant_lons = mov["lon"].tolist()

        lat_min, lat_max = min(relevant_lats), max(relevant_lats)
        lon_min, lon_max = min(relevant_lons), max(relevant_lons)
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        lat_span = max(lat_max - lat_min, 0.01)
        lon_span = max((lon_max - lon_min) * math.cos(math.radians(center_lat)), 0.01)
        # 2.2x padding (generous, to allow for the viewport not being a
        # perfect square and for imprecision in this rough zoom-to-degree
        # estimate) so points aren't jammed against, or clipped past, the
        # edge of the view. The 0.22 reference span is calibrated to roughly
        # match the old fixed zoom=10.2 for the tight Middle Keys cluster.
        span = max(lat_span, lon_span) * 2.2
        zoom = 10.2 - math.log2(span / 0.22)
        zoom = max(7.0, min(zoom, 11.5))

        view_state = pdk.ViewState(
            latitude=center_lat, longitude=center_lon,
            zoom=zoom, pitch=0,
        )
        tooltip = {"html": "<b>{person}</b><br/>{location}<br/>{status}",
                   "style": {"backgroundColor": "white", "color": "black"}}
        # key forces Streamlit to remount the map (not just pass new props to
        # the existing one) whenever the camera target changes. pydeck/deck.gl
        # only actually applies initial_view_state when a chart is (re)mounted
        # -- without a changing key, an already-mounted chart keeps whatever
        # camera position it last had client-side and ignores updates to
        # initial_view_state, which is what made the camera stop tracking
        # Prev/Next clicks (it would hold the very first position, or
        # whatever a user last panned/zoomed to, regardless of what the
        # Python code computed afterward).
        map_key = f"route_map_{round(center_lat, 4)}_{round(center_lon, 4)}_{round(zoom, 2)}"
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state,
                                  tooltip=tooltip, map_style=None), key=map_key)
    else:
        st.info("Select at least one person to plot.")

with col_text:
    st.subheader("Right now")
    for person in people:
        if person not in states:
            continue
        st_ = states[person]
        cur = st_["cur"]
        conf_note = CONF_LABEL.get(cur["time_confidence"], cur["time_confidence"])
        st.markdown(f"**{person}** -- {st_['status']}")
        if st_["status"] == "not yet departed":
            st.markdown(
                f"Hasn't started yet -- begins at **{cur['location_canonical']}** "
                f"({cur['est_time_display']}, {conf_note})"
            )
        else:
            st.markdown(
                f"At **{cur['location_canonical']}** (reached ~{cur['est_time_display']}, {conf_note})"
            )
        st.markdown(f"> {cur['action']}")
        st.markdown(f"> {cur['quote']}")
        if st_["nxt"] is not None and st_["frac"] > 0:
            st.caption(f"Heading toward {st_['nxt']['location_canonical']} "
                       f"(~{st_['nxt']['est_time_display']}, {CONF_LABEL.get(st_['nxt']['time_confidence'], '')})")
        st.markdown("---")

st.info(
    "**Hemingway was not there yet.** At 3:00 PM, when Cavendish reached the "
    "Fill from the north and looked across at where Camp 5 had stood, "
    "Hemingway's party had not yet arrived -- the time model above puts "
    "Hemingway at the Fill no earlier than roughly 6:00 PM (extrapolated, not "
    "reported). The two accounts describe the same washed-out crossing from "
    "opposite sides hours apart, not a missed sighting of each other. See "
    "`notes/methodology_09-04-1935.md` for the full reasoning and the caveat "
    "that Hemingway's exact arrival time is still an estimate, not a fact."
)

st.divider()
with st.expander("Full itinerary (reference)"):
    for person in people:
        sub = mov[mov["person"] == person].sort_values("seq")
        st.markdown(f"**{person}**")
        for _, row in sub.iterrows():
            st.markdown(
                f"{int(row['seq'])}. **{row['location_canonical']}** -- "
                f"~{row['est_time_display']} ({row['time_confidence']}; source label: \"{row['time_label']}\")\n\n"
                f"> {row['action']}\n\n"
                f"> {row['quote']}"
            )

st.divider()
tab1, tab2 = st.tabs(["Data quality", "About this data"])

with tab1:
    st.markdown("Confidence rating behind every plotted location:")
    st.dataframe(
        gaz[["canonical_name", "mile_marker", "confidence", "method", "notes"]],
        use_container_width=True, hide_index=True,
    )

with tab2:
    st.markdown(
        "Source: `Sandbox Seven Thousand Hells - Document Master List.csv` "
        "(original, untouched). This app reads only a working copy "
        "(`working/document_master_list_working.csv`) and two derived tables "
        "(`data/gazetteer_09-04-1935.csv`, `data/movements_09-04-1935.csv`) built by "
        "`scripts/generate_09_04_data.py`. Regenerate the derived tables at any time "
        "by re-running that script; it does not touch the original or working CSV."
    )
    st.markdown("Raw movement table:")
    st.dataframe(mov.drop(columns=["canonical_name"]), use_container_width=True, hide_index=True)
