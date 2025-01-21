# AntiRecoil_RP2040
Uses RP2040 as a mouse to counteract recoil (AntiRecoil). It also features an AutoClicker.

# Usage
* Install Circuitpython to Raspgerry Pi Pico W (Any board that supports Circuitpython will be fine).
* Take a mouse and solder 2 wires to left and right buttons so that when pressed, they get connected to ground.
* Take a third wite and solder it to a toggle switch which connects to the ground of the mouse.
* Take those wires and connect them to the microcontroler according to the GPIO pin given in the code.
* MLB(Left button), MRB(Right Button), Check(Toggle Switch).
