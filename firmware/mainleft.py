from __future__ import annotations

from keyboardcreator import KeyboardCreator
from virtualkeyboard import KeySequence, KeyCmdKind

try:
    from typing import Iterator
except ImportError:
    pass

import time
import board
import usb_hid
from digitalio import DigitalInOut, Direction, Pull
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse

from base import PhysicalKeySerial, TimeInMs
from button import Button
from kbdlayoutdata import LEFT_KEY_GROUPS, VIRTUAL_KEY_ORDER, LAYERS, MODIFIERS, MACROS
from keyboardhalf import KeyboardHalf, KeyGroup, VKeyPressEvent
from keysdata import *
from uart import LeftUart, MouseMove


# TRRS
#
#   T R1 R2
#   S
#
#   T:  Tip,    VCC, red
#   R1: Ring1,  GND, black
#   R2: Ring2,  RX,  blue
#   S:  Sleeve, TX,  yellow


LEFT_TX = board.GP0
LEFT_RX = board.GP1


def main():
    left_kbd = LeftKeyboardSide()
    left_kbd.init()
    left_kbd.main_loop()


class LeftKeyboardSide:
    _BUTTON_MAP = {
        LEFT_INDEX_RIGHT: board.GP2,  # blue
        LEFT_INDEX_DOWN: board.GP3,  # yellow
        LEFT_INDEX_UP: board.GP4,  # red
        LEFT_MIDDLE_DOWN: board.GP10,  # blue
        LEFT_MIDDLE_UP: board.GP11,  # yellow
        LEFT_RING_DOWN: board.GP12,  # red
        LEFT_RING_UP: board.GP13,  # blue
        LEFT_PINKY_DOWN: board.GP14,  # red
        LEFT_PINKY_UP: board.GP15,  # yellow
        LEFT_THUMB_DOWN: board.GP21,  # red
        LEFT_THUMB_UP: board.GP20,  # yellowu
    }

    def __init__(self):
        self._uart = LeftUart(tx=LEFT_TX, rx=LEFT_RX)
        self._buttons = [Button(pkey_serial=pkey_serial, gp_pin=gp_pin) for pkey_serial, gp_pin in self._BUTTON_MAP.items()]
        self._kbd_half = KeyboardHalf(key_groups=[KeyGroup(group_serial, group_data)
                                                  for group_serial, group_data in LEFT_KEY_GROUPS.items()])
        creator = KeyboardCreator(virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  )
        self._virt_keyboard = creator.create()

        self._kbd_device = Keyboard(usb_hid.devices)
        self._mouse_device = Mouse(usb_hid.devices)
        self._queue: list[QueueItem] = []

    def init(self) -> None:
        print('init uart...')
        self._uart.wait_for_start()

    def main_loop(self) -> None:
        print('start main loop')
        while True:
            self._read_devices()

            for queue_item in self._read_queue_items():
                self._process_queue_item(queue_item)

            time.sleep(0.001)

    def _read_devices(self) -> None:
        t = time.monotonic() * 1000

        #print(f'_read_devices: t={t}')
        my_pressed_pkeys = self._get_pressed_pkeys()

        mouse_dx = mouse_dy = 0
        other_vkey_events: list[VKeyPressEvent] = []
        for uart_item in self._uart.read_items():
            if isinstance(uart_item, MouseMove):
                mouse_move = uart_item
                mouse_dx += mouse_move.dx
                mouse_dy += mouse_move.dy
            elif isinstance(uart_item, VKeyPressEvent):
                vkey_evt = uart_item
                other_vkey_events.append(vkey_evt)

        queue_item = QueueItem(time=t, mouse_move=MouseMove(dx=mouse_dx, dy=mouse_dy),
                               my_pressed_pkeys=my_pressed_pkeys,
                               other_vkey_events=other_vkey_events)
        #print(f'read_devices: {queue_item}')
        self._queue.append(queue_item)

    def _read_queue_items(self) -> Iterator[QueueItem]:
        while len(self._queue) > 0:
            queue_item = self._queue[0]
            self._queue = self._queue[1:]
            yield queue_item

    def _process_queue_item(self, queue_item: QueueItem) -> None:
        #print(f'_process_queue_item: {queue_item}')
        mouse_dx = queue_item.mouse_move.dx
        mouse_dy = queue_item.mouse_move.dy
        if mouse_dx != 0 or mouse_dy != 0:
            self._mouse_device.move(mouse_dx, mouse_dy)

        my_vkey_events = list(self._kbd_half.update(time=queue_item.time,
                                                    cur_pressed_pkeys=queue_item.my_pressed_pkeys))
        t = time.monotonic() * 1000
        key_seq = list(self._virt_keyboard.update(time=t,
                                                  vkey_events=queue_item.other_vkey_events + my_vkey_events))
        self._send_key_seq(key_seq)

    def _get_pressed_pkeys(self) -> set[PhysicalKeySerial]:
        return {button.pkey_serial
                for button in self._buttons
                if button.is_pressed()}

    def _send_key_seq(self, key_seq: KeySequence) -> None:
        if len(key_seq) == 0:
            return

        # print(f'{int(time)} key_seq: {key_seq}')
        for key_cmd in key_seq:
            if key_cmd.kind == KeyCmdKind.PRESS:
                self._kbd_device.press(key_cmd.key_code)
            elif key_cmd.kind == KeyCmdKind.RELEASE:
                self._kbd_device.release(key_cmd.key_code)


class QueueItem:

    def __init__(self, time: TimeInMs, mouse_move: MouseMove,
                 my_pressed_pkeys: set[PhysicalKeySerial], other_vkey_events: list[VKeyPressEvent]):
        # public
        self.time = time
        self.mouse_move = mouse_move
        self.my_pressed_pkeys = my_pressed_pkeys
        self.other_vkey_events = other_vkey_events

    def __str__(self) -> str:
        return f'QueueItem({self.time}, mouse=({self.mouse_move.dx, self.mouse_move.dy}), my-pkeys=({self.my_pressed_pkeys})), other-vkey={self.other_vkey_events})'


if __name__ == '__main__':
    main()
