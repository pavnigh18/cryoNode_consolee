import numpy as np

class KalmanCV:
    def __init__(self):
        self.x = None
        self.P = np.eye(4) * 0.1
    def update(self, lat, lon, dt=1.0):
        if self.x is None:
            self.x = np.array([lat, lon, 0.0, 0.0], dtype=float)
            return lat, lon
        F = np.array([[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]],float)
        Q = np.eye(4)*1e-5
        H = np.array([[1,0,0,0],[0,1,0,0]],float)
        R = np.eye(2)*1e-5
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q
        z=np.array([lat,lon])
        y=z-H@self.x
        S=H@self.P@H.T+R
        K=self.P@H.T@np.linalg.inv(S)
        self.x=self.x+K@y
        self.P=(np.eye(4)-K@H)@self.P
        return float(self.x[0]), float(self.x[1])
