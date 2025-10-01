from base import VirtualKeySerial
from keyboardcreator import ReactionData, KEYCODES_DATA
from keyboardhalf import VirtualKeyboard2, ModKey2, SimpleKey2, LayerKey2
from keysdata import NO_KEY

try:
    from typing import Callable, Iterator
except ImportError:
    pass

from adafruit_hid.keycode import Keycode as KC

from virtualkeyboard import KeyReaction, KeyCmd, KeyCmdKind

MacroName = str  # p.e. 'M3'
MacroDescription = str
ModKeyName = str  # p.e. 'LCtrl'
ReactionName = str  # p.e. 'a', '$', 'M5'


class KeyboardCreator2:
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

    def __init__(self, virtual_key_order: list[list[VirtualKeySerial]],
                 layers: dict[VirtualKeySerial, list[str]],
                 modifiers: dict[VirtualKeySerial, ModKeyName],
                 macros: dict[MacroName, MacroDescription]
                 ):
        self._virtual_key_order = virtual_key_order
        self._layers = layers
        self._modifiers = modifiers
        self._macros = macros

        self._reaction_map: dict[ReactionName, ReactionData] = {}

    def create(self) -> VirtualKeyboard2:
        self._reaction_map = dict(self._create_reaction_map())

        all_vkey_serials = {vkey_serial
                            for vkey_row in self._virtual_key_order
                            for vkey_serial in vkey_row}

        simple_key_serials = all_vkey_serials - set(self._modifiers.keys()) - set(self._layers.keys())

        self._macros = {
            macro_name: self._create_macro(macro_desc)
            for macro_name, macro_desc in self._macros.items()
        }

        simple_keys = [self._create_simple_key(vkey_serial)
                       for vkey_serial in simple_key_serials]
        mod_keys = [self._create_mod_key(vkey_serial, mod_key_name)
                    for vkey_serial, mod_key_name in self._modifiers.items()]
        layer_keys = [self._create_layer_key(vkey_serial, lines)
                      for vkey_serial, lines in self._layers.items() if vkey_serial != NO_KEY]

        return VirtualKeyboard2(
            simple_keys=simple_keys,
            mod_keys= mod_keys,
            layer_keys=layer_keys,
            default_layer=dict(self._create_layer(self._layers[NO_KEY])),
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

    @staticmethod
    def _create_simple_key(vkey_serial: VirtualKeySerial) -> SimpleKey2:
        return SimpleKey2(vkey_serial)

    def _create_mod_key(self, vkey_serial: VirtualKeySerial, mod_key_name: ModKeyName) -> ModKey2:
        mod_key_code = self._MOD_KEY_CODE_MAP[mod_key_name]

        return ModKey2(vkey_serial, mod_key_code=mod_key_code)

    def _create_layer_key(self, vkey_serial: VirtualKeySerial, lines: list[str]) -> LayerKey2:
        layer = dict(self._create_layer(lines))

        return LayerKey2(vkey_serial, layer=layer)

    def _create_layer(self, lines: list[str]) -> Iterator[tuple[VirtualKeySerial, KeyReaction]]:
        assert len(lines) == len(self._virtual_key_order)

        for line, key_order_in_row in zip(lines, self._virtual_key_order):
            items = line.split()
            if len(items) != len(key_order_in_row):
                pass
            assert len(items) == len(key_order_in_row)

            for item, vkey_serial in zip(items, key_order_in_row):
                reaction = self._create_reaction(item)
                if reaction:
                    yield vkey_serial, reaction

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
