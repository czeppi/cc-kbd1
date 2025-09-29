from keysdata import RIGHT_THUMB_DOWN, RIGHT_THUMB_UP
from virtualkeyboard import VirtualKeyboard

try:
    from typing import Callable
except ImportError:
    pass


from keyboardcreator import KeyboardCreator


def create_thumb_up_keyboard() -> VirtualKeyboard:
    vkeys = {
        'rtu': [RIGHT_THUMB_UP],
        'rtm': [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
        'rtd': [RIGHT_THUMB_DOWN],
    }

    key_order = ['rtu', 'rtm', 'rtd']

    layers = {
        '': ['Space', 'Backspace', 'Enter'],
        'rtu': ['·', '·', '·'],
        'rtd': ['·', '·', '·'],
        'rtm': ['·', '·', '·'],
    }

    creator = KeyboardCreator(virtual_keys=vkeys,
                              virtual_key_order=key_order,
                              layers=layers,
                              modifiers={},
                              macros={},
                              )
    return creator.create()