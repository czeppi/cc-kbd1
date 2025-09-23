import unittest

from adafruit_hid.keycode import Keycode as KC
from dummyphysicalkey import DummyPhysicalKey

from virtualkeyboard import TimeInMs, VirtualKey, VirtualKeyboard, ModKey, SimpleKey, Layer, \
    KeyReaction, KeyCmd, KeyCmdKind, KeyCode, TapHoldKey, KeySequence


class VirtualKeyTestWithOnePhysicalKey(unittest.TestCase):
    LEFT_PINKY_UP = 'LeftPinkyUp'
    VKEY_NAME = 'a'

    def setUp(self):
        self._pkey = DummyPhysicalKey(self.LEFT_PINKY_UP)
        self._vkey = VirtualKey(name=self.VKEY_NAME, physical_keys=[self._pkey], is_part_of_bigger_one=False)

    def test_initial(self) -> None:
        vkey = self._vkey

        self.assertEqual(self.VKEY_NAME, vkey.name)
        self.assertEqual([self.LEFT_PINKY_UP], [pkey.name for pkey in self._vkey.physical_keys])
        self.assertFalse(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=0))
        self.assertFalse(vkey.is_begin_pressing(time=0))
        self.assertFalse(vkey.is_end_pressing(time=0))

    def test_one_press_and_one_release(self) -> None:
        pkey = self._pkey
        vkey = self._vkey

        t1 = 10
        pkey.set_bound(False)
        chg = vkey.update_press_state(time=t1)
        self.assertFalse(chg)
        self.assertFalse(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=t1))
        self.assertFalse(vkey.is_begin_pressing(time=t1))
        self.assertFalse(vkey.is_end_pressing(time=t1))

        t2 = 20
        pkey.press(time=t2)
        pkey.set_bound(False)
        chg = vkey.update_press_state(time=t2)
        self.assertTrue(chg)

        self.assertTrue(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=t2))
        self.assertTrue(vkey.is_begin_pressing(time=t2))
        self.assertFalse(vkey.is_end_pressing(time=t2))

        t3 = 30
        pkey.set_bound(False)
        vkey.update_press_state(time=t3)
        self.assertTrue(vkey.will_be_pressed)
        self.assertTrue(vkey.was_pressed(time=t3))
        self.assertFalse(vkey.is_begin_pressing(time=t3))
        self.assertFalse(vkey.is_end_pressing(time=t3))

        t4 = 40
        pkey.release()
        pkey.set_bound(False)
        vkey.update_press_state(time=t4)
        self.assertFalse(vkey.will_be_pressed)
        self.assertTrue(vkey.was_pressed(time=t4))
        self.assertFalse(vkey.is_begin_pressing(time=t4))
        self.assertTrue(vkey.is_end_pressing(time=t4))

        t5 = 50
        pkey.set_bound(False)
        vkey.update_press_state(time=t5)
        self.assertFalse(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=t5))
        self.assertFalse(vkey.is_begin_pressing(time=t5))
        self.assertFalse(vkey.is_end_pressing(time=t5))


class VirtualKeyTestWithTwoPhysicalKey(unittest.TestCase):
    LEFT_PINKY_UP = 'LeftPinkyUp'
    LEFT_PINKY_DOWN = 'LeftPinkyDown'
    VKEY_NAME = 'a'

    def setUp(self):
        self._pkey1 = DummyPhysicalKey(self.LEFT_PINKY_UP)
        self._pkey2 = DummyPhysicalKey(self.LEFT_PINKY_DOWN)
        self._vkey = VirtualKey(name=self.VKEY_NAME, physical_keys=[self._pkey1, self._pkey2], is_part_of_bigger_one=False)

    def test_positive(self) -> None:
        vkey = self._vkey
        pkey1, pkey2 = self._pkey1, self._pkey2

        # press pkey1
        t1 = 0
        pkey1.press(time=t1)
        pkey1.set_bound(False)
        pkey2.set_bound(False)
        vkey.update_press_state(time=t1)
        self.assertFalse(vkey.will_be_pressed)

        # press pkey2
        t2 = VirtualKey.COMBO_TERM - 1
        pkey2.press(time=t2)
        pkey1.set_bound(False)
        pkey2.set_bound(False)
        vkey.update_press_state(time=t2)
        self.assertTrue(vkey.will_be_pressed)  # => vkey pressed

    def test_negative(self) -> None:
        vkey = self._vkey
        pkey1, pkey2 = self._pkey1, self._pkey2

        # press pkey1
        t1 = 0
        pkey1.press(time=t1)
        pkey1.set_bound(False)
        pkey2.set_bound(False)
        vkey.update_press_state(time=t1)
        self.assertFalse(vkey.will_be_pressed)

        # press pkey2
        t2 = VirtualKey.COMBO_TERM + 1
        pkey2.press(time=t2)
        pkey1.set_bound(False)
        pkey2.set_bound(False)
        vkey.update_press_state(time=t2)
        self.assertFalse(vkey.will_be_pressed)  # => vkey NOT pressed

    def test_part_of_bigger_one(self) -> None:
        pass  # todo: implement


A_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.A)
A_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.A)
B_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.B)
B_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.B)
SHIFT_DOWN = KeyCmd(kind=KeyCmdKind.PRESS, key_code=KC.LEFT_SHIFT)
SHIFT_UP = KeyCmd(kind=KeyCmdKind.RELEASE, key_code=KC.LEFT_SHIFT)


class TapKeyTest(unittest.TestCase):
    VKEY_A = 'a'
    VKEY_B = 'b'

    def setUp(self):
        self._pkey1 = DummyPhysicalKey('A')
        self._pkey2 = DummyPhysicalKey('B')
        self._vkey_a = VirtualKey(name=self.VKEY_A, physical_keys=[self._pkey1], is_part_of_bigger_one=False)
        self._vkey_b = VirtualKey(name=self.VKEY_B, physical_keys=[self._pkey2], is_part_of_bigger_one=False)

        self._key1 = ModKey(name=self.VKEY_A, physical_keys=[self._pkey1], is_part_of_bigger_one=False,
                            mod_key_code=KC.LEFT_SHIFT)
        self._key2 = SimpleKey(name=self.VKEY_B, physical_keys=[self._pkey2], is_part_of_bigger_one=False)
        default_layer: Layer = {
            self.VKEY_A: self._create_key_assignment(KC.A),
            self.VKEY_B: self._create_key_assignment(KC.B),
        }
        self._kbd = VirtualKeyboard(simple_keys=[self._key2], mod_keys=[self._key1], layer_keys=[],
                                    default_layer=default_layer)
        TapHoldKey.TAP_HOLD_TERM = 200

    @staticmethod
    def _create_key_assignment(keycode: KeyCode) -> KeyReaction:
        return KeyReaction(on_press_key_sequence=[KeyCmd(kind=KeyCmdKind.PRESS, key_code=keycode)],
                           on_release_key_sequence=[KeyCmd(kind=KeyCmdKind.RELEASE, key_code=keycode)])

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
            pkey.press(time=time)
        elif release is not None:
            pkey = self._get_physical_key(serial=release)
            pkey.release()

        act_key_seq = list(self._kbd.update(time=time))

        self.assertEqual(expected_key_seq, act_key_seq)

    def _get_physical_key(self, serial: int) -> DummyPhysicalKey:
        if serial == 1:
            return self._pkey1
        else:
            assert serial == 2
            return self._pkey2
