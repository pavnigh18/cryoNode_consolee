import base64
import struct
from dataclasses import dataclass
from typing import Any

MAGIC = 0xC7
VERSION = 1
# magic/version/node/time/lat/lon/SST/sal/depth/Hs/Tp/wave_dir/wind/wdir/airT/pressure/batt/solar/internal/rssi/status
FMT = ">BBHIiihHHHBBHHHhHHHhBbH"
BODY_SIZE = struct.calcsize(FMT)
PACKET_SIZE = BODY_SIZE
MAX_PACKET_SIZE = 340

def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc

@dataclass
class Reading:
    node_id: int
    unix_time: int
    lat: float
    lon: float
    sst: float
    salinity: float
    depth_m: float
    hs: float
    tp: float
    wave_dir: int
    wind_speed: float
    wind_dir: int
    air_temp: float
    pressure: float
    battery_v: float
    solar_mw: float
    internal_temp: float
    rssi: int
    status: int

def encode(r: Reading) -> bytes:
    body = struct.pack(
        FMT, MAGIC, VERSION, r.node_id, r.unix_time,
        round(r.lat * 1e5), round(r.lon * 1e5), round(r.sst * 100),
        round(r.salinity * 1000), round(r.depth_m * 10), round(r.hs * 100),
        round(r.tp * 10), r.wave_dir, round(r.wind_speed * 10), r.wind_dir,
        round(r.air_temp * 10), round(r.pressure * 10), round(r.battery_v * 1000),
        round(r.solar_mw), round(r.internal_temp * 10), r.rssi, r.status
    )
    return body + struct.pack(">H", crc16_ccitt(body))

def decode(packet: bytes) -> tuple[Reading, dict[str, Any]]:
    if len(packet) != PACKET_SIZE:
        raise ValueError(f"invalid packet size {len(packet)}")
    body, got_crc = packet[:-2], struct.unpack(">H", packet[-2:])[0]
    calc_crc = crc16_ccitt(body)
    if got_crc != calc_crc:
        raise ValueError("CRC mismatch")
    vals = struct.unpack(FMT, body)
    if vals[0] != MAGIC or vals[1] != VERSION:
        raise ValueError("bad magic/version")
    r = Reading(
        node_id=vals[2], unix_time=vals[3], lat=vals[4]/1e5, lon=vals[5]/1e5,
        sst=vals[6]/100, salinity=vals[7]/1000, depth_m=vals[8]/10,
        hs=vals[9]/100, tp=vals[10]/10, wave_dir=vals[11],
        wind_speed=vals[12]/10, wind_dir=vals[13], air_temp=vals[14]/10,
        pressure=vals[15]/10, battery_v=vals[16]/1000, solar_mw=vals[17],
        internal_temp=vals[18]/10, rssi=vals[19], status=vals[20]
    )
    validate(r)
    return r, {"crc_ok": True, "crc": got_crc}

def validate(r: Reading) -> None:
    checks = [
        (0 <= r.node_id <= 65535, "node id"),
        (-90 <= r.lat <= -35, "latitude"),
        (-180 <= r.lon <= 180, "longitude"),
        (-3 <= r.sst <= 12, "SST"),
        (30 <= r.salinity <= 38, "salinity"),
        (0 <= r.depth_m <= 1000, "depth"),
        (0 <= r.hs <= 20, "Hs"),
        (0 <= r.tp <= 30, "Tp"),
        (0 <= r.wind_speed <= 60, "wind speed"),
        (0 <= r.pressure <= 1100, "pressure"),
        (0 <= r.battery_v <= 20, "battery"),
        (0 <= r.solar_mw <= 5000, "solar"),
        (-60 <= r.internal_temp <= 60, "internal temp"),
        (-127 <= r.rssi <= 0, "RSSI"),
    ]
    for ok, name in checks:
        if not ok:
            raise ValueError(f"out-of-range {name}")

def parse_payload(payload: str) -> bytes:
    s = payload.strip()
    try:
        return bytes.fromhex(s)
    except ValueError:
        return base64.b64decode(s, validate=True)
