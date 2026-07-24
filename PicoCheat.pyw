import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import serial
import serial.tools.list_ports
import json
import os
import time
import keycodes

CONFIG_FILE = "antirecoil_config.json"
APP_TITLE = "PicoCheat"

# Default schema for the new nested structure
DEFAULT_CONFIG = {
    "games": {},
    "sensitivity": 66,
    "pull": 1.2,
    "auto_clicker": {
        "Fire_Button": "MOUSE_1",
        "Enable_Button": "Unmapped",
        "CPS": 10
    }
}

default_pattern = []
for i in range(100):
    if i < 10:
        default_pattern.append([0.0, 0.0])
    else:
        default_pattern.append([0.0, 0.5])

class MappingDialog(tk.Toplevel):
    """Reused and slightly adapted mapping dialog from your original code."""
    def __init__(self, parent, btn_name, current_val, save_callback):
        super().__init__(parent)
        self.title(f"Map Button: {btn_name}")
        self.geometry("350x160")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()

        self.btn_name = btn_name
        self.new_val = current_val
        self.save_callback = save_callback

        ttk.Label(self, text=f"Mapping for {btn_name}", font=("Segoe UI", 12, "bold")).pack(pady=10)
        self.lbl_display = ttk.Label(self, text=f"Current: {self.new_val}", font=("Segoe UI", 10))
        self.lbl_display.pack(pady=5)
        ttk.Label(self, text="Press any Key or Mouse Button...", foreground="gray").pack(pady=5)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15, padx=10)

        self.btn_save = ttk.Button(btn_frame, text="Save", command=self.apply_save)
        self.btn_save.pack(side=tk.LEFT, expand=True, padx=2)
        
        self.btn_unmap = ttk.Button(btn_frame, text="Unmap", command=self.apply_unmap)
        self.btn_unmap.pack(side=tk.LEFT, expand=True, padx=2)
        
        self.btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        self.btn_cancel.pack(side=tk.LEFT, expand=True, padx=2)

        self.bind("<Key>", self.record_event)
        self.bind("<Button>", self.record_event)
        self.focus_set()

    def record_event(self, event):
        if event.widget in (self.btn_save, self.btn_cancel, self.btn_unmap):
            return
        if event.type == tk.EventType.KeyPress:
            self.new_val = f"KEY_{event.keysym.upper()}"
        elif event.type == tk.EventType.ButtonPress:
            self.new_val = f"MOUSE_{event.num}" 
        else:
            return
        self.lbl_display.config(text=f"New: {self.new_val}")

    def apply_save(self):
        self.save_callback(self.btn_name, self.new_val)
        self.destroy()

    def apply_unmap(self):
        self.save_callback(self.btn_name, "Unmapped")
        self.destroy()


class ScrollableFrame(ttk.Frame):
    """Utility class to create dynamic scrollable areas."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def clear(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()


class ControllerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("620x600")

        #self.iconbitmap("pico.ico")

        self.config = self.load_config()
        self.serial_conn = None
        self.current_menu = "root"
        
        self.setup_fixed_ui()
        self.show_root_menu()
        self.refresh_ports()
        self.monitor_connection()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_fixed_ui(self):
        """Sets up the UART connection header and Status bar visible on all pages."""
        # --- Top Frame: Serial Connection ---
        serial_frame = ttk.LabelFrame(self, text="UART Connection")
        serial_frame.pack(fill=tk.X, padx=10, pady=5)

        self.port_var = tk.StringVar()
        self.cb_ports = ttk.Combobox(serial_frame, textvariable=self.port_var, state="readonly", width=15)
        self.cb_ports.pack(side=tk.LEFT, padx=10, pady=10)

        btn_refresh = ttk.Button(serial_frame, text="↻ Refresh", command=self.refresh_ports, width=10)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(serial_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Status: Disconnected")
        status_label = ttk.Label(self, textvariable=self.status_var, foreground="blue")
        status_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        ttk.Separator(self, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)

        # --- Dynamic View Container ---
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def navigate(self, menu_func, menu_name):
        """Checks connection before navigating to any sub-menu."""
        if menu_name != "root":
            if not self.serial_conn or not self.serial_conn.is_open:
                messagebox.showwarning("Connection Required", "Please connect a device to access this menu.")
                return
        self.current_menu = menu_name
        menu_func()

    # ============================
    # VIEW RENDERING METHODS
    # ============================

    def show_root_menu(self):
        self.clear_container()
        
        lbl_title = ttk.Label(self.main_container, text="Main Menu", font=("Segoe UI", 14, "bold"))
        lbl_title.pack(pady=10)

        # Dynamic features list to allow easy addition later
        features = [
            ("Anti Recoil", lambda: self.navigate(self.show_anti_recoil_menu, "anti_recoil")),
            ("Auto Clicker", lambda: self.navigate(self.show_auto_clicker_menu, "auto_clicker"))
        ]

        for text, command in features:
            btn = ttk.Button(self.main_container, text=text, command=command, width=30)
            btn.pack(pady=10, ipady=5)

    def show_anti_recoil_menu(self):
        self.clear_container()
        
        top_bar = ttk.Frame(self.main_container)
        top_bar.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_bar, text="⬅ Back", command=lambda: self.navigate(self.show_root_menu, "root")).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="Anti Recoil Menu", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # Scrollable Games Area
        scroll_area = ScrollableFrame(self.main_container)
        scroll_area.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Default Button
        btn_default = ttk.Button(scroll_area.scrollable_frame, text="Default", 
                                 command=lambda: self.navigate(self.show_defaultMenu, "default_sens"))
        btn_default.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Dynamic Games Buttons
        col = 1
        row = 0
        for game_name in self.config["games"].keys():
            if col > 3:
                col = 0
                row += 1
            btn = ttk.Button(scroll_area.scrollable_frame, text=game_name, 
                             command=lambda g=game_name: self.navigate(lambda: self.show_game_menu(g), f"game_{g}"))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1

        # Configure columns to expand evenly
        for i in range(4):
            scroll_area.scrollable_frame.columnconfigure(i, weight=1)

        # Bottom Add/Remove
        bottom_bar = ttk.Frame(self.main_container)
        bottom_bar.pack(fill=tk.X, pady=10)
        ttk.Button(bottom_bar, text="Add Game", command=self.add_game).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(bottom_bar, text="Remove Game", command=self.remove_game).pack(side=tk.LEFT, expand=True, padx=5)

    def show_defaultMenu(self):
        self.clear_container()
        
        top_bar = ttk.Frame(self.main_container)
        top_bar.pack(fill=tk.X, pady=5)
        ttk.Button(top_bar, text="⬅ Back", command=lambda: self.navigate(self.show_anti_recoil_menu, "anti_recoil")).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="Default Config", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=10)

        content = ttk.Frame(self.main_container)
        content.pack(expand=True)

        ttk.Label(content, text="Sensitivity:").pack(side=tk.LEFT, padx=5)
        sens_var = tk.IntVar(value=self.config["sensitivity"])

        def save_sens(*args):
            self.config["sensitivity"] = sens_var.get()
            self.save_config()

        sens_var.trace_add("write", save_sens)
        ttk.Spinbox(content, from_=8, to=100, textvariable=sens_var, width=10).pack(side=tk.LEFT, padx=5)

        ttk.Label(content, text="Pull:").pack(side=tk.LEFT, padx=5)
        pull_var = tk.DoubleVar(value=self.config["pull"])  # Use the configured pull value

        def save_pull(*args):
            self.config["pull"] = pull_var.get()
            self.save_config()

        pull_var.trace_add("write", save_pull)
        ttk.Spinbox(content, from_=1.0, to=20.0, increment=0.1, textvariable=pull_var, width=10).pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Start", command=lambda: [self.send_command("Start_Default_Recoil", None), self.status_var.set("Status: Default Anti-Recoil Started")]).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stop", command=lambda: [self.send_command("Stop_Default_Recoil"), self.status_var.set("Status: Default Anti-Recoil Stopped")]).pack(side=tk.LEFT, padx=5)

    def show_game_menu(self, game_name):
        self.clear_container()
        
        top_bar = ttk.Frame(self.main_container)
        top_bar.pack(fill=tk.X, pady=5)
        ttk.Button(top_bar, text="⬅ Back", command=lambda: self.navigate(self.show_anti_recoil_menu, "anti_recoil")).pack(side=tk.LEFT)
        ttk.Label(top_bar, text=f"{game_name} Guns", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        lbl_selected = ttk.Label(self.main_container, text="Selected Gun: None", foreground="green", font=("Segoe UI", 10, "bold"))
        lbl_selected.pack(pady=5)

        scroll_area = ScrollableFrame(self.main_container)
        scroll_area.pack(fill=tk.BOTH, expand=True, pady=5)

        # Render Gun Buttons
        self.current_gun = ""
        guns = self.config["games"].get(game_name, {})
        col, row = 0, 0
        for gun_name in guns.keys():
            if col > 3:
                col = 0
                row += 1
            btn = ttk.Button(scroll_area.scrollable_frame, text=gun_name, 
                             command=lambda g=gun_name: [lbl_selected.config(text=f"Selected Gun: {g}"), assign_current_gun(g)])
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            col += 1

        def assign_current_gun(gun):
            self.current_gun = gun

        for i in range(4):
            scroll_area.scrollable_frame.columnconfigure(i, weight=1)

        ttk.Label(self.main_container, text="Sensitivity:").pack(side=tk.TOP, padx=5)
        sens_var = tk.IntVar(value=self.config["sensitivity"])
        
        def save_sens(*args):
            self.config["sensitivity"] = sens_var.get()
            self.save_config()

        sens_var.trace_add("write", save_sens)
        ttk.Spinbox(self.main_container, from_=8, to=100, textvariable=sens_var, width=10).pack(side=tk.TOP, padx=5)

        bottom_bar = ttk.Frame(self.main_container)
        bottom_bar.pack(fill=tk.X, pady=10)
        ttk.Button(bottom_bar, text="Add", command=lambda: self.add_gun(game_name)).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(bottom_bar, text="Remove", command=lambda: self.remove_gun(game_name)).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(bottom_bar, text="Start", command=lambda: [self.send_command("Start_Anti_Recoil", game_name, self.current_gun) if self.current_gun else None, self.status_var.set(f"Status: {game_name} Anti-Recoil Started")]).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(bottom_bar, text="Stop", command=lambda: [self.send_command("Stop_Anti_Recoil"), self.status_var.set(f"Status: {game_name} Anti-Recoil Stopped")]).pack(side=tk.LEFT, expand=True, padx=2)

    def show_auto_clicker_menu(self):
        self.clear_container()
        
        top_bar = ttk.Frame(self.main_container)
        top_bar.pack(fill=tk.X, pady=5)
        ttk.Button(top_bar, text="⬅ Back", command=lambda: self.navigate(self.show_root_menu, "root")).pack(side=tk.LEFT)
        ttk.Label(top_bar, text="Auto Clicker", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=10)

        # Mapping Buttons
        map_frame = ttk.Frame(self.main_container)
        map_frame.pack(pady=15)
        
        def save_mapping(key, val):
            self.config["auto_clicker"][key] = val
            self.save_config()
            self.show_auto_clicker_menu() # Refresh view to show new map

        current_fire = self.config["auto_clicker"].get("Fire_Button", "Unmapped")
        ttk.Button(map_frame, text=f"Fire Button: {current_fire}", 
                   command=lambda: MappingDialog(self, "Fire_Button", current_fire, save_mapping)).pack(side=tk.LEFT, padx=10)
        
        current_enable = self.config["auto_clicker"].get("Enable_Button", "Unmapped")
        ttk.Button(map_frame, text=f"Enable Button: {current_enable}", 
                   command=lambda: MappingDialog(self, "Enable_Button", current_enable, save_mapping)).pack(side=tk.LEFT, padx=10)

        # CPS Spinbox
        cps_frame = ttk.Frame(self.main_container)
        cps_frame.pack(pady=15)
        ttk.Label(cps_frame, text="CPS (Clicks Per Second):").pack(side=tk.LEFT, padx=5)
        cps_var = tk.IntVar(value=self.config["auto_clicker"].get("CPS", 10))
        
        def save_cps(*args):
            self.config["auto_clicker"]["CPS"] = cps_var.get()

        cps_var.trace_add("write", save_cps)
        ttk.Spinbox(cps_frame, from_=1, to=100, textvariable=cps_var, width=10).pack(side=tk.LEFT, padx=5)

        # Controls
        ctrl_frame = ttk.Frame(self.main_container)
        ctrl_frame.pack(pady=20)
        ttk.Button(ctrl_frame, text="Start", command=lambda: [self.send_command("Start_Auto_Clicker"), self.status_var.set("Status: Auto Clicker Started")]).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Save", command=lambda: [self.save_config(), self.status_var.set("Status: Auto Clicker Saved")]).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Stop", command=lambda: [self.send_command("Stop_Auto_Clicker"), self.status_var.set("Status: Auto Clicker Stopped")]).pack(side=tk.LEFT, padx=5)

    # ============================
    # DATA MANAGEMENT METHODS
    # ============================

    def add_game(self):
        game_name = simpledialog.askstring("Add Game", "Enter Game Name:", parent=self)
        if game_name:
            if game_name in self.config["games"] or game_name.lower() == "default":
                messagebox.showerror("Error", "Game already exists or invalid name.")
            else:
                self.config["games"][game_name] = {}
                self.save_config()
                self.show_anti_recoil_menu() # Refresh screen

    def remove_game(self):
        game_name = simpledialog.askstring("Remove Game", "Enter Game Name to Remove:", parent=self)
        if game_name and game_name in self.config["games"]:
            del self.config["games"][game_name]
            self.save_config()
            self.show_anti_recoil_menu()

    def add_gun(self, game_name):
        file_path = filedialog.askopenfilename(
            title="Select Gun Profile",
            filetypes=[("Text Files", "*.txt")],
            parent=self
        )
        if file_path:
            # Uses the selected file's name (without the path) as the button name. 
            gun_name = os.path.basename(file_path)[:-4]
            self.config["games"][game_name][gun_name] = file_path
            self.save_config()
            self.show_game_menu(game_name)

    def remove_gun(self, game_name):
        gun_name = simpledialog.askstring("Remove Gun", "Enter Gun Name to Remove:", parent=self)
        if gun_name and gun_name in self.config["games"][game_name]:
            del self.config["games"][game_name][gun_name]
            self.save_config()
            self.show_game_menu(game_name)

    # ============================
    # UART CONNECTION METHODS
    # ============================

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.cb_ports['values'] = ports
        if ports:
            self.cb_ports.current(0)
        else:
            self.cb_ports.set("No Ports Found")

    def toggle_connection(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
            self.btn_connect.config(text="Connect")
            self.status_var.set("Status: Disconnected")
            self.cb_ports.config(state="readonly")
            
            # Kick back to root menu if disconnecting while inside a tool
            if self.current_menu != "root":
                self.show_root_menu()
        else:
            port = self.port_var.get()
            if not port or port == "No Ports Found":
                messagebox.showerror("Error", "Please select a valid COM port.")
                return
            try:
                # Connected utilizing standard fast baudrate 
                self.serial_conn = serial.Serial(port, baudrate=115200, timeout=1)
                self.btn_connect.config(text="Disconnect")
                self.cb_ports.config(state=tk.DISABLED)
                self.status_var.set(f"Status: Connected to {port}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect to {port}\n{e}")

    def monitor_connection(self):
        """Background process to check if device was abruptly unplugged."""
        if self.serial_conn and not self.serial_conn.is_open:
            # Device lost
            self.toggle_connection() # Triggers the UI disconnect logic and pushes to root
            self.status_var.set("Status: Connection Lost. Returned to main menu.")
            
        # Call this function again after 1000ms
        self.after(1000, self.monitor_connection)

    def send_command(self, *message):
        """Sends a command to the connected device."""
        if self.serial_conn and self.serial_conn.is_open:
            command = [b'\xff', b'\xaa']
            try:
                if message[0] == "Start_Auto_Clicker":
                    command.append(b'\x11')
                    command.append(bytes([self.config["auto_clicker"]["CPS"]]))
                    command += self.buttonByteConversion(self.config["auto_clicker"]["Fire_Button"]) + self.buttonByteConversion(self.config["auto_clicker"]["Enable_Button"])

                elif message[0] == "Stop_Auto_Clicker":
                    command.append(b'\x10')

                elif message[0] == "Start_Anti_Recoil":
                    pattern, delay = self.patternToBytes(self.config["games"][message[1]][message[2]], self.config["sensitivity"])
                    command += [b'\x21', delay, bytes([int(len(pattern)/2)])] + pattern

                elif message[0] == "Start_Default_Recoil":
                    pattern, delay = self.patternToBytes("Default", self.config["sensitivity"])
                    command += [b'\x21', delay, bytes([int(len(pattern)/2)])] + pattern

                elif message[0] == "Stop_Anti_Recoil" or message[0] == "Stop_Default_Recoil":
                    command.append(b'\x20')

                command = b''.join(command)
                print(f"Sending command: {command}")

                self.serial_conn.reset_input_buffer()
                self.serial_conn.write(command)
                self.serial_conn.flush()

            except Exception as e:
                self.status_var.set("Status: Send Error", f"Failed to send command.\n{e}")
        else:
            messagebox.showwarning("Not Connected", "Please connect to a device first.")

    def patternToBytes(self, filename, sensitivity):
        """Converts a pattern file into a byte array for sending to the device."""
        if filename == "Default":
            final_patterns = [b'\x00', b'\x00']
            delay = bytes([80])
            yaw = sensitivity * 0.00101
            for i in default_pattern:  # Example default pattern
                final_patterns.append(bytes([round(float(i[0])/yaw) & 0xff]))
                final_patterns.append(bytes([round(float(i[1] + self.config["pull"])/yaw) & 0xff]))
            return final_patterns, delay
        elif not os.path.exists(filename):
            messagebox.showerror("File Error", f"Pattern file not found: {filename}")
            return None, None

        try:
            with open(filename, 'r') as f:
                patterns = f.readlines()
                f.close()

            yaw = sensitivity * 0.00101

            final_patterns = []
            delay = 0
            for i in range(len(patterns)):
                patterns[i] = patterns[i].strip('\n').split(', ')
                if i == 0:
                    delay = bytes([int(patterns[i][0])])
                    continue
                final_patterns.append(bytes([round(float(patterns[i][0])/yaw) & 0xff]))
                final_patterns.append(bytes([round(float(patterns[i][1])/yaw) & 0xff]))

            return final_patterns, delay
        
        except Exception as e:
            messagebox.showerror("Read Error", f"Failed to read pattern file.\n{e}")
            return None, None
        
    def buttonByteConversion(self, key):
        final_bytes = []

        if key in keycodes.asciiToKeycode:
            final_bytes.append(keycodes.asciiToKeycode[key])
            final_bytes.append(b'\x01')

        elif key in keycodes.modifier:
            final_bytes.append(keycodes.modifier[key])
            final_bytes.append(b'\x02')

        elif key in keycodes.mouse:
            final_bytes.append(keycodes.mouse[key])
            final_bytes.append(b'\x03')

        else:
            final_bytes += [b'\x00', b'\x00']

        return final_bytes


if __name__ == "__main__":
    app = ControllerApp()
    app.mainloop()