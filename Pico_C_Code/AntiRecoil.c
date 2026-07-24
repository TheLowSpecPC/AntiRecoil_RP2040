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
bool AntiRecoilEnable = false, AutoClickerEnable = false, fire = false, enable = false;

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
    for(int i = 0; i < 6; i++){
        if(Fire_Button[1] == 1 && AutoClickerEnable && fire && enable){continue;} // Skip rapid fire button if enabled
        else{keyboard.keycode[i] = report->keycode[i];}
    }

    for(int i = 0; i < 8; i++){
        if(Fire_Button[1] == 2 && AutoClickerEnable && fire && enable){continue;} // Skip rapid fire button if enabled
        else{keyboard.modifier = report->modifier & TU_BIT(i) ? keyboard.modifier | TU_BIT(i) : keyboard.modifier & ~TU_BIT(i);}
    }

    if(Fire_Button[1] == 1){fire = check(Fire_Button[0], report->keycode);}
    else if(Fire_Button[1] == 2){fire  = report->modifier & Fire_Button[0];}

    if(Enable_Button[1] == 1){enable = pushButton(check(Enable_Button[0], report->keycode));}
    else if(Enable_Button[1] == 2){enable = pushButton(report->modifier & Enable_Button[0]);}

    tud_hid_keyboard_report(REPORT_ID_KEYBOARD, keyboard.modifier, (uint8_t*) keyboard.keycode);
}

// convert hid mouse report to hid gamepad report
void mouse_report(hid_mouse_report_t const *report) {
    mouse.x = report->x; mouse.y = report->y; mouse.wheel = report->wheel;

    for(int i = 0; i < 5; i++){
        if(Fire_Button[1] == 3 && AutoClickerEnable && fire && enable){continue;} // Skip rapid fire button if enabled
        else{mouse.buttons = report->buttons & TU_BIT(i) ? mouse.buttons | TU_BIT(i) : mouse.buttons & ~TU_BIT(i);}
    }

    if(Fire_Button[1] == 3){fire = report->buttons & Fire_Button[0];}
    if(Enable_Button[1] == 3){enable = pushButton(report->buttons & Enable_Button[0]);}

    tud_hid_mouse_report(REPORT_ID_MOUSE, mouse.buttons, mouse.x, mouse.y, mouse.wheel, 0);
}

void modified_task(){
    absolute_time_t now = get_absolute_time();

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

    if(AutoClickerEnable && enable){
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
        delay = config_arr[1]*1000;
        pattern_length = config_arr[2];
        pattern_length_temp = pattern_length;
        for(int i = 0; i < pattern_length; i++){
            pattern[i][0] = config_arr[3 + i*2];
            pattern[i][1] = config_arr[4 + i*2];
        }
    }

    else if(config_arr[0] == 0x20){AntiRecoilEnable = false;}
}