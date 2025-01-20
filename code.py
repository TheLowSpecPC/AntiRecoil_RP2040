import time, board, digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

m = Mouse(usb_hid.devices)

MLB = digitalio.DigitalInOut(board.GP28)
MLB.direction = digitalio.Direction.INPUT
MLB.pull = digitalio.Pull.DOWN

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

gunsSelect = [akm, fcar]
gun = []

def SetGun(name):
    if name == "akm":
        print("AKM Selected\n")
        return gunsSelect[0]
    elif name == "fcar":
        print("FCAR Selected\n")
        return gunsSelect[1]
    else:
        print("Enter valid Gun\n")
        return SetGun(input())

name = ""
print("Enter Options:\n 1.akm\n 2.fcar\n")
name = input()
gun = SetGun(name)

while True:
    if(MLB.value):
        for i in range(len(gun[0])):
            if(i==0):
                m.press(Mouse.RIGHT_BUTTON)
                time.sleep(1)
                
            m.press(Mouse.LEFT_BUTTON)
            m.move(x=gun[0][i][0], y=gun[0][i][1])
            time.sleep(gun[1])
            
            if(MLB.value == False):
                m.release(Mouse.LEFT_BUTTON)
                m.release(Mouse.RIGHT_BUTTON)
                break