# -*- coding: utf-8 -*-
"""
Shared building blocks for all HCSR map pages:
colours, page styling, basemap, the in-map legend, popups, photos and data helpers.
Change a colour or font here and every map follows.
"""

import base64
import json
import math
import os
from os import path as os_path
from urllib.parse import quote

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely import force_2d
from streamlit_extras.metric_cards import style_metric_cards

# ---------------------------------------------------------------- folders
ROOT = os_path.dirname(os_path.abspath(__file__))
DATA_DIR = os_path.join(ROOT, "data")            # one sub-folder per map
STATIC_DIR = os_path.join(ROOT, "static")        # served by Streamlit at /app/static/
PHOTOS_DIR = os_path.join(STATIC_DIR, "photos")  # one sub-folder per map (client photos)


def data_path(app, filename):
    return os_path.join(DATA_DIR, app, filename)


# ---------------------------------------------------------------- look & feel (HCSR blues)
NAVY = "#0B2E59"
BLUE = "#1565C0"
LIGHT_BLUE = "#EAF2FB"
BORDER_BLUE = "#C9DCF2"
TEXT_DARK = "#1F2937"
FONT = "Cairo, Tahoma, sans-serif"
CHART_FONT = dict(family=FONT, color=NAVY)

MAP_HEIGHT = 600           # map height in pixels (laptop friendly)
FILL_OPACITY = 0.8         # polygon fill opacity on every map
MAP_CACHE_ENTRIES = 8      # finished maps kept in memory per page (one per filter combination)

# Esri World Dark Gray Canvas — no labels, no API key
BASEMAP_TILES = ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
                 "World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}")
LABEL_TILES = ("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
               "World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}")
BASEMAP_ATTR = "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"
ESRI_CREDIT = "Tiles © Esri — Esri, HERE, Garmin, © OpenStreetMap contributors"

PAGE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, .stMetric, .stSelectbox, .stSlider,
.stCheckbox, .stRadio, .stMultiSelect, h1, h2, h3, h4, p, label, div[role="dialog"] {{
    font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
}}
.main .block-container, section[data-testid="stSidebar"], div[role="dialog"] {{
    direction: rtl; text-align: right;
}}
iframe, .stPlotlyChart, .js-plotly-plot {{ direction: ltr; }}
.main .block-container, [data-testid="stMainBlockContainer"] {{
    padding-top: 1.6rem; padding-bottom: 0.5rem; padding-left: 1rem; padding-right: 1rem;
    max-width: 100%;
}}
[data-testid="stVerticalBlock"] {{ gap: 0.55rem; }}
.app-title {{
    background: linear-gradient(90deg, {NAVY}, {BLUE});
    color: #FFFFFF; font-size: 1.2rem; font-weight: 700;
    padding: 0.45rem 1rem; border-radius: 8px; margin-bottom: 0.2rem;
}}
[data-testid="stMetric"] {{ background-color: #FFFFFF !important; padding: 0.35rem 0.8rem !important; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
    color: {NAVY} !important; font-size: 0.85rem !important; font-weight: 600 !important;
}}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{
    color: {TEXT_DARK} !important; font-size: 1.35rem !important; font-weight: 700 !important;
}}
[data-testid="stMetricDelta"], [data-testid="stMetricDelta"] div {{
    color: {BLUE} !important; font-size: 0.8rem !important;
}}
[data-testid="stMetricDelta"] svg {{ display: none; }}
[data-testid="stExpander"] details {{ border: 1px solid {BORDER_BLUE}; border-radius: 8px; }}
[data-testid="stExpander"] summary {{ background: {LIGHT_BLUE}; color: {NAVY}; font-weight: 600; }}
section[data-testid="stSidebar"] {{ background: {LIGHT_BLUE}; }}
.info-table {{ width: 100%; border-collapse: collapse; direction: rtl; }}
.info-table td {{ padding: 6px 10px; border-bottom: 1px solid {BORDER_BLUE}; color: {TEXT_DARK}; }}
.info-table td:first-child {{ font-weight: 600; width: 55%; color: {NAVY}; }}
.highlight-row td {{ background: #E5F5E0; font-weight: 700; }}
.home-card {{ border: 1px solid {BORDER_BLUE}; border-radius: 10px; padding: 0.7rem 0.9rem;
    background: #FFFFFF; min-height: 7.2rem; }}
.home-card h4 {{ color: {NAVY}; margin: 0 0 0.3rem 0; font-size: 1.02rem; }}
.home-card p {{ color: {TEXT_DARK}; margin: 0; font-size: 0.88rem; }}
</style>
"""


def page_title(text, icon=""):
    st.markdown(f'<div class="app-title">{icon} {text}</div>', unsafe_allow_html=True)


def metric_cards():
    style_metric_cards(background_color="#FFFFFF", border_size_px=1, border_color=BORDER_BLUE,
                       border_radius_px=8, border_left_color=BLUE, box_shadow=True)


# ---------------------------------------------------------------- small helpers
def fmt(v):
    if v is None or v == "" or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if isinstance(v, float):
        return f"{v:,.0f}" if v.is_integer() or abs(v) >= 100 else f"{v:,.1f}"
    return str(v)


def unique_labels(names):
    """Make bar labels unique so identical names don't merge into one bar."""
    seen, out = {}, []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} ({seen[n]})")
    return out


def hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def read_geo(path, simplify=None):
    """Read a GeoJSON, force WGS84 and 2-D, optionally simplify (degrees)."""
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    if simplify:
        gdf["geometry"] = gdf.geometry.simplify(simplify, preserve_topology=True)
    return gdf.reset_index(drop=True)


def _round_coords(c, nd=6):
    if isinstance(c, (list, tuple)):
        if c and isinstance(c[0], (int, float)):
            return [round(c[0], nd), round(c[1], nd)]
        return [_round_coords(x, nd) for x in c]
    return c


def to_geojson(gdf, cols):
    """GeoJSON dict with only the needed properties and coordinates rounded to ~10 cm
    (keeps the map small for the browser)."""
    geo = json.loads(gdf[list(cols) + ["geometry"]].to_json(na="null"))
    for f in geo["features"]:
        if f.get("geometry"):
            f["geometry"]["coordinates"] = _round_coords(f["geometry"]["coordinates"])
    return geo


def file_data_uri(path, mime="image/svg+xml"):
    """Embed a small file (e.g. an SVG icon) as-is."""
    if not os_path.exists(path):
        return None
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def svg_data_uri(path, color="#333333"):
    """Load an SVG icon (filling in QGIS 'param(...)' placeholders) as a data URI."""
    if not os_path.exists(path):
        return None
    svg = open(path, encoding="utf-8").read()
    has_params = "param(fill)" in svg
    svg = (svg.replace("param(fill)", color).replace("param(fill-opacity)", "1")
              .replace("param(outline)", "none").replace("param(outline-opacity)", "0")
              .replace("param(outline-width)", "0"))
    if not has_params and "<svg" in svg and 'fill="' not in svg.split(">", 1)[1][:300]:
        svg = svg.replace("<path", f'<path fill="{color}"')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


# ---------------------------------------------------------------- photos (served as files)
PHOTO_PATTERNS = ["C__Program Files_QGIS 3.22.5_map pictures_{}", "{}"]
PHOTO_WIDTH = 400


def static_url(rel_path):
    """URL of a file in ./static — works with or without a server.baseUrlPath."""
    base = (st.get_option("server.baseUrlPath") or "").strip("/")
    prefix = f"/{base}" if base else ""
    return f"{prefix}/app/static/" + quote(rel_path.replace(os_path.sep, "/"))


def photo_url(app, filename):
    """Find a feature's photo in static/photos/<app>/ (or its 'images' sub-folder).
    Photos are only downloaded when a popup is opened, so the map stays light."""
    if not isinstance(filename, str) or not filename:
        return None
    for sub in ("", "images"):
        for pattern in PHOTO_PATTERNS:
            rel = os_path.join("photos", app, sub, pattern.format(filename))
            if os_path.exists(os_path.join(STATIC_DIR, rel)):
                return static_url(rel)
    return None


def photos_available(app):
    d = os_path.join(PHOTOS_DIR, app)
    return os_path.isdir(d) and any(True for _ in os.scandir(d))


# ---------------------------------------------------------------- popups & tooltips
def popup_html(title, badge, badge_color, rows, photo=None, badge_text="white"):
    """rows: list of (label, value_html)."""
    body = "".join(
        f'<tr><td style="padding:4px 6px;border-bottom:1px solid {BORDER_BLUE};color:{NAVY};'
        f'font-weight:600;width:36%;vertical-align:top">{k}</td>'
        f'<td style="padding:4px 6px;border-bottom:1px solid {BORDER_BLUE};color:{TEXT_DARK}">{v}</td></tr>'
        for k, v in rows)
    img = (f'<img src="{photo}" loading="lazy" style="width:100%;max-width:{PHOTO_WIDTH}px;'
           f'border-radius:6px;margin-top:8px;display:block">' if photo else "")
    return (
        f'<div style="direction:rtl;text-align:right;font-family:{FONT};min-width:280px;'
        f'max-width:{PHOTO_WIDTH + 20}px">'
        f'<div style="color:{NAVY};font-weight:700;font-size:15px;margin-bottom:4px">{title}</div>'
        f'<span style="background:{badge_color};color:{badge_text};padding:1px 10px;border-radius:10px;'
        f'font-weight:600;font-size:12px">{badge}</span>'
        f'<table style="width:100%;border-collapse:collapse;margin-top:6px;font-size:13px">{body}</table>'
        f'{img}</div>')


def tip_html(title, sub=""):
    return f'<div style="direction:rtl;font-family:{FONT}"><b>{title}</b><br>{sub}</div>'


def text_on(color):
    """Dark text on light badge colours, white text on dark ones."""
    h = color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return TEXT_DARK if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "white"


# ---------------------------------------------------------------- in-map legend
# Each legend item is a layer group inside the map: ticking it on/off happens in the
# browser (no Streamlit rerun, no reload). Groups are added bottom layer first and the
# CSS shows the list reversed, so it reads top-down like the client's original legend.
# On wide screens the legend is always open; on phones it folds into the layers icon.
LEGEND_CSS = """
<style>
  .leaflet-container { background: #262626 !important; }
  .leaflet-tile-container img.leaflet-tile {
      width: 256.6px !important; height: 256.6px !important; outline: 1px solid transparent; }
  .leaflet-popup-content { margin: 10px 12px; }
  .leaflet-control-layers { direction: rtl; text-align: right; font-family: Cairo, Tahoma, sans-serif;
      border: 1px solid #C9DCF2 !important; border-radius: 8px !important;
      box-shadow: 0 2px 10px rgba(0,0,0,0.45) !important; overflow: hidden; background: #FFFFFF; }
  .leaflet-control-layers-expanded { padding: 0 !important; }
  .leaflet-control-layers-list::before { content: "مفتاح الخريطة"; display: block; background: #0B2E59;
      color: #FFFFFF; font-weight: 700; font-size: 14px; text-align: center; padding: 5px 12px;
      margin: 0 -10px 6px -10px; }
  .leaflet-control-layers-list { padding: 0 10px 8px 10px; max-height: 430px; overflow-y: auto; }
  .leaflet-control-layers-overlays { display: flex; flex-direction: column-reverse; }
  .leaflet-control-layers-overlays label { margin: 3px 0; font-size: 13px; font-weight: 700;
      color: #0B2E59; white-space: nowrap; cursor: pointer; }
  .leaflet-control-layers-selector { accent-color: #1565C0; margin: 0 0 0 6px !important;
      vertical-align: middle; }
  .leaflet-control-layers-separator, .leaflet-control-layers-base { display: none; }
  @media (min-width: 701px) {
      .leaflet-control-layers .leaflet-control-layers-list { display: block !important; }
      .leaflet-control-layers-toggle { display: none !important; }
      .leaflet-control-layers { padding: 0 !important; }
  }
  @media (max-width: 700px) {
      .leaflet-control-layers-list { max-height: 300px; }
      .leaflet-control-layers-overlays label { font-size: 12px; }
  }
  .lg-sw { display: inline-block; width: 16px; height: 16px; border-radius: 3px; vertical-align: middle;
      margin-left: 6px; }
  .lg-ln { display: inline-block; width: 22px; height: 4px; border-radius: 2px; vertical-align: middle;
      margin-left: 6px; }
  .lg-dot { display: inline-block; border-radius: 50%; vertical-align: middle; margin-left: 6px;
      border: 1.5px solid #FFFFFF; box-shadow: 0 0 0 1px rgba(0,0,0,0.35); }
  .lg-img { width: 18px; height: 18px; vertical-align: middle; margin-left: 6px; }
  .lg-n { color: #6B7280; font-weight: 600; font-size: 11px; margin-right: 4px; }
</style>"""


def lg_swatch(fill, border=None):
    return f'<span class="lg-sw" style="background:{fill};border:1px solid {border or fill}"></span>'


def lg_line(color):
    return f'<span class="lg-ln" style="background:{color}"></span>'


def lg_dot(color, size=12):
    return f'<span class="lg-dot" style="width:{size}px;height:{size}px;background:{color}"></span>'


def lg_img(uri):
    return f'<img class="lg-img" src="{uri}">' if uri else ""


def lg_label(text, symbol="", count=None):
    n = f'<span class="lg-n">({count})</span>' if count is not None else ""
    return f"{symbol}<span>{text}</span>{n}"


def new_map():
    """Dark basemap + (hidden) place-name labels as the last legend item."""
    m = folium.Map(tiles=None, control_scale=True, prefer_canvas=True)
    folium.TileLayer(BASEMAP_TILES, attr=BASEMAP_ATTR, name="Dark Gray", control=False,
                     max_zoom=20, max_native_zoom=16).add_to(m)
    folium.map.CustomPane("labels", z_index=650, pointer_events=False).add_to(m)
    folium.TileLayer(LABEL_TILES, attr=BASEMAP_ATTR, overlay=True, show=False, pane="labels",
                     name=lg_label("أسماء الأماكن", "🏷️ "), max_zoom=20, max_native_zoom=16).add_to(m)
    return m


def finish_map(m, bounds, title="مفتاح الخريطة", padding=15):
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    css = LEGEND_CSS.replace('content: "مفتاح الخريطة"', f'content: "{title}"')
    m.get_root().header.add_child(folium.Element(css))
    minx, miny, maxx, maxy = bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(padding, padding))
    return m


def group(m, label):
    fg = folium.FeatureGroup(name=label)
    fg.add_to(m)
    return fg


def add_geojson(parent, geo, style, weight_hover=4, marker=None):
    """One GeoJSON object per layer (much lighter than one per feature).
    Features must carry 'popup' and 'tip' properties (HTML strings)."""
    if not geo["features"]:
        return
    kwargs = {}
    if marker is not None:
        kwargs["marker"] = marker
    folium.GeoJson(
        geo,
        style_function=style,
        highlight_function=lambda _f: {"weight": weight_hover, "color": "#FFD400"},
        tooltip=folium.GeoJsonTooltip(fields=["tip"], labels=False, sticky=True),
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False, maxWidth=PHOTO_WIDTH + 40),
        **kwargs,
    ).add_to(parent)


def _fresh_copy(m):
    """Copy of a cached map for this run. The cached map itself is never drawn, because a
    folium map that has been drawn once does not draw again (blank map on the second visit).
    The big GeoJSON data and the HTML templates are shared, not copied, so this is fast."""
    try:
        import copy
        from jinja2 import Template
        memo, stack, seen = {}, [m.get_root()], set()
        while stack:
            el = stack.pop()
            if id(el) in seen:
                continue
            seen.add(id(el))
            for v in vars(el).values():
                if isinstance(v, Template) or (isinstance(el, folium.GeoJson) and v is el.data):
                    memo[id(v)] = v
            stack.extend(getattr(el, "_children", {}).values())
        return copy.deepcopy(m, memo)
    except Exception:          # never break the page over this: fall back to the cached map
        return m


def show_map(m, key):
    """Render a folium map. returned_objects=[] stops reruns when the map is panned.
    The key changes on every visit to the page, so the map is redrawn when you come back."""
    from streamlit_folium import st_folium
    visit = st.session_state.get("_page_visit", 0)
    st_folium(_fresh_copy(m), height=MAP_HEIGHT, use_container_width=True, returned_objects=[],
              key=f"{key}_{visit}")


# ---------------------------------------------------------------- plotly basemap
def plotly_map_layout(fig, bounds, width_guess=1250, height=MAP_HEIGHT):
    minx, miny, maxx, maxy = bounds

    def merc(lat):
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    def inv_merc(y):
        return math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)

    zx = math.log2(width_guess * 0.9 * 360 / (512 * (maxx - minx)))
    zy = math.log2(height * 0.9 * 2 * math.pi / (512 * (merc(maxy) - merc(miny))))
    center = dict(lat=inv_merc((merc(miny) + merc(maxy)) / 2), lon=(minx + maxx) / 2)
    fig.update_layout(
        map_style="white-bg",
        map_layers=[dict(sourcetype="raster", source=[BASEMAP_TILES], below="traces")],
        map_zoom=min(zx, zy), map_center=center,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=height,
        hoverlabel=dict(font_family=FONT, font_size=13, align="right",
                        bgcolor="white", bordercolor=BLUE, font_color=TEXT_DARK),
        clickmode="event+select", uirevision=True,
        annotations=[dict(text=ESRI_CREDIT, showarrow=False, xref="paper", yref="paper",
                          x=0.005, y=0.005, xanchor="left", yanchor="bottom",
                          font=dict(size=10, color=TEXT_DARK), bgcolor="rgba(255,255,255,0.7)",
                          borderpad=2)],
    )
    return fig


def plotly_colorbar(title_html, **extra):
    return dict(title=dict(text=title_html, side="top", font=dict(size=15, color=NAVY, family=FONT)),
                tickfont=dict(size=14, color=NAVY, family=FONT),
                x=0.985, xanchor="right", y=0.5, yanchor="middle", len=0.62, thickness=20,
                bgcolor="rgba(255,255,255,0.92)", bordercolor=NAVY, borderwidth=1,
                outlinecolor=NAVY, outlinewidth=1, xpad=12, ypad=12, **extra)


def bar_layout(fig, height=360, **kw):
    fig.update_layout(height=height, margin={"r": 10, "t": 10, "l": 10, "b": 30},
                      font=CHART_FONT, template="plotly_white", **kw)
    return fig


def show_chart(fig):
    st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)


def require_files(app, files):
    missing = [f for f in files if not os_path.exists(data_path(app, f))]
    if missing:
        st.error(f"لم يتم العثور على الملفات التالية في مجلد data/{app}:\n\n" + "\n".join(missing))
        st.stop()
