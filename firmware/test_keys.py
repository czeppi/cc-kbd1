from __future__ import annotations
import unittest

from keyboard import Keyboard, IAction, IButton, IClock


class TestButton(IButton):

    def __init__(self):
        self._is_pressed = False

    def is_pressed(self) -> bool:
        return self._is_pressed

    def set_pressed(self, is_pressed: bool):
        self._is_pressed = is_pressed


class TestClock(IClock):

    def __init__(self):
        self._value: float = 0.0

    @property
    def value(self) -> float:
        return self._value

    def set_value(self, value: float):
        self._value = value


class TestAction(IAction):

    def __init__(self, send_char: str, keyboard: TestKeyboard):
        self._send_char = send_char
        self._keyboard = keyboard

    def do(self) -> None:
        self._keyboard.send_key(self._send_char)


class TestKeyboard(Keyboard):

    def __init__(self, clock: IClock):
        super().__init__(clock)
        self._result = ''

    @property
    def result(self) -> str:
        return self._result

    def send_key(self, ch: str) -> None:
        self._result += ch


class SimpleKeyTest(unittest.TestCase):

    def setUp(self):
        self._clock = TestClock()
        self._button = TestButton()
        self._kbd = TestKeyboard(clock=self._clock)
        self._key = self._kbd.add_physical_key(button=self._button, action=TestAction('a', keyboard=self._kbd))

    def test_simple_key(self) -> None:
        self._step(10, pressed=True, expected_result='a')
        self._step(20, pressed=False, expected_result='a')

    def _step(self, clock_value: float, expected_result: str, pressed: bool | None = None) -> None:
        if pressed is not None:
            self._button.set_pressed(pressed)
        self._clock.set_value(clock_value)
        self._kbd.update()
        self.assertEqual(expected_result, self._kbd.result)


class ComboKeyTest(unittest.TestCase):

    def setUp(self):
        self._clock = TestClock()
        self._button1 = TestButton()
        self._button2 = TestButton()

        self._kbd = TestKeyboard(clock=self._clock)
        self._key1 = self._kbd.add_physical_key(button=self._button1, action=TestAction('a'))
        self._key2 = self._kbd.add_physical_key(button=self._button2, action=TestAction('b'))
        self._kbd.add_combo_key(physical_keys=[self._key1, self._key2], action=TestAction('c'))

    def test_a(self) -> None:
        self._step(10, pressed1=True, expected_result='')
        self._step(500, expected_result='a')
        self._step(510, pressed1=False, expected_result='a')

    def test_ab(self) -> None:
        self._step(10, pressed1=True, expected_result='')
        self._step(20, pressed2=True, expected_result='c')

    def test_aabb(self) -> None:
        self._step(10, pressed1=True, expected_result='')
        self._step(20, pressed1=False, expected_result='a')
        self._step(30, pressed2=True, expected_result='a')
        self._step(40, pressed2=False, expected_result='ab')

    def _step(self, clock_value: float, expected_result: str,
              pressed1: bool | None = None, pressed2: bool | None = None) -> None:
        if pressed1 is not None:
            self._button1.set_pressed(pressed1)
        if pressed2 is not None:
            self._button2.set_pressed(pressed2)
        self._clock.set_value(clock_value)
        self._kbd.update()
        self.assertEqual(expected_result, self._kbd.result)


class ModKeyTest(unittest.TestCase):
    """ s. https://docs.qmk.fm/tap_hold - this implements the PERMISSIVE_HOLD variant
    """

    def setUp(self):
        self._clock = TestClock()
        self._button1 = TestButton()
        self._button2 = TestButton()

        self._kbd = TestKeyboard(clock=self._clock)
        self._key1 = self._kbd.add_physical_key(button=self._button1, action=TestAction('a'))
        self._key2 = self._kbd.add_physical_key(button=self._button2, action=TestAction('b'))
        self._kbd.add_mod_key(key1=self._key1, key2=self._key2, action=TestAction('c'))

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
        self._step(0, pressed1=True, expected_result='')
        self._step(199, pressed1=False, expected_result='a')
        self._step(210, pressed2=True, expected_result='ab')
        self._step(220, pressed2=False, expected_result='ab')

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
        self._step(0, pressed1=True, expected_result='')
        self._step(201, pressed1=False, expected_result='')
        self._step(205, pressed2=True, expected_result='b')
        self._step(210, pressed2=False, expected_result='b')

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
        self._step(0, pressed1=True, expected_result='')
        self._step(110, pressed2=True, expected_result='')
        self._step(120, pressed2=False, expected_result='c')
        self._step(199, pressed1=False, expected_result='c')

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
        self._step(0, pressed1=True, expected_result='')
        self._step(110, pressed2=True, expected_result='')
        self._step(120, pressed2=False, expected_result='c')
        self._step(210, pressed1=False, expected_result='c')

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
        self._step(0, pressed1=True, expected_result='')
        self._step(205, pressed2=True, expected_result='c')
        self._step(210, pressed2=False, expected_result='c')
        self._step(220, pressed1=False, expected_result='c')

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
        self._step(0, pressed1=True, expected_result='')
        self._step(110, pressed2=True, expected_result='')
        self._step(130, pressed1=False, expected_result='ab')
        self._step(140, pressed2=False, expected_result='ab')

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

        self._step(0, pressed1=True, expected_result='')
        self._step(110, pressed2=True, expected_result='')
        self._step(205, pressed1=False, expected_result='c')
        self._step(210, pressed2=False, expected_result='c')

    def _step(self, clock_value: float, expected_result: str,
              pressed1: bool | None = None, pressed2: bool | None = None) -> None:
        if pressed1 is not None:
            self._button1.set_pressed(pressed1)
        if pressed2 is not None:
            self._button2.set_pressed(pressed2)
        self._clock.set_value(clock_value)
        self._kbd.update()
        self.assertEqual(expected_result, self._kbd.result)


if __name__ == '__main__':
    unittest.main()
