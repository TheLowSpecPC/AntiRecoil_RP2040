import board
import busio
import time

# Initialize UART on UART0 
# TX = GP12, RX = GP13 (Matching the hardware wiring)
uart = busio.UART(board.GP12, board.GP13, baudrate=115200, receiver_buffer_size=64, timeout=0.1)

MLB, MRB, MMB, FWB, BWB, x, y, wheel = False, False, False, False, False, 0, 0, 0
def MouseCon():
    global MLB, MRB, MMB, FWB, BWB, x, y, wheel
    waiting = uart.in_waiting # Check how many bytes are waiting in the hardware buffer

    if waiting >= 4:
        all_data = uart.read(waiting) # Read everything in the buffer to clear out the backlog instantly
        data = all_data[-4:]          # Slice the array to keep ONLY the most recent 4 bytes (the latest state)
        
        btn_byte = data[0]
        MLB = bool(btn_byte & (1 << 0)) # 1st bit from right
        MRB = bool(btn_byte & (1 << 1)) # 2nd bit
        MMB = bool(btn_byte & (1 << 2)) # 3rd bit
        BWB = bool(btn_byte & (1 << 3)) # 4th bit
        FWB = bool(btn_byte & (1 << 4)) # 5th bit

        x = data[1] - 256 if (data[1] & 0x80) else data[1]
        y = data[2] - 256 if (data[2] & 0x80) else data[2]
        wheel = data[3] - 256 if (data[3] & 0x80) else data[3]
            
    #[[Left, Right, Middle, Forward Backward], x, y, wheel]
    return [[MLB, MRB, MMB, FWB, BWB], x, y, wheel]

while True:
    mouse_report = MouseCon()
    left = mouse_report[0][0]
    print(f"Received: {mouse_report}")
    #print(left)
    
    time.sleep(0.01)
