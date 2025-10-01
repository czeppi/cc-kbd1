import unittest

from adafruit_hid.keycode import Keycode as KC
from base import KeyCode, TimeInMs, VirtualKeySerial, PhysicalKeySerial
from keyboardcreator2 import KeyboardCreator2
from keyboardhalf import TapHoldKey2, SimpleKey2, Layer, VirtualKeyboard2, ModKey2, VKeyPressEvent, KeyGroup, \
    KeyboardHalf
from virtualkeyboard import KeyCmd, KeyCmdKind, KeyReaction, KeySequence
from keysdata import RIGHT_THUMB_DOWN, RIGHT_THUMB_UP, RTU, RTM, RTD, NO_KEY, RT

A_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.A)
A_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.A)
B_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.B)
B_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.B)
SHIFT_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.LEFT_SHIFT)
SHIFT_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.LEFT_SHIFT)


class TapKeyTest(unittest.TestCase):
    VKEY_A = 1
    VKEY_B = 2

    def setUp(self):
        self._mod_key = ModKey2(serial=self.VKEY_A, mod_key_code=KC.LEFT_SHIFT)
        self._simple_key = SimpleKey2(serial=self.VKEY_B)
        default_layer: Layer = {
            self.VKEY_A: self._create_key_assignment(KC.A),
            self.VKEY_B: self._create_key_assignment(KC.B),
        }
        self._kbd =  VirtualKeyboard2(simple_keys=[self._simple_key], mod_keys=[self._mod_key], layer_keys=[],
                                      default_layer=default_layer)
        TapHoldKey2.TAP_HOLD_TERM = 200

    @staticmethod
    def _create_key_assignment(keycode: KeyCode) -> KeyReaction:
        return KeyReaction(on_press_key_sequence=[KeyCmd(kind=KeyCmdKind.PRESS, key_code=keycode)],
                           on_release_key_sequence=[KeyCmd(kind=KeyCmdKind.RELEASE, key_code=keycode)])

    def test_b_solo(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        |   +--------+ |              |
        |   |   b    | |              |
        |   +--------+ |              |
        +--------------|--------------+
        =>  b
        """
        self._step(0, press='b', expected_key_seq=[B_DOWN])
        self._step(100, release='b', expected_key_seq=[B_UP])

    def test_aabb_fast(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |              | +----------+ |
        |              | |    b     | |
        |              | +----------+ |
        +--------------|--------------+
        =>           a   b
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(199, release='a', expected_key_seq=[A_DOWN, A_UP])
        self._step(210, press='b', expected_key_seq=[B_DOWN])
        self._step(220, release='b', expected_key_seq=[B_UP])

    def test_aabb_slow(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |              |   +--------+ |
        |              |   |    b   | |
        |              |   +--------+ |
        +--------------|--------------+
        =>                 b
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, release='a', expected_key_seq=[SHIFT_UP])
        self._step(220, press='b', expected_key_seq=[B_DOWN])
        self._step(230, release='b', expected_key_seq=[B_UP])

    def test_abba1(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
        =>         c
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(110, press='b', expected_key_seq=[])
        self._step(120, release='b', expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(199, release='a', expected_key_seq=[SHIFT_UP])

    def test_abba2(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
        =>         c
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(110, press='b', expected_key_seq=[])
        self._step(120, release='b', expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(201, expected_key_seq=[])
        self._step(210, release='a', expected_key_seq=[SHIFT_UP])

    def test_abba3(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-------+      |
        | |    a       |       |      |
        | +------------|-------+      |
        |              | +---+        |
        |              | | b |        |
        |              | +---+        |
        +--------------|--------------+
        =>               c
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, press='b', expected_key_seq=[B_DOWN])
        self._step(220, release='b', expected_key_seq=[B_UP])
        self._step(230, release='a', expected_key_seq=[SHIFT_UP])

    def test_abab_fast(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +-------+    |              |
        | |   a   |    |              |
        | +-------+    |              |
        |    +-------+ |              |
        |    |  b    | |              |
        |    +-------+ |              |
        +--------------|--------------+
        =>        ab
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(110, press='b', expected_key_seq=[])
        self._step(130, release='a', expected_key_seq=[A_DOWN, A_UP, B_DOWN])
        self._step(140, release='b', expected_key_seq=[B_UP])

    def test_abab_slow(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |    +---------|----+         |
        |    |  b      |    |         |
        |    +---------|----+         |
        +--------------|--------------+
        =>               c
        """
        self._step(0, press='a', expected_key_seq=[])
        self._step(110, press='b', expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN, B_DOWN])
        self._step(210, release='a', expected_key_seq=[SHIFT_UP])
        self._step(220, release='b', expected_key_seq=[B_UP])

    def _step(self, time: TimeInMs, expected_key_seq: KeySequence,
              press: str | None = None, release: str | None = None) -> None:

        vkey_events: list[VKeyPressEvent] = []
        if press is not None:
            vkey_serial = self._get_vkey_serial_by_name(vkey_name=press)
            vkey_event = VKeyPressEvent(time, vkey_serial, pressed=True)
            vkey_events.append(vkey_event)
        elif release is not None:
            vkey_serial = self._get_vkey_serial_by_name(vkey_name=release)
            vkey_event = VKeyPressEvent(time, vkey_serial, pressed=False)
            vkey_events.append(vkey_event)

        act_key_seq = list(self._kbd.update(time=time, vkey_events=vkey_events))

        self.assertEqual(expected_key_seq, act_key_seq)

    def _get_vkey_serial_by_name(self, vkey_name: str) -> VirtualKeySerial:
        if vkey_name == 'a':
            return self.VKEY_A
        else:
            assert vkey_name == 'b'
            return self.VKEY_B


class ThumbUpKeyTest(unittest.TestCase):  # keyboard with only 'thumb-up' key
    """ like real keyboard, but only with the Thumb-Up-key

    """
    _SPACE_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.SPACE)
    _SPACE_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.SPACE)

    def setUp(self):
        self._kbd_half = self._create_kbd_half()
        self._virt_keyboard = self._create_keyboard()
        self._pressed_pkeys: set[PhysicalKeySerial] = set()

        KeyGroup.COMBO_TERM = 50
        TapHoldKey2.TAP_HOLD_TERM = 200

    @staticmethod
    def _create_kbd_half() -> KeyboardHalf:
        rt_group = KeyGroup(RT, {
                        RTU: [RIGHT_THUMB_UP],
                        RTM: [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
                        RTD: [RIGHT_THUMB_DOWN],
                    })
        return KeyboardHalf(key_groups=[rt_group])

    @staticmethod
    def _create_keyboard() -> VirtualKeyboard2:
        key_order = [[RTU], [RTM], [RTD]]

        layers = {
            NO_KEY: ['Space', 'Backspace', 'Enter'],
            RTU: ['·', '·', '·'],
            RTD: ['·', '·', '·'],
            RTM: ['·', '·', '·'],
        }

        creator = KeyboardCreator2(virtual_key_order=key_order,
                                   layers=layers,
                                   modifiers={},
                                   macros={},
                                   )
        return creator.create()

    def test_press_short1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(20, release='rtu', expected_key_seq=[self._SPACE_DOWN, self._SPACE_UP])

    def test_press_short2(self):
        self._step(00, press='rtu', expected_key_seq=[])
        self._step(10, expected_key_seq=[])
        self._step(20, release='rtu', expected_key_seq=[self._SPACE_DOWN, self._SPACE_UP])

    def test_press_longer_as_combo_term1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(70, release='rtu', expected_key_seq=[self._SPACE_DOWN, self._SPACE_UP])

    def test_press_longer_as_combo_term2(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(60, expected_key_seq=[])
        self._step(70, release='rtu', expected_key_seq=[self._SPACE_DOWN, self._SPACE_UP])

    def test_press_longer_as_hold_term1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(300, release='rtu', expected_key_seq=[self._SPACE_DOWN, self._SPACE_UP])  # ???

    def test_press_longer_as_hold_term2(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(60, expected_key_seq=[])
        self._step(270, expected_key_seq=[])
        self._step(300, release='rtu', expected_key_seq=[])

    def _step(self, time: TimeInMs, expected_key_seq: KeySequence, press='', release=''):
        if press == 'rtu':
            self._pressed_pkeys.add(RIGHT_THUMB_UP)
        elif release == 'rtu':
            self._pressed_pkeys.remove(RIGHT_THUMB_UP)

        vkey_events = list(self._kbd_half.update(time, cur_pressed_pkeys=self._pressed_pkeys))
        act_key_seq = list(self._virt_keyboard.update(time=time, vkey_events=vkey_events))

        self.assertEqual(expected_key_seq, act_key_seq)