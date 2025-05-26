from __future__ import annotations
from pipedalclient.pedalboard import Pedalboard

import websockets
import json
from typing import Callable, Optional
import asyncio
from events import Event

_message_handlers: dict[str, list[Callable]] = {}
def message_handler(message_type: str):
    def decorator(func):
        if message_type not in _message_handlers:
            _message_handlers[message_type] = []
        _message_handlers[message_type].append(func)
        return func
    return decorator

class PiPedalClient():
    __ws: websockets.ClientConnection
    __client_id: int = -1
    __pedalboard: Optional[Pedalboard] = None
    __on_pedalboard_changed: Event[Pedalboard] = Event()
    __loop: asyncio.AbstractEventLoop

    @property
    def on_pedalboard_changed(self) -> Event[Pedalboard]:
        if self.__on_pedalboard_changed is None:
            self.__on_pedalboard_changed = Event()
        return self.__on_pedalboard_changed

    @property
    def pedalboard(self) -> Optional[Pedalboard]:
        return self.__pedalboard

    @classmethod
    async def create(cls, url: str) -> "PiPedalClient":
        obj = cls()
        obj.__ws = await websockets.connect(url)
        return obj

    async def connect(self) -> None:
        await self.__ws.send(json.dumps([{"message": "hello", "replyTo": 1}]))

        # run receive thread asynchronously
        self.__loop = asyncio.get_event_loop()
        asyncio.create_task(self.__receive_thread())

    @property
    def client_id(self) -> int:
        return self.__client_id

    async def __receive_thread(self) -> None:
        while True:
            try:
                response = await self.__ws.recv()
                root = json.loads(response)
                message_type = root[0].get("message")
                if message_type in _message_handlers:
                    for handler in _message_handlers[message_type]:
                        await handler(self, root)
                elif message_type == "error":
                    print(f"Error: {root[1]}")
                else:
                    print(f"Unhandled message type: {message_type}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

    @message_handler("ehlo")
    async def __onHelloResponse(client: "PiPedalClient", root):
        client.__client_id = int(root[1])
        print(f"Hello response received, clientId: {client.__client_id}")

    @message_handler("onControlChanged")
    async def __onControlChanged(client: "PiPedalClient", root):
        instance = root[1].get("instanceId")
        symbol = root[1].get("symbol")
        value = root[1].get("value")

        if client.pedalboard is not None:
            client.pedalboard.item(instance).control(symbol).value = value
        print(f"Control changed: {symbol} = {value}")

    @message_handler("onPedalboardChanged")
    async def __onPedalboardChanged(client: "PiPedalClient", root):
        pb = Pedalboard(client, root[1]["pedalboard"])
        client.__pedalboard = pb
        client.on_pedalboard_changed(pb)
        print(f"Pedalboard changed.")

    def send_set_control(self, instance_id, symbol, value):
        asyncio.run_coroutine_threadsafe(self.send_set_control_async(instance_id, symbol, value), self.__loop)

    async def send_set_control_async(self, instance_id, symbol, value):
        message = [
            {
                "message": "setControl",
            },
            {
                "clientId": self.__client_id,
                "instanceId": instance_id,
                "symbol": symbol,
                "value": value,
            }
        ]
        print("Sent setControl ", message)
        await self.__ws.send(json.dumps(message))