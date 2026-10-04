export class MapView{
constructor(app){this.app=app;this.map=null;this.markers={};this.data={}}
render(){
this.app.innerHTML=`<section class="view active"><div class="layout"><div class="panel"><div class="section-head">FLEET / 25 SIMULATED + LIVE SLOT</div><div class="dense"><input id="search" placeholder="Search node" style="width:100%"></div><div id="buoyList" class="list"></div></div><div class="panel"><div id="map"></div></div></div></section>`;
if(!this.map){this.map=L.map("map",{zoomControl:false}).setView([-60,0],3);L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{attribution:"CARTO"}).addTo(this.map)}
fetch("/api/buoys").then(r=>r.json()).then(d=>d.forEach(x=>this.set(x)));document.querySelector("#search").oninput=e=>this.list(e.target.value)
}
set(x){this.data[x.id]=x;let m=this.markers[x.id];if(!m){m=L.circleMarker([x.lat,x.lon],{radius:6,color:"#0070C0",fillOpacity:.85}).addTo(this.map).on("click",()=>window.selectBuoy(x.id));this.markers[x.id]=m}m.setLatLng([x.lat,x.lon]);this.list(document.querySelector("#search")?.value||"")}
list(q=""){document.querySelector("#buoyList").innerHTML=Object.values(this.data).filter(x=>String(x.id).includes(q)).map(x=>`<div class="buoy" onclick="selectBuoy(${x.id})"><b>NODE ${String(x.id).padStart(2,"0")}</b> <span class="tag ${x.source==="LIVE"?"live":""}">${x.source}</span><br><span class="mono small">${x.sst.toFixed(2)} C · ${x.hs.toFixed(2)} m · ${x.battery_v.toFixed(2)} V</span></div>`).join("")}
update(m){if(this.data[m.node_id]){this.data[m.node_id]={...this.data[m.node_id],...m.reading};this.set(this.data[m.node_id])}}
}