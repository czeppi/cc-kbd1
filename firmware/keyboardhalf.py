from __future__ import annotations

from typing import Iterator

from base import PhysicalKeySerial, TimeInMs, VirtualKeySerial, KeyGroupSerial, KeyCode
from virtualkeyboard import KeyCmd, KeyCmdKind

"""
     !!!! TESTED, BUT UNUSED !!!!
"""




# def main():
#     while True:
#         read_devices()
#         while queue.is_not_empty():
#             for queue_item in queue.read():
#                 _process_one_queue_item(queue_item)
#
#
# def _process_one_queue_item(queue_item):
#     vkey_events = queue_item.other_kbd_half_vkey_events
#     for vkey_evt in my_kbd_half.update(queue_item.pressed_pkeys):
#         read_devices()
#         vkey_events.append(vkey_evt)
#
#     sorted_vkey_events = sort_vkey_events(vkey_events)
#     for vkey_evt in sorted_vkey_events:
#         read_devices()
#         for key in kbd.update(vkey_evt):
#             send_key(key)


class KeyboardHalf:

    def __init__(self, key_groups: list[KeyGroup]):
        self._key_groups = key_groups

        self._prev_pressed_pkeys: set[PhysicalKeySerial] = set()
        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, cur_pressed_pkeys: set[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        if cur_pressed_pkeys == self._prev_pressed_pkeys:
            if self._next_decision_time is None or self._next_decision_time > time:
                return  # too early
            else:
                for group in self._key_groups:
                    yield from group.update_by_time(time)
        else:
            for group in self._key_groups:
                yield from group.update(time, cur_pressed_pkeys)

            self._prev_pressed_pkeys = cur_pressed_pkeys.copy()

        self._next_decision_time = min((group.time_of_decision
                                        for group in self._key_groups
                                        if group.time_of_decision is not None),
                                       default=None)


class VKeyPressEvent:

    def __init__(self, time: TimeInMs, vkey_serial: VirtualKeySerial, pressed: bool):
        # public
        self.time = time
        self.vkey_serial = vkey_serial
        self.pressed = pressed


class KeyGroup:
    COMBO_TERM = 50  # ms

    def __init__(self, serial: KeyGroupSerial, vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]):
        # static
        self._serial = serial
        self._pkeys_of_this_group = frozenset(self._iter_group_pkeys(vkey_map))
        self._vkey2pkeys = { vkey: frozenset(pkeys) for vkey, pkeys in vkey_map.items()}
        self._pkeys2vkeys = { frozenset(pkeys): vkey for vkey, pkeys in vkey_map.items()}
        self._is_vkey_part_of_bigger_one_map = self._create_is_part_of_bigger_one_map(vkey_map)

        # dynamic
        self._prev_pressed_pkeys: set[PhysicalKeySerial] = set()
        self._bound_pkeys: set[PhysicalKeySerial] = set()

        self._pressed_vkeys: set[VirtualKeySerial] = set()
        self._undecided_vkey: VirtualKeySerial | None = None  # pressed or undecided
        self._time_of_decision: TimeInMs | None = None  # if open_vkey is undecided

    @staticmethod
    def _iter_group_pkeys(vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]
                          ) -> Iterator[PhysicalKeySerial]:
        for pkeys in vkey_map.values():
            yield from pkeys

    @staticmethod
    def _create_is_part_of_bigger_one_map(vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]
                                          ) -> dict[VirtualKeySerial, bool]:
        vkey2pkeys = {vkey: frozenset(pkey_list) for vkey, pkey_list in vkey_map.items()}
        return {
            vkey: any(pkeys_set < other_set for other_set in vkey2pkeys.values())
            for vkey, pkeys_set in vkey2pkeys.items()
        }

    @property
    def serial(self) -> KeyGroupSerial:
        return self._serial

    @property
    def time_of_decision(self) -> TimeInMs | None:
        return self._time_of_decision

    def update(self, time: TimeInMs, all_pressed_pkeys: set[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        """
            all_pressed_pkeys: this can contain pkeys of other groups
        """
        cur_pressed_pkeys = frozenset(all_pressed_pkeys & self._pkeys_of_this_group)

        if cur_pressed_pkeys == self._prev_pressed_pkeys:
            yield from self.update_by_time(time)

        else:  # pressed pkeys has changed
            if self._prev_pressed_pkeys < cur_pressed_pkeys:
                yield from self._update_with_press(time, cur_pressed_pkeys)
            elif cur_pressed_pkeys < self._prev_pressed_pkeys:
                yield from self._update_with_release(time, cur_pressed_pkeys)
            else:
                yield from self._update_with_press_and_release(time, cur_pressed_pkeys)

            self._prev_pressed_pkeys = cur_pressed_pkeys

    def update_by_time(self, time: TimeInMs) -> Iterator[VKeyPressEvent]:
        if self._time_of_decision is None or time < self._time_of_decision:
            return  # too early

        # decided: press now
        if self._undecided_vkey is None:
            self._time_of_decision = None  # ERROR => fix it
            return

        yield VKeyPressEvent(time, self._undecided_vkey, pressed=True)
        self._bound_pkeys |= self._vkey2pkeys[self._undecided_vkey]
        self._pressed_vkeys.add(self._undecided_vkey)
        self._undecided_vkey = None
        self._time_of_decision = None

    def _update_with_press(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        # undecided timed out?
        yield from self.update_by_time(time)

        unbound_pressed_pkeys = frozenset(cur_pressed_pkeys - self._bound_pkeys)

        vkey_serial = self._pkeys2vkeys.get(unbound_pressed_pkeys)  # !! only recognize one vkey-press at a time !!
        if vkey_serial is None:
            self._undecided_vkey = None
            self._time_of_decision = None
            return

        if self._is_vkey_part_of_bigger_one_map.get(vkey_serial, False):
            # undecided
            self._undecided_vkey = vkey_serial
            self._time_of_decision = time + self.COMBO_TERM
        else:
            # press detected
            yield VKeyPressEvent(time, vkey_serial=vkey_serial, pressed=True)
            self._bound_pkeys |= unbound_pressed_pkeys
            self._pressed_vkeys.add(vkey_serial)
            self._undecided_vkey = None
            self._time_of_decision = None

    def _update_with_release(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]
                             ) -> Iterator[VKeyPressEvent]:
        released_pkeys = self._prev_pressed_pkeys - cur_pressed_pkeys

        # release pressed keys...
        for vkey_serial in self._pressed_vkeys.copy():
            pkeys = self._vkey2pkeys[vkey_serial]
            if (pkeys & released_pkeys) != frozenset():
                yield VKeyPressEvent(time, vkey_serial=vkey_serial, pressed=False)
                self._bound_pkeys -= self._vkey2pkeys[vkey_serial]
                self._pressed_vkeys.remove(vkey_serial)

        # release undecided key ...
        if self._undecided_vkey:
            vkey_serial = self._undecided_vkey
            pkeys = self._vkey2pkeys[vkey_serial]
            if (pkeys & released_pkeys) != frozenset():
                yield VKeyPressEvent(time, vkey_serial=vkey_serial, pressed=True)
                yield VKeyPressEvent(time, vkey_serial=vkey_serial, pressed=False)
                self._undecided_vkey = None
                self._time_of_decision = None
            else:
                yield from self.update_by_time(time)

    def _update_with_press_and_release(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]
                                       ) -> Iterator[VKeyPressEvent]:
        """ This is VERY unusual - the reaction can change later maybe
        """
        yield from self._update_with_release(time, cur_pressed_pkeys)
        yield from self._update_with_press(time, cur_pressed_pkeys)


Layer = dict  # dict[VirtualKeySerial, KeyReaction]


class VirtualKey2:

    def __init__(self, serial: VirtualKeySerial):
        # public
        self.serial = serial
        self.last_press_time: TimeInMs = -1


class SimpleKey2(VirtualKey2):

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


# class HoldReaction:
#
#     def __init__(self, layer: Layer | None = None, key_cmd: KeyCmd | None = None):
#         # public
#         self.layer = layer
#         self.key_cmd = key_cmd


class TapHoldKey2(VirtualKey2):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class ModKey2(TapHoldKey2):

    def __init__(self, serial: VirtualKeySerial, mod_key_code: KeyCode):
        super().__init__(serial=serial)
        self._mod_key_code = mod_key_code

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code


class LayerKey2(TapHoldKey2):

    def __init__(self, serial: VirtualKeySerial, layer: Layer):
        super().__init__(serial=serial)

        # public
        self.layer = layer



class VirtualKeyboard2:

    def __init__(self, simple_keys: list[SimpleKey2], mod_keys: list[ModKey2], layer_keys: list[LayerKey2],
                 default_layer: Layer):
        self._simple_keys = simple_keys
        self._mod_keys = mod_keys
        self._layer_keys = layer_keys
        self._all_keys = {key.serial: key for key in simple_keys + mod_keys + layer_keys}
        self._default_layer = default_layer

        self._cur_layer = default_layer
        self._undecided_tap_hold_keys: list[TapHoldKey2] = []
        self._deferred_simple_keys: list[SimpleKey2] = []  # wait for Tap/Hold decision
        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, vkey_events: list[VKeyPressEvent]) -> Iterator[KeyCmd]:
        if len(vkey_events) == 0 and (self._next_decision_time is None or self._next_decision_time > time):
            return  # too early

        yield from self._update_by_time(time)

        for vkey_event in self._sorted_vkey_events(vkey_events):
            yield from self._update_vkey_event(vkey_event)

        self._next_decision_time = min((vkey.last_press_time + TapHoldKey2.TAP_HOLD_TERM
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
        tap_hold_keys_to_remove: list[TapHoldKey2] = []

        for tap_hold_key in self._undecided_tap_hold_keys:
            if time - tap_hold_key.last_press_time >= TapHoldKey2.TAP_HOLD_TERM:
                yield from self._on_begin_holding_reaction(tap_hold_key)
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)
                tap_hold_keys_to_remove.append(tap_hold_key)

        for tap_hold_key in tap_hold_keys_to_remove:
            self._undecided_tap_hold_keys.remove(tap_hold_key)

        # simple: deferred -> press
        if len(tap_hold_key_press_times) > 0:
            oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)
            simple_keys_to_remove: list[SimpleKey2] = []

            for simple_key in self._deferred_simple_keys:
                if simple_key.last_press_time > oldest_tap_hold_key_press_time:
                    reaction = self._cur_layer.get(simple_key.serial)  # for simplifying, take current layer
                    if reaction:
                        yield from reaction.on_press_key_sequence
                    simple_keys_to_remove.append(simple_key)

            for simple_key in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key)

    def _update_vkey_event(self, vkey_event: VKeyPressEvent) -> Iterator[KeyCmd]:
        time = vkey_event.time
        vkey_serial = vkey_event.vkey_serial
        vkey = self._all_keys[vkey_serial]

        if isinstance(vkey, TapHoldKey2):
            if vkey_event.pressed:
                self._on_begin_press_tap_hold_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_tap_hold_key(vkey)

        elif isinstance(vkey, SimpleKey2):
            if vkey_event.pressed:
                yield from self._on_begin_press_simple_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_simple_key(vkey)

    def _on_begin_press_tap_hold_key(self, tap_hold_key: TapHoldKey2) -> None:
        """
            tap/hold: inactive -> undecided
        """
        self._undecided_tap_hold_keys.append(tap_hold_key)

    def _on_end_press_tap_hold_key(self, tap_hold_key: TapHoldKey2) -> Iterator[KeyCmd]:
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
            simple_keys_to_remove: list[SimpleKey2] = []

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

    def _on_begin_press_simple_key(self, simple_key: SimpleKey2) -> Iterator[KeyCmd]:
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

    def _on_end_press_simple_key(self, simple_key: SimpleKey2) -> Iterator[KeyCmd]:
        """
            tap/hold: undecided -> hold   # Permissive Hold (s. https://docs.qmk.fm/tap_hold)
            simple: deferred -> press + release
                    pressed -> release
        """
        # tap/hold: undecided -> hold
        tap_hold_key_press_times: list[TimeInMs] = []
        tap_hold_keys_to_remove: list[TapHoldKey2] = []

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
            simple_keys_to_remove: list[SimpleKey2] = []

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

    def _on_begin_holding_reaction(self, tap_hold_key: TapHoldKey2) -> Iterator[KeyCmd]:
        if isinstance(tap_hold_key, LayerKey2):
            layer_key = tap_hold_key
            self._cur_layer = layer_key.layer
        elif isinstance(tap_hold_key, ModKey2):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.PRESS, key_code=mod_key.mod_key_code)

    def _on_end_holding_reaction(self, tap_hold_key: TapHoldKey2) -> Iterator[KeyCmd]:
        if isinstance(tap_hold_key, LayerKey2):
            self._cur_layer = self._default_layer
        elif isinstance(tap_hold_key, ModKey2):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.RELEASE, key_code=mod_key.mod_key_code)
