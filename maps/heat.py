# -*- coding: utf-8 -*-
"""أنماط الجزر الحرارية بالإسكندرية فى الفترة (2000-2020) — data in data/heat/"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import common as c

APP = "heat"
FILE = "Alexandria_heat_islands.geojson"
TITLE = "أنماط الجزر الحرارية بالإسكندرية فى الفترة (2000-2020)"
NAME_COL = "اسم المنطقة"
PATTERN_COL = "نمط الجزيرة الحرارية"
VALUE_COL = "متوسط درجة الحرارة السنوية"
SEASON_COLS = {
    "متوسط درجة الحرارة - الربيع": "الربيع",
    "متوسط درجة الحرارة - الصيف": "الصيف",
    "متوسط درجة الحرارة - الخريف": "الخريف",
    "متوسط درجة الحرارة - الشتاء": "الشتاء",
}
POPUP_COLS = [PATTERN_COL] + list(SEASON_COLS) + [VALUE_COL]
# legend classes from the original map, lowest first: (lower, upper, colour, label)
CLASSES = [(21.35, 23.09, "#ECBE40", "23.09° - 21.35"),
           (23.09, 23.19, "#F79533", "23.19° - 23.09"),
           (23.19, 23.20, "#C34B05", "23.2° - 23.19")]


def value_class(v):
    for i, (_lo, hi, _c, _l) in enumerate(CLASSES):
        if v <= hi:
            return i
    return len(CLASSES) - 1


@st.cache_data(show_spinner=False)
def load():
    gdf = c.read_geo(c.data_path(APP, FILE), simplify=0.0002)
    for col in list(SEASON_COLS) + [VALUE_COL]:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce")
    gdf["class"] = gdf[VALUE_COL].apply(value_class)
    gdf["id"] = gdf.index.astype(str)
    return gdf


@st.cache_resource(show_spinner=False)
def build_map():
    gdf = load()
    geo = c.to_geojson(gdf, ["id"])
    n = len(CLASSES)
    scale = []
    for i, (_lo, _hi, color, _l) in enumerate(CLASSES):
        scale += [[i / n, color], [(i + 1) / n, color]]
    hover = f"<b>%{{text}}</b><br>{PATTERN_COL}: %{{customdata[0]}}<br>"
    for i, col in enumerate(SEASON_COLS, start=1):
        hover += f"{SEASON_COLS[col]}: %{{customdata[{i}]:.2f}}°<br>"
    hover += f"<b>{VALUE_COL}: %{{customdata[{len(POPUP_COLS) - 1}]:.2f}}°</b><br>"
    hover += "<i>انقر لعرض التفاصيل</i><extra></extra>"
    outline = go.Choroplethmap(
        geojson=geo, featureidkey="properties.id", locations=gdf["id"], z=[0] * len(gdf),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
        marker_line_width=1.5, marker_line_color="white", hoverinfo="skip")
    fill = go.Choroplethmap(
        geojson=geo, featureidkey="properties.id", locations=gdf["id"], z=gdf["class"] + 0.5,
        zmin=0, zmax=n, colorscale=scale, marker_opacity=c.FILL_OPACITY, marker_line_width=0,
        selected=dict(marker=dict(opacity=1.0)), unselected=dict(marker=dict(opacity=c.FILL_OPACITY)),
        text=gdf[NAME_COL], customdata=gdf[POPUP_COLS].to_numpy(), hovertemplate=hover,
        colorbar=c.plotly_colorbar("<b>متوسط درجة الحرارة<br>السنوية</b>",
                                   tickvals=[i + 0.5 for i in range(n)], ticktext=[x[3] for x in CLASSES]))
    return c.plotly_map_layout(go.Figure([outline, fill]), gdf.total_bounds)


@st.dialog("تفاصيل المنطقة", width="large")
def show_popup(row):
    color = CLASSES[int(row["class"])][2]
    st.markdown(f"<h3 style='color:{c.NAVY};margin-top:0'>{row[NAME_COL]}</h3>"
                f"<p style='margin-top:-0.6rem'><span style='background:{color};color:white;"
                f"padding:2px 10px;border-radius:10px;font-weight:600'>جزيرة حرارية {row[PATTERN_COL]}</span></p>",
                unsafe_allow_html=True)
    rows = "".join(
        f'<tr{" class=highlight-row" if col == VALUE_COL else ""}>'
        f'<td>{col if col == PATTERN_COL else col + " (°م)"}</td>'
        f'<td>{row[col] if col == PATTERN_COL else f"{row[col]:.2f}°"}</td></tr>' for col in POPUP_COLS)
    st.markdown(f'<table class="info-table">{rows}</table>', unsafe_allow_html=True)


# ---------------------------------------------------------------- page
c.require_files(APP, [FILE])
gdf = load()
c.page_title(TITLE, "🌡️")

k = st.columns(4)
hot, cool = gdf.loc[gdf[VALUE_COL].idxmax()], gdf.loc[gdf[VALUE_COL].idxmin()]
k[0].metric("عدد المناطق", f"{len(gdf)}")
k[1].metric("أعلى متوسط سنوي (°م)", f"{hot[VALUE_COL]:.2f}", hot[NAME_COL], delta_color="off")
k[2].metric("أدنى متوسط سنوي (°م)", f"{cool[VALUE_COL]:.2f}", cool[NAME_COL], delta_color="off")
k[3].metric("الفرق بين الأعلى والأدنى (°م)", f"{hot[VALUE_COL] - cool[VALUE_COL]:.2f}")
c.metric_cards()

event = st.plotly_chart(build_map(), key="heat_map", on_select="rerun", selection_mode="points",
                        config={"scrollZoom": True, "displaylogo": False}, use_container_width=True)
clicked = None
if event and event.selection and event.selection.points:
    pts = [p for p in event.selection.points if p.get("curve_number", 1) == 1]
    if pts:
        loc = pts[0].get("location")
        if loc is None and pts[0].get("point_index") is not None:
            loc = gdf["id"].iloc[pts[0]["point_index"]]
        clicked = str(loc) if loc is not None else None
if clicked is not None and clicked != st.session_state.get("heat_last"):
    st.session_state["heat_last"] = clicked
    show_popup(gdf[gdf["id"] == clicked].iloc[0])
if clicked is None:
    st.session_state["heat_last"] = None
st.caption("انقر على أي منطقة في الخريطة لعرض تفاصيلها.")

with st.expander("متوسط درجة الحرارة حسب الفصل"):
    seasons = list(SEASON_COLS)
    fig = go.Figure()
    for _, row in gdf.sort_values(VALUE_COL).iterrows():
        fig.add_trace(go.Bar(
            name=row[NAME_COL], x=[SEASON_COLS[s] for s in seasons], y=[row[s] for s in seasons],
            marker_color=CLASSES[int(row["class"])][2], marker_line_color=c.NAVY, marker_line_width=0.5,
            text=[f"{row[s]:.1f}°" for s in seasons], textposition="outside",
            hovertemplate=f"<b>{row[NAME_COL]}</b><br>%{{x}}: %{{y:.2f}}°<extra></extra>"))
    c.bar_layout(fig, 380, barmode="group", yaxis_title="°م", xaxis=dict(autorange="reversed"),
                 legend=dict(orientation="h", y=1.08, x=1, xanchor="right"))
    c.show_chart(fig)

with st.expander("جدول البيانات الكامل"):
    st.dataframe(gdf[[NAME_COL] + POPUP_COLS].sort_values(VALUE_COL, ascending=False),
                 hide_index=True, use_container_width=True)
