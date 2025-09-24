from __future__ import annotations

try:
    from typing import Iterator, Optional
except ImportError:
    pass


WITH_PRINT = False


TimeInMs = float
KeyCode = int  # 0 - 255
KeyName = str  # must be unique


class KeyCmdKind:  # enum
    RELEASE = 0
    PRESS = 1
    SEND = 2


class KeyCmd:
    def __init__(self, kind: KeyCmdKind, key_code: KeyCode):
        self.kind = kind
        self.key_code = key_code

    def __eq__(self, other: KeyCmd) -> bool:
        return self.kind == other.kind and self.key_code == other.key_code

    def __ne__(self, other: KeyCmd) -> bool:
        return not self == other


KeySequence = list  # list[KeyCmd]


class KeyReaction:  # KeySetting?
    def __init__(self, on_press_key_sequence: KeySequence, on_release_key_sequence: KeySequence):
        self.on_press_key_sequence = on_press_key_sequence
        self.on_release_key_sequence = on_release_key_sequence


# class SplitSide:
#     LEFT = 1
#     RIGHT = 2


Layer = dict  # dict[KeyName, KeyReaction]


class IPhysicalKey:

    @property
    def name(self) -> str:
        raise NotImplementedError()  # abstract

    @property
    def press_time(self) -> Optional[TimeInMs]:
        """ if the key is pressed, get the time
        """
        raise NotImplementedError()  # abstract

    @property
    def is_bound(self) -> bool:
        """ when a virtual key is recognized, bound all physical keys

        example:
            physical keys: LeftPinkyUp, LeftPinkyDown

            virtual keys:
                'q': LeftPinkyUp
                'a': LeftPinkyUp + LeftPinkyDown
                'y': LeftPinkyDown

            if a 'q' is recognized, than bound the two physical keys, to avoid double using.
        """
        raise NotImplementedError()  # abstract

    def set_bound(self, is_bound: bool) -> None:
        raise NotImplementedError()  # abstract

    def update(self, time: TimeInMs) -> None:
        raise NotImplementedError()  # abstract

    @property
    def is_pressed(self) -> bool:
        return self.press_time is not None


class VirtualKey:
    COMBO_TERM = 50  # ms

    def __init__(self, name: str, physical_keys: list[IPhysicalKey], is_part_of_bigger_one: bool):
        """ a virtual key has one or more physical keys

        is_part_of_bigger_one: if the physical keys are a real sub part of another virtual key
                               p.e.: 'q' (LeftPinkyUp) is a part of 'a' (LeftPinkyUp + LeftPinkDown)
                               this decides, if the press should defer.
        """
        assert len(physical_keys) >= 1

        self._name = name
        self._physical_keys = physical_keys
        self._is_part_of_bigger_one = is_part_of_bigger_one

        self._last_press_time: TimeInMs = -2000  # last pressed time
        self._last_release_time: TimeInMs = -1000  # last released time

    @property
    def name(self) -> str:
        return self._name

    @property
    def physical_keys(self) -> list[IPhysicalKey]:
        return self._physical_keys

    @property
    def last_press_time(self) -> TimeInMs:
        return self._last_press_time

    @property
    def will_be_pressed(self) -> bool:  # from now until the next update
        return self._last_press_time > self._last_release_time

    def was_pressed(self, time: TimeInMs) -> bool:  # from the prev update until now
        """
                        was  is
            R < P < C    T   T
            R < P == C   F   T
            P < R < C    F   F
            P < R == C   T   F

            R=released-time
            P=pressed-time
            C=current-time
            T=true
            F=False
        """
        released = self._last_release_time
        pressed = self._last_press_time

        return released < pressed < time or pressed < released == time

    def is_begin_pressing(self, time: TimeInMs) -> bool:
        return self.will_be_pressed and not self.was_pressed(time)

    def is_end_pressing(self, time: TimeInMs) -> bool:
        return not self.will_be_pressed and self.was_pressed(time)

    def update_press_state(self, time: TimeInMs) -> bool:
        """ return: has state changed
        """
        sorted_pressed_times = sorted(self._iter_pressed_times_of_physical_keys())
        if self._name == 'rtd':
            if WITH_PRINT:
                for pkey in self._physical_keys:
                    print(f'  {self._name} / {pkey.name}: {pkey.press_time}')
                print(f'  {self._name}: {len(self._physical_keys)} {sorted_pressed_times}')

        print(f'update {self.name}')
        if self._all_pressed_in_time(sorted_pressed_times):
            print('  all in time')
            if self._last_press_time < self._last_release_time:  # was released?
                print('  was released')
                if self._is_part_of_bigger_one:
                    print('  is part of bigger one')
                    last_press_time = sorted_pressed_times[-1]
                    if time - last_press_time > self.COMBO_TERM:
                        print('  COMBO term is passed -> press')
                        self._press(time)
                        return True
                    else:
                        print('  COMBO term is NOT passed')
                else:
                    print('  is NOT part of bigger one -> press')
                    self._press(time)
                    return True
            else:
                print('  was pressed')
        else:
            print('  NOT all in time')
            if self._last_release_time < self._last_press_time:  # was pressed?
                print('  was pressed -> release')
                self._release(time)
                return True
            else:
                print('  was NOT pressed')

        return False

    def _iter_pressed_times_of_physical_keys(self) -> Iterator[TimeInMs]:
        for pkey in self._physical_keys:
            if pkey.press_time is not None:
                yield pkey.press_time

    def _all_pressed_in_time(self, sorted_pressed_times: list[TimeInMs]) -> bool:
        return (all(pkey.is_pressed and not pkey.is_bound for pkey in self._physical_keys) and
                all(t2 - t1 < self.COMBO_TERM
                    for t1, t2 in zip(sorted_pressed_times[:-1], sorted_pressed_times[1:])))

    def _press(self, time: TimeInMs) -> None:
        self._last_press_time = time
        for pkey in self._physical_keys:
            pkey.set_bound(is_bound=True)

    def _release(self, time: TimeInMs) -> None:
        self._last_release_time = time


class KeyAction:
    vkey: VirtualKey
    press: bool
    time: TimeInMs


class KeyActionHistory:
    actions: list[KeyAction]


class SimpleKey(VirtualKey):

    def __init__(self, name: str, physical_keys: list[IPhysicalKey], is_part_of_bigger_one: bool):
        super().__init__(name=name, physical_keys=physical_keys, is_part_of_bigger_one=is_part_of_bigger_one)

        self._was_deferred = False  # from last update until now
        self._will_be_deferred = False  # from now, to the next update

    @property
    def was_deferred(self) -> bool:
        return self._was_deferred

    @property
    def will_be_deferred(self) -> bool:
        return self._will_be_deferred

    def update_deferred(self, will_be_deferred: bool) -> None:
        self._was_deferred = self._will_be_deferred
        self._will_be_deferred = will_be_deferred


class TapHoldState:  # enum
    INACTIVE = 0  # or RELEASED?
    UNDECIDED = 1  # or PENDING?
    HOLD = 2


class TapHoldKey(VirtualKey):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, name: str, physical_keys: list[IPhysicalKey], is_part_of_bigger_one: bool):
        super().__init__(name=name, physical_keys=physical_keys, is_part_of_bigger_one=is_part_of_bigger_one)
        self._prev_tap_hold_state = TapHoldState.INACTIVE
        self._cur_tap_hold_state = TapHoldState.INACTIVE

    @property
    def prev_tap_hold_state(self) -> TapHoldState:
        return self._prev_tap_hold_state

    @property
    def cur_tap_hold_state(self) -> TapHoldState:
        return self._cur_tap_hold_state

    @property
    def is_decided(self) -> bool:
        return self._cur_tap_hold_state != TapHoldState.UNDECIDED

    def update_tap_hold_state(self, time: TimeInMs, changed_vkeys: list[VirtualKey]) -> None:
        # was       is         reaction
        # ------------------------------
        # inactive  inactive   other
        # inactive  undecided  -
        # inactive  hold       start-hold + other
        # undecided inactive   tap
        # undecided undecided  -
        # undecided hold       start-hold + other
        # hold      inactive   end-hold
        # hold      undecided  ERR
        # hold      hold       other
        next_state = self._calc_tap_hold_state(time=time, changed_vkeys=changed_vkeys)
        self._prev_tap_hold_state = self._cur_tap_hold_state
        self._cur_tap_hold_state = next_state
        print(f'  update_tap_hold_state({self.name}): next_state={next_state}, prev_state={self._prev_tap_hold_state}')

    def _calc_tap_hold_state(self, time: TimeInMs, changed_vkeys: list[VirtualKey]) -> TapHoldState:
        if not self.will_be_pressed:
            return TapHoldState.INACTIVE

        dt = time - self._last_press_time
        if dt >= self.TAP_HOLD_TERM:
            return TapHoldState.HOLD

        # check for Permissive Hold (s. https://docs.qmk.fm/tap_hold)
        for key in changed_vkeys:
            if self.will_be_pressed and key.is_end_pressing(time) and self._last_press_time < key._last_press_time:
                return TapHoldState.HOLD

        return TapHoldState.UNDECIDED

    def is_begin_holding(self) -> bool:
        return (self._prev_tap_hold_state != TapHoldState.HOLD
                and self._cur_tap_hold_state == TapHoldState.HOLD)

    def is_end_holding(self) -> bool:
        return (self._prev_tap_hold_state == TapHoldState.HOLD
                and self._cur_tap_hold_state != TapHoldState.HOLD)


class ModKey(TapHoldKey):

    def __init__(self, name: str, physical_keys: list[IPhysicalKey], is_part_of_bigger_one: bool,
                 mod_key_code: KeyCode):
        super().__init__(name=name, physical_keys=physical_keys, is_part_of_bigger_one=is_part_of_bigger_one)
        self._mod_key_code = mod_key_code

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code


class LayerKey(TapHoldKey):

    def __init__(self, name: str, physical_keys: list[IPhysicalKey], is_part_of_bigger_one: bool,
                 layer: Layer):
        super().__init__(name=name, physical_keys=physical_keys, is_part_of_bigger_one=is_part_of_bigger_one)
        self._layer = layer

    @property
    def layer(self) -> Layer:
        return self._layer


class DeferredSimpleKey:
    def __init__(self, key: SimpleKey, layer: Layer):
        self.key = key
        self.layer = layer


class VirtualKeyboard:

    def __init__(self, simple_keys: list[SimpleKey], mod_keys: list[ModKey], layer_keys: list[LayerKey],
                 default_layer: Layer):
        self._simple_keys = simple_keys
        self._mod_keys = mod_keys
        self._layer_keys = layer_keys
        self._default_layer = default_layer

        self._physical_keys = self._get_physical_keys()
        self._cur_layer = default_layer
        self._deferred_simple_keys: list[DeferredSimpleKey] = []

    def _get_physical_keys(self) -> list[IPhysicalKey]:
        pkey_map: dict[str, IPhysicalKey] = {}
        for vkey in self.iter_all_virtual_keys():
            for pkey in vkey.physical_keys:
                pkey_map[pkey.name] = pkey
        return list(pkey_map.values())

    def iter_physical_keys(self) -> Iterator[IPhysicalKey]:
        yield from self._physical_keys

    def iter_all_virtual_keys(self) -> Iterator[VirtualKey]:
        yield from self._simple_keys
        yield from self._layer_keys
        yield from self._mod_keys

    def update(self, time: TimeInMs) -> Iterator[KeyCmd]:
        if WITH_PRINT:
            print(f'update({time}):')
            print(f'  _update_physical_keys()...')

        # update states
        self._update_physical_keys(time)

        changed_virtual_keys = list(self._update_press_state_of_virtual_keys(time))

        if WITH_PRINT:
            print(f'  changed_virt_keys: {changed_virtual_keys}')
            print(f'  _update_tap_hold_states()...')

        self._update_tap_hold_states(time=time, changed_virtual_keys=changed_virtual_keys)
        self._update_deferred_state_of_simple_keys(time=time)

        self._update_cur_layer()

        # create key commands
        yield from self._create_mod_holding_key_commands()
        yield from self._create_all_tap_key_commands()
        yield from self._create_simple_key_commands(time)

    def _update_physical_keys(self, time: TimeInMs) -> None:
        for pkey in self._physical_keys:
            pkey.set_bound(False)
            pkey.update(time=time)

    def _update_press_state_of_virtual_keys(self, time: TimeInMs) -> Iterator[VirtualKey]:
        for vkey in self.iter_all_virtual_keys():
            changed = vkey.update_press_state(time=time)
            if changed:
                yield vkey

    def _update_tap_hold_states(self, time: TimeInMs, changed_virtual_keys: list[VirtualKey]) -> None:
        for key in self._iter_tap_hold_keys():
            key.update_tap_hold_state(time=time, changed_vkeys=changed_virtual_keys)

    def _update_deferred_state_of_simple_keys(self, time: TimeInMs) -> None:
        undecided_tap_hold_keys = [key for key in self._iter_tap_hold_keys()
                                   if key.cur_tap_hold_state == TapHoldState.UNDECIDED]
        # no undecided keys
        if len(undecided_tap_hold_keys) == 0:
            for key in self._simple_keys:
                key.update_deferred(False)
            return

        # at least one undecided key
        oldest_tap_hold_time = min(key.last_press_time for key in undecided_tap_hold_keys)

        for key in self._simple_keys:
            will_be_deferred = (key.will_be_pressed and key.last_press_time > oldest_tap_hold_time)
            key.update_deferred(will_be_deferred)

    def _update_cur_layer(self) -> None:
        for layer_key in self._layer_keys:
            if layer_key.is_begin_holding():
                self._cur_layer = layer_key.layer  # if more than one possible (weired) than take any
            if layer_key.is_end_holding():
                if self._cur_layer == layer_key.layer:  # was set by this key?
                    self._cur_layer = self._default_layer

    def _create_mod_holding_key_commands(self) -> Iterator[KeyCmd]:
        for mod_key in self._mod_keys:
            if mod_key.is_begin_holding():
                yield KeyCmd(kind=KeyCmdKind.PRESS, key_code=mod_key.mod_key_code)
            if mod_key.is_end_holding():
                yield KeyCmd(kind=KeyCmdKind.RELEASE, key_code=mod_key.mod_key_code)

    def _create_all_tap_key_commands(self) -> Iterator[KeyCmd]:
        for key in self._iter_all_tap_keys_where_a_tap_is_detected():
            reaction = self._cur_layer.get(key.name)  # for simplifying, take current layer
            if reaction:
                yield from reaction.on_press_key_sequence
                yield from reaction.on_release_key_sequence

    def _iter_all_tap_keys_where_a_tap_is_detected(self) -> Iterator[TapHoldKey]:
        for key in self._iter_tap_hold_keys():
            if key.prev_tap_hold_state == TapHoldState.UNDECIDED:
                if key.cur_tap_hold_state == TapHoldState.INACTIVE:
                    yield key

    def _create_simple_key_commands(self, time: TimeInMs) -> Iterator[KeyCmd]:
        for key in self._simple_keys:
            reaction = self._cur_layer.get(key.name)  # for simplifying, take current layer
            if reaction is None:
                continue

            was_deferred = key.was_deferred
            if key.is_begin_pressing(time):
                was_deferred = True

            will_be_deferred = key.will_be_deferred
            if key.is_end_pressing(time):
                will_be_deferred = False

            if was_deferred and not will_be_deferred:
                yield from reaction.on_press_key_sequence

            if key.is_end_pressing(time):
                yield from reaction.on_release_key_sequence

    @staticmethod
    def _create_key_commands(time: TimeInMs, key: SimpleKey, layer: Layer) -> Iterator[KeyCmd]:
        key_assignment = layer[key.name]

        if key.is_end_pressing(time):
            yield from key_assignment.on_press_key_sequence
            yield from key_assignment.on_release_key_sequence
        elif key.will_be_pressed:
            yield from key_assignment.on_press_key_sequence

    def _iter_tap_hold_keys(self) -> Iterator[TapHoldKey]:
        yield from self._layer_keys
        yield from self._mod_keys

