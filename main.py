import asyncio

from wifi import handle_wifi_connectivity
from brightness import handle_screen_brightness


async def main():
    tasks = [
        asyncio.create_task(handle_wifi_connectivity()),
        asyncio.create_task(handle_screen_brightness()),
    ]

    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    asyncio.run(main())
