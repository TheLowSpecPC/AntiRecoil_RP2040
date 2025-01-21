import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)
CPS = 9                                     #20 CPS is the limit

MLB = digitalio.DigitalInOut(board.GP16)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.UP

Check = digitalio.DigitalInOut(board.GP18)
Check.direction = digitalio.Direction.INPUT
Check.pull = digitalio.Pull.UP

def main():
    print("Started!!!")
    while True:
        if(MLB.value==False and Check.value==False):
            m.press(Mouse.LEFT_BUTTON)
            time.sleep(0.05)
            m.release(Mouse.LEFT_BUTTON)
        time.sleep((1/CPS)-0.05)

if __name__ == '__main__':
    main()