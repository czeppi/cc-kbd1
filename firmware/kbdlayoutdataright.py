
VIRTUAL_KEYS = {
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
    'rtu ri2u ri1u rmu rru rpu',
    'rtm ri2m ri1m rmm rrm rpm',
    'rtd ri2d ri1d rmd rrd rpd',
]


LAYERS = {
    '': [
        'Space      z u i o p',
        'Backspace  h j k l ö',
        'Enter      n m , . -',
    ],
    'ltu': [
        '· @ " { } `',
        '· \\ / ( ) $',
        "· # ' [ ] ´",
    ],
    'ltd': [
        '· + 7 8 9 %',
        '· - 4 5 6 ,',
        '0 · 1 2 3 .',
    ],
    'rtu': [
        ' · · F1 F2  F3  F4',
        ' · · F5 F6  F7  F8',
        ' · · F9 F10 F11 F12',
    ],
    'rtd': [
        '· · · · · ·',
        '· · · · · ·',
        '· · · · · ·',
    ],
    'rtm': [
        '· · PageUp   Home Up   End',
        '· · PageDown Left Down Right',
        '· · ·        ·    ·    ·',
    ],
}

MODIFIERS = {
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