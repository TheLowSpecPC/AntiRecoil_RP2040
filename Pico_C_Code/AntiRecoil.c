#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/bootrom.h"
#include "pico/time.h"
#include "hardware/flash.h"
#include "hardware/sync.h"

#include "tusb.h"
#include "usb_descriptors.h"

hid_keyboard_report_t keyboard = {0};
hid_mouse_report_t mouse = {0};

uint8_t Fire_Button[2] = {0}, Enable_Button[2] = {0}, cps = 0;
bool fire = false, enable = false;

// Helper function to check if a key is pressed in current report
bool check(uint8_t c, uint8_t arr[]){
    for(uint8_t i=0; i<6; i++)
    {
        if(arr[i] == c) return true;
    }
    return false;
}


uint8_t n = 0;
bool pushButton(uint8_t now) {
    if(now && n == 0) {
        n = 1;
        return true; // Button was just pressed
    } else if(!now && n == 1) {
        return true; // Button was just released
    }else if(now && n == 1) {
        n = 0;
        return false; // Button is still pressed
    } else if(!now && n == 0) {
        return false; // Button is still released
    }
    return false;
}

// convert hid keyboard report to hid gamepad report
void kbd_report(hid_keyboard_report_t const *report) {
    keyboard = *report;

    if(Fire_Button[1] == 1){fire = check(Fire_Button[0], report->keycode);}
    else if(Fire_Button[1] == 2){fire  = report->modifier & Fire_Button[0];}

    if(Enable_Button[1] == 1){enable = pushButton(check(Enable_Button[0], report->keycode));}
    else if(Enable_Button[1] == 2){enable = pushButton(report->modifier & Enable_Button[0]);}
}

// convert hid mouse report to hid gamepad report
void mouse_report(hid_mouse_report_t const *report) {
    mouse = *report;

    if(Fire_Button[1] == 3){fire = report->buttons & Fire_Button[0];}
    if(Enable_Button[1] == 3){enable = pushButton(report->buttons & Enable_Button[0]);}
}

void modified_task(){
    tud_hid_keyboard_report(REPORT_ID_KEYBOARD, keyboard.modifier, (uint8_t*) keyboard.keycode);
    tud_hid_mouse_report(REPORT_ID_MOUSE, mouse.buttons, mouse.x, mouse.y, mouse.wheel, 0);
}

void saveConfig(uint8_t* config_arr) {
    if(config_arr == NULL) { return;}
    else if(config_arr[0] == 0x11){}
}