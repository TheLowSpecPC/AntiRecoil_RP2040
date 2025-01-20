import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)

MLB = digitalio.DigitalInOut(board.GP28)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.DOWN

MRB = digitalio.DigitalInOut(board.GP27)
MRB.direction = digitalio.Direction.INPUT
MRB.pull = digitalio.Pull.DOWN

sensitivity = 50

def LoadPattern(filename):
    yaw = sensitivity * 0.00101
    
    with open(filename, 'r') as file:
        patterns = file.readlines()

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round(float(patterns[i][1])/yaw)

    return(patterns)

akm = [LoadPattern('Patterns/AKM.txt'), 99/1000]
fcar = [LoadPattern('Patterns/FCAR.txt'), 111/1000]
xp54 = [LoadPattern('Patterns/XP54.txt'), 68/1000]
m60 = [LoadPattern('Patterns/M60.txt'), 100/1000]
famas = [LoadPattern('Patterns/FAMAS.txt'), 52/1000]
lewisgun = [LoadPattern('Patterns/LGUN.txt'), 114/1000]
m11 = [LoadPattern('Patterns/M11.txt'), 60/1000]
r93 = [LoadPattern('Patterns/93R.txt'), 64/1000]

gunsSelect = [akm, fcar, xp54, m60, famas, lewisgun, m11, r93]
gun = []

def SetGun(name):
    if name == "AKM":
        print("AKM Selected\n")
        return gunsSelect[0]
    elif name == "FCAR":
        print("FCAR Selected\n")
        return gunsSelect[1]
    elif name == "XP54":
        print("XP54 Selected\n")
        return gunsSelect[2]
    elif name == "M60":
        print("M60 Selected\n")
        return gunsSelect[3]
    elif name == "Famas":
        print("Famas Selected\n")
        return gunsSelect[4]
    elif name == "LewisGun":
        print("LewisGun Selected\n")
        return gunsSelect[5]
    elif name == "M11":
        print("M11 Selected\n")
        return gunsSelect[6]
    elif name == "93R":
        print("93R Selected\n")
        return gunsSelect[7]
    else:
        print("Enter valid Gun\n")
        return SetGun(input())

def main():
    while True:
        name = ""
        print("Enter Options:\n 1.AKM\n 2.FCAR\n 3.XP54\n 4.M60\n 5.Famas\n 6.LewisGun\n 7.M11\n 8.93R\n")
        name = input()
        gun = SetGun(name)

        while True:
            if(MLB.value and MRB.value):
                for i in range(len(gun[0])):
#                    if(i==0):
#                        m.press(Mouse.RIGHT_BUTTON)
#                        time.sleep(1)
                        
#                    m.press(Mouse.LEFT_BUTTON)
                    m.move(x=gun[0][i][0], y=gun[0][i][1])
                    time.sleep(gun[1])
                    
                    if(MLB.value == False or MRB.value == False):
#                        m.release(Mouse.LEFT_BUTTON)
#                        m.release(Mouse.RIGHT_BUTTON)
                        break

if __name__ == '__main__':
    main()