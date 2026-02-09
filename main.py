import time
import subprocess
import httpx

WIFI_STATUS_URL = "http://localhost:8000/wifi/status"

DISCONNECTED_URL = "http://localhost:8001"
CONNECTED_URL = "https://guests.escapia.com/login?property_manager_id=1305"

POLL_INTERVAL = 5  # seconds


def get_wifi_status():
    try:
        resp = httpx.get(WIFI_STATUS_URL, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to get wifi status: {e}")
        return None


def get_current_kiosk_url():
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
        return None


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

    while True:
        status = get_wifi_status()
        if not status:
            time.sleep(POLL_INTERVAL)
            continue

        connected = status.get("connected")
        ssid = status.get("ssid")

        current_url = get_current_kiosk_url()
        if current_url is None:
            time.sleep(POLL_INTERVAL)
            continue

        if not connected:
            print("[STATE] WiFi disconnected")
            if current_url != DISCONNECTED_URL:
                set_kiosk_url(DISCONNECTED_URL)
        else:
            print(f"[STATE] WiFi connected (SSID={ssid})")
            if current_url != CONNECTED_URL:
                set_kiosk_url(CONNECTED_URL)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
