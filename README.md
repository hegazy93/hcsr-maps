# HCSR interactive maps (one Streamlit app)

Nine maps in one app, chosen from a dropdown at the top of the page.

| Address | Map |
|---|---|
| `/` | Home page (a card for each map) |
| `/greenspace` | Green space per person |
| `/heat-islands` | Urban heat islands |
| `/roads` | New axes, roads and bridges |
| `/transport` | Public transport lines |
| `/collapsed-buildings` | Collapsed buildings |
| `/alexandria-corniche` | Alexandria corniche |
| `/baltim` | Baltim corniche |
| `/ras-el-bar` | Ras El Bar corniche |
| `/port-said` | Port Said corniche |

## Folders

```
hcsr_maps/
├── app.py                 <- start here: streamlit run app.py
├── menu.py                <- list of maps (titles, web addresses, home-page text)
├── common.py              <- shared style, colours, map/legend/popup helpers
├── corniche.py            <- shared engine for the 4 corniche maps
├── maps/                  <- one small file per map
├── data/<map>/            <- the GeoJSON data (and icons) for each map
├── static/photos/<map>/   <- the client's photos (served as plain files)
├── .streamlit/config.toml <- theme + server settings (keep this folder!)
├── requirements.txt
└── deploy/                <- server files for the web developer (see deploy/README_DEPLOY.md)
```

## Run on your computer (Anaconda PowerShell Prompt)

```
conda activate spatialenv
pip install -r requirements.txt        # once; needs Streamlit 1.45 or newer
cd path\to\hcsr_maps
streamlit run app.py
```

## Before handing over: photos

The corniche popups show the client's photos. Copy them in once:

| Map | Copy the contents of the client's `images` folder into |
|---|---|
| Alexandria corniche | `static/photos/alex_waterfront/` |
| Baltim corniche | `static/photos/baltim/` |
| Ras El Bar corniche | `static/photos/rasbar/` |
| Port Said corniche | `static/photos/portsaid/` |

(Each `images` folder is inside that corniche's `all resources files.rar`. Copying the
`images` folder itself into the map's folder also works.) A map whose photos are
missing still works and shows a small warning under the map.

## Editing

* Colours, legend names, popup fields: the settings at the top of each file in `maps/`.
* Map height, fill opacity (0.8), basemap: the top of `common.py`.
* Dropdown titles and web addresses: `menu.py`.
* To replace data, overwrite the GeoJSON in `data/<map>/` with the same file name and
  restart the app.
