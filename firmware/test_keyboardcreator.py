import unittest

from adafruit_hid.keycode import Keycode as KC

from dummyphysicalkey import DummyPhysicalKey
from kbdlayoutdata import LEFT_CONTROLLER_PINS, RIGHT_CONTROLLER_PINS, VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator
from virtualkeyboard import IPhysicalKey, KeyCmd, KeyCmdKind
from base import KeyName


class KeyboardCreatorTest(unittest.TestCase):

    def test_one_simple_key(self):
        creator = KeyboardCreator(physical_key_creator=_create_physical_key,
                                  left_controller_pins={'left-pinky-up': 5},
                                  right_controller_pins={},
                                  virtual_keys={'lpu': ['left-pinky-up']},
                                  virtual_key_order=['lpu'],
                                  layers={'': ['a']},
                                  modifiers={},
                                  macros={},
                                  )
        keyboard = creator.create()
        pkeys = list(keyboard.iter_physical_keys())
        self.assertEqual(1, len(pkeys))

        pkey = pkeys[0]
        assert isinstance(pkey, DummyPhysicalKey)

        pkey.press(time=0)
        pkey.press(time=0)

        act_key_seq = list(keyboard.update(time=210))
        expected_key_seq = [KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.A)]
        self.assertEqual(expected_key_seq, act_key_seq)

    def test_with_real_layout(self):
        creator = KeyboardCreator(physical_key_creator=_create_physical_key,
                                  left_controller_pins=LEFT_CONTROLLER_PINS,
                                  right_controller_pins=RIGHT_CONTROLLER_PINS,
                                  virtual_keys=VIRTUAL_KEYS,
                                  virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  )
        keyboard = creator.create()
        pkeys = {pkey.name: pkey for pkey in keyboard.iter_physical_keys()}

        pkey = pkeys['left-pinky-up']
        assert isinstance(pkey, DummyPhysicalKey)

        pkey.press(time=0)
        act_key_seq = list(keyboard.update(time=210))   # todo: not working with 10

        expected_key_seq = [KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.Q)]
        self.assertEqual(expected_key_seq, act_key_seq)


def _create_physical_key(key_name: KeyName, serial: int) -> IPhysicalKey:
    return DummyPhysicalKey(key_name)
