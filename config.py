from __future__ import annotations

from dataclasses import dataclass
import os
from logging import getLogger
from pathlib import Path

import tomlkit
from tomlkit.items import Table
from tomlkit.exceptions import ParseError

DEFAULT_CONFIG_PATH = Path('/etc/acorn-guide/config.toml')

logger = getLogger(__name__)


@dataclass
class BrightnessConfig:
    min_brightness: int
    max_brightness: int
    lux_soft_on: int
    lux_soft_off: int
    smoothing: int
    brightness_step: int
    max_poll_interval: int
    min_poll_interval: int

    def __init__(self, table: Table | None = None):
        if table:
            self.min_brightness = table.get('min_brightness', 5)
            self.max_brightness = table.get('max_brightness', 96000)
            self.lux_soft_on = table.get('lux_soft_on', 10)
            self.lux_soft_off = table.get('lux_soft_off', 0)
            self.smoothing = table.get('smoothing', 1500)
            self.brightness_step = table.get('brightness_step', 300)
            self.max_poll_interval = table.get('max_poll_interval', 5)
            self.min_poll_interval = table.get('min_poll_interval', .05)
        else:
            self.min_brightness = 5
            self.max_brightness = 96000
            self.smoothing = 1500
            self.lux_soft_on = 10
            self.lux_soft_off = 0
            self.brightness_step = 300
            self.max_poll_interval = 5
            self.min_poll_interval = .05


@dataclass
class KioskConfig:
    online_url: str

    def __init__(self, table: Table | None = None):
        if table:
            self.online_url = table.get('online_url', 'https:/pasoroblesvacationrentals.com/')
        else:
            self.online_url = 'https://pasoroblesvacationrentals.com/'


@dataclass
class AcornCapConfig:
    kiosk: KioskConfig
    brightness: BrightnessConfig

    def __init__(self):
        path = Path(os.environ.get('ACORN_CAP_CONFIG', DEFAULT_CONFIG_PATH))
        if path.exists():
            self.load(path)
            return
        logger.warning(f"Config file {path} not found. Loading defaults.")
        self.create_default_config()


    def create_default_config(self):
        self.kiosk = KioskConfig()
        self.brightness = BrightnessConfig()


    def load(self, path) -> None:
        logger.debug(f'Loading config from {path}')
        try:
            with open(path, 'r') as f:
                doc = tomlkit.load(f)
        except ParseError as e:
            logger.error(f"Invalid config file {path}: {e}")
            logger.error(f"Loading defaults.")
            self.create_default_config()
            return
        except FileNotFoundError:
            logger.error(f"Config file {path} not found. Loading defaults.")
            logger.error(f"Loading defaults.")
            self.create_default_config()
            return

        self.kiosk = KioskConfig(doc.get('kiosk'))
        self.brightness = BrightnessConfig(doc.get('brightness'))

        logger.info(f'Loaded config from {path}')

