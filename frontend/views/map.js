export class MapView {
  constructor(app) {
    this.app = app;
    this.map = null;
    this.markers = {};
    this.data = {};
  }

  render() {
    this.app.innerHTML = `<section class="view active"><div class="layout"><div class="panel"><div class="section-head">FLEET / 25 SIMULATED + LIVE SLOT</div><input id="search" placeholder="Search node" style="width:100%;margin-bottom:8px;padding:4px"><div id="buoyList" class="buoy-list"></div></div><div class="panel"><div id="map"></div></div></div></section>`;
    if (!this.map) {
      this.map = L.map("map", { zoomControl: false }).setView([-68, 0], 3);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(this.map);
    }
    fetch("/api/buoys")
      .then((r) => r.json())
      .then((d) => {
        d.forEach((x) => this.set(x));
        document.querySelector("#search").oninput = (e) => this.list(e.target.value);
      });
  }

  set(x) {
    this.data[x.id] = x;
    let m = this.markers[x.id];
    if (!m) {
      m = L.circleMarker([x.lat, x.lon], { radius: 6, color: "#0070c0", fillOpacity: 0.85 }).addTo(this.map);
      m.on("click", () => this.app.showTwin?.(x.id));
      this.markers[x.id] = m;
    } else {
      m.setLatLng([x.lat, x.lon]);
    }
    this.list();
  }

  list(q = "") {
    const listEl = document.querySelector("#buoyList");
    if (!listEl) return;
    listEl.innerHTML = Object.values(this.data)
      .filter((x) => String(x.id).includes(q))
      .map((x) => `<div class="buoy" onclick="window.app.showTwin('${x.id}')">Node ${x.id} [${x.lat.toFixed(2)}, ${x.lon.toFixed(2)}]</div>`)
      .join("");
  }

  update(m) {
    if (this.data[m.node_id]) {
      this.data[m.node_id] = { ...this.data[m.node_id], ...m.reading };
      this.set(this.data[m.node_id]);
    }
  }
}
