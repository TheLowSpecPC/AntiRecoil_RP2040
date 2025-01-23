# AntiRecoil_RP2040
Uses RP2040 as a mouse to counteract recoil (AntiRecoil). It also features an AutoClicker.
Current recoil patterns consist of guns from the game The Finals.

# Usage
* Install Circuitpython to Raspgerry Pi Pico W (Any board that supports Circuitpython will be fine).
* Copy all the files in the repository and upload them to the microcontroller.
* Take a mouse and solder 2 wires to left and right buttons so that when pressed, they get connected to ground.
* Take a third wite and solder it to a toggle switch which connects to the ground of the mouse.
* Take those wires and connect them to the microcontroler according to the GPIO pin given in the code.
* Now you will be ready to use AntiRecoil.py and AutoClicker.py
* You can use your own recoil pattern by uploading the script to Patterns folder.
* MLB(Left button), MRB(Right Button), Check(Toggle Switch).
