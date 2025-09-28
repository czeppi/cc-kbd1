import cProfile
import pstats

from kbdlayoutdata import VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator

cProfile.run('my_module.main()')

p = pstats.Stats('profiling_results.prof')
p.strip_dirs().sort_stats('cumulative').print_stats(10)


def main():
    creator = KeyboardCreator(virtual_keys=VIRTUAL_KEYS,
                              virtual_key_order=VIRTUAL_KEY_ORDER,
                              layers=LAYERS,
                              modifiers=MODIFIERS,
                              macros=MACROS,
                              )
    virt_keyboard = creator.create()