from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Iterator, Optional


TimeInMs = float
KeyCode = int  # 0 - 255
KeyName = str  # must be unique


class KeyCmdKind(Enum):
    RELEASED = 0
    PRESSED = 1
    SEND = 2


@dataclass
class KeyCmd:
    kind: KeyCmdKind
    key_code: KeyCode


class TapHoldState(Enum):
    INACTIVE = 0  # or RELEASED?
    UNDECIDED = 1  # or PENDING?
    HOLD_ACTIVE = 2
    TAP_ACTIVE = 3


# class IKeyboardDevice(ABC):
#
#     def press(self, keycodes: List[KeyCode]) -> None:
#         pass
#
#     def release(self, keycodes: List[KeyCode]) -> None:
#         pass
#
#     def release_all(self) -> None:
#         pass
#
#     def send(self, keycodes: List[KeyCode]) -> None:
#         pass


class IReaction:
    pass


Layer = Dict[KeyName, IReaction]


class KeyCommandsReaction(IReaction):

    def __init__(self, key_commands: List[KeyCmd]):
        self._key_commands = key_commands

    def iter_key_commands(self) -> Iterator[KeyCmd]:
        yield self._key_commands


class SwitchLayerReaction(IReaction):

    def __init__(self, layer: Optional[Layer]):
        self._layer = layer

    def get_layer(self) -> Optional[None]:
        return self._layer


# class MacroAction(IReaction):
#
#     def __init__(self, key_commands: List[KeyCmd]):
#         self._key_commands = key_commands
#
#     def do(self, kbd) -> None:
#         for kc in self._key_codes:
#             kbd.send_code(kc)


class IPhysicalKey(ABC):

    @abstractmethod
    @property
    def name(self) -> str:
        pass

    @abstractmethod
    @property
    def pressed_time(self) -> Optional[TimeInMs]:
        """ if the key is pressed, get the time
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def set_bound(self, is_bound: bool) -> None:
        pass

    @abstractmethod
    def update(self, time: TimeInMs) -> None:
        pass

    @property
    def is_pressed(self) -> bool:
        return self.pressed_time is not None


class VirtualKey:
    COMBO_TERM = 50  # ms

    def __init__(self, name: str, physical_keys: List[IPhysicalKey], is_part_of_bigger_one: bool):
        """ a virtual key has one or more physical keys

        is_part_of_bigger_one: if the physical keys are a real sub part of another virtual key
                               p.e.: 'q' (LeftPinkyUp) is a part of 'a' (LeftPinkyUp + LeftPinkDown)
                               this decides, if the press should defer.
        """
        assert len(physical_keys) >= 1

        self._name = name
        self._physical_keys = physical_keys
        self._is_part_of_bigger_one = is_part_of_bigger_one

        self._last_pressed_time: TimeInMs = -2000  # last pressed time
        self._last_released_time: TimeInMs = -1000  # last relased time

    @property
    def name(self) -> str:
        return self._name

    @property
    def physical_keys(self) -> List[IPhysicalKey]:
        return self._physical_keys

    def update(self, time: TimeInMs) -> IReaction:
        sorted_pressed_times = sorted(self._iter_pressed_times_of_physical_keys())

        if self._all_pressed_in_time(sorted_pressed_times):
            if self._last_pressed_time is None:
                if self._is_part_of_bigger_one:
                    last_press_time = sorted_pressed_times[-1]
                    if time - last_press_time > self.COMBO_TERM:
                        return self._press(time)
                else:
                    return self._press(time)
        else:
            if self._last_pressed_time is not None:
                return self._release(time)

    def _iter_pressed_times_of_physical_keys(self) -> Iterator[TimeInMs]:
        for pkey in self._physical_keys:
            if pkey.pressed_time is not None:
                yield pkey.pressed_time

    def _all_pressed_in_time(self, sorted_pressed_times: List[TimeInMs]) -> bool:
        return (all(pkey.is_pressed and not pkey.is_bound for pkey in self._physical_keys) and
                all(t2 - t1 < self.COMBO_TERM
                    for t1, t2 in zip(sorted_pressed_times[:-1], sorted_pressed_times[1:])))

    def _press(self, time: TimeInMs) -> IReaction:
        self._last_pressed_time = time
        for pkey in self._physical_keys:
            pkey.set_bound(is_bound=True)
        self._on_pressed(time)

    def _release(self, time: TimeInMs) -> IReaction:
        self._last_released_time = None
        for pkey in self._physical_keys:
            pkey.set_bound(is_bound=False)
        self._on_released(time)

    def _on_pressed(self, time: TimeInMs) -> None:
        raise NotImplementedError()

    def _on_released(self, time: TimeInMs) -> None:
        raise NotImplementedError()


class KeyAction:
    vkey: VirtualKey
    press: bool
    time: TimeInMs


class KeyActionHistory:
    actions: List[KeyAction]


class IKeyLogic(ABC):

    def __init__(self, vkey: VirtualKey):
        self._vkey = vkey

    @abstractmethod
    def add_action(self, action: KeyAction) -> None:
        pass

    @abstractmethod
    def calc_reaction(self, time: TimeInMs) -> Optional[IReaction]:
        pass


class SimpleKeyLogic(IKeyLogic):

    def __init__(self, vkey: VirtualKey, key_code: KeyCode):
        super().__init__(vkey)
        self._key_code = key_code
        self._cur_action: Optional[KeyAction] = None

    def add_action(self, action: KeyAction) -> None:
        if action.vkey.name == self._vkey.name:
            self._cur_action = action
        else:
            self._cur_action = None

    def calc_reaction(self, time: TimeInMs) -> Optional[IReaction]:
        raise NotImplementedError()

    def _on_pressed(self, time: TimeInMs) -> Optional[IReaction]:
        return KeyCommandsReaction([KeyCmd(kind=KeyCmdKind.PRESSED, key_code=self._key_code)])

    def _on_released(self, time: TimeInMs) -> Optional[IReaction]:
        return KeyCommandsReaction([KeyCmd(kind=KeyCmdKind.RELEASED, key_code=self._key_code)])


class TapHoldKeyLogic(IKeyLogic):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, vkey: VirtualKey):
        super().__init__(vkey=vkey)
        self._vkey = vkey
        self._actions: List[KeyAction] = []
        self._pressed_time: Optional[TimeInMs] = None
        self._holding_mode = False
        self._other_pressed_keys: List[VirtualKey] = []

    # def add_action(self, action: KeyAction) -> None:
    #     if action.vkey.name == self._vkey.name:
    #         if action.press:
    #             self._pressed_time = action.time
    #             self._actions = [action]
    #         else:
    #             if len(self._actions) > 0:
    #                 self._actions.append(action)
    #     else:
    #         if len(self._actions) > 0:
    #             self._actions.append(action)

    def calc_reaction(self, time: TimeInMs, action: Optional[KeyAction] = None) -> Optional[IReaction]:
        if action is None:
            if self._pressed_time is None:
                return
            else:
                dt = time - self._pressed_time
                if dt == self.TAP_HOLD_TERM:
                    yield self._create_start_holding_reaction()
                    for other_key in self._other_pressed_keys:
                        yield self._create_tap_reaction()
                else:
                    return
        elif action.vkey.name == self._vkey.name:
            if action.press:
                self._pressed_time = time
            else:  # vkey release





        if self._is_start_holding(time):
            return self._on_start_holding(time)
        elif self._is_end_holding(time):
            return self._on_end_holding(time)
        elif self._is_start_tap(time):
            return self._on_start_tap(time)

    def _is_start_holding(self, time: TimeInMs) -> bool:
        raise NotImplementedError()

    def _is_end_holding(self, time: TimeInMs) -> bool:
        raise NotImplementedError()

    def _is_start_tap(self, time: TimeInMs) -> bool:
        raise NotImplementedError()

    def _create_start_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_end_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_tap_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()


class ModKeyLogic(TapHoldKeyLogic):

    def __init__(self, vkey: VirtualKey, tap_key_code: KeyCode, mod_key_code: KeyCode):
        super().__init__(vkey)

    def _create_start_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_end_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_tap_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()



class LayerKeyLogic(TapHoldKeyLogic):

    def __init__(self, vkey: VirtualKey, tap_key_code: KeyCode, layer: Layer):
        super().__init__(vkey)
        self._layer = layer

    def _create_start_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_end_holding_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()

    def _create_tap_reaction(self, time: TimeInMs) -> IReaction:
        raise NotImplementedError()



class VirtualKeyboard:

    def __init__(self, simple_keys: List[SimpleKeyLogic], mod_keys: List[ModKeyLogic], layer_keys: List[LayerKeyLogic],
                 default_layer: Layer):
        self._simple_keys = simple_keys
        self._mod_keys = mod_keys
        self._layer_keys = layer_keys
        self._default_layer = default_layer

        all_virtual_keys = simple_keys + mod_keys + layer_keys
        self._sorted_vkeys = self._get_sorted_keys(all_virtual_keys)
        self._physical_keys = self._find_physical_keys(all_virtual_keys)

        self._cur_layer = default_layer

        #self._pressed_layer_key: Optional[LayerKey] = None
        #self._pressed_mod_keys: List[ModKey] = []

    @staticmethod
    def _get_sorted_keys(virtual_keys: List[VirtualKey]) -> List[VirtualKey]:
        """ sort keys for update

        start with virtual keys with the most physical keys, so an 'a' will be updated before a 'q'
        """
        return sorted(virtual_keys, key=lambda vkey: len(vkey.physical_keys), reverse=True)

    @staticmethod
    def _find_physical_keys(virtual_keys: List[VirtualKey]) -> List[IPhysicalKey]:
        pkey_map: Dict[str, IPhysicalKey] = {}
        for vkey in virtual_keys:
            for pkey in vkey.physical_keys:
                pkey_map[pkey.name] = pkey
        return list(pkey_map.values())

    def update(self, time: TimeInMs) -> List[KeyCmd]:
        # update physical keys
        for pkey in self._physical_keys:
            pkey.update(time=time)

        # update virtual key states
        changed_virtual_keys: List[VirtualKey] = []  # normal one or none
        for vkey in self._virtual_keys:
            changed = vkey.update_press_state(time=time)
            if changed:
                changed_virtual_keys.append(vkey)

        # create reactions
        switch_layer_reactions: List[SwitchLayerReaction] = []
        key_cmd_reactions: List[KeyCommandsReaction] = []
        for layer_key in self._layer_keys:
            if layer_key.is_pressed:
                reactions = layer_key.create_reactions(time=time, changed_keys=changed_virtual_keys)
                for reaction in reactions:
                    if isinstance(reaction, SwitchLayerReaction):
                        self._update_layer(reaction.get_layer())
                    elif isinstance(reaction, KeyCommandsReaction):
                        for key_cmd in reaction.iter_key_commands():
                            new_key_code = self._cur_layer.get(key_cmd.key_code)
                            key_commands.append(new_key_code)

        for tap_hold_key in self._pressed_tap_hold_keys:
            reaction = tap_hold_key.update(time=time, changed_keys=changed_virtual_keys)
            if isinstance(reaction, SwitchLayerReaction):
                self._update_layer(reaction.get_layer())
            elif isinstance(reaction, KeyCommandsReaction):
                for key_cmd in reaction.iter_key_commands():
                    new_key_code = self._cur_layer.get(key_cmd.key_code)
                    key_commands.append(new_key_code)





        key_commands: List[KeyCmd] = []
        for vkey in self._sorted_vkeys:
            reaction = vkey.update(time=time)
            if isinstance(reaction, SwitchLayerReaction):
                self._update_layer(reaction.get_layer())
            elif isinstance(reaction, KeyCommandsReaction):
                for key_cmd in reaction.iter_key_commands():
                    new_key_code = self._cur_layer.get(key_cmd.key_code)
                    key_commands.append(new_key_code)

        return key_commands

    def _update_layer(self, next_layer: Optional[Layer]):
        if next_layer is None:
            self._cur_layer = self._default_layer
        else:
            self._cur_layer = next_layer


# def main():
#     keyboard = KeyboardReader().read()
#     mouse = Mouse()
#     clock = Clock()
#
#     while True:
#         update_mouse()
#
#         time = clock.value
#         key_commands = keyboard.update(time)
#         for key_cmd in key_commands:
#             send_key_cmd(key_cmd, kbd_device)
#
#         time.wait(2)  # ms


