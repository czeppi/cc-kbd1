from base import PinName, PinIndex, VirtualKeyName, KeyCode, KeyName
from dummyphysicalkey import DummyPhysicalKey

try:
    from typing import Callable, Iterator
except ImportError:
    pass

from adafruit_hid.keycode import Keycode as KC

from virtualkeyboard import VirtualKeyboard, IPhysicalKey, SimpleKey, ModKey, KeyReaction, LayerKey, KeyCmd, KeyCmdKind, VirtualKey

MacroName = str  # p.e. 'M3'
MacroDescription = str
ModKeyName = str  # p.e. 'LCtrl'
ReactionName = str  # p.e. 'a', '$', 'M5'


KEYCODES_DATA = [
    # function row
    [KC.ESCAPE, 'esc', '', 'esc', ''],
    [KC.F1, 'F1', '', 'F1', ''],
    [KC.F2, 'F2', '', 'F2', ''],
    [KC.F3, 'F3', '', 'F3', ''],
    [KC.F4, 'F4', '', 'F4', ''],
    [KC.F5, 'F5', '', 'F5', ''],
    [KC.F6, 'F6', '', 'F6', ''],
    [KC.F7, 'F7', '', 'F7', ''],
    [KC.F8, 'F8', '', 'F8', ''],
    [KC.F9, 'F9', '', 'F9', ''],
    [KC.F10, 'F10', '', 'F10', ''],
    [KC.F11, 'F11', '', 'F11', ''],
    [KC.F12, 'F12', '', 'F12', ''],

    # row 1
    [KC.GRAVE_ACCENT, '`', '~', '^', '°'],
    [KC.ONE, '1', '!', '1', '!'],
    [KC.TWO, '2', '@', '2', '"'],
    [KC.THREE, '3', '#', '3', '§'],
    [KC.FOUR, '4', '$', '4', '$'],
    [KC.FIVE, '5', '%', '5', '%'],
    [KC.SIX, '6', '^', '6', '&'],
    [KC.SEVEN, '7', '&', '7', '/', '{'],
    [KC.EIGHT, '8', '*', '8', '(', '['],
    [KC.NINE, '9', '(', '9', ')', ']'],
    [KC.ZERO, '0', ')', '0', '=', '}'],
    [KC.MINUS, '-', '_', 'ß', '?', '\\'],
    [KC.EQUALS, '=', '+', '´', '`'],
    [KC.BACKSPACE, 'Backspace', '', 'Backspace', ''],

    # row 2
    [KC.TAB, 'Tab', 'BackTab', 'Tab', 'BackTab'],
    # q ... p
    [KC.LEFT_BRACKET, '[', '{', 'ü', 'Ü'],
    [KC.RIGHT_BRACKET, ']', '}', '+', '*', '~'],
    [KC.ENTER, 'Enter', '', 'Enter', ''],

    # row 3
    [KC.CAPS_LOCK, 'CapsLock', '', 'CapsLock', ''],
    # a ... l
    [KC.SEMICOLON, ';', ':', 'ö', 'Ö'],
    [KC.QUOTE, "'", '"', 'ä', 'Ä'],
    [KC.POUND, '#', '~', '#', "'"],

    # row 4
    [KC.LEFT_SHIFT, 'LShift', '', 'LShift', ''],
    [KC.BACKSLASH, '\\', '|', '<', '>', '|'],
    # y ... m
    [KC.COMMA, ',', '<', ',', ';'],
    [KC.PERIOD, '.', '>', '.', ':'],
    [KC.FORWARD_SLASH, '/', '?', '-', '_'],
    [KC.RIGHT_SHIFT, 'RShift', '', 'RShift', ''],

    # row 5
    [KC.LEFT_CONTROL, 'LCtrl', '', 'LCtrl', ''],
    [KC.LEFT_GUI, 'LGui', '', 'LGui', ''],
    [KC.LEFT_ALT, 'LAlt', '', 'LAlt', ''],
    [KC.SPACE, 'Space', '', 'Space', ''],
    [KC.RIGHT_ALT, 'RAlt', '', 'RAlt', ''],
    [KC.RIGHT_GUI, 'RGui', '', 'RGui', ''],
    [KC.APPLICATION, 'Menu', '', 'Menu', ''],

    # cursor row 1
    [KC.INSERT, 'Insert', '', 'Insert', ''],
    [KC.HOME, 'Home', '', 'Home', ''],
    [KC.PAGE_UP, 'PageUp', '', 'PageUp', ''],

    # cursor row 2
    [KC.DELETE, 'Del', '', 'Del', ''],
    [KC.END, 'End', '', 'End', ''],
    [KC.PAGE_DOWN, 'PageDown', '', 'PageDown', ''],

    # cursor row 3
    [KC.UP_ARROW, 'Up', '', 'Up', ''],

    # cursor row 4
    [KC.LEFT_ARROW, 'Left', '', 'Left', ''],
    [KC.DOWN_ARROW, 'Down', '', 'Down', ''],
    [KC.RIGHT_ARROW, 'Right', '', 'Right', ''],

    # keypad row 1
    [KC.KEYPAD_NUMLOCK, 'KpNumLock', '', 'KpNumLock', ''],
    [KC.KEYPAD_FORWARD_SLASH, 'Kp/', '', 'Kp/', ''],
    [KC.KEYPAD_ASTERISK, 'Kp*', '', 'Kp*', ''],
    [KC.KEYPAD_MINUS, 'Kp', '', 'Kp', ''],

    # keypad row 2
    [KC.KEYPAD_SEVEN, 'Kp7', '', 'Kp7', ''],
    [KC.KEYPAD_EIGHT, 'Kp8', '', 'Kp8', ''],
    [KC.KEYPAD_NINE, 'Kp9', '', 'Kp9', ''],
    [KC.KEYPAD_PLUS, 'Kp+', '', 'Kp+', ''],

    # keypad row 3
    [KC.KEYPAD_FOUR, 'Kp4', '', 'Kp4', ''],
    [KC.KEYPAD_FIVE, 'Kp5', '', 'Kp5', ''],
    [KC.KEYPAD_SIX, 'Kp6', '', 'Kp6', ''],

    # keypad row 4
    [KC.KEYPAD_ONE, 'Kp1', '', 'Kp1', ''],
    [KC.KEYPAD_TWO, 'Kp2', '', 'Kp2', ''],
    [KC.KEYPAD_THREE, 'Kp3', '', 'Kp3', ''],
    [KC.KEYPAD_ENTER, 'KpEnter', '', 'KpEnter', ''],

    # keypad row 5
    [KC.KEYPAD_ZERO, 'Kp0', 'KpInsert', 'Kp0', 'KpInsert'],
    [KC.KEYPAD_PERIOD, 'Kp.', 'KpDel', '', 'KpDel'],
]


class ReactionData:

    def __init__(self, key_code: KeyCode, with_shift: bool, with_alt: bool = False):
        self.key_code = key_code
        self.with_shift = with_shift
        self.with_alt = with_alt


class KeyboardCreator:
    _MOD_KEY_CODE_MAP={
        'LShift': KC.LEFT_SHIFT,
        'LCtrl': KC.LEFT_CONTROL,
        'LAlt': KC.LEFT_ALT,
        'LGui': KC.LEFT_GUI,
        'RShift': KC.RIGHT_SHIFT,
        'RCtrl': KC.RIGHT_CONTROL,
        'RAlt': KC.RIGHT_ALT,
        'RGui': KC.RIGHT_GUI,
    }

    def __init__(self, physical_key_creator: Callable[[PinName, PinIndex], IPhysicalKey],
                 left_controller_pins: dict[PinName, PinIndex],
                 right_controller_pins: dict[PinName, PinIndex],
                 virtual_keys: dict[VirtualKeyName, list[PinName]],
                 virtual_key_order: list[str],
                 layers: dict[VirtualKeyName, list[str]],
                 modifiers: dict[VirtualKeyName, ModKeyName],
                 macros: dict[MacroName, MacroDescription]
                 ):
        self._physical_key_creator = physical_key_creator
        self._left_controller_pins = left_controller_pins
        self._right_controller_pins = right_controller_pins
        self._virtual_keys = virtual_keys
        self._virtual_key_order = [line.split() for line in virtual_key_order]
        self._layers = layers
        self._modifiers = modifiers
        self._macros = macros

        self._physical_key_map: dict[PinName, IPhysicalKey] = {}
        self._reaction_map: dict[ReactionName, ReactionData] = {}

    def create(self) -> VirtualKeyboard:
        self._reaction_map = dict(self._create_reaction_map())

        all_controller_pins = self._left_controller_pins | self._right_controller_pins
        #all_controller_pins = self._right_controller_pins  # todo
        self._physical_key_map = {
            pin_name: self._physical_key_creator(pin_name, pin_index)
                      if pin_name.startswith('right-') and not pin_name.endswith('x')
                      else DummyPhysicalKey(pin_name)
            for pin_name, pin_index in all_controller_pins.items()
        }
        # for pin_name, pin_index in self._left_controller_pins.items():
        #     self._physical_key_map[]

        simple_key_names = set(self._virtual_keys.keys()) - set(self._modifiers.keys()) - set(self._layers.keys())

        self._macros = {
            macro_name: self._create_macro(macro_desc)
            for macro_name, macro_desc in self._macros.items()
        }

        simple_keys = [self._create_simple_key(vkey_name)
                       for vkey_name in simple_key_names]
        mod_keys = [self._create_mod_key(vkey_name, mod_key_name)
                    for vkey_name, mod_key_name in self._modifiers.items()]
        layer_keys = [self._create_layer_key(vkey_name, lines)
                      for vkey_name, lines in self._layers.items() if vkey_name != '']

        all_vkeys = simple_keys + mod_keys + layer_keys
        self._build_dependencies(all_vkeys)

        return VirtualKeyboard(
            simple_keys=simple_keys,
            mod_keys= mod_keys,
            layer_keys=layer_keys,
            default_layer=dict(self._create_layer(self._layers[''])),
        )

    @staticmethod
    def _create_reaction_map() -> Iterator[tuple[ReactionName, ReactionData]]:
        for data in KEYCODES_DATA:
            key_code, en_reaction_without_shift, en_reaction_with_shift, de_reaction_without_shift, de_reaction_with_shift = data[:5]

            yield de_reaction_without_shift, ReactionData(key_code=key_code, with_shift=False)

            if de_reaction_with_shift != '':
                yield de_reaction_with_shift, ReactionData(key_code=key_code, with_shift=True)

            if len(data) >= 6:
                de_reaction_with_alt = data[5]
                yield de_reaction_with_alt, ReactionData(key_code=key_code, with_shift=False, with_alt=True)

        for i in range(26):
            key_code = KC.A + i
            en_lower_char = chr(ord('a') + i)
            en_upper_char = chr(ord('A') + i)

            if en_lower_char == 'y':
                de_lower_char = 'z'
                de_upper_char = 'Z'
            elif en_lower_char == 'z':
                de_lower_char = 'y'
                de_upper_char = 'Y'
            else:
                de_lower_char = en_lower_char
                de_upper_char = en_upper_char

            yield de_lower_char, ReactionData(key_code=key_code, with_shift=False)
            yield de_upper_char, ReactionData(key_code=key_code, with_shift=True)

            if de_lower_char == 'q':
                yield '@', ReactionData(key_code=key_code, with_shift=False, with_alt=True)

    def _create_macro(self, macro_desc: str) -> KeyReaction:
        pass  # todo: implement

    def _create_simple_key(self, key_name: VirtualKeyName) -> SimpleKey:
        pin_names = self._virtual_keys[key_name]

        return SimpleKey(key_name,
                         physical_keys=[self._physical_key_map[pin_name] for pin_name in pin_names])

    def _create_mod_key(self, key_name: VirtualKeyName, mod_key_name: VirtualKeyName) -> ModKey:
        pin_names = self._virtual_keys[key_name]
        mod_key_code = self._MOD_KEY_CODE_MAP[mod_key_name]

        return ModKey(key_name,
                      physical_keys=[self._physical_key_map[pin_name] for pin_name in pin_names],
                      mod_key_code=mod_key_code)

    def _create_layer_key(self, key_name: VirtualKeyName, lines: list[str]) -> LayerKey:
        pin_names = self._virtual_keys[key_name]
        layer = dict(self._create_layer(lines))

        return LayerKey(key_name,
                        physical_keys=[self._physical_key_map[pin_name] for pin_name in pin_names],
                        layer=layer)

    @staticmethod
    def _build_dependencies(all_vkeys: list[VirtualKey]) -> None:
        sorted_vkeys = sorted(all_vkeys, key=lambda vkey: len(vkey.physical_keys))

        n = len(sorted_vkeys)
        for i in range(n - 1):
            vkey1 = sorted_vkeys[i]
            for j in range(i + 1, n):
                vkey2 = sorted_vkeys[j]
                if vkey1 < vkey2:
                    vkey1.set_is_part_of_bigger_one(True)

    def _create_layer(self, lines: list[str]) -> Iterator[tuple[KeyName, KeyReaction]]:
        assert len(lines) == len(self._virtual_key_order)

        for line, key_order_in_row in zip(lines, self._virtual_key_order):
            items = line.split()
            assert len(items) == len(key_order_in_row)

            for item, key_name in zip(items, key_order_in_row):
                reaction = self._create_reaction(item)
                if reaction:
                    yield key_name, reaction

    def _create_reaction(self, reaction_name: ReactionName) -> KeyReaction | None:
        if reaction_name == '·':
            return None  # not set

        if reaction_name in self._macros:
            return None  # todo: implement

        assert reaction_name in self._reaction_map
        reaction_data: ReactionData = self._reaction_map[reaction_name]
        key_code = reaction_data.key_code
        press_cmd = KeyCmd(kind=KeyCmdKind.PRESS, key_code=key_code)
        release_cmd = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=key_code)

        if reaction_data.with_shift:
            shift_press_cmd = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.LEFT_SHIFT)
            shift_release_cmd = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.LEFT_SHIFT)
            return KeyReaction(on_press_key_sequence=[shift_press_cmd, press_cmd],
                               on_release_key_sequence=[release_cmd, shift_release_cmd])
        elif reaction_data.with_alt:
            alt_press_cmd = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.RIGHT_ALT)
            alt_release_cmd = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.RIGHT_ALT)
            return KeyReaction(on_press_key_sequence=[alt_press_cmd, press_cmd],
                               on_release_key_sequence=[release_cmd, alt_release_cmd])
        else:
            return KeyReaction(on_press_key_sequence=[press_cmd],
                               on_release_key_sequence=[release_cmd])
