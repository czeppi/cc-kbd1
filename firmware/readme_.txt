

Install 
=======

Circuit-Python:
    download circuitpython:
        pico:
            https://circuitpython.org/board/raspberry_pi_pico_w/
            => adafruit-circuitpython-raspberry_pi_pico_w-en_US-9.2.9.uf2
        pico2:
            https://circuitpython.org/board/raspberry_pi_pico2_w/
            => adafruit-circuitpython-raspberry_pi_pico2_w-en_US-9.2.9.uf2
    install:
        - connect Pico to USB while Sel-button is pressed => new drive appears
        - drag&drop utf2 file to that drive => a new drive appears
    download bundle:
        - https://circuitpython.org/libraries
          => adafruit-circuitpython-bundle-9.x-mpy-20250911.zip
    install bundle:
        copy folders adafruit_bus_device + adafruit_hid
        from adafruit-circuitpython-bundle-9.x-mpy-20250911.zip/adafruit-circuitpython-bundle-9.x-mpy-20250911/lib
        to   [CIRCUIT-Python-drive]:/lib



PMW3389
=======

board |    | color  | description
-------------------------------
RST   | RS | brown  | Reset
GND   | GD | red    | Ground
MT    | MT | orange | Motion (active low interrupt line)
SS    | SS | yellow | Slave Select / Chip Select
SCK   | SC | green  | SPI Clock
MOSI  | MO | blue   |
MISO  | MI | purple |
VIN   | VI | gray   | Voltage in up to +5.5V








	SPI0_SCK  Pin 6  # SPI0_SCK
	SPI0_MOSI Pin 7  # SPI0_TX
	SPI0_MISO Pin 4  # SPI0_RX
	
	SPI1_SCK  Pin 10  # SPI1_SCK
	SPI1_MOSI Pin 11  # SPI1_TX
	SPI1_MISO Pin 8   # SPI1_RX
	
