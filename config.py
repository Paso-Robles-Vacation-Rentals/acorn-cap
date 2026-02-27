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
class KioskConfig:
    online_url: str

    def __init__(self, table: Table | None = None):
        self.online_url = 'https://pasoroblesvacationrentals.com/'
        if table is not None:
            self.online_url = table.get('online_url', self.online_url)


@dataclass
class AcornCapConfig:
    kiosk: KioskConfig

    def __init__(self):
        path = Path(os.environ.get('ACORN_CAP_CONFIG', DEFAULT_CONFIG_PATH))
        if path.exists():
            self.load(path)
            return
        logger.warning(f"Config file {path} not found. Loading defaults.")
        self.create_default_config()


    def create_default_config(self):
        self.kiosk = KioskConfig()


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

        logger.info(f'Loaded config from {path}')

