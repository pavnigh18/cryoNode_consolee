# CryoNode Console

Run:
1. `python -m venv .venv`
2. Windows: `.venv\\Scripts\\activate` / macOS-Linux: `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python run.py`
5. Open http://localhost:8000

The demo starts 25 simulated buoys and emits a 5-second packet cadence. Node 99 is reserved for real packets posted to `/api/ingest`.

Note: the frontend uses CDN libraries for Leaflet and Three.js. An internet connection is needed for those CDN assets and CARTO map tiles.
