import asyncio
from knobs import *
from typing import Optional
from pipedalclient import *

URI = "ws://127.0.0.1/pipedal"




async def main():
    client: Optional[PiPedalClient] = await PiPedalClient.create(URI)
    knob_manager: KnobManager = KnobManager(client)
    
    await client.connect()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())