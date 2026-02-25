import asyncio
import subprocess
from pathlib import Path

ILLUMINANCE_PATH = Path("/sys/bus/iio/devices/iio:device0/in_illuminance_input")

# Brightness bounds (percentage)
BRIGHTNESS_MIN = 5
BRIGHTNESS_MAX = 96000

LUX_SOFT_OFF = 0
LUX_SOFT_ON = 10

MAX_BRIGHTNESS_STEP = 300

MAX_POLL_INTERVAL = 5
MIN_POLL_INTERVAL = .05

SMOOTHING = 0.2


def read_ambient_lux() -> int:
    return int(ILLUMINANCE_PATH.read_text().strip())


def get_current_brightness() -> int:
    """Get current brightness using brightnessctl."""
    result = subprocess.run(
        ["brightnessctl", "get"],
        capture_output=True, text=True, check=True
    )
    return int(result.stdout.strip())


def set_brightness(brightness: int):
    """Set brightness using brightnessctl (clamped)."""
    subprocess.run(["brightnessctl", "set", f"{brightness}"])


def map_lux_to_brightness(lux: int) -> int:
    """Map ambient light value to brightness"""
    # Simple linear mapping: adjust these thresholds to taste
    lux_min = 0
    lux_max = 40
    brightness = int((lux - lux_min) / (lux_max - lux_min) * BRIGHTNESS_MAX)
    return max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, brightness))

def get_poll_time(current_brightness, target_brightness):
    delta = abs(current_brightness - target_brightness)
    poll_time = MIN_POLL_INTERVAL
    if delta > 0:
        poll_time = 1500 / delta
    poll_time = max(min(poll_time, MAX_POLL_INTERVAL), MIN_POLL_INTERVAL)
    return poll_time


async def handle_screen_brightness():
    current_brightness = get_current_brightness()
    soft_counter = 0
    poll_time = 0
    while True:
        await asyncio.sleep(poll_time)
        lux = read_ambient_lux()
        if current_brightness > 0 and lux <= LUX_SOFT_OFF:
            if soft_counter < 5:
                soft_counter += 1
            else:
                poll_time = MAX_POLL_INTERVAL
                soft_counter = 0
                current_brightness = 0
                set_brightness(current_brightness)
                continue
        if current_brightness == 0 and lux >= LUX_SOFT_ON:
            if soft_counter < 5:
                soft_counter += 1
                continue

        if current_brightness == 0 and lux <= LUX_SOFT_OFF:
            continue

        target = map_lux_to_brightness(lux)
        # Smooth adjustment
        poll_time = get_poll_time(current_brightness, target)
        delta = target - current_brightness
        step = max(-MAX_BRIGHTNESS_STEP, min(MAX_BRIGHTNESS_STEP, delta))

        if step != 0:
            current_brightness += step
            set_brightness(current_brightness)

if __name__ == "__main__":
    asyncio.run(handle_screen_brightness())
                                                                      
