from base import VirtualKeyName, TimeInMs, KeyName

try:
    from typing import Optional
except ImportError:
    pass

from virtualkeyboard import IPhysicalKey


class DummyPhysicalKey(IPhysicalKey):

    def __init__(self, name: KeyName):
        self._name = name
        self._pressed_time: TimeInMs | None = None
        self._bound_vkey_name: VirtualKeyName | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def press_time(self) -> Optional[TimeInMs]:
        return self._pressed_time

    @property
    def bound_vkey_name(self) -> VirtualKeyName | None:
        return self._bound_vkey_name

    def set_bound_by_vkey(self, vkey_name: VirtualKeyName | None) -> None:
        self._bound_vkey_name = vkey_name

    def update(self, time: TimeInMs) -> None:
        pass

    def press(self, time: TimeInMs | None) -> None:
        self._pressed_time = time

    def release(self) -> None:
        self._pressed_time = None
