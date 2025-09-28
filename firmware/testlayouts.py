from virtualkeyboard import PhysicalKey, VirtualKeyboard

try:
    from typing import Callable
except ImportError:
    pass

try:
    import board
    GP20 = board.GP20
    GP21 = board.GP21
except ImportError:
    GP20 = 20
    GP21 = 21


from keyboardcreator import KeyboardCreator


def create_thumb_up_keyboard() -> VirtualKeyboard:
    pins = {
        'right-thumb-up': GP21,
        'right-thumb-down': GP20,
    }
    vkeys = {
        'rtu': ['right-thumb-up'],
        'rtm': ['right-thumb-up', 'right-thumb-down'],
        'rtd': ['right-thumb-down'],
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