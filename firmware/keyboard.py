from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Iterator

from IPython.utils.contexts import preserve_keys

Handler = Callable[[], None]
TimeInMs = float


class IClock:

    @property
    def value(self) -> float:  # in ms
        raise NotImplementedError()



class IButton:

    def is_pressed(self) -> bool:
        raise NotImplementedError()


class DigitalIOButton(IButton):

    def __init__(self, gp_index: int):
        self._inout = DigitalInOut(gp_index)  # any GP pin can used
        self._inout.direction = Direction.INPUT
        self._inout.pull = Pull.UP

    def is_pressed(self) -> bool:
        return self._inout.value


class IAction:

    def do(self) -> None:
        raise NotImplementedError()
       
       
class SendKeyAction(IAction):

    def __init__(self, key_code):  # p.e. Keycode.A
        self._key_code = key_code

    def do(self) -> None:
        kbd.send(self._key_code)
    
    
class Macro(IAction):
    pass
    
    
class Layer:
    pass
    

class SplitSide:
    LEFT = 1
    RIGHT = 2


class KeyState(Enum):
    RELEASED = 1
    PARTLY_PRESSED = 2
    PRESSED = 3
    WAIT_FOR_RELEASE = 4

#    PENDING = 1
#    COMPLETE = 2
#    TIME_OUT = 3

class Key:

    def __init__(self, name: str, action: IAction):
        self._name = name  # must be unique
        self._action = action
        self._state = KeyState.RELEASED
        self._press_time: TimeInMs | None = None
        self._depending_keys: List[Key] = []   # p.e. ComboKey => List[PhysicalKey]
        self._depends_on_keys: List[Key] = []  # p.e. PhysicalKey => List[ComboKey]

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> KeyState:
        return self._state

    @property
    def is_pending(self) -> bool:
        pass

    @property
    def is_pressed(self) -> bool:
        return self._is_pressed

    @property
    def is_ready_for_fire(self) -> bool:
        pass

    @property
    def is_released(self) -> bool:
        pass

    def update(self, time: TimeInMs) -> None:
        raise NotImplementedError()

    def can_fire(self) -> bool:
        return self._is_pressed and all(key.is_released for key in self._depends_on_keys)

    def fire(self) -> None:
        self._action.do()
        self._is_pressed = False
        for key in self._depending_keys:
            self._is_pressed = False

        for key in self._depends_on_keys:
            # ???

        
class PhysicalKey(Key):

    def __init__(self, name: str, side: SplitSide, button: IButton, action: IAction):
        """ gp_index: p.e. board.GP16
        """
        super().__init__(name=name, action=action)
        self._side = side
        self._button = button
        self._is_pressed = button.is_pressed()

    @property
    def side(self) -> SplitSide:
        return self._side
        
    def update(self, time: TimeInMs) -> None:
        self._state = self._calc_new_state()

    def _calc_new_state(self) -> KeyState:
        """
                            button            button
                            pressed           released
          --------------------------------------------
          RELEASED          PRESSED           RELEASED
          PRESSED           PRESSED           RELEASED
          WAIT_FOR_RELEASE  WAIT_FOR_RELEASE  RELEASED
        """
        if self._button.is_pressed():
            if self._state == KeyState.RELEASED:
                return KeyState.PRESSED
        else:
            return KeyState.RELEASED

    def fire(self) -> None:
        self._action.do()


class ComboKey(Key):   # todo: -> VirtualKey
    COMBO_TERM = 50  # ms

    def __init__(self, name: str, physical_keys: List[PhysicalKey], action: IAction):
        assert len(physical_keys) > 0
        assert all(key.side == physical_keys[0].side for key in physical_keys[1:])

        super().__init__(name=name, action=action)
        self._physical_keys = physical_keys

    def update(self, time: TimeInMs) -> None:
        self._state = self._calc_new_state()

    def _calc_new_state(self) -> KeyState:
        state_counter = Counter()
        for key in self._physical_keys:
            state_counter[key.state] += 1

        if state_counter[KeyState.WAIT_FOR_RELEASE] > 0:
            return KeyState.WAIT_FOR_RELEASE

        num_wait = state_counter[KeyState.WAIT_FOR_RELEASE]
        num_partly = state_counter[KeyState.PARTLY_PRESSED]
        num_pressed = state_counter[KeyState.PRESSED]
        num_released = state_counter[KeyState.RELEASED]

        if num_wait > 0:
            return KeyState.WAIT_FOR_RELEASE

        sorted_pressed_times = self._calc_sorted_pressed_times()
        if max_time_gap > self.COMBO_TERM:
            return KeyState.OUT_OF_TIME

        if num_partly > 0 or num_pressed > 0 and num_released > 0:
            return KeyState.PARTLY_PRESSED

        if num_pressed > 0:
            return KeyState.PRESSED

        assert num_released == len(self._physical_keys)
        return KeyState.RELEASED


class TapHoldKey(Key):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, name: str, source_key: Key, action: IAction):
        super().__init__(name=name, action=action)
        self._source_key = source_key
        self._source_key_pressed_time: TimeInMs | None = None
        self._other_key: Key | None = None
        self._other_key_pressed_time: TimeInMs | None = None

    def on_key_pressed(self, key: Key, time: TimeInMs) -> None:
        if key.name == self._source_key.name:
            self._on_source_key_pressed(time)
        else:
            self._on_other_key_pressed(other_key=key, time=time)

    def _on_source_key_pressed(self, time: TimeInMs) -> None:
        self._source_key_pressed_time = time

    def _on_other_key_pressed(self, other_key: Key, time: TimeInMs) -> None:
        if self._source_key_pressed_time is None:
            return

        dt = time - self._source_key_pressed_time
        if dt < self.TAP_HOLD_TERM:
            self._other_key = other_key
            self._other_key_pressed_time = time
            return

        self._do_hold_action(other_key)

    def on_key_released(self, key: Key | None, time: TimeInMs) -> None:
        if key.name == self._source_key.name:
            self._on_source_key_released(time)
        else:
            self._on_other_key_released(other_key=key, time=time)

    def _on_source_key_released(self, time: TimeInMs) -> None:
        dt = time - self._source_key_pressed_time
        if dt < self.TAP_HOLD_TERM:
            self._do_tap_action()

        self._source_key_pressed_time = None

    def _do_tap_action(self) -> None:
        self._send_key_code(self._source_key)
        if self._other_key:
            self._send_key_code(self._other_key)

        self._source_key_pressed_time = None
        self._other_key_pressed_time = None
        self._other_key = None

    def _on_other_key_released(self, other_key: Key, time: TimeInMs) -> None:
        if self._source_key_pressed_time is None:
            return

        dt = time - self._source_key_pressed_time
        if dt < self.TAP_HOLD_TERM:
            self._do_hold_action(other_key)

    def _do_hold_action(self, other_key: Key) -> None:
        raise NotImplementedError()




class ModKey(TapHoldKey):
    
    def __init__(self, name: str, source_key: Key, key2: Key, action: IAction):
        super().__init__(name=name, source_key=source_key, action=action)
        self._key2 = key2

    def _do_hold_action(self, other_key: Key) -> None:
        self._send_key_code(self._modifier, other_key)


class LayerKey(TapHoldKey):

    def __init__(self, name: str, source_key: Key, key2: Key, action: IAction):
        super().__init__(name=name, source_key=source_key, action=action)

    def _do_hold_action(self, other_key: Key) -> None:
        new_key = self._layer.get(other_key)
        self._send_key_code(new_key)


@dataclass
class EventData:
    time: TimeInMs
    key: Key
    pressed: bool  # or False -> release


class Keyboard:

    def __init__(self, clock: IClock):
        self._clock = clock
        self._physical_keys: List[PhysicalKey] = []
        self._combo_keys: List[ComboKey] = []
        self._mod_keys: List[ModKey] = []
        self._pending_events: List[EventData] = []

    def add_physical_key(self, button: IButton, action: IAction) -> PhysicalKey:
        key = PhysicalKey(button=button, action=action)
        self._physical_keys.append(key)
        return key

    def add_combo_key(self, physical_keys: List[PhysicalKey], action: IAction) -> ComboKey:
        key = ComboKey(physical_keys=physical_keys, action=action)
        self._combo_keys.append(key)
        return key

    def add_mod_key(self, key1: Key, key2: Key, action: IAction) -> ModKey:
        key = ModKey(key1=key1, key2=key2, action=action)
        self._mod_keys.append(key)
        return key

    def add_layer_key(self, key1: Key, key2: Key, action: IAction) -> ModKey:
        key = ModKey(key1=key1, key2=key2, action=action)
        self._mod_keys.append(key)
        return key

    def _iter_keys_forward(self) -> Iterator[Key]:
        yield from self._physical_keys
        yield from self._combo2_keys
        yield from self._combo3_keys
        yield from self._tap_hold_keys

    def _iter_keys_backward(self) -> Iterator[Key]:
        yield from self._tap_hold_keys
        yield from self._combo3_keys
        yield from self._combo2_keys
        yield from self._physical_keys

    def update(self) -> None:
        for key in self._iter_keys_forward():
            key.update()

        for key in self._iter_keys_backward():
            if key.can_fire():
                key.fire()

    def _process_combo_keys_in_pending_event(self, now: TimeInMs) -> None:
        """ combine pending_events
        """
        for event1 in self._pending_events:
            event1.pending = False

        for combo_key in self._combo_keys:
            state = combo_key.calc_state(self._pending_events, now)
            if state == KeyState.PENDING:
                for key2 in combo_key.sub_keys:
                    key2.pending = True
            elif state == KeyState.COMPLETE:
                combo_key.squash_pending(self._pending_events)
                combo_key.do_action()
            else:
                assert state == KeyState.TIME_OUT
                pass

    def _process_mod_keys_in_pending_event(self) -> None:
        pass


class KeyboardState:
    pressed_layer_key: LayerKey | None
    pressed_mod_keys: List[ModKey]
