import time
import board
import PMW3389

from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse
from kbdlayoutdata import LEFT_CONTROLLER_PINS, RIGHT_CONTROLLER_PINS, VIRTUAL_KEYS, VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, MACROS
from keyboardcreator import KeyboardCreator
from virtualkeyboard import VirtualKeyboard, KeyCmd, KeyCmdKind


TARGET_CPI = 800


# Set up a keyboard and mouse device.
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# board.CLK may be board.SCK depending on the board
# board.D10 is the cs pin
sensor = PMW3389.PMW3389(sck=board.GP6, mosi=board.GP7, miso=board.GP4, cs=board.GP22)


def main():
    init_trackball_sensor()

    creator = KeyboardCreator(physical_key_creator=_create_physical_key,
                              left_controller_pins=LEFT_CONTROLLER_PINS,
                              right_controller_pins=RIGHT_CONTROLLER_PINS,
                              virtual_keys=VIRTUAL_KEYS,
                              virtual_key_order=VIRTUAL_KEY_ORDER,
                              layers=LAYERS,
                              modifiers=MODIFIERS,
                              macros=MACROS,
                              )
    keyboard = creator.create()

    while True:
        update_mouse()
        update_keyboard_new(keyboard)
        time.sleep(0.01)  # from ChatGPT


def calc_role():
    if len(usb_hid.devices) > 0:
        return 'master'
    else:
        return 'slave'


def init_keyboard_very_old():
    # CS can be connect to an GP pin.

    # Any pin. Goes LOW if motion is detected. More reliable.
    mt_pin = DigitalInOut(board.A0)
    mt_pin.direction = Direction.INPUT

    button_thumb_down = DigitalInOut(board.GP16)   # any GP pin can used
    button_thumb_down.direction = Direction.INPUT
    button_thumb_down.pull = Pull.UP

    button_thumb_up = DigitalInOut(board.GP17)
    button_thumb_up.direction = Direction.INPUT
    button_thumb_up.pull = Pull.UP


def init_trackball_sensor():
    # Initialize sensor. You can specify CPI as an argument. Default CPI is 800.
    if sensor.begin():
        print("sensor ready")
    else:
        print("firmware upload failed")

    # Setting and getting CPI values
    sensor.set_CPI(TARGET_CPI)
    while True:
        cpi = sensor.get_CPI()
        print(f'cpi = {cpi}')
        if cpi == TARGET_CPI:
            break
            time(0.5)


# Convert 16-bit unsigned value into a signed value
def delta(value):
    # Negative if MSB is 1
    if value & 0x8000:
        return -(~value & 0x7FFF)

    return value & 0x7FFF


def update_mouse():
    data = sensor.read_burst()
    dx = delta(data["dx"])
    dy = delta(data["dy"])

    # Limit values if needed
    dx = constrain(delta(data["dx"]), -127, 127)
    dy = constrain(delta(data["dy"]), -127, 127)

    # uncomment if mt_pin isn't used
    # if data["isOnSurface"] == True and data["isMotion"] and mt_pin.value == True:
    if mt_pin.value == 0 and (dy != 0 or dy != 0):
        print(f'move ({dx}, {dy})')
        mouse.move(-dy, -dx)  # !! swap values - only for testing !!

    cpi = sensor.get_CPI()
    if cpi != TARGET_CPI:
        print(f'cpi = {cpi}')
        sensor.set_CPI(TARGET_CPI)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


def update_keyboard_very_old():
    button_thumb_down_old_value = button_thumb_down.value
    if button_thumb_down.value != button_thumb_down_old_value:
        if button_thumb_down.value:  # pressed (HI)
            kbd.send(Keycode.A)  # Type lowercase 'a'. Presses the 'a' key and releases it.
        button_thumb_down_old_value = button_thumb_down.value


def update_keyboard_new(keyboard: VirtualKeyboard):
    time = time()  # todo: in Ms
    key_sequence = keyboard.update(time)
    for key_cmd in key_sequence:
        send_key_cmd(key_cmd)


def send_key_cmd(key_cmd: KeyCmd) -> None:
    if key_cmd.kind == KeyCmdKind.PRESS:
        kbd.press(key_cmd.key_code)
    elif key_cmd.kind == KeyCmdKind.RELEASE:
        kbd.release(key_cmd.key_code)
