from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from bleak import BleakScanner
from asyncio import sleep
from binascii import hexlify
from datetime import datetime
import json
from time import time_ns

app = FastAPI()

MIN_RSSI = -60
AIRPODS_MANUFACTURER = 76
AIRPODS_DATA_LENGTH = 54
RECENT_BEACONS_MAX_T_NS = 10_000_000_000  # 10 segundos
UPDATE_DURATION = 1

recent_beacons = []


def get_best_result(device):
    recent_beacons.append({
        "time": time_ns(),
        "device": device
    })
    strongest = None
    i = 0
    while i < len(recent_beacons):
        if time_ns() - recent_beacons[i]["time"] > RECENT_BEACONS_MAX_T_NS:
            recent_beacons.pop(i)
            continue
        if strongest is None or strongest.rssi < recent_beacons[i]["device"].rssi:
            strongest = recent_beacons[i]["device"]
        i += 1
    return device if strongest and strongest.address == device.address else strongest


async def get_device():
    devices = await BleakScanner.discover()
    for d in devices:
        d = get_best_result(d)
        if d and d.rssi >= MIN_RSSI and AIRPODS_MANUFACTURER in d.metadata.get("manufacturer_data", {}):
            data_hex = hexlify(bytearray(d.metadata["manufacturer_data"][AIRPODS_MANUFACTURER]))
            if len(data_hex) == AIRPODS_DATA_LENGTH:
                return data_hex
    return None


def is_flipped(raw):
    return (int(chr(raw[10]), 16) & 0x02) == 0


def parse_data(raw):
    if not raw:
        return {"status": 0, "model": "AirPods not found"}

    flip = is_flipped(raw)
    model_codes = {'e': 'AirPodsPro', '3': 'AirPods3', 'f': 'AirPods2', '2': 'AirPods1', 'a': 'AirPodsMax'}
    model = model_codes.get(chr(raw[7]), "unknown")

    def parse_battery(index): 
        val = int(chr(raw[index]), 16)
        return 100 if val == 10 else (val * 10 + 5 if val <= 10 else -1)

    left = parse_battery(12 if flip else 13)
    right = parse_battery(13 if flip else 12)
    case = parse_battery(15)

    charging = int(chr(raw[14]), 16)
    return {
        "status": 1,
        "charge": {"left": left, "right": right, "case": case},
        "charging_left": bool(charging & (0b00000010 if flip else 0b00000001)),
        "charging_right": bool(charging & (0b00000001 if flip else 0b00000010)),
        "charging_case": bool(charging & 0b00000100),
        "model": model,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "raw": raw.decode()
    }


@app.websocket("/ws/airpods")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await get_device()
            data = parse_data(raw)
            await websocket.send_text(json.dumps(data))
            await sleep(UPDATE_DURATION)
    except WebSocketDisconnect:
        print("Cliente desconectado")
