import unittest

from adafruit_hid.keycode import Keycode as KC
from base import PinName, TimeInMs, KeyCode
from testlayouts import create_thumb_up_keyboard

from virtualkeyboard import VirtualKeyboard, ModKey, SimpleKey, Layer, \
    KeyReaction, KeyCmd, KeyCmdKind, TapHoldKey, KeySequence, PhysicalKey, VirtualKey

A_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.A)
A_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.A)
B_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.B)
B_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.B)
SHIFT_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.LEFT_SHIFT)
SHIFT_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.LEFT_SHIFT)


class ThumbUpKeyTest(unittest.TestCase):  # keyboard with only 'thumb-up' key
    """ like real keyboard, but only with the Thumb-Up-key

    """
    _SPACE_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.SPACE)
    _SPACE_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.SPACE)

    def setUp(self):
        self._virt_keyboard = create_thumb_up_keyboard()
        self._rtu = self._find_pkey('right-thumb-up')
        self._pressed_pkeys: set[PinName] = set()

        VirtualKey.COMBO_TERM = 50
        TapHoldKey.TAP_HOLD_TERM = 200

    def _find_pkey(self, pkey_name: PinName) -> PhysicalKey | None:
        for pkey in self._virt_keyboard.iter_physical_keys():
            if pkey_name == pkey.name:
                assert isinstance(pkey, PhysicalKey)
                return pkey

        return None

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
            self._pressed_pkeys.add(self._rtu.name)
        elif release == 'rtu':
            self._pressed_pkeys.remove(self._rtu.name)

        act_key_seq = list(self._virt_keyboard.update(time=time, pressed_pkeys=self._pressed_pkeys, pkey_update_time=time))

        self.assertEqual(expected_key_seq, act_key_seq)


class TapKeyTest(unittest.TestCase):
    VKEY_A = 'a'
    VKEY_B = 'b'

    def setUp(self):
        self._pkey1 = PhysicalKey('A')
        self._pkey2 = PhysicalKey('B')

        self._mod_key = ModKey(name=self.VKEY_A, physical_keys=[self._pkey1],
                               mod_key_code=KC.LEFT_SHIFT)
        self._simple_key = SimpleKey(name=self.VKEY_B, physical_keys=[self._pkey2])
        default_layer: Layer = {
            self.VKEY_A: self._create_key_assignment(KC.A),
            self.VKEY_B: self._create_key_assignment(KC.B),
        }
        self._kbd = VirtualKeyboard(simple_keys=[self._simple_key], mod_keys=[self._mod_key], layer_keys=[],
                                    default_layer=default_layer)
        self._pkey_pressed_keys: set[PinName] = set()
        TapHoldKey.TAP_HOLD_TERM = 200

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
        self._step(0, press=2, expected_key_seq=[B_DOWN])
        self._step(100, release=2, expected_key_seq=[B_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(199, release=1, expected_key_seq=[A_DOWN, A_UP])
        self._step(210, press=2, expected_key_seq=[B_DOWN])
        self._step(220, release=2, expected_key_seq=[B_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, release=1, expected_key_seq=[SHIFT_UP])
        self._step(220, press=2, expected_key_seq=[B_DOWN])
        self._step(230, release=2, expected_key_seq=[B_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(110, press=2, expected_key_seq=[])
        self._step(120, release=2, expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(199, release=1, expected_key_seq=[SHIFT_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(110, press=2, expected_key_seq=[])
        self._step(120, release=2, expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(201, expected_key_seq=[])
        self._step(210, release=1, expected_key_seq=[SHIFT_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, press=2, expected_key_seq=[B_DOWN])
        self._step(220, release=2, expected_key_seq=[B_UP])
        self._step(230, release=1, expected_key_seq=[SHIFT_UP])

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
        self._step(0, press=1, expected_key_seq=[])
        self._step(110, press=2, expected_key_seq=[])
        self._step(130, release=1, expected_key_seq=[A_DOWN, A_UP, B_DOWN])
        self._step(140, release=2, expected_key_seq=[B_UP])

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

        self._step(0, press=1, expected_key_seq=[])
        self._step(110, press=2, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN, B_DOWN])
        self._step(210, release=1, expected_key_seq=[SHIFT_UP])
        self._step(220, release=2, expected_key_seq=[B_UP])

    def _step(self, time: TimeInMs, expected_key_seq: KeySequence,
              press: int | None = None, release: int | None = None) -> None:

        if press is not None:
            pkey = self._get_physical_key(serial=press)
            self._pkey_pressed_keys.add(pkey.name)
        elif release is not None:
            pkey = self._get_physical_key(serial=release)
            self._pkey_pressed_keys.remove(pkey.name)

        act_key_seq = list(self._kbd.update(time=time, pressed_pkeys=self._pkey_pressed_keys, pkey_update_time=time))

        self.assertEqual(expected_key_seq, act_key_seq)

    def _get_physical_key(self, serial: int) -> PhysicalKey:
        if serial == 1:
            return self._pkey1
        else:
            assert serial == 2
            return self._pkey2
