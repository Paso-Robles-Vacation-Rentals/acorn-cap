import asyncio
import subprocess
from pathlib import Path

ILLUMINANCE_PATH = Path("/sys/bus/iio/devices/iio:device0/in_illuminance_input")

# Brightness bounds (percentage)
BRIGHTNESS_MIN = 5
BRIGHTNESS_MAX = 100

LUX_SOFT_OFF = 0
LUX_SOFT_ON = 10

BRIGHTNESS_STEP = .5

POLL_INTERVAL = .25

SMOOTHING = 0.2


def read_ambient_lux() -> int:
    return int(ILLUMINANCE_PATH.read_text().strip())


def get_current_brightness() -> int:
    """Get current brightness percentage using brightnessctl."""
    result = subprocess.run(
        ["brightnessctl", "get"],
        capture_output=True, text=True, check=True
    )
    current = int(result.stdout.strip())

    result_max = subprocess.run(
        ["brightnessctl", "max"],
        capture_output=True, text=True, check=True
    )
    max_val = int(result_max.stdout.strip())

    return round((current / max_val) * 100)


def set_brightness(percent: int):
    """Set brightness using brightnessctl (clamped)."""
    subprocess.run(["brightnessctl", "set", f"{percent}%"])


def map_lux_to_brightness(lux: int) -> int:
    """Map ambient light value to brightness percentage."""
    # Simple linear mapping: adjust these thresholds to taste
    lux_min = 0
    lux_max = 2000
    percent = int((lux - lux_min) / (lux_max - lux_min) * BRIGHTNESS_MAX)
    return max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, percent))


async def handle_screen_brightness():
    current_brightness = get_current_brightness()
    soft_counter = 0
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        lux = read_ambient_lux()
        if current_brightness > 0 and lux <= LUX_SOFT_OFF:
            if soft_counter < 10:
                soft_counter += 1
                continue
            soft_counter = 0
            current_brightness = 0
            set_brightness(current_brightness)
            continue
        if current_brightness == 0 and lux >= LUX_SOFT_ON:
            if soft_counter < 20:
                soft_counter += 1
                continue
            soft_counter = 0
        target = map_lux_to_brightness(lux)

        # Smooth adjustment
        delta = target - current_brightness
        step = max(-BRIGHTNESS_STEP, min(BRIGHTNESS_STEP, int(delta * SMOOTHING)))

        if step != 0:
            current_brightness += step
            set_brightness(current_brightness)
