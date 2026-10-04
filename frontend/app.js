import {MapView} from "./views/map.js";
import {TwinView} from "./views/twin.js";
import {PipelineView} from "./views/pipeline.js";
import {PlannerView} from "./views/planner.js";

const app=document.querySelector("#app"); const views={map:new MapView(app),twin:new TwinView(app),pipeline:new PipelineView(app),planner:new PlannerView(app)};
let current="map", selected=1, socket=null;
function show(name){current=name;document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===name));views[name].render(selected)}
document.querySelectorAll("nav button").forEach(b=>b.onclick=()=>show(b.dataset.view));
window.selectBuoy=id=>{selected=id;show("twin")};
document.querySelector("#alertsBtn").onclick=()=>document.querySelector("#drawer").classList.add("drawer-open");
document.querySelector("#closeAlerts").onclick=()=>document.querySelector("#drawer").classList.remove("drawer-open");
document.querySelector("#scenario").onchange=async e=>{if(!e.target.value)return;await fetch("/api/inject",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({type:e.target.value,node_id:selected})});e.target.value=""};
function connect(){
 socket=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws");
 socket.onopen=()=>{document.querySelector("#conn").className="dot on";document.querySelector("#connText").textContent="CONNECTED";socket.send("hello")};
 socket.onclose=()=>{document.querySelector("#conn").className="dot off";document.querySelector("#connText").textContent="RECONNECTING";setTimeout(connect,1500)};
 socket.onmessage=e=>{const m=JSON.parse(e.data); if(m.type==="reading"){views.map.update(m);views.twin.update(m);views.pipeline.update(m);if(current==="twin")views.twin.render(selected)}};
}
setInterval(()=>document.querySelector("#clock").textContent=new Date().toISOString().replace("T"," ").slice(0,19)+"Z",1000);
setInterval(async()=>{const a=await fetch("/api/alerts").then(r=>r.json());document.querySelector("#alertCount").textContent=a.length;document.querySelector("#alerts").innerHTML=a.map(x=>`<div class="alert ${x.severity?.toLowerCase()}"><b>${x.severity||"WARNING"}</b> · NODE ${x.node_id}<br>${x.message||x.kind}<br><span class="mono small">${x.feature||""}</span></div>`).join("")},3000);
show("map"); connect();