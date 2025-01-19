import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)

pin = digitalio.DigitalInOut(board.GP28)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.DOWN

while True:
    time.sleep(0.1)
    print(pin.value)
    if(pin.value):
        while True:
            m.move(x=50,y=60)
            time.sleep(0.2)
            if(pin.value == False):
                break
            m.move(x=-50,y=-60)
            time.sleep(0.2)
            if(pin.value == False):
                break

#m.move(x=50,y=60)
#time.sleep(1)
#m.move(x=-50,y=-60)

#print("Done!")