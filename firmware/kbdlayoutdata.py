#import board
from keysdata import *

# following combination are possible (ChatGPT)
#
# SPI0:
# SCK : GP2, GP6, GP18   # SPI0 SC/SCK
# MOSI: GP3, GP7, GP19   # SPI0 TX
# MISO: GP0, GP4, GP16   # SPI0 RX
# CS:   GP0 - GP28
#
# SPI1:
# SCK:  GP10, GP14   # SPI1 SCK
# MOSI: GP11, GP15   # SPI1 TX
# MISO: GP8,  GP12   # SPI1 RX
# CS:   GP0 - GP28

# MOSI(TX) = Microcontroler OUT - Sensor IN
# MISO(RX) = Microcontroler IN - Sensor OUT
# TX = out
# RX = in


# following TX/RX combination are possible (ChatGPT)
#        TX               RX
# UART0  GP0, GP12, GP16  GP1, GP13, GP17
# UART1  GP4, GP8,  GP20  GP5, GP9,  GP21

# UART0:
# TX: GP0, GP12, GP16
# RX: GP1, GP13, GP17

# UART1:
# TX: GP4, GP8,  GP20?  # GP20 not in data sheet
# RX: GP5, GP9,  GP21?  # GP21 not in data sheet



# KEY_GROUPS = {  # !! preparing !!
#     'lp': {
#         'lpu': ['left-pinky-up'],
#         'lpm': ['left-pinky-up', 'left-pinky-down'],
#         'lpd': ['left-pinky-down'],
#     },
#     #...
#     'li': {
#         'li1u': ['left-index-up'],
#         'li1m': ['left-index-up', 'left-index-down'],
#         'li1d': ['left-index-down'],
#         'li2u': ['left-index-up', 'left-index-right'],
#         'li2m': ['left-index-right'],
#         'li2d': ['left-index-down', 'left-index-right'],
#     },
# }


VIRTUAL_KEYS = {
    'lpu': [LEFT_PINKY_UP],
    'lpm': [LEFT_PINKY_UP, LEFT_PINKY_DOWN],
    'lpd': [LEFT_PINKY_DOWN],
    'lru': [LEFT_RING_UP],
    'lrm': [LEFT_RING_UP, LEFT_RING_DOWN],
    'lrd': [LEFT_RING_DOWN],
    'lmu': [LEFT_MIDDLE_UP],
    'lmm': [LEFT_MIDDLE_UP, LEFT_MIDDLE_DOWN],
    'lmd': [LEFT_MIDDLE_DOWN],
    'li1u': [LEFT_INDEX_UP],
    'li1m': [LEFT_INDEX_UP, LEFT_INDEX_DOWN],
    'li1d': [LEFT_INDEX_DOWN],
    'li2u': [LEFT_INDEX_UP, LEFT_INDEX_RIGHT],
    'li2m': [LEFT_INDEX_RIGHT],
    'li2d': [LEFT_INDEX_DOWN, LEFT_INDEX_RIGHT],
    'ltu': [LEFT_THUMB_UP],
    'ltm': [LEFT_THUMB_UP, LEFT_THUMB_DOWN],
    'ltd': [LEFT_THUMB_DOWN],
    'rtu': [RIGHT_THUMB_UP],
    'rtm': [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
    'rtd': [RIGHT_THUMB_DOWN],
    'ri2u': [RIGHT_INDEX_UP, RIGHT_INDEX_LEFT],
    'ri2m': [RIGHT_INDEX_LEFT],
    'ri2d': [RIGHT_INDEX_DOWN, RIGHT_INDEX_LEFT],
    'ri1u': [RIGHT_INDEX_UP],
    'ri1m': [RIGHT_INDEX_UP, RIGHT_INDEX_DOWN],
    'ri1d': [RIGHT_INDEX_DOWN],
    'rmu': [RIGHT_MIDDLE_UP],
    'rmm': [RIGHT_MIDDLE_UP, RIGHT_MIDDLE_DOWN],
    'rmd': [RIGHT_MIDDLE_DOWN],
    'rru': [RIGHT_RING_UP],
    'rrm': [RIGHT_RING_UP, RIGHT_RING_DOWN],
    'rrd': [RIGHT_RING_DOWN],
    'rpu': [RIGHT_PINKY_UP],
    'rpm': [RIGHT_PINKY_UP, RIGHT_PINKY_DOWN],
    'rpd': [RIGHT_PINKY_DOWN],
}

VIRTUAL_KEY_ORDER = [
    'lpu lru lmu li1u li2u ltu   rtu ri2u ri1u rmu rru rpu',
    'lpm lrm lmm li1m li2m ltm   rtm ri2m ri1m rmm rrm rpm',
    'lpd lrd lmd li1d li2d ltd   rtd ri2d ri1d rmd rrd rpd',
]


LAYERS = {
    '': [
        'q w e r t Space   Space      z u i o p',
        'a s d f g Del     Backspace  h j k l ö',
        'y x c v b Tab     Enter      n m , . -',
    ],
    'ltu': [
        '· · · · · ·   · @ " { } `',
        '· · · · · ·   · \\ / ( ) $',
        "· · · · · ·   · # ' [ ] ´",
    ],
    'ltd': [
        '· · · · · ·   · + 7 8 9 %',
        '· · · · · ·   · - 4 5 6 ,',
        '· · · · · ·   0 · 1 2 3 .',
    ],
    'rtu': [
        '· · · · · ·   · · F1 F2  F3  F4',
        '· · · · · ·   · · F5 F6  F7  F8',
        '· · · · · ·   · · F9 F10 F11 F12',
    ],
    'rtd': [
        '/ * < ^ | ·   · · · · · ·',
        '% + ! = & ·   · · · · · ·',
        '· > l ? ~ ·   · · · · · ·',
    ],
    'rtm': [
        '· · M5 M2 M4 ·   · · PageUp   Home Up   End',
        '· · ·  ·  M0 ·   · · PageDown Left Down Right',
        '· · ·  ·  M1 ·   · · ·        ·    ·    ·',
    ],
}

MODIFIERS = {
    'li1d': 'LShift',
    'lmd': 'LCtrl',
    'lrd': 'LAlt',
    'lpd': 'LGui',
    'ri1d': 'LShift',
    'rmd': 'LCtrl',
    'rrd': 'LAlt',
    'rpd': 'LGui',
}

MACROS = {
    'M0': 'x x x',
    'M1': 'x x x',
    'M2': 'x x x',
    'M3': 'x x x',
    'M4': 'x x x',
    'M5': 'x x x',
}