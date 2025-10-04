from __future__ import annotations

from base import TimeInMs, KeyCode, VirtualKeySerial, PhysicalKeySerial
from keyboardhalf import VKeyPressEvent

try:
    from typing import Iterator
except ImportError:
    pass


class KeyCmdKind:  # enum
    RELEASE = 0
    PRESS = 1
    SEND = 2


KeyCmdKindValue = int


class KeyCmd:
    def __init__(self, kind: KeyCmdKindValue, key_code: KeyCode):
        self.kind = kind
        self.key_code = key_code

    def __str__(self) -> str:
        if self.kind == KeyCmdKind.PRESS:
            return f'press({self.key_code})'
        elif self.kind == KeyCmdKind.RELEASE:
            return f'release({self.key_code})'
        else:
            return f'???({self.key_code})'

    def __repr__(self):
        return str(self)

    def __eq__(self, other: KeyCmd) -> bool:
        return self.kind == other.kind and self.key_code == other.key_code

    def __ne__(self, other: KeyCmd) -> bool:
        return not self == other


KeySequence = list  # list[KeyCmd]


class KeyReaction:  # KeySetting?
    def __init__(self, on_press_key_sequence: KeySequence, on_release_key_sequence: KeySequence):
        self.on_press_key_sequence = on_press_key_sequence
        self.on_release_key_sequence = on_release_key_sequence


Layer = dict  # dict[VirtualKeySerial, KeyReaction]


class VirtualKey:

    def __init__(self, serial: VirtualKeySerial):
        # public
        self.serial = serial
        self.last_press_time: TimeInMs = -1


class SimpleKey(VirtualKey):

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class TapHoldKey(VirtualKey):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class ModKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, mod_key_code: KeyCode):
        super().__init__(serial=serial)
        self._mod_key_code = mod_key_code

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code


class LayerKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, layer: Layer):
        super().__init__(serial=serial)

        # public
        self.layer = layer


class VirtualKeyboard:

    def __init__(self, simple_keys: list[SimpleKey], mod_keys: list[ModKey], layer_keys: list[LayerKey],
                 default_layer: Layer):
        self._simple_keys = simple_keys
        self._mod_keys = mod_keys
        self._layer_keys = layer_keys
        self._all_keys = {key.serial: key for key in simple_keys + mod_keys + layer_keys}
        self._default_layer = default_layer

        self._cur_layer = default_layer
        self._undecided_tap_hold_keys: list[TapHoldKey] = []
        self._deferred_simple_keys: list[SimpleKey] = []  # wait for Tap/Hold decision
        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, vkey_events: list[VKeyPressEvent]) -> Iterator[KeyCmd]:
        if len(vkey_events) == 0 and (self._next_decision_time is None or self._next_decision_time > time):
            return  # too early

        yield from self._update_by_time(time)

        for vkey_event in self._sorted_vkey_events(vkey_events):
            yield from self._update_vkey_event(time, vkey_event)

        self._next_decision_time = min((vkey.last_press_time + TapHoldKey.TAP_HOLD_TERM
                                        for vkey in self._undecided_tap_hold_keys),
                                        default=None)

    def _sorted_vkey_events(self, vkey_events: list[VKeyPressEvent]) -> Iterator[VKeyPressEvent]:
        yield from vkey_events   # todo: implement it correct

    def _update_by_time(self, time: TimeInMs) -> Iterator[KeyCmd]:
        """
            tap/hold: undecided -> hold
            simple: deferred -> press
        """
        # tap/hold: undecided -> hold
        tap_hold_key_press_times: list[TimeInMs] = []
        tap_hold_keys_to_remove: list[TapHoldKey] = []

        for tap_hold_key in self._undecided_tap_hold_keys:
            if time - tap_hold_key.last_press_time >= TapHoldKey.TAP_HOLD_TERM:
                yield from self._on_begin_holding_reaction(tap_hold_key)
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)
                tap_hold_keys_to_remove.append(tap_hold_key)

        for tap_hold_key in tap_hold_keys_to_remove:
            self._undecided_tap_hold_keys.remove(tap_hold_key)

        # simple: deferred -> press
        if len(tap_hold_key_press_times) > 0:
            oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)
            simple_keys_to_remove: list[SimpleKey] = []

            for simple_key in self._deferred_simple_keys:
                if simple_key.last_press_time > oldest_tap_hold_key_press_time:
                    reaction = self._cur_layer.get(simple_key.serial)  # for simplifying, take current layer
                    if reaction:
                        yield from reaction.on_press_key_sequence
                    simple_keys_to_remove.append(simple_key)

            for simple_key in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key)

    def _update_vkey_event(self, time: TimeInMs, vkey_event: VKeyPressEvent) -> Iterator[KeyCmd]:
        vkey_serial = vkey_event.vkey_serial
        vkey = self._all_keys[vkey_serial]

        if isinstance(vkey, TapHoldKey):
            if vkey_event.pressed:
                self._on_begin_press_tap_hold_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_tap_hold_key(vkey)

        elif isinstance(vkey, SimpleKey):
            if vkey_event.pressed:
                yield from self._on_begin_press_simple_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_simple_key(vkey)

    def _on_begin_press_tap_hold_key(self, tap_hold_key: TapHoldKey) -> None:
        """
            tap/hold: inactive -> undecided
        """
        self._undecided_tap_hold_keys.append(tap_hold_key)

    def _on_end_press_tap_hold_key(self, tap_hold_key: TapHoldKey) -> Iterator[KeyCmd]:
        """
            tap/hold: undecided -> tap (press + release) + simple: deferred -> press
                      hold -> inactive
        """
        if tap_hold_key in self._undecided_tap_hold_keys:
            # tap/hold: tap (press + release)
            reaction = self._cur_layer.get(tap_hold_key.serial)  # for simplifying, take current layer
            if reaction:
                yield from reaction.on_press_key_sequence
                yield from reaction.on_release_key_sequence

            self._undecided_tap_hold_keys.remove(tap_hold_key)

            # simple: deferred -> press
            simple_keys_to_remove: list[SimpleKey] = []

            for simple_key in self._deferred_simple_keys:
                if simple_key.last_press_time > tap_hold_key.last_press_time:
                    # simple: -> press
                    reaction = self._cur_layer.get(simple_key.serial)  # for simplifying, take current layer
                    if reaction:
                        yield from reaction.on_press_key_sequence
                    simple_keys_to_remove.append(simple_key)

            for simple_key in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key)

        else:  # was hold
            # tap/hold: hold -> inactive
            yield from self._on_end_holding_reaction(tap_hold_key)

    def _on_begin_press_simple_key(self, simple_key: SimpleKey) -> Iterator[KeyCmd]:
        """
             simple: inactive -> press or deferred
        """
        if len(self._undecided_tap_hold_keys) > 0:
            # simple: -> deferred
            self._deferred_simple_keys.append(simple_key)
        else:
            # simple: -> press
            reaction = self._cur_layer.get(simple_key.serial)  # for simplifying, take current layer
            if reaction:
                yield from reaction.on_press_key_sequence

    def _on_end_press_simple_key(self, simple_key: SimpleKey) -> Iterator[KeyCmd]:
        """
            tap/hold: undecided -> hold   # Permissive Hold (s. https://docs.qmk.fm/tap_hold)
            simple: deferred -> press + release
                    pressed -> release
        """
        # tap/hold: undecided -> hold
        tap_hold_key_press_times: list[TimeInMs] = []
        tap_hold_keys_to_remove: list[TapHoldKey] = []

        for tap_hold_key in self._undecided_tap_hold_keys:
            if tap_hold_key.last_press_time < simple_key.last_press_time:
                yield from self._on_begin_holding_reaction(tap_hold_key)
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)
                tap_hold_keys_to_remove.append(tap_hold_key)

        for tap_hold_key in tap_hold_keys_to_remove:
            self._undecided_tap_hold_keys.remove(tap_hold_key)

        # other simples: deferred -> press (cause tap/hold is decided now)
        if len(tap_hold_key_press_times) > 0:
            oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)
            simple_keys_to_remove: list[SimpleKey] = []

            for simple_key2 in self._deferred_simple_keys:
                if simple_key2.serial == simple_key.serial:
                    continue  # this case will be later considered

                if simple_key2.last_press_time > oldest_tap_hold_key_press_time:
                    # simple: -> press
                    reaction = self._cur_layer.get(simple_key2.serial)  # for simplifying, take current layer
                    if reaction:
                        yield from reaction.on_press_key_sequence
                    simple_keys_to_remove.append(simple_key2)

            for simple_key2 in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key2)

        # this simple:
        reaction = self._cur_layer.get(simple_key.serial)  # for simplifying, take current layer

        if simple_key in self._deferred_simple_keys:
            # simple: deferred -> press + release
            if reaction:
                yield from reaction.on_press_key_sequence
                yield from reaction.on_release_key_sequence

            self._deferred_simple_keys.remove(simple_key)
        else:
            # simple: pressed -> release
            if reaction:
                yield from reaction.on_release_key_sequence

    def _on_begin_holding_reaction(self, tap_hold_key: TapHoldKey) -> Iterator[KeyCmd]:
        if isinstance(tap_hold_key, LayerKey):
            layer_key = tap_hold_key
            self._cur_layer = layer_key.layer
        elif isinstance(tap_hold_key, ModKey):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.PRESS, key_code=mod_key.mod_key_code)

    def _on_end_holding_reaction(self, tap_hold_key: TapHoldKey) -> Iterator[KeyCmd]:
        if isinstance(tap_hold_key, LayerKey):
            self._cur_layer = self._default_layer
        elif isinstance(tap_hold_key, ModKey):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.RELEASE, key_code=mod_key.mod_key_code)
