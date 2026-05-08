import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Debouncer
from hid_device_uart import MouseCon

m = Mouse(usb_hid.devices)
CPS = 9                    #20 CPS is the limit

def get_mmb(): return MouseCon()[0][2]
def get_bwb(): return MouseCon()[0][3]
def get_fwb(): return MouseCon()[0][4]

DMMB, DFWB, DBWB = Debouncer(get_mmb), Debouncer(get_fwb), Debouncer(get_bwb)

def main():
    print("Started!!!")
    flag = False
    while True:
        DMMB.update()
        
        if DMMB.fell:
            if not flag:
                flag = True
                print("Activated")
            else:
                flag = False
                print("Deactivated")
        
        if MouseCon()[0][0] and MouseCon()[0][1] and flag:
            m.press(Mouse.LEFT_BUTTON)
            time.sleep(0.05)
            m.release(Mouse.LEFT_BUTTON)
        time.sleep((1/CPS)-0.05)

if __name__ == '__main__':
    main()