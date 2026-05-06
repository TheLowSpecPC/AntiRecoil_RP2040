import board
import busio
import time

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

while True:
    mouse_report = MouseCon()
    left = mouse_report[0][0]
    print(f"Received: {mouse_report}")
    #print(left)
    
    time.sleep(0.02)