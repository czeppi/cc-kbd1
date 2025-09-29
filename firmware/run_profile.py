import cProfile
import pstats
from typing import Iterator

from base import TimeInMs, PhysicalKeySerial
from kbdlayoutdata import VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator
from keysdata import LEFT_INDEX_DOWN
from virtualkeyboard import VirtualKeyboard


keyboard: VirtualKeyboard | None = None


def main():
    global keyboard

    creator = KeyboardCreator(virtual_keys=VIRTUAL_KEYS,
                              virtual_key_order=VIRTUAL_KEY_ORDER,
                              layers=LAYERS,
                              modifiers=MODIFIERS,
                              macros=MACROS,
                              )
    keyboard = creator.create()

    cProfile.run('simulate()', 'profiling_results.prof')
    p = pstats.Stats('profiling_results.prof')
    #p.strip_dirs().sort_stats('cumulative').print_stats(100)
    p.strip_dirs().sort_stats('tottime').print_stats(100)


def simulate() -> None:
    for _ in range(1000):
        for time, pressed_pkeys in iter_steps():
            act_key_seq = list(keyboard.update(time=time, pressed_pkeys=pressed_pkeys, pkey_update_time=time))


def iter_steps() -> Iterator[tuple[TimeInMs, set[PhysicalKeySerial]]]:
    yield 0, {LEFT_INDEX_DOWN}
    yield 30, {LEFT_INDEX_DOWN}
    yield 60, set()


main()