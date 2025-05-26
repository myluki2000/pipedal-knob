from knobs.knob import Knob
from pipedalclient import PiPedalClient
from typing import Optional
import yaml

class KnobManager():
    def __init__(self, pedal_client: PiPedalClient):
        self.pedal_client: PiPedalClient = pedal_client
        self.pedal_client.on_pedalboard_changed.add_listener(lambda pb: self.__init_knobs())

        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
            self.__knob_configs = config["knobs"]
        
        self.__knobs: list[Knob] = []
        self.__init_knobs()
        
    def __init_knobs(self) -> None:
        for knob in self.__knobs:
            knob.close()
        self.__knobs: list[Knob] = []
        for knob_config in self.__knob_configs:
            knob = Knob(
                self,
                display_addr=int(knob_config["display_addr"]),
                rotary_pin1=knob_config["rotary_pin1"],
                rotary_pin2=knob_config["rotary_pin2"],
                push_pin=knob_config["push_pin"]
            )
            self.__knobs.append(knob)
