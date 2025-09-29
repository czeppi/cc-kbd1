import unittest
from typing import Iterator

from virtualkeyboard import VirtualKey, PhysicalKey
from base import TimeInMs, PhysicalKeyName

type PhysicalKeyName = str   # upper case
type VirtualKeyName = str    # lower case
type VKeyPressStateTransientStr = str  # '-x', 'x-', '-?', '?-', '?x'


class VirtualKeyTestWithOnePhysicalKey(unittest.TestCase):
    LEFT_PINKY_UP = 'LeftPinkyUp'
    VKEY_NAME = 'a'

    def setUp(self):
        self._pkey = PhysicalKey(self.LEFT_PINKY_UP)
        self._vkey = VirtualKey(name=self.VKEY_NAME, physical_keys=[self._pkey])

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
        pkey.set_bound_by_vkey(None)
        chg = vkey.update_press_state(time=t1)
        self.assertFalse(chg)
        self.assertFalse(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=t1))
        self.assertFalse(vkey.is_begin_pressing(time=t1))
        self.assertFalse(vkey.is_end_pressing(time=t1))

        t2 = 20
        pkey.update(time=t2, will_be_pressed=True)
        pkey.set_bound_by_vkey(None)
        chg = vkey.update_press_state(time=t2)
        self.assertTrue(chg)

        self.assertTrue(vkey.will_be_pressed)
        self.assertFalse(vkey.was_pressed(time=t2))
        self.assertTrue(vkey.is_begin_pressing(time=t2))
        self.assertFalse(vkey.is_end_pressing(time=t2))

        t3 = 30
        pkey.set_bound_by_vkey(None)
        vkey.update_press_state(time=t3)
        self.assertTrue(vkey.will_be_pressed)
        self.assertTrue(vkey.was_pressed(time=t3))
        self.assertFalse(vkey.is_begin_pressing(time=t3))
        self.assertFalse(vkey.is_end_pressing(time=t3))

        t4 = 40
        pkey.update(time=t4, will_be_pressed=False)
        pkey.set_bound_by_vkey(None)
        vkey.update_press_state(time=t4)
        self.assertFalse(vkey.will_be_pressed)
        self.assertTrue(vkey.was_pressed(time=t4))
        self.assertFalse(vkey.is_begin_pressing(time=t4))
        self.assertTrue(vkey.is_end_pressing(time=t4))

        t5 = 50
        pkey.set_bound_by_vkey(None)
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
        self._pkey1 = PhysicalKey(self.LEFT_PINKY_UP)
        self._pkey2 = PhysicalKey(self.LEFT_PINKY_DOWN)
        self._vkey = VirtualKey(name=self.VKEY_NAME, physical_keys=[self._pkey1, self._pkey2])

    def test_positive(self) -> None:
        vkey = self._vkey
        pkey1, pkey2 = self._pkey1, self._pkey2

        # press pkey1
        t1 = 0
        pkey1.update(time=t1, will_be_pressed=True)
        pkey1.set_bound_by_vkey(None)
        pkey2.set_bound_by_vkey(None)
        vkey.update_press_state(time=t1)
        self.assertFalse(vkey.will_be_pressed)

        # press pkey2
        t2 = VirtualKey.COMBO_TERM - 1
        pkey2.update(time=t2, will_be_pressed=True)
        pkey1.set_bound_by_vkey(None)
        pkey2.set_bound_by_vkey(None)
        vkey.update_press_state(time=t2)
        self.assertTrue(vkey.will_be_pressed)  # => vkey pressed

    def test_negative(self) -> None:
        vkey = self._vkey
        pkey1, pkey2 = self._pkey1, self._pkey2

        # press pkey1
        t1 = 0
        pkey1.update(time=t1, will_be_pressed=True)
        pkey1.set_bound_by_vkey(None)
        pkey2.set_bound_by_vkey(None)
        vkey.update_press_state(time=t1)
        self.assertFalse(vkey.will_be_pressed)

        # press pkey2
        t2 = VirtualKey.COMBO_TERM + 1
        pkey2.update(time=t2, will_be_pressed=True)
        pkey1.set_bound_by_vkey(None)
        pkey2.set_bound_by_vkey(None)
        vkey.update_press_state(time=t2)
        self.assertFalse(vkey.will_be_pressed)  # => vkey NOT pressed

    def test_part_of_bigger_one(self) -> None:
        pass  # todo: implement


class VirtualKeyPressTestBase(unittest.TestCase):

    def _iter_pkeys(self) -> Iterator[PhysicalKey]:
        raise NotImplementedError()  # abstract

    def _iter_vkeys(self) -> Iterator[VirtualKey]:
        raise NotImplementedError()  # abstract

    def _step(self, time: TimeInMs,
              press: PhysicalKeyName | None = None,
              release: PhysicalKeyName | None = None,
              expect: dict[VirtualKeyName, VKeyPressStateTransientStr] | None = None
              ) -> None:
        # update keys
        self._update_pkeys(time=time, press_pkey=press, release_pkey=release)

        if expect is None:
            return   # no expect => no checks

        for vkey in self._iter_vkeys():
            vkey.update_press_state(time)

        # check
        actual_press_transient_strings = {}
        for vkey in self._iter_vkeys():
            if vkey.prev_press_state != vkey.cur_press_state:  # skip 'unchanged' case, to reduce length of expect_parameter
                actual_press_transient_strings[vkey.name] = f'{vkey.prev_press_state}{vkey.cur_press_state}'

        self.assertEqual(expect, actual_press_transient_strings)

    def _update_pkeys(self, time: TimeInMs,
                      press_pkey: PhysicalKeyName | None,
                      release_pkey: PhysicalKeyName | None
                      ) -> None:
        pkey_map = {pkey.name: pkey for pkey in self._iter_pkeys()}
        if press_pkey:
            pkey = pkey_map[press_pkey]
            pkey.update(time, will_be_pressed=True)
        if release_pkey:
            pkey = pkey_map[release_pkey]
            pkey.update(time=time, will_be_pressed=False)


class VirtualKeyPressTestSolo(VirtualKeyPressTestBase):

    def setUp(self):
        super().setUp()

        VirtualKey.COMBO_TERM = 50

        self._pkey1 = PhysicalKey('A')
        self._vkey1 = VirtualKey(name='a', physical_keys=[self._pkey1])

    def _iter_pkeys(self) -> Iterator[PhysicalKey]:
        yield self._pkey1

    def _iter_vkeys(self) -> Iterator[VirtualKey]:
        yield self._vkey1

    def test_simple(self):
        self._step(0, press='A', expect={'a': '-x'})
        self._step(10, release='A', expect={'a': 'x-'})


class VirtualKeyPressTest2Combo(VirtualKeyPressTestBase):

    def setUp(self):
        super().setUp()

        self._pkey1 = PhysicalKey('A')
        self._pkey2 = PhysicalKey('B')

        self._vkey1 = VirtualKey(name='a', physical_keys=[self._pkey1])
        self._vkey1.set_is_part_of_bigger_one(True)

        self._vkey2 = VirtualKey(name='b', physical_keys=[self._pkey2])
        self._vkey2.set_is_part_of_bigger_one(True)

        self._vkey12 = VirtualKey(name='c', physical_keys=[self._pkey1, self._pkey2])

    def _iter_pkeys(self) -> Iterator[PhysicalKey]:
        yield self._pkey1
        yield self._pkey2

    def _iter_vkeys(self) -> Iterator[VirtualKey]:  # in descending order
        yield self._vkey12  # must come first, cause it has the most pkeys
        yield self._vkey1
        yield self._vkey2

    def test_a_fast1(self):
        """       COMBO_TERM
        +--------------|--------------+
        |  +--------+  |              |
        |  |   a    |  |              |
        |  +--------+  |              |
        +--------------|--------------+
           |        |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(10, release='A', expect={'a': '?-'})

    # def test_a_fast2(self):
    #     """       COMBO_TERM
    #     +--------------|--------------+
    #     |  +--------+  |              |
    #     |  |   a    |  |              |
    #     |  +--------+  |              |
    #     +--------------|--------------+
    #                 |
    #     This can be happen, if this ia a TapHold Key
    #     """
    #     self._step(0, press='A')
    #     self._step(10, release='A', expect={'a': '?-'})

    def test_a_slow1(self):
        """       COMBO_TERM
        +--------------|----------------+
        | +------------|---+            |
        | |    a       |   |            |
        | +------------|---+            |
        +--------------|----------------+
          |              | |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(60, expect={'a': '?x'})
        self._step(70, release='A', expect={'a': 'x-'})

    def test_a_slow2(self):
        """       COMBO_TERM
        +--------------|----------------+
        | +------------|---+            |
        | |    a       |   |            |
        | +------------|---+            |
        +--------------|----------------+
          |                |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(70, release='A', expect={'a': '?-'})

    def test_a_unaware(self) -> None:
        """       COMBO_TERM
        +--------------|--------------+
        |    +----+    |              |
        |    | a  |    |              |
        |    +----+    |              |
        +--------------|--------------+
          |         |
        """
        self._step(0, press='A')  # no update
        self._step(30, release='A', expect={})

    def test_abba_fast(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
          | |      | |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(10, press='B', expect={'c': '-x'})  # reset a + b by c
        self._step(20, release='B', expect={'c': 'x-'})
        self._step(30, release='A', expect={})

    def test_abba_slow(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +------------|-------+      |
        | |      a     |       |      |
        | +------------|-------+      |
        |      +-------|---+          |
        |      |    b  |   |          |
        |      +-------|---+          |
        +--------------|--------------+
          |    |           |   |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(30, press='B', expect={'c': '-x'})  # reset a + b by c
        self._step(60, release='B', expect={'c': 'x-'})
        self._step(80, release='A', expect={})

    def test_abba3(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +------------|---------+    |
        | |      a     |         |    |
        | +------------|---------+    |
        |              | +---+        |
        |              | | b |        |
        |              | +---+        |
        +--------------|--------------+
          |              |   |   |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(60, press='B', expect={'a': '?x', 'b': '-?'})
        self._step(80, release='B')
        self._step(90, release='A',expect={'a': 'x-', 'b': '?-'})

    def test_abab_fast(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +-------+    |              |
        | |   a   |    |              |
        | +-------+    |              |
        |    +-------+ |              |
        |    |  b    | |              |
        |    +-------+ |              |
        +--------------|--------------+
          |  |    |  |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(10, press='B', expect={'c': '-x'})
        self._step(20, release='A', expect={'c': 'x-'})
        self._step(30, release='B', expect={})

    def test_abab_slow(self):
        """       COMBO_TERM1     COMBO_TERM2
        +--------------|--------------|--------------+
        | +------------|--------------|-+            |
        | |    a       |              | |            |
        | +------------|--------------|-+            |
        |              | +------------|----+         |
        |              | |  b         |    |         |
        |              | +------------|----+         |
        +--------------|--------------|--------------+
          |              |              |  |
        """
        self._step(0, press='A', expect={'a': '-?'})
        self._step(60, press='B', expect={'a': '?x', 'b': '-?'})
        self._step(120, release='A', expect={'a': 'x-', 'b': '?x'})
        self._step(130, release='B', expect={'b': 'x-'})
