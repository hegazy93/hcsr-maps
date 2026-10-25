# Deployment notes for the web developer (option 1: small Linux server)

The app is a normal Python web app (Streamlit). It runs as one process on port 8501
behind Nginx, on a subdomain such as **maps.hcsr-eg.org**. The main website does not need
to change, apart from linking to (or embedding) the maps.

## Server

* Ubuntu 22.04 or 24.04 VPS, 2 vCPU / 2-4 GB RAM is plenty (about 5-10 USD a month).
* A DNS **A record**: `maps.hcsr-eg.org -> <server IP>`.
* Ports 80 and 443 open.

## Install (about 10 minutes)

```bash
# copy the zip to the server, then:
sudo apt-get install -y unzip
unzip hcsr_maps.zip && cd hcsr_maps
sudo bash deploy/install.sh                  # Python venv + packages + service + nginx
sudo certbot --nginx -d maps.hcsr-eg.org     # free HTTPS certificate (auto-renews)
```

`install.sh` copies the app to `/opt/hcsr_maps`, creates a virtual environment, installs
`requirements.txt`, installs `deploy/hcsr-maps.service` (systemd keeps it running and
restarts it after a crash or a reboot) and `deploy/nginx-hcsr-maps.conf` (reverse proxy).

**Nginx must pass WebSocket headers** (`Upgrade` / `Connection`) - they are already in the
config. Without them the page stays on "Please wait..." forever.

## Everyday commands

```bash
sudo systemctl status hcsr-maps      # is it running?
sudo systemctl restart hcsr-maps     # after changing data, photos or code
sudo journalctl -u hcsr-maps -f      # live log
```

Updating: replace the files in `/opt/hcsr_maps` (keep `.venv/`), then restart.

## Linking / embedding in hcsr-eg.org

* Full app with dropdown: `https://maps.hcsr-eg.org/`
* One map directly: `https://maps.hcsr-eg.org/ras-el-bar` (all addresses are in `menu.py`)
* Embed one map in a website page (no dropdown, no Streamlit toolbar):

```html
<iframe src="https://maps.hcsr-eg.org/ras-el-bar?embed=true&menu=off"
        style="width:100%;height:1100px;border:0" loading="lazy"></iframe>
```

## Performance notes

* Data is read once and finished maps are kept in memory (up to 8 filter combinations
  per map), so after the first visit maps open almost instantly for everyone.
  The very first visit after a restart is slower (a few seconds per map).
* Photos are plain files served at `/app/static/...` and only downloaded when a popup is
  opened; Nginx tells browsers to cache them for a week.
* Memory use: roughly 300-600 MB once every map has been opened.
