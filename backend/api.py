import asyncio, json, time, base64
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .db import init_db, rows, one, add_reject, count_rejects, add_alert
from .packet import decode, parse_payload, encode
from .simulator import Simulator

app=FastAPI(title="CryoNode Console")
ROOT=Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=ROOT/"frontend"), name="static")
clients=set()
state={"last":{},"smooth":{},"alerts":[],"pipeline":{k:0 for k in ["firmware","packet","satellite","gateway","decoder","database","ai","dashboard"]}}
sim=None

@app.on_event("startup")
async def startup():
    global sim
    init_db()
    async def bc(msg):
        dead=[]
        for ws in clients:
            try: await ws.send_json(msg)
            except Exception: dead.append(ws)
        for ws in dead: clients.discard(ws)
    sim=Simulator(state,bc)
    asyncio.create_task(sim.run())

@app.get("/")
async def index(): return FileResponse(ROOT/"frontend/index.html")

@app.post("/api/ingest")
async def ingest(request: Request):
    raw=await request.body()
    text=raw.decode().strip()
    try:
        packet=parse_payload(text)
        r,meta=decode(packet)
    except Exception as e:
        add_reject(str(e), text[:1000])
        raise HTTPException(400,str(e))
    from .db import add_reading
    add_reading(r,packet.hex())
    state["last"][r.node_id]=r
    return {"accepted":True,"node_id":r.node_id,"bytes":len(packet),"crc":meta["crc_ok"]}

@app.get("/api/buoys")
def buoys():
    out=[]
    now=time.time()
    for i,r in state["last"].items():
        age=now-r.unix_time
        status="normal" if age<15 else "offline"
        if i==99: kind="LIVE"
        else: kind="SIMULATED"
        out.append({**r.__dict__,"id":i,"age":age,"status":status,"source":kind,
                    "smooth":state["smooth"].get(i)})
    return sorted(out,key=lambda x:x["id"])

@app.get("/api/buoys/{id}/history")
def history(id:int,hours:int=24):
    return rows("SELECT * FROM readings WHERE node_id=? AND ts>=? ORDER BY ts",(id,int(time.time())-hours*3600))

@app.get("/api/alerts")
def alerts():
    db=rows("SELECT * FROM alerts ORDER BY id DESC LIMIT 100")
    return (state["alerts"][-100:][::-1] + db)[:100]

@app.get("/api/packet/last")
def packet_last():
    if not state["last"]: return {"raw_hex":"","decoded":None,"crc_ok":None,"bytes":0}
    r=max(state["last"].values(),key=lambda x:x.unix_time)
    raw=one("SELECT raw_hex FROM readings WHERE node_id=? AND ts=? ORDER BY id DESC LIMIT 1",(r.node_id,r.unix_time))
    return {"raw_hex":raw["raw_hex"] if raw else encode(r).hex(),"decoded":r.__dict__,"crc_ok":True,"bytes":len(bytes.fromhex(raw["raw_hex"])) if raw else 0}

@app.get("/api/status")
def status():
    return {"rejects":count_rejects(),"pipeline":state["pipeline"]}

@app.get("/api/model/{id}")
def model(id:int):
    if sim is None: raise HTTPException(503)
    return sim.ai.forecast(id)

@app.post("/api/inject")
async def inject(payload:dict):
    if payload.get("type") not in {"ice_event","sensor_fault","battery_fade","storm"}: raise HTTPException(400,"bad injection")
    node=int(payload.get("node_id",1))
    sim.inject(node,payload["type"])
    return {"ok":True,"node_id":node,"type":payload["type"]}

@app.websocket("/ws")
async def ws(websocket:WebSocket):
    await websocket.accept(); clients.add(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: clients.discard(websocket)
