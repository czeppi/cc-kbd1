import time
import board
import PMW3389

from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

from keysdata import *
from kbdlayoutdata import VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator
from virtualkeyboard import VirtualKeyboard, KeyCmdKind
from base import TimeInMs, PhysicalKeySerial

TARGET_CPI = 800

KEY_GP_MAP = {
    # 'right-tx': DigitalInOut(board.GP0),
    # 'right-rx': DigitalInOut(board.GP1),
    RIGHT_INDEX_LEFT: DigitalInOut(board.GP2),
    RIGHT_INDEX_UP: DigitalInOut(board.GP3),
    RIGHT_INDEX_DOWN: DigitalInOut(board.GP4),
    RIGHT_MIDDLE_UP: DigitalInOut(board.GP10),
    RIGHT_MIDDLE_DOWN: DigitalInOut(board.GP11),
    RIGHT_RING_UP: DigitalInOut(board.GP12),
    RIGHT_RING_DOWN: DigitalInOut(board.GP13),
    RIGHT_PINKY_UP: DigitalInOut(board.GP14),
    RIGHT_PINKY_DOWN: DigitalInOut(board.GP15),
    RIGHT_THUMB_UP: DigitalInOut(board.GP21),
    RIGHT_THUMB_DOWN: DigitalInOut(board.GP20),
}

# Set up a keyboard device.
kbd_device = Keyboard(usb_hid.devices)

# Type lowercase 'a'. Presses the 'a' key and releases it.
# kbd.send(Keycode.A)  # OK
mouse_device = Mouse(usb_hid.devices)

# board.CLK may be board.SCK depending on the board
# board.D10 is the cs pin
# sensor = PMW3360.PMW3360(board.CLK, board.MOSI, board.MISO, board.D10)
# sensor = PMW3389.PMW3389(sck=board.GP6, mosi=board.GP7, miso=board.GP4, cs=board.GP22)
trackball_sensor = PMW3389.PMW3389(sck=board.GP18, mosi=board.GP19, miso=board.GP16, cs=board.GP22)
#                                  green            blue             purple

# vin miso mosi sck ss mt gnd rst
#      4    7    6  22

# Any pin. Goes LOW if motion is detected. More reliable.
mt_pin = DigitalInOut(board.A0)
mt_pin.direction = Direction.INPUT

# # button_thumb_down = DigitalInOut(board.GP16)
# #button_thumb_down = DigitalInOut(board.GP20)
# button_thumb_down = DigitalInOut(board.GP5)  # not connected - only temporary
# button_thumb_down.direction = Direction.INPUT
# button_thumb_down.pull = Pull.UP
# button_thumb_down_old_value = button_thumb_down.value
#
# # button_thumb_up = DigitalInOut(board.GP17)
# #button_thumb_up = DigitalInOut(board.GP21)
# button_thumb_up = DigitalInOut(board.GP6)  # not connected - only temporary
# button_thumb_up.direction = Direction.INPUT
# button_thumb_up.pull = Pull.UP


def main():
    init_sensor()
    init_key_gp_map()

    creator = KeyboardCreator(virtual_keys=VIRTUAL_KEYS,
                              virtual_key_order=VIRTUAL_KEY_ORDER,
                              layers=LAYERS,
                              modifiers=MODIFIERS,
                              macros=MACROS,
                              )
    virt_keyboard = creator.create()
    # #print_keyboard_info(virt_keyboard)

    sensor_times = []
    gp_times = []
    keyboard_times = []
    n = 100

    while True:
        t0 = time.monotonic() * 1000  # in ms
        for i in range(n):
            t1 = time.monotonic() * 1000  # in ms

            update_sensor()
            t2 = time.monotonic() * 1000  # in ms
            sensor_times.append(t2 - t1)

            pressed_pkeys = get_pressed_pkeys()
            pkey_update_time = time.monotonic() * 1000  #  todo: before or after get_pressed_keys()?
            t3 = time.monotonic() * 1000  # in ms
            gp_times.append(t3 - t2)

            update_virtual_keyboard(virt_keyboard, pressed_pkeys=pressed_pkeys, pkey_update_time=pkey_update_time)
            t4 = time.monotonic() * 1000  # in ms
            keyboard_times.append(t4 - t3)

            time.sleep(0.01)  # from ChatGPT

        t5 = time.monotonic() * 1000  # in ms
        print(f'CYCLUS: sensor={sum(sensor_times)/n} ({max(sensor_times)}), '
              f'gp_times={sum(gp_times)/n} ({max(gp_times)}) '
              f'keyboard={sum(keyboard_times)/n} ({max(keyboard_times)}), '
              f'cyclus={(t5 - t0) / n}')

        sensor_times.clear()
        gp_times.clear()
        keyboard_times.clear()


def init_key_gp_map():
    for gp in KEY_GP_MAP.values():
        gp.direction = Direction.INPUT
        gp.pull = Pull.UP


def print_keyboard_info(virt_keyboard: VirtualKeyboard) -> None:
    for vkey in virt_keyboard.iter_all_virtual_keys():
        print(f'{vkey.name} ({str(type(vkey))}): ')
        for pkey in vkey.physical_keys:
            print(f'- {pkey.serial} ({id(pkey)}) ({str(type(pkey))})')


def init_sensor():
    # Initialize sensor. You can specify CPI as an argument. Default CPI is 800.
    if trackball_sensor.begin():
        print("sensor ready")
    else:
        print("firmware upload failed")

    # Setting and getting CPI values
    trackball_sensor.set_CPI(TARGET_CPI)
    while True:
        cpi = trackball_sensor.get_CPI()
        print(f'cpi = {cpi}')
        if cpi == TARGET_CPI:
            break
        time.sleep(0.1)


def update_sensor():
    data = trackball_sensor.read_burst()

    # Limit values if needed
    dx = constrain(delta(data["dx"]), -127, 127)
    dy = constrain(delta(data["dy"]), -127, 127)

    # uncomment if mt_pin isn't used
    # if data["isOnSurface"] == True and data["isMotion"] and mt_pin.value == True:
    if mt_pin.value == 0 and (dy != 0 or dy != 0):
        print(f'move ({dx}, {dy})')
        mouse_device.move(-dy, -dx)  # !! swap values - only for testing !!

    #cpi = trackball_sensor.get_CPI()
    #if cpi != TARGET_CPI:
    #    # print(f'cpi = {cpi}')
    #    trackball_sensor.set_CPI(TARGET_CPI)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


# Convert 16-bit unsigned value into a signed value
def delta(value):
    # Negative if MSB is 1
    if value & 0x8000:
        return -(~value & 0x7FFF)

    return (value & 0x7FFF)


def get_pressed_pkeys() -> set[PhysicalKeySerial]:
    return {pkey_serial
            for pkey_serial, gp in KEY_GP_MAP.items()
            if not gp.value}


def update_virtual_keyboard(virt_keyboard: VirtualKeyboard, pressed_pkeys: set[PhysicalKeySerial], pkey_update_time: TimeInMs):
    time_in_ms = time.monotonic() * 1000

    key_seq = list(virt_keyboard.update(time_in_ms, pressed_pkeys=pressed_pkeys, pkey_update_time=pkey_update_time))

    if key_seq:
        print(f'{int(time_in_ms)} key_seq: {key_seq}')
        for key_cmd in key_seq:
            if key_cmd.kind == KeyCmdKind.PRESS:
                kbd_device.press(key_cmd.key_code)
            elif key_cmd.kind == KeyCmdKind.RELEASE:
                kbd_device.release(key_cmd.key_code)


def update_thumb_down_button():
    global button_thumb_down_old_value

    new_value = button_thumb_down.value

    if new_value != button_thumb_down_old_value:
        if new_value:  # pressed (HI)
            kbd_device.send(Keycode.A)
        button_thumb_down_old_value = button_thumb_down.value


class DigitalInput:

    def __init__(self, gp_index: int):
        self._inout = DigitalInOut(gp_index)
        self._inout.direction = Direction.INPUT
        self._inout.pull = Pull.UP

main()
