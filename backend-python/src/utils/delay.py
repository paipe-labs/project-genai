import asyncio


async def delay(delay_ms: int):
    await asyncio.sleep(delay_ms / 1000)
