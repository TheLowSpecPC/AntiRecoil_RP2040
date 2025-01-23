import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)

MLB = digitalio.DigitalInOut(board.GP16)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.UP

MRB = digitalio.DigitalInOut(board.GP17)
MRB.direction = digitalio.Direction.INPUT
MRB.pull = digitalio.Pull.UP

sensitivity = 52

def LoadPattern(filename):
    yaw = sensitivity * 0.00101
    
    with open(filename, 'r') as file:
        patterns = file.readlines()

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round(float(patterns[i][1])/yaw)

    return(patterns)

akm = [LoadPattern('Patterns/AKM.txt'), 99]
fcar = [LoadPattern('Patterns/FCAR.txt'), 111]
xp54 = [LoadPattern('Patterns/XP54.txt'), 68]
m60 = [LoadPattern('Patterns/M60.txt'), 100]
famas = [LoadPattern('Patterns/FAMAS.txt'), 52]
lewisgun = [LoadPattern('Patterns/LGUN.txt'), 114]
m11 = [LoadPattern('Patterns/M11.txt'), 60]
r93 = [LoadPattern('Patterns/93R.txt'), 64]

gunsSelect = [akm, fcar, xp54, m60, famas, lewisgun, m11, r93]
gun = []

def SetGun(name):
    if name == "1":
        print("AKM Selected\n")
        return gunsSelect[0]
    elif name == "2":
        print("FCAR Selected\n")
        return gunsSelect[1]
    elif name == "3":
        print("XP54 Selected\n")
        return gunsSelect[2]
    elif name == "4":
        print("M60 Selected\n")
        return gunsSelect[3]
    elif name == "5":
        print("Famas Selected\n")
        return gunsSelect[4]
    elif name == "6":
        print("LewisGun Selected\n")
        return gunsSelect[5]
    elif name == "7":
        print("M11 Selected\n")
        return gunsSelect[6]
    elif name == "8":
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
            if(MLB.value == False and MRB.value == False):
                for i in range(len(gun[0])):
                    m.move(x=gun[0][i][0], y=gun[0][i][1])
                    time.sleep(gun[1]/1000)
                    if(MLB.value or MRB.value):
                        break
                    
if __name__ == '__main__':
    main()