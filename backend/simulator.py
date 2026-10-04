import asyncio, math, random, time
from .packet import Reading, encode
from .db import add_reading
from .ai import AIEngine
from .kalman import KalmanCV

class Simulator:
    def __init__(self, state, broadcast):
        self.state=state; self.broadcast=broadcast; self.ai=AIEngine()
        self.filters={i:KalmanCV() for i in range(1,26)}
        self.nodes={}
        for i in range(1,26):
            lat=-45-random.random()*23
            lon=-180+random.random()*360
            self.nodes[i]={"lat":lat,"lon":lon,"phase":random.random()*6.28,"storm":0}
        self.injects={}
    def inject(self,node_id,typ):
        self.injects[node_id]=typ
    def make(self,i,now):
        n=self.nodes[i]; phase=n["phase"]+now/86400*2*math.pi
        lat=n["lat"]; lon=(n["lon"]+0.00001*random.uniform(10,40)*300)%360-180
        ice=max(0,(-lat-45)/23)
        sst=8-9.8*ice+0.35*math.sin(phase)+random.gauss(0,.08)
        sal=34.0+0.45*ice+random.gauss(0,.025)
        hs=2.2+2.0*ice+0.7*math.sin(now/2500)+random.random()*1.1
        wind=7+8*random.random()+3*math.sin(now/4000)
        if n["storm"]>0: hs+=4; wind+=8; n["storm"]-=1
        batt=12.7-0.8*max(0,math.sin(phase))*ice
        solar=max(0,850*math.sin(phase)+random.gauss(0,30))*(1-0.55*ice)
        typ=self.injects.get(i)
        if typ=="ice_event": sst-=2.0; batt-=1.0
        elif typ=="sensor_fault": sal=34.2
        elif typ=="battery_fade": batt-=2.0
        elif typ=="storm": hs+=4.0; wind+=8.0
        r=Reading(i,int(now),lat,lon,sst,sal,120,hs,8+4*random.random(),random.randrange(360),
                  max(1,wind),random.randrange(360),-2+5*math.sin(phase)+random.gauss(0,.5),
                  985+18*math.sin(phase)+random.gauss(0,1.5),max(10.8,batt),solar,
                  3+4*math.sin(phase),-75+random.randrange(12),0)
        return r
    async def run(self):
        while True:
            now=int(time.time())
            for i in self.nodes:
                r=self.make(i,now)
                raw=encode(r)
                add_reading(r,raw.hex())
                score,feature=self.ai.observe(r)
                sm=self.filters[i].update(r.lat,r.lon)
                self.state["last"][i]=r
                self.state["smooth"][i]=(sm[0],sm[1])
                self.state["pipeline"]["firmware"]+=1
                self.state["pipeline"]["packet"]+=1
                self.state["pipeline"]["satellite"]+=1
                self.state["pipeline"]["gateway"]+=1
                self.state["pipeline"]["decoder"]+=1
                self.state["pipeline"]["database"]+=1
                self.state["pipeline"]["ai"]+=1
                self.state["pipeline"]["dashboard"]+=1
                if score is not None:
                    self.state["alerts"].append({"node_id":i,"severity":"WARNING","kind":"anomaly","message":f"Anomaly detected in {feature}","feature":feature,"score":score,"ts":now})
                await self.broadcast({"type":"reading","node_id":i,"reading":r.__dict__,"smooth":self.state["smooth"][i],"anomaly":score})
            await asyncio.sleep(5)
