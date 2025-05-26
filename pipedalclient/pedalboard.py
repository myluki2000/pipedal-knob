from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pipedalclient import PiPedalClient

from typing import Optional
from events import Event
import asyncio

class Pedalboard():
    def __init__(self, pipedal_client: PiPedalClient, json_root: dict):
        self.client: PiPedalClient = pipedal_client
        self.name = json_root["name"]
        self.__items: list[PedalboardItem] = []
        for item in json_root["items"]:
            self.__items.append(PedalboardItem(self, item))

    def item(self, instanceId: int) -> PedalboardItem:
        for item in self.__items:
            if item.instance_id == instanceId:
                return item
        raise KeyError(f"Pedalboard item with instanceId {instanceId} not found")
    
    def next_item(self, item: PedalboardItem) -> Optional[PedalboardItem]:
        for i in range(len(self.__items)):
            if self.__items[i] == item:
                if i + 1 < len(self.__items):
                    return self.__items[i + 1]
                else:
                    return None
        raise KeyError(f"Pedalboard item {item.instance_id} not found")
    
    def previous_item(self, item: PedalboardItem) -> Optional[PedalboardItem]:
        for i in range(len(self.__items)):
            if self.__items[i] == item:
                if i - 1 >= 0:
                    return self.__items[i - 1]
                else:
                    return None
        raise KeyError(f"Pedalboard item {item.instance_id} not found")
    
    @property
    def items(self) -> list[PedalboardItem]:
        return self.__items
        

class PedalboardItem():
    def __init__(self, pedalboard: Pedalboard, json_root: dict):
        self.pedalboard: Pedalboard = pedalboard
        self.instance_id: int = json_root["instanceId"]
        self.uri: str = json_root["uri"]
        self.is_enabled: bool = json_root["isEnabled"]
        self.plugin_name: str = json_root["pluginName"]

        self.__controls: list[PedalboardItemControl] = []
        for control in json_root["controlValues"]:
            self.__controls.append(PedalboardItemControl(self, control))

    def control(self, symbol: str) -> PedalboardItemControl:
        for control in self.__controls:
            if control.symbol == symbol:
                return control
        raise KeyError(f"Pedalboard item control with symbol {symbol} not found")
    
    def next_control(self, control: PedalboardItemControl) -> Optional[PedalboardItemControl]:
        for i in range(len(self.__controls)):
            if self.__controls[i] == control:
                if i + 1 < len(self.__controls):
                    return self.__controls[i + 1]
                else:
                    return None
        raise KeyError(f"Pedalboard item control {control.symbol} not found")
    
    def previous_control(self, control: PedalboardItemControl) -> Optional[PedalboardItemControl]:
        for i in range(len(self.__controls)):
            if self.__controls[i] == control:
                if i - 1 >= 0:
                    return self.__controls[i - 1]
                else:
                    return None
        raise KeyError(f"Pedalboard item control {control.symbol} not found")
    
    @property
    def controls(self) -> list[PedalboardItemControl]:
        return self.__controls
    
    def send_set_control(self, symbol, value):
        self.pedalboard.client.send_set_control(self.instance_id, symbol, value)


class PedalboardItemControl():
    def __init__(self, pedalboard_item: PedalboardItem, json_root: dict):
        self.__pedalboard_item: PedalboardItem = pedalboard_item
        self.symbol: str = json_root["key"]
        self.__value: float = json_root["value"]
        self.__on_value_changed: Event[float] = Event()

    @property
    def on_value_changed(self) -> Event[float]:
        return self.__on_value_changed

    @property
    def value(self) -> float:
        return self.__value
    
    @value.setter
    def value(self, value: float) -> None:
        if self.__value != value:
            self.__value = value
            self.__on_value_changed(value)
            self.send_set_control(value)

    def send_set_control(self, value):
        self.__pedalboard_item.send_set_control(self.symbol, value)
        