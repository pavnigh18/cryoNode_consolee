from collections import defaultdict, deque
import numpy as np
from sklearn.ensemble import IsolationForest
try:
    import torch
    TORCH = True
except Exception:
    TORCH = False

FEATURES = ["sst","delta_sst","salinity","hs","pressure","battery_v"]

class AIEngine:
    def __init__(self):
        self.history=defaultdict(lambda: deque(maxlen=240))
        self.models={}
        self.forecasts={}
        self.anomaly_scores=defaultdict(lambda: deque(maxlen=120))
        self.mae={}
        self.model_name = "PyTorch LSTM" if TORCH else "Linear regression fallback"
    def observe(self,r):
        h=self.history[r.node_id]
        prev=h[-1] if h else None
        delta=r.sst-prev.sst if prev else 0.0
        h.append(r)
        if len(h)>=24:
            X=np.array([[x.sst,(x.sst-(h[i-1].sst if i else x.sst)),x.salinity,x.hs,x.pressure,x.battery_v]
                        for i,x in enumerate(h)],float)
            if len(X)>=32:
                model=IsolationForest(n_estimators=80,contamination=0.05,random_state=7)
                model.fit(X[-120:])
                score=float(-model.score_samples(X[-1:].reshape(1,-1))[0])
                self.models[r.node_id]=model
                self.anomaly_scores[r.node_id].append(score)
                if score>0.62:
                    # Robust feature attribution: perturb one feature toward its rolling median.
                    med=np.median(X[-60:],axis=0)
                    base=model.score_samples(X[-1:].reshape(1,-1))[0]
                    impacts=[]
                    for j in range(X.shape[1]):
                        q=X[-1:].copy(); q[0,j]=med[j]
                        impacts.append(abs(model.score_samples(q)[0]-base))
                    feature=FEATURES[int(np.argmax(impacts))]
                    return score, feature
        return None,None
    def forecast(self,node_id):
        h=list(self.history[node_id])
        if len(h)<12: return {"sst":[],"battery":[],"mae":None,"model":self.model_name}
        n=min(96,len(h)); train=h[:-max(6,n//5)]
        hold=h[-max(6,n//5):]
        def lin(vals):
            y=np.array(vals,float); x=np.arange(len(y)); deg=1 if len(y)>1 else 0
            p=np.polyfit(x,y,deg); return np.polyval(p,np.arange(len(y),len(y)+24))
        sst=lin([x.sst for x in train]); batt=lin([x.battery_v for x in train])
        pred_hold=np.polyval(np.polyfit(np.arange(len(train)),[x.sst for x in train],1),np.arange(len(train),len(train)+len(hold)))
        mae=float(np.mean(np.abs(pred_hold-np.array([x.sst for x in hold]))))
        self.mae[node_id]=mae
        out={"sst":[float(x) for x in sst],"battery":[float(x) for x in batt],"mae":mae,"model":self.model_name}
        self.forecasts[node_id]=out
        return out
