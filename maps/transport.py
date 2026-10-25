# -*- coding: utf-8 -*-
"""خطوط المواصلات الرسمية فى الإسكندرية 2023 — data in data/transport/ (icons in data/transport/icons/)"""
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import common as c

APP = "transport"
TITLE = "خطوط المواصلات الرسمية فى الإسكندرية 2023"
FILES = {
    "bus": "Alex_bus_lines.geojson",
    "micro": "Alex_microbus_lines.geojson",
    "rail": "Alex_rail_lines.geojson",
    "stations": "Alex_rail_stations.geojson",
    "endpoints": "Alex_start_end_stops.geojson",
    "main": "Alex_main_stops.geojson",
}
ICONS = {"main": "icons/main_stop.svg", "tram": "icons/tram_station.svg", "train": "icons/train_station.svg"}
# colours from the original web map legend
BUS_COLOR = "#F2571E"
MICRO_COLOR = "#2E6D60"
TRAM_COLOR = "#3684D2"
TRAIN_COLOR = "#4F1101"
ENDPOINT_COLOR = "#72A8DF"
ICON_COLOR = "#333333"
CASING = {MICRO_COLOR: "#A2BEB8", TRAIN_COLOR: "#D9C2BC"}   # light casing under dark lines
BUS_FIELDS = ["رقم الخط", "مسار الطالع", "مسار النازل", "المسافة (كم)", "التسعير (ج.م)", "إدارة الخط"]
MICRO_FIELDS = ["نوع الخط", "المسافة (كم)", "التسعير (ج.م)"]
RAIL_FIELDS = ["نوع الخط", "رقم الخط", "المسافة (كم)", "التسعير (ج.م)", "عدد المحطات بالخط"]
STATION_FIELDS = ["نوع الخطوط بالمحطة", "وصف الخطوط بالمحطة"]
ENDPOINT_FIELDS = ["الجهة الإدارية", "عدد الخطوط بالموقف", "الخطوط المارة بالموقف"]
MAIN_FIELDS = ["عدد خطوط الأتوبيسات", "عدد خطوط الميكروباصات", "عدد خطوط القطار",
               "عدد خطوط الترام", "إجمالي عدد الخطوط", "الحي"]
LINE_SIMPLIFY = 0.00004          # ~4 m
CENTRAL_BOUNDS = (29.83, 31.13, 30.08, 31.33)   # start on central Alexandria


def _popups(gdf, title_col, badge, color, fields, badge_text=None):
    return [c.popup_html(r[title_col], badge(r) if callable(badge) else badge,
                         color(r) if callable(color) else color,
                         [(f, c.fmt(r.get(f))) for f in fields],
                         badge_text=badge_text or c.text_on(color(r) if callable(color) else color))
            for _, r in gdf.iterrows()]


@st.cache_data(show_spinner=False)
def load():
    data = {}
    for key, file in FILES.items():
        simplify = LINE_SIMPLIFY if key in ("bus", "micro", "rail") else None
        data[key] = c.read_geo(c.data_path(APP, file), simplify=simplify)

    bus, micro, rail = data["bus"], data["micro"], data["rail"]
    bus["mode"], bus["color"] = "أتوبيس", BUS_COLOR
    bus["popup"] = _popups(bus, "اسم الخط", "خط أتوبيس", BUS_COLOR, BUS_FIELDS)
    micro["mode"], micro["color"] = "ميكروباص", MICRO_COLOR
    micro["popup"] = _popups(micro, "اسم الخط", "خط ميكروباص", MICRO_COLOR, MICRO_FIELDS)
    rail["mode"] = rail["نوع الخط"]
    rail["color"] = rail["نوع الخط"].map({"ترام": TRAM_COLOR, "قطار": TRAIN_COLOR}).fillna(TRAM_COLOR)
    rail["popup"] = _popups(rail, "اسم الخط", lambda r: f"خط {r['نوع الخط']}", lambda r: r["color"], RAIL_FIELDS)
    for g in (bus, micro, rail):
        g["tip"] = [c.tip_html(r["اسم الخط"], f"{r['mode']} — {c.fmt(r['المسافة (كم)'])} كم")
                    for _, r in g.iterrows()]

    s = data["stations"]
    s["popup"] = _popups(s, "اسم المحطة", lambda r: f"محطة {r['نوع الخطوط بالمحطة']}",
                         lambda r: TRAM_COLOR if r["نوع الخطوط بالمحطة"] == "ترام" else TRAIN_COLOR,
                         STATION_FIELDS)
    s["tip"] = [c.tip_html(r["اسم المحطة"], f"محطة {r['نوع الخطوط بالمحطة']}") for _, r in s.iterrows()]
    e = data["endpoints"]
    e["popup"] = _popups(e, "اسم الموقف", "محطة بداية ونهاية", ENDPOINT_COLOR, ENDPOINT_FIELDS)
    e["tip"] = [c.tip_html(r["اسم الموقف"], "محطة بداية ونهاية لخطوط السير") for _, r in e.iterrows()]
    mn = data["main"]
    mn["popup"] = _popups(mn, "اسم الموقف", "موقف رئيسي", c.NAVY, MAIN_FIELDS)
    mn["tip"] = [c.tip_html(r["اسم الموقف"], f"موقف رئيسي — {r['إجمالي عدد الخطوط']} خط")
                 for _, r in mn.iterrows()]
    return data


@st.cache_data(show_spinner=False)
def load_routes():
    data = load()
    return pd.concat([data["bus"], data["micro"], data["rail"]], ignore_index=True)


@st.cache_data(show_spinner=False)
def route_labels():
    labels = []
    for _, r in load_routes().iterrows():
        label = f"{r['mode']}: {r['اسم الخط']}"
        if isinstance(r.get("رقم الخط"), str) and r["mode"] == "أتوبيس":
            label += f" (خط {r['رقم الخط']})"
        labels.append(label)
    return c.unique_labels(labels)


def add_lines(parent, gdf, weight):
    """One GeoJson per mode, with a light casing under dark colours."""
    if gdf.empty:
        return
    geo = c.to_geojson(gdf, ["color", "popup", "tip"])
    for color, casing in CASING.items():
        sub = [f for f in geo["features"] if f["properties"]["color"] == color]
        if sub:
            folium.GeoJson({"type": "FeatureCollection", "features": sub},
                           style_function=lambda _f, cs=casing: {"color": cs, "weight": weight + 2.5,
                                                                 "opacity": 0.85}).add_to(parent)
    c.add_geojson(parent, geo, lambda f: {"color": f["properties"]["color"], "weight": weight, "opacity": 0.95},
                  weight_hover=weight + 3)


def icon_markers(parent, gdf, uri, ring, size):
    html = (f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#FFFFFF;'
            f'border:2px solid {ring};box-shadow:0 0 3px rgba(0,0,0,0.7);display:flex;'
            f'align-items:center;justify-content:center">'
            f'<img src="{uri}" style="width:{size - 8}px;height:{size - 8}px"></div>')
    for _, r in gdf.iterrows():
        folium.Marker([r.geometry.y, r.geometry.x],
                      icon=folium.DivIcon(html=html, icon_size=(size, size), icon_anchor=(size // 2, size // 2)),
                      tooltip=folium.Tooltip(r["tip"]),
                      popup=folium.Popup(r["popup"], max_width=c.PHOTO_WIDTH + 40)).add_to(parent)


@st.cache_resource(max_entries=c.MAP_CACHE_ENTRIES, show_spinner=False)
def build_map(highlight_idx, full_extent):
    data = load()
    m = c.new_map()
    rail = data["rail"]
    tram_lines, train_lines = rail[rail["نوع الخط"] == "ترام"], rail[rail["نوع الخط"] == "قطار"]
    # bottom layer first (the legend shows them reversed: main stops at the top)
    add_lines(c.group(m, c.lg_label("خطوط الأتوبيسات", c.lg_line(BUS_COLOR), len(data["bus"]))), data["bus"], 2.5)
    add_lines(c.group(m, c.lg_label("خطوط الميكروباصات", c.lg_line(MICRO_COLOR), len(data["micro"]))),
              data["micro"], 2.5)
    add_lines(c.group(m, c.lg_label("خطوط السكك الحديدية: قطار", c.lg_line(TRAIN_COLOR), len(train_lines))),
              train_lines, 3.5)
    add_lines(c.group(m, c.lg_label("خطوط السكك الحديدية: ترام", c.lg_line(TRAM_COLOR), len(tram_lines))),
              tram_lines, 3.5)

    stations = data["stations"]
    for kind, icon_key, ring in [("قطار", "train", TRAIN_COLOR), ("ترام", "tram", TRAM_COLOR)]:
        uri = c.svg_data_uri(c.data_path(APP, ICONS[icon_key]), ICON_COLOR)
        sub = stations[stations["نوع الخطوط بالمحطة"] == kind]
        fg = c.group(m, c.lg_label(f"محطات السكك الحديدية: {kind}", c.lg_img(uri) or c.lg_dot(ring), len(sub)))
        if uri:
            icon_markers(fg, sub, uri, ring, 22)

    ep = data["endpoints"]
    c.add_geojson(c.group(m, c.lg_label("محطات البداية والنهاية لخطوط السير", c.lg_dot(ENDPOINT_COLOR), len(ep))),
                  c.to_geojson(ep, ["popup", "tip"]),
                  lambda _f: {"fillColor": ENDPOINT_COLOR, "fillOpacity": 0.95, "color": "#FFFFFF",
                              "weight": 1.5, "radius": 5},
                  weight_hover=3, marker=folium.CircleMarker(radius=5, fill=True))

    uri = c.svg_data_uri(c.data_path(APP, ICONS["main"]), ICON_COLOR)
    fg = c.group(m, c.lg_label("المواقف الرئيسية", c.lg_img(uri) or c.lg_dot(c.NAVY), len(data["main"])))
    if uri:
        icon_markers(fg, data["main"], uri, c.NAVY, 28)

    routes = load_routes()
    if highlight_idx is not None:          # chosen route drawn on top in yellow, map zooms to it
        h = routes.iloc[highlight_idx]
        folium.GeoJson(h.geometry.__geo_interface__,
                       style_function=lambda _f: {"color": "#FFD400", "weight": 7, "opacity": 1},
                       tooltip=folium.Tooltip(h["tip"]), popup=folium.Popup(h["popup"], max_width=460),
                       control=False).add_to(m)
        return c.finish_map(m, h.geometry.bounds, padding=30)
    return c.finish_map(m, tuple(routes.total_bounds) if full_extent else CENTRAL_BOUNDS, padding=10)


# ---------------------------------------------------------------- page
c.require_files(APP, list(FILES.values()))
data = load()
routes = load_routes()
labels = route_labels()
with st.sidebar:
    st.header("إعدادات الخريطة")
    options = ["— بدون —"] + labels
    choice = st.selectbox("إبراز خط معين على الخريطة", options, index=0)
    full = st.checkbox("عرض المحافظة بالكامل (برج العرب والعامرية)", value=False)
highlight_idx = options.index(choice) - 1 if choice != options[0] else None

c.page_title(TITLE, "🚌")
n_tram = int((data["rail"]["نوع الخط"] == "ترام").sum())
n_train = int((data["rail"]["نوع الخط"] == "قطار").sum())
k = st.columns(5)
k[0].metric("خطوط الأتوبيسات", f"{len(data['bus'])}")
k[1].metric("خطوط الميكروباصات", f"{len(data['micro'])}")
k[2].metric("خطوط الترام / القطار", f"{n_tram} / {n_train}")
k[3].metric("المواقف الرئيسية", f"{len(data['main'])}")
k[4].metric("إجمالي أطوال الخطوط (كم)", f"{routes['المسافة (كم)'].sum():,.0f}")
c.metric_cards()

c.show_map(build_map(highlight_idx, full), key="transport_map")
st.caption("انقر على أي خط أو محطة لعرض تفاصيلها، واستخدم مفتاح الخريطة لإظهار الطبقات أو إخفائها، "
           "أو اختر خطًا من القائمة الجانبية (») لإبرازه.")

with st.expander("المواقف الرئيسية حسب عدد الخطوط"):
    ms = data["main"].sort_values("إجمالي عدد الخطوط")
    fig = go.Figure()
    for col, name, color in [("عدد خطوط الأتوبيسات", "أتوبيس", BUS_COLOR),
                             ("عدد خطوط الميكروباصات", "ميكروباص", MICRO_COLOR),
                             ("عدد خطوط الترام", "ترام", TRAM_COLOR),
                             ("عدد خطوط القطار", "قطار", TRAIN_COLOR)]:
        fig.add_trace(go.Bar(name=name, x=ms[col], y=ms["اسم الموقف"] + "  ", orientation="h",
                             marker_color=color, hovertemplate="<b>%{y}</b><br>" + name + ": %{x}<extra></extra>"))
    c.bar_layout(fig, max(420, 24 * len(ms)), barmode="stack", xaxis_title="عدد الخطوط",
                 yaxis=dict(side="right"), legend=dict(orientation="h", y=1.05, x=1, xanchor="right"))
    c.show_chart(fig)

with st.expander("أطوال الخطوط حسب وسيلة النقل"):
    bins = [0, 10, 20, 30, 40, 1000]
    band_names = ["أقل من 10 كم", "10 - 20 كم", "20 - 30 كم", "30 - 40 كم", "40 كم فأكثر"]
    r = routes.dropna(subset=["المسافة (كم)"]).copy()
    r["band"] = pd.cut(r["المسافة (كم)"], bins=bins, labels=band_names, right=False)
    counts = r.groupby(["band", "mode"], observed=False).size().unstack(fill_value=0)
    fig = go.Figure()
    for mode, color in [("أتوبيس", BUS_COLOR), ("ميكروباص", MICRO_COLOR), ("ترام", TRAM_COLOR), ("قطار", TRAIN_COLOR)]:
        if mode in counts.columns:
            fig.add_trace(go.Bar(name=mode, x=band_names, y=counts[mode], marker_color=color,
                                 hovertemplate="<b>%{x}</b><br>" + mode + ": %{y} خط<extra></extra>"))
    c.bar_layout(fig, 360, barmode="group", yaxis_title="عدد الخطوط", xaxis=dict(autorange="reversed"),
                 legend=dict(orientation="h", y=1.12, x=1, xanchor="right"))
    c.show_chart(fig)

with st.expander("خطوط الأتوبيسات حسب الإدارة"):
    mgmt = (data["bus"]["إدارة الخط"].fillna("غير محدد")
            .str.replace("الخط تابع ل", "", regex=False).value_counts().sort_values())
    fig = go.Figure(go.Bar(x=mgmt.values, y=[n + "  " for n in mgmt.index], orientation="h",
                           marker_color=BUS_COLOR, text=mgmt.values, textposition="outside",
                           hovertemplate="<b>%{y}</b><br>%{x} خط<extra></extra>"))
    c.bar_layout(fig, max(300, 40 * len(mgmt)), xaxis_title="عدد الخطوط", yaxis=dict(side="right"))
    c.show_chart(fig)

with st.expander("جدول الخطوط الكامل"):
    cols = ["mode", "اسم الخط", "رقم الخط", "نوع الخط", "المسافة (كم)", "التسعير (ج.م)",
            "إدارة الخط", "مسار الطالع", "مسار النازل"]
    table = routes[[col for col in cols if col in routes.columns]].rename(columns={"mode": "وسيلة النقل"})
    st.dataframe(table, hide_index=True, use_container_width=True)
