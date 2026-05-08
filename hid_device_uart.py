import board
import busio
import time

# Initialize UART on UART0 
# TX = GP12, RX = GP13 (Matching the hardware wiring)
uart = busio.UART(board.GP12, board.GP13, baudrate=115200, receiver_buffer_size=64, timeout=0.1)

buttons, x, y, wheel = [0,0,0,0,0], 0, 0, 0
sync_state = 0 
payload = bytearray()

def MouseCon():
    global buttons, x, y, wheel, sync_state, payload
    
    # If in_waiting is 0 (no data), returns old button states with all other values being null.
    if uart.in_waiting == 0:
        return [buttons, 0, 0, 0]
    
    # Process all bytes currently sitting in the buffer, one by one.
    while uart.in_waiting > 0:
        byte = uart.read(1)
        
        # State 0: Hunting for the first sync byte (0xAA)
        if sync_state == 0:
            if byte == b'\xAA':
                sync_state = 1
                
        # State 1: Hunting for the second sync byte (0x55)
        elif sync_state == 1:
            if byte == b'\x55':
                sync_state = 2       # We are fully synced!
                payload = bytearray() # Clear old payload data
            elif byte == b'\xAA':
                pass # Edge case: if we get AA AA 55, stay in state 1
            else:
                sync_state = 0 # False alarm, go back to hunting
                
        # State 2: Collecting the 4 payload bytes
        elif sync_state == 2:
            payload.extend(byte)
            
            # Once we have all 4 bytes, process the data!
            if len(payload) == 4:
                btn_byte = payload[0]
                for i in range(5):
                    buttons[i] = int(bool(btn_byte & (1 << i)))

                x = payload[1] - 256 if (payload[1] & 0x80) else payload[1]
                y = payload[2] - 256 if (payload[2] & 0x80) else payload[2]
                wheel = payload[3] - 256 if (payload[3] & 0x80) else payload[3]
                
                # Reset state machine to hunt for the NEXT packet
                sync_state = 0 

    #[[Left, Right, Middle, Forward Backward], x, y, wheel]
    return [buttons, x, y, wheel]

def test():
    while True:
        mouse_report = MouseCon()
        left = mouse_report[0][0]
        print(f"Received: {mouse_report}")
        #print(left)
        
        time.sleep(0.02)
        
#test()