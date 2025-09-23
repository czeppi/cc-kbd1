from typing import Optional

from virtualkeyboard import IPhysicalKey, KeyName, TimeInMs


class DummyPhysicalKey(IPhysicalKey):

    def __init__(self, name: KeyName):
        self._name = name
        self._pressed_time: TimeInMs | None = None
        self._is_bound = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def pressed_time(self) -> Optional[TimeInMs]:
        return self._pressed_time

    @property
    def is_bound(self) -> bool:
        return self._is_bound

    def set_bound(self, is_bound: bool) -> None:
        self._is_bound = is_bound

    def update(self, time: TimeInMs) -> None:
        pass

    def press(self, time: TimeInMs | None) -> None:
        self._pressed_time = time

    def release(self) -> None:
        self._pressed_time = None
