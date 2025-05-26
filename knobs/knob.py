from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from knobs.knobmanager import KnobManager

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas

from gpiozero import RotaryEncoder, Button

from pipedalclient.pedalboard import *

from PIL import ImageFont, ImageDraw
import util
from enum import Enum
import math
import time

class KnobMode(Enum):
    REGULAR = 0
    SELECT_ITEM = 1
    SELECT_CONTROL = 2

class Knob():

    def __init__(self, knob_manager: "KnobManager", display_addr: int, rotary_pin1: int, rotary_pin2: int, push_pin: int):
        self.__knob_manager = knob_manager

        self.__display_serial: i2c = i2c(port=1, address=display_addr)
        self.__display: ssd1306 = ssd1306(self.__display_serial, rotate=0)

        self.__rotary_encoder: RotaryEncoder = RotaryEncoder(rotary_pin1, rotary_pin2)
        self.__rotary_encoder.when_rotated_clockwise = lambda x: self.__on_rotary_change(x, 1)
        self.__rotary_encoder.when_rotated_counter_clockwise = lambda x: self.__on_rotary_change(x, -1)

        self.__button: Button = Button(pin=push_pin, bounce_time = 0.05)
        self.__button.when_activated = self.__on_button_press
        self.__button.hold_time = 3
        self.__button.when_held = self.__on_button_hold
        
        self.__mode: KnobMode = KnobMode.REGULAR

        if self.__knob_manager.pedal_client.pedalboard is not None:
            self.__selected_pedalboard_item: PedalboardItem = self.__knob_manager.pedal_client.pedalboard.items[0]
            self.__selected_control: PedalboardItemControl = self.__selected_pedalboard_item.controls[0]
            self.__selected_control.on_value_changed.add_listener(self.__on_selected_control_value_changed)
            self.__display_draw_regular()

    @property
    def mode(self) -> KnobMode:
        return self.__mode
    
    @mode.setter
    def mode(self, value: KnobMode) -> None:
        self.__mode = value
        if self.__mode == KnobMode.REGULAR:
            self.__display_draw_regular()
        elif self.__mode == KnobMode.SELECT_ITEM:
            self.__display_draw_select_item()
        elif self.__mode == KnobMode.SELECT_CONTROL:
            self.__display_draw_select_control()

    @property
    def selected_control(self) -> PedalboardItemControl:
        return self.__selected_control
    
    @selected_control.setter
    def selected_control(self, control: PedalboardItemControl) -> None:
        self.__selected_control.on_value_changed.remove_listener(self.__on_selected_control_value_changed)
        self.__selected_control = control
        self.__selected_control.on_value_changed.add_listener(self.__on_selected_control_value_changed)
        
    def __on_selected_control_value_changed(self, value: float):
        self.__display_draw_regular()

    def __on_rotary_change(self, rotary_encoder: RotaryEncoder, direction: int) -> None:
        if self.mode == KnobMode.REGULAR:
            self.__selected_control.value = round(self.__selected_control.value + direction * 0.05, 3)
            self.__display_draw_regular()

        elif self.mode == KnobMode.SELECT_ITEM:
            new_item: Optional[PedalboardItem] = None
            if direction > 0:
                new_item = self.__selected_pedalboard_item.pedalboard.next_item(self.__selected_pedalboard_item)
            elif direction < 0:
                new_item = self.__selected_pedalboard_item.pedalboard.previous_item(self.__selected_pedalboard_item)
            if new_item is not None:
                self.select_item_animated(new_item)
                self.selected_control = self.__selected_pedalboard_item.controls[0]

        elif self.mode == KnobMode.SELECT_CONTROL:
            new_control: Optional[PedalboardItemControl] = None
            if direction > 0:
                new_control = self.__selected_pedalboard_item.next_control(self.__selected_control)
            elif direction < 0:
                new_control = self.__selected_pedalboard_item.previous_control(self.__selected_control)
            if new_control is not None:
                self.select_control_animated(new_control)
        

    def __on_button_press(self, button: Button) -> None:
        if self.mode == KnobMode.REGULAR:
            pass
        elif self.mode == KnobMode.SELECT_ITEM:
            self.mode = KnobMode.SELECT_CONTROL
        elif self.mode == KnobMode.SELECT_CONTROL:
            self.mode = KnobMode.REGULAR

    def __on_button_hold(self, button: Button) -> None:
        print("hold")
        if self.mode == KnobMode.REGULAR:
            self.mode = KnobMode.SELECT_ITEM
    
    def __display_draw_regular(self):
        with canvas(self.__display) as draw:
            draw.text((64, 0), self.__selected_pedalboard_item.plugin_name, fill="white", font=ImageFont.truetype(util.FONT_PATH_SANS, 10), anchor="ma")
            draw.text((64, 10), self.__selected_control.symbol, fill="white", font=ImageFont.truetype(util.FONT_PATH_SANS, 20), anchor="ma")
            draw.text((64, 64), str(self.__selected_control.value), fill="white", font=ImageFont.truetype(util.FONT_PATH_SANS, 32), anchor="md")

    def __display_draw_select_item(self):
        all_items = self.__selected_pedalboard_item.pedalboard.items
        self.__draw_circle_menu([x.plugin_name for x in all_items], all_items.index(self.__selected_pedalboard_item))

    def select_item_animated(self, new_item: PedalboardItem) -> None:
        all_items = self.__selected_pedalboard_item.pedalboard.items

        ANIM_FRAMES = 3
        for i in range(ANIM_FRAMES):
            if all_items.index(new_item) - all_items.index(self.__selected_pedalboard_item) > 0:
                # forward
                self.__draw_circle_menu([x.plugin_name for x in all_items], all_items.index(new_item) - 1 + i / ANIM_FRAMES)
            elif all_items.index(new_item) - all_items.index(self.__selected_pedalboard_item) < 0:
                # backward
                self.__draw_circle_menu([x.plugin_name for x in all_items], all_items.index(new_item) + 1 - i / ANIM_FRAMES)
            else:
                break
        self.__draw_circle_menu([x.plugin_name for x in all_items], all_items.index(new_item))
        self.__selected_pedalboard_item = new_item

    def __display_draw_select_control(self):
        all_controls = self.__selected_pedalboard_item.controls
        self.__draw_circle_menu([x.symbol for x in all_controls], all_controls.index(self.__selected_control))

    def select_control_animated(self, new_control: PedalboardItemControl) -> None:
        all_controls = self.__selected_pedalboard_item.controls

        ANIM_FRAMES = 3
        for i in range(ANIM_FRAMES):
            if all_controls.index(new_control) - all_controls.index(self.__selected_control) > 0:
                # forward
                self.__draw_circle_menu([x.symbol for x in all_controls], all_controls.index(new_control) - 1 + i / ANIM_FRAMES)
            elif all_controls.index(new_control) - all_controls.index(self.__selected_control) < 0:
                # backward
                self.__draw_circle_menu([x.symbol for x in all_controls], all_controls.index(new_control) + 1 - i / ANIM_FRAMES)
            else:
                break
        self.__draw_circle_menu([x.symbol for x in all_controls], all_controls.index(new_control))
        self.selected_control = new_control

    def __draw_circle_menu(self, items: list[str], selected_item: float) -> None:
        with canvas(self.__display) as draw:
            draw.line((13, 32, 16, 32), fill="white")

            DISPLAYED_ITEMS = 7
            decimals = selected_item % 1
            index_offset = int(selected_item) - DISPLAYED_ITEMS // 2
            for i in range(0, DISPLAYED_ITEMS):
                if index_offset + i < 0 or index_offset + i >= len(items):
                    continue

                alpha = -math.pi / 2 + ((i + 1 - decimals) * math.pi / (DISPLAYED_ITEMS + 1))
                x = -20 + math.cos(alpha) * 40
                y = 32 + math.sin(alpha) * 40

                font_size = -8 * math.pow(alpha, 2) + 12
                if font_size < 0:
                    continue
                draw.text((x, y), items[index_offset + i], fill="white", font=ImageFont.truetype(util.FONT_PATH_SANS, font_size), anchor="lm")

    def close(self):
        self.__rotary_encoder.close()
        self.__button.close()

    def __del__(self):
        self.close()