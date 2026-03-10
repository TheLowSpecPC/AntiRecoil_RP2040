import time, board, digitalio, storage, busio
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Debouncer

m = Mouse(usb_hid.devices)

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

def get_mmb(): return MouseCon()[0][2]
def get_fwb(): return MouseCon()[0][3]
def get_bwb(): return MouseCon()[0][4]

DMMB, DFWB, DBWB = Debouncer(get_mmb), Debouncer(get_fwb), Debouncer(get_bwb)
    

def LoadPattern(*filename):
    filename = list(filename)
    with open(filename[0], 'r') as file:
        patterns = file.readlines()
        file.close()
        
    sensitivity = 66.0
    yaw = sensitivity * 0.00101
    
    if 2 > len(filename):
        filename.append(0)

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round((float(patterns[i][1])+filename[1])/yaw)
        if i==0:
            patterns[i][1] = 0

    return(patterns)


def SetGun(name):
    if name == "1":
        print("AKM Selected\n")
        return [LoadPattern('Patterns/TheFinals/AKM.txt'), 99]
    elif name == "2":
        print("FCAR Selected\n")
        return [LoadPattern('Patterns/TheFinals/FCAR.txt'), 111]
    elif name == "3":
        print("XP54 Selected\n")
        return [LoadPattern('Patterns/TheFinals/XP54.txt'), 68]
    elif name == "4":
        print("M60 Selected\n")
        return [LoadPattern('Patterns/TheFinals/M60.txt'), 100]
    elif name == "5":
        print("Famas Selected\n")
        return [LoadPattern('Patterns/TheFinals/FAMAS.txt'), 52]
    elif name == "6":
        print("LewisGun Selected\n")
        return [LoadPattern('Patterns/TheFinals/LGUN.txt'), 114]
    elif name == "7":
        print("M11 Selected\n")
        return [LoadPattern('Patterns/TheFinals/M11.txt'), 60]
    elif name == "8":
        print("93R Selected\n")
        return [LoadPattern('Patterns/TheFinals/93R.txt'), 64]
    elif name == "0":
        print("Default Selected\n")
        with open('Patterns/DefaultSen.txt', 'r') as pat:
            yPos = float(pat.read())
            pat.close()
        return [LoadPattern('Patterns/Default.txt', yPos), 80]
    else:
        print("Enter valid Gun\n")
        return SetGun(input())
    

gun = []
def main():
    while True:
        name = ""
        check = False
        print("Enter Options: \n\nThe Finals: \n0.Default, 1.AKM, 2.FCAR, 3.XP54, 4.M60, 5.Famas, 6.LewisGun, 7.M11, 8.93R\n")
        name = input()
        gun = SetGun(name)

        while True:
            DMMB.update()
            DFWB.update()
            DBWB.update()
            
            if MouseCon()[0][0] and MouseCon()[0][1]:
                for i in range(len(gun[0])):
                    m.move(x=gun[0][i][0], y=gun[0][i][1])
                    time.sleep(gun[1]/1000)
                    if not(MouseCon()[0][0]) or not(MouseCon()[0][1]):
                        break
                    
            if DMMB.rose:
                if check:
                    check = False
                else:
                    check = True
                    
            if check:
                with open('Patterns/DefaultSen.txt', 'r') as pat:
                    yPos = float(pat.read())
                    pat.close()
                    
                if DFWB.rose:
                    yPos = yPos+0.1
                    print(yPos)
                    with open('Patterns/DefaultSen.txt', 'w') as pat:
                        pat.write(str(yPos))
                        pat.close()
                    gun = SetGun(name)
                    
                if DBWB.rose:
                    if yPos > 0.1:
                        yPos = yPos-0.1
                    print(yPos)
                    with open('Patterns/DefaultSen.txt', 'w') as pat:
                        pat.write(str(yPos))
                        pat.close()
                    gun = SetGun(name)
                    
                    
if __name__ == '__main__':
    main()