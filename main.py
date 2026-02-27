import asyncio

from config import AcornCapConfig
from kiosk import handle_kiosk
from brightness import handle_screen_brightness


async def main():
    config = AcornCapConfig()
    tasks = [
        asyncio.create_task(handle_kiosk(config.kiosk)),
        asyncio.create_task(handle_screen_brightness()),
    ]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    asyncio.run(main())
