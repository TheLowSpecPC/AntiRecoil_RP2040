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

absolute_time_t recoilTime = 0, clickerTime = 0;

uint8_t Fire_Button[2] = {0}, Enable_Button[2] = {0}, pattern[264][2];
uint32_t cps = 0, delay = 0, pattern_length = 0, pattern_length_temp = 0;
bool AntiRecoilEnable = false, AutoClickerEnable = false, fire = false, defaultRecoil = false;

// Helper function to check if a key is pressed in current report
bool check(uint8_t c, uint8_t arr[]){
    for(uint8_t i=0; i<6; i++)
    {
        if(arr[i] == c) return true;
    }
    return false;
}

typedef struct {
    uint8_t n;
    bool output;
    absolute_time_t debounceTime;
    bool rose; // Triggers once when output turns true
    bool fell; // Triggers once when output turns false
} DebounceState;

// Initialize your buttons (all false/0 by default)
DebounceState enable = {0}, middle = {0}, forward = {0}, backward = {0};

void updateButton(uint8_t state, DebounceState* button, absolute_time_t time) {
    // 1. Reset edge detectors
    button->rose = false;
    button->fell = false;

    // --- ON PRESS LOGIC (Toggle turns ON) ---
    if(state && button->n == 0) {
        button->n = 1;
        button->debounceTime = time;
        button->output = false; 
    } 
    else if(!state && button->n == 1) {
        button->n = 0; 
    }
    else if(state && button->n == 1 && (time - button->debounceTime) >= 10000) {
        button->n = 2;
        button->debounceTime = 0;
        button->output = true; 
        button->rose = true; // Physical Press 1 (Debounced)
    }
    else if(!state && button->n == 2) {
        button->n = 3;
        button->output = true; 
        button->fell = true; // Physical Release 1
    }

    // --- OFF PRESS LOGIC (Toggle turns OFF) ---
    else if(state && button->n == 3) {
        button->n = 4;
        button->debounceTime = time;
        button->output = true; 
    }
    else if(!state && button->n == 4) {
        button->n = 3; 
    }
    else if(state && button->n == 4 && (time - button->debounceTime) >= 10000) {
        button->n = 5;
        button->debounceTime = 0;
        button->output = false; 
        button->rose = true; // Physical Press 2 (Debounced)
    }
    else if(!state && button->n == 5) {
        button->n = 0;
        button->output = false; 
        button->fell = true; // Physical Release 2
    }
}

// convert hid keyboard report to hid gamepad report
void kbd_report(hid_keyboard_report_t const *report) {
    for(int i = 0; i < 6; i++){
        if(Fire_Button[1] == 1 && AutoClickerEnable && fire && enable.output){continue;} // Skip rapid fire button if enabled
        else{keyboard.keycode[i] = report->keycode[i];}
    }

    for(int i = 0; i < 8; i++){
        if(Fire_Button[1] == 2 && AutoClickerEnable && fire && enable.output){continue;} // Skip rapid fire button if enabled
        else{keyboard.modifier = report->modifier & TU_BIT(i) ? keyboard.modifier | TU_BIT(i) : keyboard.modifier & ~TU_BIT(i);}
    }

    if(Fire_Button[1] == 1){fire = check(Fire_Button[0], report->keycode);}
    else if(Fire_Button[1] == 2){fire  = report->modifier & Fire_Button[0];}

    tud_hid_keyboard_report(REPORT_ID_KEYBOARD, keyboard.modifier, (uint8_t*) keyboard.keycode);
}

// convert hid mouse report to hid gamepad report
void mouse_report(hid_mouse_report_t const *report) {
    mouse.x = report->x; mouse.y = report->y; mouse.wheel = report->wheel;

    for(int i = 0; i < 5; i++){
        if(Fire_Button[1] == 3 && AutoClickerEnable && fire && enable.output){continue;} // Skip rapid fire button if enabled
        else{mouse.buttons = report->buttons & TU_BIT(i) ? mouse.buttons | TU_BIT(i) : mouse.buttons & ~TU_BIT(i);}
    }

    if(Fire_Button[1] == 3){fire = report->buttons & Fire_Button[0];}

    tud_hid_mouse_report(REPORT_ID_MOUSE, mouse.buttons, mouse.x, mouse.y, mouse.wheel, 0);
}

void modified_task(){
    absolute_time_t now = get_absolute_time();

    //Keyboard AutoClicker Button Check
    if(Enable_Button[1] == 1){updateButton(check(Enable_Button[0], keyboard.keycode), &enable, now);}
    else if(Enable_Button[1] == 2){updateButton(keyboard.modifier & Enable_Button[0], &enable, now);}

    //Mouse AutoClicker Button Check
    if(Enable_Button[1] == 3){updateButton(mouse.buttons & Enable_Button[0], &enable, now);}

    if(AntiRecoilEnable){
        if(mouse.buttons & TU_BIT(0) && mouse.buttons & TU_BIT(1)){
            if(pattern_length_temp == 0){pattern_length_temp = pattern_length;}

            if((now - recoilTime) >= delay){
                recoilTime = now;

                int8_t x = pattern[pattern_length - pattern_length_temp][0];
                int8_t y = pattern[pattern_length - pattern_length_temp][1];
                pattern_length_temp--;

                tud_hid_mouse_report(REPORT_ID_MOUSE, mouse.buttons, x, y, 0, 0);
            }
        }
        else{
            pattern_length_temp = pattern_length;
        }
    }

    if(AutoClickerEnable && enable.output){
        gpio_put(25, 1);
        if(fire){
            if((now - clickerTime) >= 1000000/cps){
                clickerTime = now;

                if(Fire_Button[1] == 1){
                    for(int i = 0; i < 6; i++){
                        if(keyboard.keycode[i] == Fire_Button[0]){
                            keyboard.keycode[i] = 0;
                            break;
                        }
                        else if(keyboard.keycode[i] == 0){
                            keyboard.keycode[i] = Fire_Button[0];
                            break;
                        }
                    }
                    tud_hid_keyboard_report(REPORT_ID_KEYBOARD, keyboard.modifier, (uint8_t*) keyboard.keycode);
                }
                else if(Fire_Button[1] == 2){
                    keyboard.modifier = keyboard.modifier ^ Fire_Button[0];
                    tud_hid_keyboard_report(REPORT_ID_KEYBOARD, keyboard.modifier, (uint8_t*) keyboard.keycode);
                }
                else if(Fire_Button[1] == 3){
                    mouse.buttons = mouse.buttons ^ Fire_Button[0];
                    tud_hid_mouse_report(REPORT_ID_MOUSE, mouse.buttons, 0, 0, 0, 0);
                }
            }
        }
        else{
            if(Fire_Button[1] == 1){
                for(int i = 0; i < 6; i++){
                    if(keyboard.keycode[i] == Fire_Button[0]){
                        keyboard.keycode[i] = 0;
                        break;
                    }
                }
            }
            else if(Fire_Button[1] == 2){keyboard.modifier = keyboard.modifier & ~Fire_Button[0];}
            else if(Fire_Button[1] == 3){mouse.buttons = mouse.buttons & ~Fire_Button[0];}
        }
    }
    else{
        gpio_put(25, 0);
    }

    if(defaultRecoil){
        updateButton(mouse.buttons & TU_BIT(2), &middle, now);
        updateButton(mouse.buttons & TU_BIT(3), &backward, now);
        updateButton(mouse.buttons & TU_BIT(4), &forward, now);

        if(middle.rose && middle.output){tud_cdc_write_str("Enable\r\n");}
        else if(middle.fell && !middle.output){tud_cdc_write_str("Disable\r\n");}

        if(middle.output){
            if(forward.rose){tud_cdc_write_str("UP\r\n");}
            else if(backward.rose){tud_cdc_write_str("DOWN\r\n");}
        }
    }
}

void saveConfig(uint8_t* config_arr) {
    if(config_arr == NULL) { return;}

    else if(config_arr[0] == 0x11){
        AutoClickerEnable = true;
        cps = config_arr[1]*2;
        Fire_Button[0] = config_arr[2];
        Fire_Button[1] = config_arr[3];
        Enable_Button[0] = config_arr[4];
        Enable_Button[1] = config_arr[5];
    }

    else if(config_arr[0] == 0x10){AutoClickerEnable = false;}

    else if(config_arr[0] == 0x21){
        AntiRecoilEnable = true;
        defaultRecoil = config_arr[1] == 0x01 ? true : false;
        delay = config_arr[2]*1000;
        pattern_length = config_arr[3];
        pattern_length_temp = pattern_length;
        for(int i = 0; i < pattern_length; i++){
            pattern[i][0] = config_arr[4 + i*2];
            pattern[i][1] = config_arr[5 + i*2];
        }
    }

    else if(config_arr[0] == 0x20){
        AntiRecoilEnable = false; 
        defaultRecoil = false;
    }
}