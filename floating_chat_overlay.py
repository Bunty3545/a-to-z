"""
Floating Chat Overlay Widget
----------------------------
A lightweight, semi-transparent desktop chat assistant widget built with Tkinter.
- Global Hotkey: Press Ctrl + Shift + C to toggle visibility anywhere.
- Semi-transparent UI: Keeps background windows partially visible.
- Non-blocking: Background thread handles responses smoothly.
"""

import os
import sys
import threading
import tkinter as tk
from pynput import keyboard

class FloatingChatWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Desktop Assistant Overlay")
        self.visible = False

        # Configure window geometry (Width x Height + X_offset + Y_offset)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.width = 380
        self.height = 520
        x_pos = screen_w - self.width - 30
        y_pos = (screen_h - self.height) // 2

        self.root.geometry(f"{self.width}x{self.height}+{x_pos}+{y_pos}")
        self.root.overrideredirect(True)       # Frameless modern look
        self.root.wm_attributes("-topmost", True)  # Floating on top of other windows
        self.root.wm_attributes("-alpha", 0.92)    # 92% Opacity (semi-transparent)
        self.root.config(bg="#0F172A")

        self._build_ui()
        self._setup_hotkey()

        # Hide initially until toggled
        self.root.withdraw()

    def _build_ui(self):
        # 1. Draggable Top Header
        header = tk.Frame(self.root, bg="#1E293B", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_lbl = tk.Label(
            header,
            text="💬 AI Assistant Overlay",
            bg="#1E293B",
            fg="#F8FAFC",
            font=("Segoe UI", 10, "bold")
        )
        title_lbl.pack(side="left", padx=12, pady=8)

        # Hotkey badge
        badge = tk.Label(
            header,
            text="Ctrl+Shift+C",
            bg="#334155",
            fg="#94A3B8",
            font=("Segoe UI", 8),
            padx=6,
            pady=2
        )
        badge.pack(side="left", padx=4)

        # Close / Minimize button
        close_btn = tk.Button(
            header,
            text="✕",
            bg="#1E293B",
            fg="#94A3B8",
            activebackground="#EF4444",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.hide
        )
        close_btn.pack(side="right", padx=10, pady=8)

        # Enable dragging window via header
        def start_drag(event):
            self.root._drag_x = event.x
            self.root._drag_y = event.y

        def do_drag(event):
            x = self.root.winfo_pointerx() - self.root._drag_x
            y = self.root.winfo_pointery() - self.root._drag_y
            self.root.geometry(f"+{x}+{y}")

        header.bind("<ButtonPress-1>", start_drag)
        header.bind("<B1-Motion>", do_drag)
        title_lbl.bind("<ButtonPress-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)

        # 2. Chat Log Display Area
        chat_frame = tk.Frame(self.root, bg="#0F172A", padx=10, pady=8)
        chat_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(chat_frame)
        scrollbar.pack(side="right", fill="y")

        self.chat_display = tk.Text(
            chat_frame,
            bg="#131D31",
            fg="#F8FAFC",
            font=("Segoe UI", 9),
            wrap="word",
            state="disabled",
            bd=0,
            padx=10,
            pady=8,
            yscrollcommand=scrollbar.set
        )
        self.chat_display.pack(fill="both", expand=True)
        scrollbar.config(command=self.chat_display.yview)

        # Styling tags for speech formatting
        self.chat_display.tag_configure("user", foreground="#38BDF8", font=("Segoe UI", 9, "bold"))
        self.chat_display.tag_configure("bot", foreground="#A7F3D0", font=("Segoe UI", 9))
        self.chat_display.tag_configure("system", foreground="#94A3B8", font=("Segoe UI", 8, "italic"))

        # Welcome message
        self.append_message("System", "Floating Assistant ready! Press Ctrl+Shift+C anytime to toggle.", "system")

        # 3. Input & Send Bar
        input_container = tk.Frame(self.root, bg="#1E293B", padx=8, pady=8)
        input_container.pack(fill="x")

        self.entry_var = tk.StringVar()
        self.entry_field = tk.Entry(
            input_container,
            textvariable=self.entry_var,
            bg="#0F172A",
            fg="#F8FAFC",
            font=("Segoe UI", 10),
            bd=0,
            insertbackground="#38BDF8",
            relief="flat"
        )
        self.entry_field.pack(side="left", fill="x", expand=True, padx=(4, 8), pady=4)
        self.entry_field.bind("<Return>", lambda e: self.send_message())

        send_btn = tk.Button(
            input_container,
            text="Send",
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.send_message
        )
        send_btn.pack(side="right")

        # Press Escape inside window to quickly dismiss
        self.root.bind("<Escape>", lambda e: self.hide())

    def append_message(self, sender, text, tag="bot"):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"{sender}: ", tag)
        self.chat_display.insert("end", f"{text}\n\n", tag)
        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    def send_message(self):
        msg = self.entry_var.get().strip()
        if not msg:
            return

        self.entry_var.set("")
        self.append_message("You", msg, "user")

        # Run bot response in a background thread to prevent UI freezing
        threading.Thread(target=self._process_bot_reply, args=(msg,), daemon=True).start()

    def _process_bot_reply(self, user_msg):
        """Simulate or connect to an actual LLM / backend endpoint."""
        # Replace this logic with your API call (e.g. requests.post to your local Node/Python bot API)
        reply = f"Acknowledged: '{user_msg}'. You can wire your bot API in _process_bot_reply()."
        self.root.after(300, lambda: self.append_message("Assistant", reply, "bot"))

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.entry_field.focus_set()
        self.visible = True

    def hide(self):
        self.root.withdraw()
        self.visible = False

    def _setup_hotkey(self):
        """Listens globally for Ctrl + Shift + C using pynput."""
        current_keys = set()

        def on_press(key):
            current_keys.add(key)
            # Check for Ctrl + Shift + C
            ctrl = any(k in current_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
            shift = any(k in current_keys for k in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r])
            c_pressed = False

            if hasattr(key, 'char') and key.char and key.char.lower() == 'c':
                c_pressed = True

            if ctrl and shift and c_pressed:
                # Trigger toggle on the main Tkinter thread
                self.root.after(0, self.toggle)

        def on_release(key):
            current_keys.discard(key)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()

    def run(self):
        print("Floating Chat Overlay is running.")
        print("Press [Ctrl + Shift + C] anywhere to open or close the widget.")
        self.root.mainloop()

if __name__ == "__main__":
    app = FloatingChatWidget()
    app.run()

