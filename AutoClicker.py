import time, board, digitalio, busio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Debouncer

m = Mouse(usb_hid.devices)
CPS = 9                    #20 CPS is the limit

# Initialize UART on UART0 
# TX = GP12, RX = GP13 (Matching the hardware wiring)
uart = busio.UART(board.GP12, board.GP13, baudrate=115200, receiver_buffer_size=64, timeout=0.1)

buttons, x, y, wheel = [0,0,0,0,0], 0, 0, 0
def MouseCon():
    global buttons, x, y, wheel
    waiting = uart.in_waiting # Check how many bytes are waiting in the hardware buffer

    if waiting >= 4:
        all_data = uart.read(waiting) # Read everything in the buffer to clear out the backlog instantly
        data = all_data[-4:]          # Slice the array to keep ONLY the most recent 4 bytes (the latest state)
        
        btn_byte = data[0]
        for i in range(5):
            buttons[i] = int(bool(btn_byte & (1 << i)))

        x = data[1] - 256 if (data[1] & 0x80) else data[1]
        y = data[2] - 256 if (data[2] & 0x80) else data[2]
        wheel = data[3] - 256 if (data[3] & 0x80) else data[3]
            
    #[[Left, Right, Middle, Forward Backward], x, y, wheel]
    return [buttons, x, y, wheel]

def get_mmb(): return MouseCon()[0][2]
def get_fwb(): return MouseCon()[0][3]
def get_bwb(): return MouseCon()[0][4]

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