import asyncio
import subprocess

import httpx

from config import KioskConfig


WIFI_STATUS_URL = "http://localhost:8000/wifi/status"
DISCONNECTED_URL = "http://localhost:8000"
POLL_INTERVAL_OFFLINE = 5  # seconds
POLL_INTERVAL_ONLINE = 60


class KioskError(Exception):
    pass


def get_wifi_status() -> dict:
    try:
        resp = httpx.get(WIFI_STATUS_URL, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise KioskError(f"Failed to get wifi status: {e}")


def get_current_kiosk_url() -> str:
    try:
        result = subprocess.run(
            ["sudo", "snap", "get", "wpe-webkit-mir-kiosk", "url"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise KioskError(f"Failed to get current kiosk url: {e.stderr}")


def set_kiosk_url(url):
    try:
        print(f"[ACTION] Setting kiosk url → {url}")
        subprocess.run(
            ["sudo", "snap", "set", "wpe-webkit-mir-kiosk", f"url={url}"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print("[ERROR] Failed to set kiosk url")


async def handle_kiosk(config: KioskConfig):
    is_online = None
    poll_interval = 1

    while is_online is None:
        try:
            is_online = get_wifi_status().get("connected", None)
        except KioskError:
            await asyncio.sleep(poll_interval)
    print("[INFO] Kiosk connectivity watcher started")
    if is_online:
        print(f"[STATE] WiFi connected")
        set_kiosk_url(config.online_url)
        poll_interval = POLL_INTERVAL_ONLINE
    else:
        print("[STATE] WiFi disconnected")
        set_kiosk_url(DISCONNECTED_URL)
    while True:
        current_status = get_wifi_status().get("connected", None)
        if current_status == is_online:
            await asyncio.sleep(poll_interval)
            continue
        is_online = current_status
        if is_online:
            print(f"[STATE] WiFi connected")
            set_kiosk_url(config.online_url)
            poll_interval = POLL_INTERVAL_ONLINE
        else:
            print("[STATE] WiFi disconnected")
            set_kiosk_url(DISCONNECTED_URL)
            poll_interval = POLL_INTERVAL_OFFLINE
        await asyncio.sleep(poll_interval)
