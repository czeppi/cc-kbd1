import board

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


LEFT_CONTROLLER_PINS = {
    'left-tx': board.GP0,
    'left-rx': board.GP1,
    'left-index-right': board.GP2,
    'left-index-up': board.GP3,
    'left-index-down': board.GP4,
    'left-middle-up': board.GP10,
    'left-middle-down': board.GP11,
    'left-ring-up': board.GP12,
    'left-ring-down': board.GP13,
    'left-pinky-up': board.GP14,
    'left-pinky-down': board.GP15,
    'left-thumb-up': board.GP5,
    'left-thumb-down': board.GP5,
}

RIGHT_CONTROLLER_PINS = {
    'right-tx': board.GP0,
    'right-rx': board.GP1,
    'right-index-left': board.GP2,
    'right-index-up': board.GP3,
    'right-index-down': board.GP4,
    'right-middle-up': board.GP10,
    'right-middle-down': board.GP11,
    'right-ring-up': board.GP12,
    'right-ring-down': board.GP13,
    'right-pinky-up': board.GP14,
    'right-pinky-down': board.GP15,
    'right-thumb-up': board.GP21,
    'right-thumb-down': board.GP20,
}

VIRTUAL_KEYS = {
    'lpu': ['left-pinky-up'],
    'lpm': ['left-pinky-up', 'left-pinky-down'],
    'lpd': ['left-pinky-down'],
    'lru': ['left-ring-up'],
    'lrm': ['left-ring-up', 'left-ring-down'],
    'lrd': ['left-ring-down'],
    'lmu': ['left-middle-up'],
    'lmm': ['left-middle-up', 'left-middle-down'],
    'lmd': ['left-middle-down'],
    'li1u': ['left-index-up'],
    'li1m': ['left-index-up', 'left-index-down'],
    'li1d': ['left-index-down'],
    'li2u': ['left-index-up', 'left-index-right'],
    'li2m': ['left-index-right'],
    'li2d': ['left-index-down', 'left-index-right'],
    'ltu': ['left-thumb-up'],
    'ltm': ['left-thumb-up', 'left-thumb-down'],
    'ltd': ['left-thumb-down'],
    'rtu': ['right-thumb-up'],
    'rtm': ['right-thumb-up', 'right-thumb-down'],
    'rtd': ['right-thumb-down'],
    'ri2u': ['right-index-up', 'right-index-left'],
    'ri2m': ['right-index-left'],
    'ri2d': ['right-index-down', 'right-index-left'],
    'ri1u': ['right-index-up'],
    'ri1m': ['right-index-up', 'right-index-down'],
    'ri1d': ['right-index-down'],
    'rmu': ['right-middle-up'],
    'rmm': ['right-middle-up', 'right-middle-down'],
    'rmd': ['right-middle-down'],
    'rru': ['right-ring-up'],
    'rrm': ['right-ring-up', 'right-ring-down'],
    'rrd': ['right-ring-down'],
    'rpu': ['right-pinky-up'],
    'rpm': ['right-pinky-up', 'right-pinky-down'],
    'rpd': ['right-pinky-down'],
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