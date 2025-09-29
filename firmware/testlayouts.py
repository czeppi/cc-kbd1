from keysdata import RIGHT_THUMB_DOWN, RIGHT_THUMB_UP, RTU, RTM, RTD, NO_KEY
from virtualkeyboard import VirtualKeyboard

try:
    from typing import Callable
except ImportError:
    pass


from keyboardcreator import KeyboardCreator


def create_thumb_up_keyboard() -> VirtualKeyboard:
    vkeys = {
        RTU: [RIGHT_THUMB_UP],
        RTM: [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
        RTD: [RIGHT_THUMB_DOWN],
    }

    key_order = [[RTU], [RTM], [RTD]]

    layers = {
        NO_KEY: ['Space', 'Backspace', 'Enter'],
        RTU: ['·', '·', '·'],
        RTD: ['·', '·', '·'],
        RTM: ['·', '·', '·'],
    }

    creator = KeyboardCreator(virtual_keys=vkeys,
                              virtual_key_order=key_order,
                              layers=layers,
                              modifiers={},
                              macros={},
                              )
    return creator.create()