import time
import subprocess
import httpx

WIFI_STATUS_URL = "http://localhost:8000/wifi/status"

DISCONNECTED_URL = "http://localhost:8001"
CONNECTED_URL = "https://guests.escapia.com/login?property_manager_id=1305"

POLL_INTERVAL_OFFLINE = 5  # seconds
POLL_INTERVAL_ONLINE = 60

class KioskError(Exception):
    pass


def get_wifi_status() -> dict:
    try:
        resp = httpx.get(WIFI_STATUS_URL, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to get wifi status: {e}")
        raise KioskError("Failed to get wifi status")


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
        print(f"[ERROR] Failed to get kiosk url: {e.stderr}")
        raise KioskError("Failed to get kiosk url")


def set_kiosk_url(url):
    try:
        print(f"[ACTION] Setting kiosk url → {url}")
        subprocess.run(
            ["sudo", "snap", "set", "wpe-webkit-mir-kiosk", f"url={url}"],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to set kiosk url: {e.stderr}")


def main():
    print("[INFO] Kiosk connectivity watcher started")

    last_status = get_wifi_status()
    poll_interval = POLL_INTERVAL_OFFLINE
    while last_status is None:
        time.sleep(1)
        try:
            last_status = get_wifi_status()
        except KioskError:
            continue
    if last_status["connected"]:
        print(f"[STATE] WiFi connected to {last_status['ssid']}")
        set_kiosk_url(CONNECTED_URL)
    else:
        print("[STATE] WiFi disconnected")
        set_kiosk_url(DISCONNECTED_URL)
    while True:
        current_status = get_wifi_status()
        if last_status == current_status:
            time.sleep(poll_interval)
            continue
        last_status = current_status
        if last_status["connected"]:
            print(f"[STATE] WiFi connected to {current_status['ssid']}")
            set_kiosk_url(CONNECTED_URL)
            poll_interval = POLL_INTERVAL_ONLINE
        else:
            print("[STATE] WiFi disconnected")
            set_kiosk_url(DISCONNECTED_URL)
            poll_interval = POLL_INTERVAL_OFFLINE
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
