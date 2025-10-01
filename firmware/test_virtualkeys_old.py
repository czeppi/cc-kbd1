import unittest
from typing import Iterator

from keysdata import LEFT_PINKY_UP, LEFT_PINKY_DOWN
from virtualkeyboard import VirtualKey, PhysicalKey
from base import TimeInMs, PhysicalKeySerial, VirtualKeySerial

type VKeyPressStateTransientStr = str  # '-x', 'x-', '-?', '?-', '?x'


PKEY_A = 1
PKEY_B = 2

VKEY_A = 1
VKEY_B = 2
VKEY_C = 3



class VirtualKeyTestWithOnePhysicalKey(unittest.TestCase):
    VKEY_SERIAL = VKEY_A

    def setUp(self):
        self._pkey = PhysicalKey(LEFT_PINKY_UP)
        self._vkey = VirtualKey(serial=self.VKEY_SERIAL, physical_keys=[self._pkey])

    def test_initial(self) -> None:
        vkey = self._vkey

        self.assertEqual(self.VKEY_SERIAL, vkey.serial)
        self.assertEqual([LEFT_PINKY_UP], [pkey.serial for pkey in self._vkey.physical_keys])
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
    VKEY_NAME = VKEY_A

    def setUp(self):
        self._pkey1 = PhysicalKey(LEFT_PINKY_UP)
        self._pkey2 = PhysicalKey(LEFT_PINKY_DOWN)
        self._vkey = VirtualKey(serial=self.VKEY_NAME, physical_keys=[self._pkey1, self._pkey2])

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
              press: PhysicalKeySerial | None = None,
              release: PhysicalKeySerial | None = None,
              expect: dict[VirtualKeySerial, VKeyPressStateTransientStr] | None = None
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
                actual_press_transient_strings[vkey.serial] = f'{vkey.prev_press_state}{vkey.cur_press_state}'

        self.assertEqual(expect, actual_press_transient_strings)

    def _update_pkeys(self, time: TimeInMs,
                      press_pkey: PhysicalKeySerial | None,
                      release_pkey: PhysicalKeySerial | None
                      ) -> None:
        pkey_map = {pkey.serial: pkey for pkey in self._iter_pkeys()}
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

        self._pkey1 = PhysicalKey(PKEY_A)
        self._vkey1 = VirtualKey(serial=VKEY_A, physical_keys=[self._pkey1])

    def _iter_pkeys(self) -> Iterator[PhysicalKey]:
        yield self._pkey1

    def _iter_vkeys(self) -> Iterator[VirtualKey]:
        yield self._vkey1

    def test_simple(self):
        self._step(0, press=PKEY_A, expect={VKEY_A: '-x'})
        self._step(10, release=PKEY_A, expect={VKEY_A: 'x-'})



