import asyncio
import subprocess
from pathlib import Path

from config import BrightnessConfig

ILLUMINANCE_PATH = Path("/sys/bus/iio/devices/iio:device0/in_illuminance_input")

SMOOTHING = 1500


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


def map_lux_to_brightness(lux: int, config: BrightnessConfig) -> int:
    """Map ambient light value to brightness"""
    # Simple linear mapping: adjust these thresholds to taste
    lux_min = 0
    lux_max = 40
    brightness = int((lux - lux_min) / (lux_max - lux_min) * config.max_brightness)
    return max(config.min_brightness, min(config.max_brightness, brightness))

def get_poll_time(current_brightness, target_brightness, config: BrightnessConfig):
    delta = abs(current_brightness - target_brightness)
    poll_time = config.min_poll_interval
    if delta > 0:
        poll_time = config.smoothing / delta
    poll_time = max(min(poll_time, config.max_poll_interval), config.min_poll_interval)
    return poll_time


async def handle_screen_brightness(config: BrightnessConfig):
    current_brightness = get_current_brightness()
    soft_counter = 0
    poll_time = 0
    while True:
        await asyncio.sleep(poll_time)
        lux = read_ambient_lux()
        if current_brightness > 0 and lux <= config.lux_soft_off:
            if soft_counter < 5:
                soft_counter += 1
            else:
                poll_time = config.max_poll_time
                soft_counter = 0
                current_brightness = 0
                set_brightness(current_brightness)
                continue
        if current_brightness == 0 and lux >= config.lux_soft_on:
            if soft_counter < 5:
                soft_counter += 1
                continue

        if current_brightness == 0 and lux <= config.lux_soft_off:
            continue

        target = map_lux_to_brightness(lux, config)
        poll_time = get_poll_time(current_brightness, target, config)
        delta = target - current_brightness
        step = max(-config.brightness_step, min(config.brightness_step, delta))

        if step != 0:
            current_brightness += step
            set_brightness(current_brightness)

if __name__ == "__main__":
    asyncio.run(handle_screen_brightness())
                                                                      
