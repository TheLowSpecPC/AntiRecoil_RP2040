import time, board, digitalio, storage
import usb_hid
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Debouncer

m = Mouse(usb_hid.devices)

MLB = digitalio.DigitalInOut(board.GP16)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.UP

MRB = digitalio.DigitalInOut(board.GP17)
MRB.direction = digitalio.Direction.INPUT
MRB.pull = digitalio.Pull.UP

MMB = digitalio.DigitalInOut(board.GP20)
MMB.direction = digitalio.Direction.INPUT
MMB.pull = digitalio.Pull.UP
MMB = Debouncer(MMB)

FWB = digitalio.DigitalInOut(board.GP18)
FWB.direction = digitalio.Direction.INPUT
FWB.pull = digitalio.Pull.UP
FWB = Debouncer(FWB)

BWB = digitalio.DigitalInOut(board.GP19)
BWB.direction = digitalio.Direction.INPUT
BWB.pull = digitalio.Pull.UP
BWB = Debouncer(BWB)

def LoadPattern(filename):
    with open(filename, 'r') as file:
        patterns = file.readlines()
        file.close()
    with open('Patterns/Sensitivity.txt', 'r') as sen:
        sensitive = sen.read()
        sensitivity = float(sensitive)
        sen.close()
        
    yaw = sensitivity * 0.00101

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round(float(patterns[i][1])/yaw)

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
        return [LoadPattern('Patterns/Default.txt'), 80]
    else:
        print("Enter valid Gun\n")
        return SetGun(input())

gun = []
def main():
    while True:
        name = ""
        check = False
        print("Enter Options:\n 0.Default\n 1.AKM\n 2.FCAR\n 3.XP54\n 4.M60\n 5.Famas\n 6.LewisGun\n 7.M11\n 8.93R\n")
        name = input()
        gun = SetGun(name)

        while True:
            FWB.update()
            BWB.update()
            MMB.update()
            if not(MLB.value and MRB.value):
                for i in range(len(gun[0])):
                    m.move(x=gun[0][i][0], y=gun[0][i][1])
                    time.sleep(gun[1]/1000)
                    if(MLB.value or MRB.value):
                        break
                    
            if MMB.fell:
                if check:
                    check = False
                else:
                    check = True
                    
            if check:
                with open('Patterns/Sensitivity.txt', 'r') as sen:
                    sensitive = sen.read()
                    sensitivity = float(sensitive)
                    sen.close()
                    
                if FWB.fell:
                    if sensitivity > 4:
                        sensitivity = sensitivity-4
                    print(sensitivity)
                    with open('Patterns/Sensitivity.txt', 'w') as sen:
                        sen.write(str(sensitivity))
                        sen.close()
                    gun = SetGun(name)
                    
                if BWB.fell:
                    sensitivity = sensitivity+4
                    print(sensitivity)
                    with open('Patterns/Sensitivity.txt', 'w') as sen:
                        sen.write(str(sensitivity))
                        sen.close()
                    gun = SetGun(name)
                    
if __name__ == '__main__':
    main()
