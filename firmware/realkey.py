try:
    from typing import Optional
except ImportError:
    pass

from digitalio import DigitalInOut, Direction, Pull

from virtualkeyboard import IPhysicalKey, KeyName, TimeInMs


class RealPhysicalKey(IPhysicalKey):
    pressed_key = False
    should_stop = False

    def __init__(self, name: KeyName, gp_index: int):
        self._name = name
        self._inout = DigitalInOut(gp_index)  # any GP pin can used
        self._inout.direction = Direction.INPUT
        self._inout.pull = Pull.UP

        self._press_time: Optional[TimeInMs] = None
        self._is_bound = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def press_time(self) -> Optional[TimeInMs]:
        return self._press_time

    @property
    def is_bound(self) -> bool:
        return self._is_bound

    def set_bound(self, is_bound: bool) -> None:
        self._is_bound = is_bound

    def update(self, time: TimeInMs) -> None:
        if self._inout.value:
            self._press_time = None  # not pressed
            if RealPhysicalKey.pressed_key:
                RealPhysicalKey.should_stop = True
                print('begin stopping...')
        else:
            self._press_time = time  # pressed
            RealPhysicalKey.pressed_key = True
