import time
import board
import PMW3389

from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
from keyboardcreator2 import KeyboardCreator2
from keyboardhalf import KeyboardHalf, KeyGroup

from keysdata import *
from kbdlayoutdata import VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS, RIGHT_KEY_GROUPS
from keyboardcreator import KeyboardCreator
from virtualkeyboard import VirtualKeyboard, KeyCmdKind, KeySequence
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

# devices
kbd_device = Keyboard(usb_hid.devices)
mouse_device = Mouse(usb_hid.devices)
trackball_sensor = PMW3389.PMW3389(sck=board.GP18, mosi=board.GP19, miso=board.GP16, cs=board.GP22)
#                                  green            blue             purple


# Any pin. Goes LOW if motion is detected. More reliable.
mt_pin = DigitalInOut(board.A0)
mt_pin.direction = Direction.INPUT


# async
#
# def fast_thread:
#     while True:
#         right_side_events = other_kbd_half_proxy.get_events()
#         update_mouse(right_side_events.mouse_events)
#         get_my_half_keyboard_events()
#         new_kbd_events =
#         queue.write(time=time, new_kbd_events)
#
#
# def main():
#     while True:
#         time_until_next_decision = kbd....
#         time, read_kbd_events = queue.read(timeout=time_until_next_decision)
#         if read_kbd_events.is_empty and not kbd.is_time_for_decision(time=time):
#             continue
#
#         pressed_left_vkeys = my_kbd_half.update(time=time, read_kbd_events.pressed_pkeys)
#         pressed_vkeys = pressed_left_vkeys + right_side_events.kbd_events
#
#         key_seq = kbd.update(time=time, pressed_vkeys)
#         send_key_seq(key_seq)


def main():
    init_sensor()
    init_key_gp_map()

    right_kbd_half = KeyboardHalf(key_groups=[KeyGroup(group_serial, group_data)
                                              for group_serial, group_data in RIGHT_KEY_GROUPS.items()])
    creator2 = KeyboardCreator2(virtual_key_order=VIRTUAL_KEY_ORDER,
                                layers=LAYERS,
                                modifiers=MODIFIERS,
                                macros=MACROS,
                                )
    virt_keyboard2 = creator2.create()

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
    kbd_half_times = []
    vkbd_times = []
    keysend_times = []
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

            vkey_events = list(right_kbd_half.update(time=pkey_update_time, cur_pressed_pkeys=pressed_pkeys))
            t4 = time.monotonic() * 1000  # in ms
            kbd_half_times.append(t4 - t3)

            key_seq = list(virt_keyboard2.update(time=pkey_update_time, vkey_events=vkey_events))
            t5 = time.monotonic() * 1000  # in ms
            vkbd_times.append(t5 - t4)

            send_key_seq(pkey_update_time, key_seq)
            t6 = time.monotonic() * 1000  # in ms
            keysend_times.append(t6 - t5)

            time.sleep(0.01)  # from ChatGPT

        t7 = time.monotonic() * 1000  # in ms
        print(f'CYCLUS: sensor={sum(sensor_times)/n} ({max(sensor_times)}), ' + \
              f'gp_times={sum(gp_times)/n} ({max(gp_times)}) ' + \
              f'kbd_half={sum(kbd_half_times)/n} ({max(kbd_half_times)}), ' + \
              f'virt_kbd={sum(vkbd_times)/n} ({max(vkbd_times)}), ' + \
              f'key_send={sum(keysend_times)/n} ({max(keysend_times)}), ' + \
              f'cyclus={(t7 - t0) / n}')

        sensor_times.clear()
        gp_times.clear()
        kbd_half_times.clear()
        vkbd_times.clear()
        keysend_times.clear()


def init_key_gp_map():
    for gp in KEY_GP_MAP.values():
        gp.direction = Direction.INPUT
        gp.pull = Pull.UP


def print_keyboard_info(virt_keyboard: VirtualKeyboard) -> None:
    for vkey in virt_keyboard.iter_all_virtual_keys():
        print(f'{vkey.serial} ({str(type(vkey))}): ')
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

    send_key_seq(key_seq)


def send_key_seq(time: TimeInMs, key_seq: KeySequence):
    if len(key_seq) == 0:
        return

    print(f'{int(time)} key_seq: {key_seq}')
    for key_cmd in key_seq:
        if key_cmd.kind == KeyCmdKind.PRESS:
            kbd_device.press(key_cmd.key_code)
        elif key_cmd.kind == KeyCmdKind.RELEASE:
            kbd_device.release(key_cmd.key_code)


main()
