void kbd_report(hid_keyboard_report_t const *report);
void mouse_report(hid_mouse_report_t const *report);
void modified_task();
void saveConfig(uint8_t* config_arr);