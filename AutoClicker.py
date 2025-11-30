import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Debouncer

m = Mouse(usb_hid.devices)
CPS = 9                                     #20 CPS is the limit

MLB = digitalio.DigitalInOut(board.GP16)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.UP

Check = digitalio.DigitalInOut(board.GP18)
Check.direction = digitalio.Direction.INPUT
Check.pull = digitalio.Pull.UP
Check = Debouncer(Check)

def main():
    print("Started!!!")
    flag = False
    while True:
        Check.update()
        
        if Check.fell:
            if flag:
                flag = False
            else:
                flag = True
        
        if(MLB.value==False and flag==False):
            m.press(Mouse.LEFT_BUTTON)
            time.sleep(0.05)
            m.release(Mouse.LEFT_BUTTON)
        time.sleep((1/CPS)-0.05)

if __name__ == '__main__':
    main()