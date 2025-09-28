import unittest

from adafruit_hid.keycode import Keycode as KC


from kbdlayoutdata import VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator
from virtualkeyboard import KeyCmd, KeyCmdKind


class KeyboardCreatorTest(unittest.TestCase):

    def test_one_simple_key(self):
        creator = KeyboardCreator(virtual_keys={'lpu': ['left-pinky-up']},
                                  virtual_key_order=['lpu'],
                                  layers={'': ['a']},
                                  modifiers={},
                                  macros={},
                                  )
        keyboard = creator.create()
        pkeys = list(keyboard.iter_physical_keys())
        self.assertEqual(1, len(pkeys))

        act_key_seq = list(keyboard.update(time=210, pressed_pkeys={'left-pinky-up'}, pkey_update_time=0))
        expected_key_seq = [KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.A)]
        self.assertEqual(expected_key_seq, act_key_seq)

    def test_with_real_layout(self):
        creator = KeyboardCreator(virtual_keys=VIRTUAL_KEYS,
                                  virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  )
        keyboard = creator.create()
        pkeys = {pkey.name: pkey for pkey in keyboard.iter_physical_keys()}

        act_key_seq = list(keyboard.update(time=210, pressed_pkeys={'left-pinky-up'}, pkey_update_time=0))   # todo: not working with 10

        expected_key_seq = [KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.Q)]
        self.assertEqual(expected_key_seq, act_key_seq)
