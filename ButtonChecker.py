import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)

Check = digitalio.DigitalInOut(board.GP16)
Check.direction = digitalio.Direction.INPUT
Check.pull = digitalio.Pull.UP

i=0
while True:
    if(Check.value == False):
        print(f"Press {i}")
        i=i+1