import sqlite3
import threading
import json
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "cryonode.sqlite3"
_lock = threading.Lock()

def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS readings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, node_id INTEGER, ts INTEGER,
          lat REAL, lon REAL, sst REAL, salinity REAL, depth_m REAL, hs REAL,
          tp REAL, wave_dir INTEGER, wind_speed REAL, wind_dir INTEGER,
          air_temp REAL, pressure REAL, battery_v REAL, solar_mw REAL,
          internal_temp REAL, rssi INTEGER, status INTEGER, raw_hex TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, node_id INTEGER, ts INTEGER,
          severity TEXT, kind TEXT, message TEXT, feature TEXT, score REAL, acknowledged INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rejects(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER, reason TEXT, raw_hex TEXT
        );
        """)

def add_reading(r, raw_hex):
    with _lock, conn() as c:
        c.execute("""INSERT INTO readings
        (node_id,ts,lat,lon,sst,salinity,depth_m,hs,tp,wave_dir,wind_speed,wind_dir,air_temp,pressure,battery_v,solar_mw,internal_temp,rssi,status,raw_hex)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (r.node_id,r.unix_time,r.lat,r.lon,r.sst,r.salinity,r.depth_m,r.hs,r.tp,r.wave_dir,r.wind_speed,r.wind_dir,r.air_temp,r.pressure,r.battery_v,r.solar_mw,r.internal_temp,r.rssi,r.status,raw_hex))

def rows(sql, args=()):
    with conn() as c:
        return [dict(x) for x in c.execute(sql,args).fetchall()]

def one(sql,args=()):
    with conn() as c:
        x=c.execute(sql,args).fetchone()
        return dict(x) if x else None

def add_alert(node_id, ts, severity, kind, message, feature="", score=None):
    with _lock, conn() as c:
        c.execute("INSERT INTO alerts(node_id,ts,severity,kind,message,feature,score) VALUES(?,?,?,?,?,?,?)",
                  (node_id,ts,severity,kind,message,feature,score))

def add_reject(reason, raw_hex):
    with _lock, conn() as c:
        c.execute("INSERT INTO rejects(ts,reason,raw_hex) VALUES(strftime('%s','now'),?,?)",(reason,raw_hex))

def count_rejects():
    return one("SELECT COUNT(*) n FROM rejects")["n"]
