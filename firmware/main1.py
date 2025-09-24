import time
import board
import PMW3389

from digitalio import DigitalInOut, Direction, Pull
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# Set up a keyboard and mouse device.
kbd = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

# board.CLK may be board.SCK depending on the board
# board.D10 is the cs pin
sensor = PMW3389.PMW3389(sck=board.GP6, mosi=board.GP7, miso=board.GP4, cs=board.GP22)






# following combination are possible (ChatGPT)
#
# SPI0:
# Pin-Set  SCK  MOSI  MISO
# Set 1    GP0  GP3   GP2
# Set 2    GP4  GP7   GP6
# Set 3    GP16 GP19  GP18
# Set 4    GP20 GP23  GP22
#
# SPI1:
# Pin-Set  SCK  MOSI  MISO
# Set 1    GP10 GP11  GP12
# Set 2    GP14 GP15  GP13
# Set 3    GP6  GP7   GP4


# following TX/RX combination are possible (ChatGPT)
#        TX               RX
# UART0  GP0, GP12, GP16  GP1, GP13, GP17
# UART1  GP4, GP8,  GP20  GP5, GP9,  GP21

role = 'slave'
try:
    import usb_hid
    if len(usb_hid.devices) > 0:
        role = 'master'
except ImportError:
    role = 'slave'


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
