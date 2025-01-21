import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)
CPS = 9                                     #20 CPS is the limit

MLB = digitalio.DigitalInOut(board.GP28)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.DOWN

Check = digitalio.DigitalInOut(board.GP26)
Check.direction = digitalio.Direction.INPUT
Check.pull = digitalio.Pull.DOWN

def main():
    while True:
        if(MLB.value and Check.value):
            m.press(Mouse.LEFT_BUTTON)
            time.sleep(0.05)
            m.release(Mouse.LEFT_BUTTON)
        time.sleep((1/CPS)-0.05)

if __name__ == '__main__':
    main()