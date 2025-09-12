import time
import board
import PMW3389

from digitalio import DigitalInOut, Direction
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# Set up a keyboard device.
#kbd = Keyboard(usb_hid.devices)

# Type lowercase 'a'. Presses the 'a' key and releases it.
#kbd.send(Keycode.A)  # OK
mouse = Mouse(usb_hid.devices)

# board.CLK may be board.SCK depending on the board
# board.D10 is the cs pin
#sensor = PMW3360.PMW3360(board.CLK, board.MOSI, board.MISO, board.D10)
sensor = PMW3389.PMW3389(sck=board.GP6, mosi=board.GP7, miso=board.GP4, cs=board.GP22)
# vin miso mosi sck ss mt gnd rst
#      4    7    6  22

# Any pin. Goes LOW if motion is detected. More reliable.
mt_pin = DigitalInOut(board.A0)
mt_pin.direction = Direction.INPUT

# Initialize sensor. You can specify CPI as an argument. Default CPI is 800.
if sensor.begin():
    print("sensor ready")
else:
    print("firmware upload failed")

# Setting and getting CPI values
target_cpi = 800
sensor.set_CPI(target_cpi)
while True:
    cpi = sensor.get_CPI()
    print(f'cpi = {cpi}')
    if cpi == target_cpi:
        break
        time(0.5)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


# Convert 16-bit unsigned value into a signed value
def delta(value):
    # Negative if MSB is 1
    if value & 0x8000:
        return -(~value & 0x7FFF)

    return (value & 0x7FFF)


while True:
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
    if cpi != target_cpi:
        print(f'cpi = {cpi}')
        sensor.set_CPI(target_cpi)

    time.sleep(0.01)  # from ChatGPT
