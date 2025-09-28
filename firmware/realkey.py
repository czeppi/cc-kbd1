from base import VirtualKeyName, TimeInMs, KeyName

try:
    from typing import Optional
except ImportError:
    pass

from digitalio import DigitalInOut, Direction, Pull

from virtualkeyboard import IPhysicalKey


class RealPhysicalKey(IPhysicalKey):
    pressed_key = False
    should_stop = False

    def __init__(self, name: KeyName, gp_index: int):
        self._name = name
        self._inout = DigitalInOut(gp_index)  # any GP pin can used
        self._inout.direction = Direction.INPUT
        self._inout.pull = Pull.UP

        self._press_time: Optional[TimeInMs] = None
        self._bound_vkey_name: VirtualKeyName | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def press_time(self) -> Optional[TimeInMs]:
        return self._press_time

    @property
    def bound_vkey_name(self) -> VirtualKeyName | None:
        return self._bound_vkey_name

    def set_bound_by_vkey(self, vkey_name: VirtualKeyName | None) -> None:
        self._bound_vkey_name = vkey_name

    def update(self, time: TimeInMs) -> None:
        if self._inout.value:
            self._press_time = None  # not pressed
            if RealPhysicalKey.pressed_key:
                RealPhysicalKey.should_stop = True
                #print('begin stopping...')
        else:
            self._press_time = time  # pressed
            RealPhysicalKey.pressed_key = True
