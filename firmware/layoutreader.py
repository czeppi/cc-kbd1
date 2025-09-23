from typing import List, Dict

from pyglet.libs.win32.constants import DELETE

from adafruit_hid.keycode import Keycode as KC

from virtualkeyboard import KeyName


class KeyboardLayer:



class KeyboardLayoutParser:

    def __init__(self, lines: List[str]):
        self._lines = lines
        self._layers: Dict[KeyName, KeyboardLayer]

    def parse(self):
        for line in self._lines:
            self._parse_one_line(line)

    def _parse_one_line(self, line: str):
        stripped_line = line.strip()

        if line.startswith('= '):
            self._on_new_block(stripped_line)


class LayersLineParser:

    def __init__(self):
        pass

    def parse(self, line: str):
        stripped_line = line.strip()

        if stripped_line.endswith(':'):
            ..

class OneLayerLineParser:

    def __init__(self):
        self._assignment_row = []

    def parse(self, line: str):
        items = line.strip().split(' ')
        assert len(items) == 12




