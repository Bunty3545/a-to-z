"""
================================================================================
🛡️ ADMIN REAL-TIME CONTROL & AUDIT CENTER v2.0 (HIGH-DPI ULTRA-SHARP EDITION)
================================================================================
Razor-sharp, native 4K/DPI-aware dashboard application for live exam monitoring,
instant student permissions control, query limits, and Telegram live notifications.
"""

import os
import sys
import json
import time
import socket
import datetime
import threading
import webbrowser
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox

# =====================================================
# WINDOWS HIGH-DPI AWARENESS (100% CRYSTAL-CLEAR GRAPHICS & TEXT)
# =====================================================
try:
    # Windows 10/11: Per-Monitor DPI Aware v2 (Zero blur / 100% Native Resolution)
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Configuration Constants
UDP_PORT = 54321
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_JSON_PATH = os.path.join(BASE_DIR, "users.json")
if not os.path.exists(USERS_JSON_PATH) and os.path.exists(os.path.join(os.getcwd(), "users.json")):
    USERS_JSON_PATH = os.path.join(os.getcwd(), "users.json")
ADMIN_LOG_PATH = os.path.join(BASE_DIR, "admin_center.log")
AUDIT_LOG_PATH = os.path.join(BASE_DIR, "app_audit_trail.jsonl")
TEMP_AUDIT_LOG_PATH = os.path.join(os.environ.get("TEMP", BASE_DIR), "app_audit_trail.jsonl")
ADMIN_CONFIG_PATH = os.path.join(BASE_DIR, "admin_config.json")
DASHBOARD_HTML_PATH = os.path.join(BASE_DIR, "admin_dashboard.html")

def log_admin(msg):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ADMIN_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

# Color Palette (High-Contrast Modern Dark Cyber-Slate)
BG_MAIN = "#0B0F19"
BG_CARD = "#111827"
BG_CARD_ALT = "#162032"
BG_HEADER = "#0F172A"
BG_TOOLBAR = "#1F2937"
BORDER_COLOR = "#334155"
TEXT_WHITE = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
ACCENT_BLUE = "#0284C7"
ACCENT_CYAN = "#38BDF8"
ACCENT_GREEN = "#10B981"
ACCENT_RED = "#EF4444"
ACCENT_PURPLE = "#A855F7"
ACCENT_AMBER = "#F59E0B"

class AdminControlCenterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Admin Real-Time Control & Telemetry Center v2.0")
        self.root.geometry("1220x760")
        self.root.minsize(1040, 640)
        self.root.configure(bg=BG_MAIN)

        # Set taskbar icon if available
        ico_path = os.path.join(BASE_DIR, "ms_office.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

        self.users_data = {}
        self.active_sessions = set()
        self.total_solves = 0
        self.is_listening = True
        self.filter_mode = "ALL"
        self.search_query = ""

        # Telegram config
        self.telegram_cfg = self._load_telegram_config()
        self.exam_policy = self._load_exam_policy()

        # Styles
        self._setup_styles()

        # Build UI layout
        self._build_header()
        self._build_kpi_bar()
        self._build_main_panels()
        self._build_footer()

        # Initial data load
        self.load_users()
        self.load_historical_logs()

        # Start background UDP receiver for real-time telemetry (<1ms latency)
        self.udp_thread = threading.Thread(target=self._listen_udp_events, daemon=True)
        self.udp_thread.start()

        # Periodic refresh timer (every 10 seconds for user list sync)
        self.root.after(10000, self._periodic_sync)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure Treeview (Ultra-crisp dark theme)
        style.configure("Dark.Treeview",
                        background=BG_CARD,
                        foreground=TEXT_WHITE,
                        fieldbackground=BG_CARD,
                        rowheight=32,
                        font=("Segoe UI", 10))
        style.configure("Dark.Treeview.Heading",
                        background=BG_TOOLBAR,
                        foreground=TEXT_MUTED,
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Dark.Treeview",
                  background=[("selected", ACCENT_BLUE)],
                  foreground=[("selected", "#FFFFFF")])

        # Scrollbar styling
        style.configure("Dark.Vertical.TScrollbar",
                        background=BG_CARD,
                        troughcolor=BG_MAIN,
                        bordercolor=BORDER_COLOR,
                        arrowcolor=TEXT_MUTED)

    def _load_telegram_config(self):
        if os.path.exists(ADMIN_CONFIG_PATH):
            try:
                with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("TELEGRAM", {"bot_token": "", "chat_id": "", "enabled": False})
            except Exception:
                pass
        return {"bot_token": "", "chat_id": "", "enabled": False}

    def _save_telegram_config(self):
        cfg = {}
        if os.path.exists(ADMIN_CONFIG_PATH):
            try:
                with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        cfg["TELEGRAM"] = self.telegram_cfg
        try:
            with open(ADMIN_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _load_exam_policy(self):
        default_policy = {
            "allowed_urls": ["https://lms.lpu.in", "https://exam.portal.edu"],
            "quit_password": "",
            "security_options": {
                "anti_screen_capture": True,
                "strict_single_monitor": True,
                "kiosk_lockdown": False,
                "block_screen_sharing": True,
                "block_screen_recording": True,
                "terminate_remote_tools": True,
                "allow_screen_sharing": False
            }
        }
        if os.path.exists(ADMIN_CONFIG_PATH):
            try:
                with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("EXAM_POLICY", default_policy)
            except Exception:
                pass
        return default_policy

    def _save_exam_policy(self):
        cfg = {}
        if os.path.exists(ADMIN_CONFIG_PATH):
            try:
                with open(ADMIN_CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        cfg["EXAM_POLICY"] = self.exam_policy
        try:
            with open(ADMIN_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save exam policy: {e}")


    def _create_hover_button(self, parent, text, bg, fg, hover_bg, command, font=("Segoe UI", 9, "bold"), padx=12, pady=6):
        btn = tk.Button(parent, text=text, font=font, bg=bg, fg=fg,
                        activebackground=hover_bg, activeforeground=fg,
                        relief="flat", bd=0, padx=padx, pady=pady, cursor="hand2", command=command)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=75, bd=0)
        header.pack(fill="x", side="top")

        # Top border highlight line (Electric Cyan)
        top_line = tk.Frame(header, bg=ACCENT_CYAN, height=2)
        top_line.pack(fill="x", side="top")

        # Left branding
        brand_frame = tk.Frame(header, bg=BG_HEADER)
        brand_frame.pack(side="left", padx=20, pady=12)

        icon_box = tk.Frame(brand_frame, bg="#0369A1", width=42, height=42, bd=0)
        icon_box.pack(side="left", padx=(0, 12))
        icon_box.pack_propagate(False)
        icon_lbl = tk.Label(icon_box, text="⚡", font=("Segoe UI", 16, "bold"), bg="#0369A1", fg="#FFFFFF")
        icon_lbl.pack(expand=True)

        title_frame = tk.Frame(brand_frame, bg=BG_HEADER)
        title_frame.pack(side="left")

        title_lbl = tk.Label(title_frame, text="ADMIN REAL-TIME CONTROL & AUDIT CENTER",
                             font=("Segoe UI", 13, "bold"), bg=BG_HEADER, fg=TEXT_WHITE)
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(title_frame, text="Live Telemetry • Remote Access Control • Zero-Latency Stream",
                           font=("Segoe UI", 9), bg=BG_HEADER, fg=TEXT_MUTED)
        sub_lbl.pack(anchor="w")

        # Right quick stats & action buttons
        actions_frame = tk.Frame(header, bg=BG_HEADER)
        actions_frame.pack(side="right", padx=20, pady=12)

        # Live Stream Badge
        pulse_frame = tk.Frame(actions_frame, bg="#064E3B", padx=12, pady=6, bd=1, relief="solid")
        pulse_frame.pack(side="left", padx=(0, 14))
        self.pulse_dot = tk.Label(pulse_frame, text="●", font=("Segoe UI", 12), fg="#34D399", bg="#064E3B")
        self.pulse_dot.pack(side="left", padx=(0, 6))
        self.pulse_text = tk.Label(pulse_frame, text="LIVE STREAM ACTIVE", font=("Segoe UI", 9, "bold"), fg="#34D399", bg="#064E3B")
        self.pulse_text.pack(side="left")

        # Header buttons with razor-sharp styling
        btn_web = self._create_hover_button(actions_frame, "🌐 Web Analytics", "#2563EB", "#FFFFFF", "#1D4ED8", self.open_web_dashboard)
        btn_web.pack(side="left", padx=4)

        btn_policy = self._create_hover_button(actions_frame, "🛡️ Exam Rules & Policy", "#D97706", "#FFFFFF", "#B45309", self.open_exam_policy_dialog)
        btn_policy.pack(side="left", padx=4)

        btn_tg = self._create_hover_button(actions_frame, "📱 Telegram Alerts", "#0284C7", "#FFFFFF", "#0369A1", self.open_telegram_dialog)
        btn_tg.pack(side="left", padx=4)

        btn_refresh = self._create_hover_button(actions_frame, "🔄 Refresh", "#334155", TEXT_WHITE, "#475569", self.refresh_all)
        btn_refresh.pack(side="left", padx=4)

    def _build_kpi_bar(self):
        kpi_bar = tk.Frame(self.root, bg=BG_MAIN, height=65)
        kpi_bar.pack(fill="x", padx=18, pady=(14, 6))

        self.kpi_users_val = self._create_kpi_card(kpi_bar, "TOTAL REGISTERED", "0 Users", ACCENT_CYAN, "👥")
        self.kpi_active_val = self._create_kpi_card(kpi_bar, "ONLINE RIGHT NOW", "0 Active", ACCENT_GREEN, "🟢")
        self.kpi_solves_val = self._create_kpi_card(kpi_bar, "QUESTIONS SOLVED", "0 Solves", ACCENT_AMBER, "🎯")
        self.kpi_blocked_val = self._create_kpi_card(kpi_bar, "BLOCKED ACCOUNTS", "0 Blocked", ACCENT_RED, "🚫")

    def _create_kpi_card(self, parent, label_text, default_val, val_color, icon_char):
        card = tk.Frame(parent, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        card.pack(side="left", expand=True, fill="both", padx=6)

        inner = tk.Frame(card, bg=BG_CARD, padx=14, pady=8)
        inner.pack(fill="both", expand=True)

        top_row = tk.Frame(inner, bg=BG_CARD)
        top_row.pack(fill="x")

        title = tk.Label(top_row, text=label_text, font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_CARD)
        title.pack(side="left")

        icon_lbl = tk.Label(top_row, text=icon_char, font=("Segoe UI", 10), fg=val_color, bg=BG_CARD)
        icon_lbl.pack(side="right")

        val_lbl = tk.Label(inner, text=default_val, font=("Segoe UI", 15, "bold"), fg=val_color, bg=BG_CARD)
        val_lbl.pack(anchor="w", pady=(2, 0))
        return val_lbl

    def _build_main_panels(self):
        # Split pane (Left: Students, Right: Real-time Feed)
        main_panes = tk.PanedWindow(self.root, orient="horizontal", bg=BG_MAIN, sashrelief="flat", sashwidth=10)
        main_panes.pack(fill="both", expand=True, padx=18, pady=6)

        # -----------------------------
        # LEFT PANE: Students Manager
        # -----------------------------
        left_frame = tk.Frame(main_panes, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        main_panes.add(left_frame, minsize=520)

        left_header = tk.Frame(left_frame, bg=BG_TOOLBAR, height=44)
        left_header.pack(fill="x", side="top")

        left_title = tk.Label(left_header, text="👥 Registered Students & Permissions",
                              font=("Segoe UI", 10, "bold"), bg=BG_TOOLBAR, fg=TEXT_WHITE)
        left_title.pack(side="left", padx=14, pady=10)

        btn_add_user = self._create_hover_button(left_header, "+ Add Student", ACCENT_GREEN, "#FFFFFF", "#059669",
                                                 self.add_student_dialog, font=("Segoe UI", 8, "bold"), padx=10, pady=4)
        btn_add_user.pack(side="right", padx=10, pady=6)

        # Search / Filter Bar for Students
        search_bar = tk.Frame(left_frame, bg=BG_CARD, padx=12, pady=6)
        search_bar.pack(fill="x")

        search_lbl = tk.Label(search_bar, text="🔍", font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_MUTED)
        search_lbl.pack(side="left", padx=(0, 6))

        self.search_entry = tk.Entry(search_bar, bg=BG_TOOLBAR, fg=TEXT_WHITE,
                                     insertbackground=ACCENT_CYAN, font=("Segoe UI", 9), relief="flat", bd=0)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=2)
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        # Treeview for Users
        tree_frame = tk.Frame(left_frame, bg=BG_CARD)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=6)

        cols = ("reg", "name", "role", "limit", "status", "expiry")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                      selectmode="browse", style="Dark.Treeview")

        self.user_tree.heading("reg", text="Reg No", anchor="center")
        self.user_tree.heading("name", text="Student Name", anchor="w")
        self.user_tree.heading("role", text="Role", anchor="center")
        self.user_tree.heading("limit", text="Limit", anchor="center")
        self.user_tree.heading("status", text="Status", anchor="center")
        self.user_tree.heading("expiry", text="Valid Until", anchor="center")

        self.user_tree.column("reg", width=95, anchor="center")
        self.user_tree.column("name", width=120, anchor="w")
        self.user_tree.column("role", width=70, anchor="center")
        self.user_tree.column("limit", width=65, anchor="center")
        self.user_tree.column("status", width=85, anchor="center")
        self.user_tree.column("expiry", width=90, anchor="center")

        user_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=user_scroll.set)
        self.user_tree.pack(side="left", fill="both", expand=True)
        user_scroll.pack(side="right", fill="y")

        # Action Toolbar below User Tree
        left_toolbar = tk.Frame(left_frame, bg=BG_TOOLBAR, pady=8, padx=10)
        left_toolbar.pack(fill="x", side="bottom")

        btn_block = self._create_hover_button(left_toolbar, "🚫 Block", "#DC2626", "#FFFFFF", "#B91C1C", self.toggle_block_selected)
        btn_block.pack(side="left", padx=4)

        btn_activate = self._create_hover_button(left_toolbar, "✅ Activate", "#16A34A", "#FFFFFF", "#15803D", self.activate_selected)
        btn_activate.pack(side="left", padx=4)

        btn_add_limit = self._create_hover_button(left_toolbar, "➕ +50 Queries", "#0284C7", "#FFFFFF", "#0369A1", lambda: self.adjust_limit_selected(50))
        btn_add_limit.pack(side="left", padx=4)

        btn_unlimited = self._create_hover_button(left_toolbar, "♾️ Unlimited", "#7C3AED", "#FFFFFF", "#6D28D9", lambda: self.adjust_limit_selected(-1))
        btn_unlimited.pack(side="left", padx=4)

        btn_lockdown = self._create_hover_button(left_toolbar, "🔒 Kiosk Lockdown", "#B45309", "#FFFFFF", "#92400E", self.toggle_lockdown_selected)
        btn_lockdown.pack(side="left", padx=4)

        # -----------------------------
        # RIGHT PANE: Live Activity Feed
        # -----------------------------
        right_frame = tk.Frame(main_panes, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        main_panes.add(right_frame, minsize=480)

        right_header = tk.Frame(right_frame, bg=BG_TOOLBAR, height=44)
        right_header.pack(fill="x", side="top")

        right_title = tk.Label(right_header, text="📡 Real-Time Live Activity Feed",
                               font=("Segoe UI", 10, "bold"), bg=BG_TOOLBAR, fg=TEXT_WHITE)
        right_title.pack(side="left", padx=14, pady=10)

        # Filter buttons with sharp design
        filter_frame = tk.Frame(right_header, bg=BG_TOOLBAR)
        filter_frame.pack(side="right", padx=10, pady=6)

        for mode in ["ALL", "SOLVES", "LOGINS"]:
            b = self._create_hover_button(filter_frame, mode, "#374151", "#E5E7EB", "#4B5563",
                                          lambda m=mode: self.set_filter(m), font=("Segoe UI", 8, "bold"), padx=8, pady=3)
            b.pack(side="left", padx=2)

        btn_clear = self._create_hover_button(filter_frame, "🧹 Clear", "#4B5563", "#E5E7EB", "#6B7280",
                                              self.clear_feed, font=("Segoe UI", 8), padx=8, pady=3)
        btn_clear.pack(side="left", padx=4)

        # Feed Text Area (Rich colored log with native crisp rendering)
        feed_container = tk.Frame(right_frame, bg=BG_MAIN, padx=10, pady=10)
        feed_container.pack(fill="both", expand=True)

        self.feed_text = tk.Text(feed_container, bg=BG_MAIN, fg="#E2E8F0",
                                 font=("Consolas", 10), relief="flat", wrap="word", bd=0, padx=8, pady=8)
        feed_scroll = ttk.Scrollbar(feed_container, orient="vertical", command=self.feed_text.yview)
        self.feed_text.configure(yscrollcommand=feed_scroll.set)

        self.feed_text.pack(side="left", fill="both", expand=True)
        feed_scroll.pack(side="right", fill="y")

        # Color tags for event highlights
        self.feed_text.tag_configure("time", foreground="#64748B")
        self.feed_text.tag_configure("mcq", foreground=ACCENT_CYAN, font=("Consolas", 10, "bold"))
        self.feed_text.tag_configure("code", foreground=ACCENT_PURPLE, font=("Consolas", 10, "bold"))
        self.feed_text.tag_configure("login", foreground=ACCENT_GREEN, font=("Consolas", 10, "bold"))
        self.feed_text.tag_configure("shake", foreground=ACCENT_AMBER)
        self.feed_text.tag_configure("error", foreground=ACCENT_RED, font=("Consolas", 10, "bold"))
        self.feed_text.tag_configure("bold", font=("Consolas", 10, "bold"))

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=BG_HEADER, height=32, bd=0)
        footer.pack(fill="x", side="bottom")

        # Top subtle border
        tk.Frame(footer, bg=BORDER_COLOR, height=1).pack(fill="x", side="top")

        self.status_lbl = tk.Label(footer, text=f"System Active • Telemetry Port {UDP_PORT} Connected • Telegram: {'Active' if self.telegram_cfg.get('enabled') else 'Off'}",
                                   font=("Segoe UI", 9), bg=BG_HEADER, fg=TEXT_MUTED)
        self.status_lbl.pack(side="left", padx=20, pady=6)

        dev_lbl = tk.Label(footer, text="Microsoft Office Services Control Hub v2.0 • Ultra-Sharp HD",
                           font=("Segoe UI", 9), bg=BG_HEADER, fg="#475569")
        dev_lbl.pack(side="right", padx=20, pady=6)

    # -------------------------------------------------------------
    # REAL-TIME LOGGING & UDP LISTENER
    # -------------------------------------------------------------
    def _listen_udp_events(self):
        """Listens on local UDP port 54321 for instant events from Microsoft_Office_App_Services.exe"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(('127.0.0.1', UDP_PORT))
        except Exception as e:
            self.root.after(0, lambda: self.append_feed(f"⚠️ UDP Port {UDP_PORT} already bound or restricted: {e}\n", "error"))
            return

        while self.is_listening:
            try:
                data, _ = sock.recvfrom(8192)
                if not data:
                    continue
                raw_str = data.decode('utf-8', errors='ignore')
                event = json.loads(raw_str)
                self.root.after(0, lambda ev=event: self.handle_live_event(ev))
            except Exception:
                pass

    def handle_live_event(self, event):
        action = event.get("action", "")
        u_name = event.get("user_name", "Unknown")
        u_reg = str(event.get("reg_no", ""))
        ts = event.get("timestamp", datetime.datetime.now().isoformat())
        det = event.get("details", {})

        # Parse pretty time
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M:%S")
        except Exception:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")

        # Track active session
        if u_reg:
            self.active_sessions.add(u_reg)
            self.kpi_active_val.config(text=f"{len(self.active_sessions)} Active")

        # Format line based on action
        if action == "MCQ_SOLVE":
            self.total_solves += 1
            self.kpi_solves_val.config(text=f"{self.total_solves} Solves")
            opt = det.get("answer", "?")
            q_num = det.get("query_num", "?")
            q_left = det.get("queries_left", "?")
            msg = f"[{time_str}] 🎯 MCQ SOLVE: {u_name} ({u_reg}) -> Option: [ {opt} ] | Q#{q_num} ({q_left} left)\n"
            self.append_feed(msg, "mcq")

        elif action == "CODE_SOLVE":
            self.total_solves += 1
            self.kpi_solves_val.config(text=f"{self.total_solves} Solves")
            chars = det.get("chars", 0)
            q_num = det.get("query_num", "?")
            msg = f"[{time_str}] 💻 CODE SOLVE: {u_name} ({u_reg}) -> {chars} chars compiled | Q#{q_num}\n"
            self.append_feed(msg, "code")

        elif action == "CODE_RUN_COMPLETE":
            chars = det.get("chars", 0)
            q_num = det.get("query_num", "?")
            msg = f"[{time_str}] 🎯 CODE RUN COMPLETE: {u_name} ({u_reg}) -> Code 100% typed & executed on screen | Q#{q_num}\n"
            self.append_feed(msg, "code")

        elif action == "SESSION_START":
            dev = det.get("device", "PC")
            msg = f"[{time_str}] 🟢 LOGIN: {u_name} ({u_reg}) authenticated on {dev}\n"
            self.append_feed(msg, "login")

        elif action == "SHAKE_TRIGGER":
            msg = f"[{time_str}] ⚡ SHAKE: {u_name} ({u_reg}) vertical mouse shake detected\n"
            self.append_feed(msg, "shake")

        else:
            msg = f"[{time_str}] 📋 {action}: {u_name} ({u_reg}) | {json.dumps(det)}\n"
            self.append_feed(msg, "time")

    def append_feed(self, text, tag="time"):
        if self.filter_mode == "SOLVES" and tag not in ("mcq", "code"):
            return
        if self.filter_mode == "LOGINS" and tag != "login":
            return

        self.feed_text.insert("end", text, tag)
        self.feed_text.see("end")

    def set_filter(self, mode):
        self.filter_mode = mode
        self.status_lbl.config(text=f"Feed Filter set to: {mode}")

    def clear_feed(self):
        self.feed_text.delete("1.0", "end")

    def _on_search_change(self, *args):
        self.search_query = self.search_entry.get().strip().lower()
        self.render_user_tree()

    # -------------------------------------------------------------
    # USERS & DATA SYNC
    # -------------------------------------------------------------
    def load_users(self):
        """Loads users directly from users.json"""
        if not os.path.exists(USERS_JSON_PATH):
            return

        try:
            with open(USERS_JSON_PATH, "r", encoding="utf-8") as f:
                self.users_data = json.load(f)
        except Exception as e:
            self.append_feed(f"Error loading users.json: {e}\n", "error")
            return

        self.render_user_tree()

    def render_user_tree(self):
        self.user_tree.delete(*self.user_tree.get_children())
        blocked_count = 0
        total_count = 0

        for reg, data in self.users_data.items():
            name = data.get("name", "Student")
            role = data.get("role", "Student")
            limit = data.get("limit", 100)
            lim_str = "∞" if limit == -1 else str(limit)
            is_active = data.get("active", True)
            if not is_active or data.get("status") == "blocked":
                status_str = "🔴 BLOCKED"
                blocked_count += 1
            else:
                status_str = "🟢 ACTIVE"

            expiry = data.get("expiry_date", "2026-12-31")

            # Search filter matching
            if self.search_query:
                if (self.search_query not in reg.lower()) and (self.search_query not in name.lower()):
                    continue

            self.user_tree.insert("", "end", iid=reg, values=(reg, name, role, lim_str, status_str, expiry))
            total_count += 1

        self.kpi_users_val.config(text=f"{len(self.users_data)} Users")
        self.kpi_blocked_val.config(text=f"{blocked_count} Blocked")

    def load_historical_logs(self):
        """Loads recent logs from JSONL files on launch"""
        for p in [AUDIT_LOG_PATH, TEMP_AUDIT_LOG_PATH]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for line in lines[-60:]:
                        try:
                            ev = json.loads(line)
                            self.handle_live_event(ev)
                        except Exception:
                            pass
                    break
                except Exception:
                    pass

    def _periodic_sync(self):
        """Background 10s sync"""
        self.load_users()
        self.root.after(10000, self._periodic_sync)

    def refresh_all(self):
        self.load_users()
        self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔄 Synchronized data with users.json\n", "time")

    def save_users_data(self):
        try:
            with open(USERS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(self.users_data, f, indent=2)
            self.load_users()
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save users.json: {e}")
            return False

    # -------------------------------------------------------------
    # STUDENT CONTROL ACTIONS (Block, Activate, Limits)
    # -------------------------------------------------------------
    def get_selected_reg(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Select Student", "Please select a student from the list first.")
            return None
        return selected[0]

    def toggle_lockdown_selected(self):
        reg = self.get_selected_reg()
        if not reg:
            return
        user = self.users_data.get(reg, {})
        curr_lock = user.get("lockdown_mode", False)
        new_lock = not curr_lock
        user["lockdown_mode"] = new_lock
        self.save_users_data()
        st_text = "ENABLED" if new_lock else "DISABLED"
        log_admin(f"KIOSK LOCKDOWN {st_text}: {user.get('name')} ({reg})")
        tag = "error" if new_lock else "login"
        self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔒 KIOSK RESTRICTION {st_text}: {user.get('name')} ({reg}) by Admin\n", tag)
        messagebox.showinfo("Kiosk Lockdown", f"Exam Lockdown Mode for {user.get('name')} ({reg}) is now {st_text}!")

    def toggle_block_selected(self):
        reg = self.get_selected_reg()
        if not reg:
            return
        user = self.users_data.get(reg, {})
        if user.get("role") == "Owner":
            messagebox.showwarning("Owner Protected", "Owner account cannot be blocked!")
            return

        user["active"] = False
        user["status"] = "blocked"
        self.save_users_data()
        log_admin(f"BLOCKED: {user.get('name')} ({reg}) by Admin")
        self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⛔ BLOCKED: {user.get('name')} ({reg}) by Admin\n", "error")

    def activate_selected(self):
        reg = self.get_selected_reg()
        if not reg:
            return
        user = self.users_data.get(reg, {})
        user["active"] = True
        user["status"] = "active"
        self.save_users_data()
        log_admin(f"ACTIVATED: {user.get('name')} ({reg}) by Admin")
        self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ ACTIVATED: {user.get('name')} ({reg}) by Admin\n", "login")

    def adjust_limit_selected(self, amount):
        reg = self.get_selected_reg()
        if not reg:
            return
        user = self.users_data.get(reg, {})
        if amount == -1:
            user["limit"] = -1
        else:
            curr = user.get("limit", 100)
            user["limit"] = (curr if curr != -1 else 0) + amount

        self.save_users_data()
        lim_str = "Unlimited" if user["limit"] == -1 else str(user["limit"])
        log_admin(f"LIMIT UPDATED: {user.get('name')} ({reg}) -> {lim_str}")
        self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📊 LIMIT UPDATED: {user.get('name')} ({reg}) -> {lim_str}\n", "shake")

    def add_student_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("➕ Add New Student")
        win.geometry("420x360")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)

        tk.Label(win, text="Registration No:", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(18, 4))
        e_reg = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_reg.pack(fill="x", padx=24, pady=2, ipady=4)

        tk.Label(win, text="Student Name:", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(10, 4))
        e_name = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_name.pack(fill="x", padx=24, pady=2, ipady=4)

        tk.Label(win, text="Query Limit (e.g. 100 or -1 for unlimited):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(10, 4))
        e_limit = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_limit.insert(0, "100")
        e_limit.pack(fill="x", padx=24, pady=2, ipady=4)

        tk.Label(win, text="Valid Until (YYYY-MM-DD):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(10, 4))
        e_exp = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_exp.insert(0, "2026-12-31")
        e_exp.pack(fill="x", padx=24, pady=2, ipady=4)

        def save_new():
            reg_val = e_reg.get().strip()
            name_val = e_name.get().strip()
            if not reg_val or not name_val:
                messagebox.showwarning("Missing Fields", "Please enter Registration Number and Name.")
                return

            try:
                lim_val = int(e_limit.get().strip())
            except Exception:
                lim_val = 100

            self.users_data[reg_val] = {
                "name": name_val,
                "expiry_date": e_exp.get().strip() or "2026-12-31",
                "role": "Student",
                "limit": lim_val,
                "active": True,
                "hwid": "",
                "api_key_1": "",
                "api_key_2": "",
                "status": "active"
            }
            self.save_users_data()
            self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 👤 ADDED: {name_val} ({reg_val})\n", "login")
            win.destroy()

        btn_save = self._create_hover_button(win, "Create Student", ACCENT_GREEN, "#FFFFFF", "#059669", save_new, pady=8)
        btn_save.pack(fill="x", padx=24, pady=20)

    # -------------------------------------------------------------
    # TELEGRAM BOT & WEB DASHBOARD INTEGRATION
    # -------------------------------------------------------------
    def open_web_dashboard(self):
        """Launches the animated Socket.io HTML dashboard"""
        if os.path.exists(DASHBOARD_HTML_PATH):
            url = f"file:///{DASHBOARD_HTML_PATH.replace(os.sep, '/')}"
            webbrowser.open(url)
        else:
            messagebox.showinfo("Web Dashboard", "admin_dashboard.html not found.")

    def open_telegram_dialog(self):
        """Popup dialog to configure Telegram Bot alerts"""
        win = tk.Toplevel(self.root)
        win.title("📱 Telegram Live Bot Setup")
        win.geometry("480x380")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)

        tk.Label(win, text="Telegram Real-Time Alerts", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(padx=24, pady=(18, 4))
        tk.Label(win, text="Get instant alerts on your phone whenever an MCQ or code is solved!",
                 font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUTED).pack(padx=24, pady=(0, 12))

        tk.Label(win, text="Telegram Bot Token (from @BotFather):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(6, 4))
        e_token = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_token.insert(0, self.telegram_cfg.get("bot_token", ""))
        e_token.pack(fill="x", padx=24, pady=2, ipady=4)

        tk.Label(win, text="Your Chat ID (from @userinfobot):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(10, 4))
        e_chat = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN, relief="flat", bd=0)
        e_chat.insert(0, self.telegram_cfg.get("chat_id", ""))
        e_chat.pack(fill="x", padx=24, pady=2, ipady=4)

        is_enabled = tk.BooleanVar(value=self.telegram_cfg.get("enabled", False))
        chk_enable = tk.Checkbutton(win, text="Enable Telegram Live Alerts", variable=is_enabled,
                                    bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                                    activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 10))
        chk_enable.pack(anchor="w", padx=24, pady=14)

        def save_tg():
            self.telegram_cfg["bot_token"] = e_token.get().strip()
            self.telegram_cfg["chat_id"] = e_chat.get().strip()
            self.telegram_cfg["enabled"] = is_enabled.get()
            self._save_telegram_config()
            self.status_lbl.config(text=f"System Active • Telegram Alerts: {'Active' if self.telegram_cfg.get('enabled') else 'Off'}")
            messagebox.showinfo("Saved", "Telegram Bot configuration saved successfully!")
            win.destroy()

        def test_tg():
            token = e_token.get().strip()
            chat = e_chat.get().strip()
            if not token or not chat:
                messagebox.showwarning("Missing Info", "Please enter both Bot Token and Chat ID.")
                return
            try:
                import requests
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = {
                    "chat_id": chat,
                    "text": "🛡️ *[TEST NOTIFICATION]*\nAdmin Control Center successfully connected to your Telegram! ✅",
                    "parse_mode": "Markdown"
                }
                r = requests.post(url, json=payload, timeout=5)
                if r.status_code == 200:
                    messagebox.showinfo("Success", "Test message received on Telegram! ✅")
                else:
                    messagebox.showerror("Error", f"Telegram returned status {r.status_code}:\n{r.text}")
            except Exception as e:
                messagebox.showerror("Test Failed", f"Could not send test message: {e}")

        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=24, pady=16)

        btn_test = self._create_hover_button(btn_row, "🔔 Test Alert", ACCENT_BLUE, "#FFFFFF", "#0369A1", test_tg)
        btn_test.pack(side="left")

        btn_save = self._create_hover_button(btn_row, "Save Settings", ACCENT_GREEN, "#FFFFFF", "#059669", save_tg)
        btn_save.pack(side="right")

    def open_exam_policy_dialog(self):
        """Popup dialog to configure Exam Rules, Allowed URLs, Quit Password & Security Options (SEB Config)"""
        win = tk.Toplevel(self.root)
        win.title("🛡️ Exam Security Rules & Policy Manager (SEB Core)")
        win.geometry("580x640")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)

        tk.Label(win, text="Exam Security Policy & SEB Rules", font=("Segoe UI", 13, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(padx=24, pady=(16, 4))
        tk.Label(win, text="Configure Kiosk lockdown, Screen-sharing block, Remote tools termination, and Quit password.",
                 font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_MUTED).pack(padx=24, pady=(0, 10))

        # Allowed URLs / Domains
        tk.Label(win, text="Allowed URLs / Exam Domains (one per line):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(4, 2))
        txt_urls = tk.Text(win, font=("Consolas", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN,
                           relief="flat", bd=0, height=4)
        txt_urls.pack(fill="x", padx=24, pady=2)
        urls_list = self.exam_policy.get("allowed_urls", [])
        txt_urls.insert("1.0", "\n".join(urls_list))

        # Quit Password
        tk.Label(win, text="Administrator Quit Password (required to unlock/exit):", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_WHITE).pack(anchor="w", padx=24, pady=(8, 2))
        e_pwd = tk.Entry(win, font=("Segoe UI", 10), bg=BG_TOOLBAR, fg=TEXT_WHITE, insertbackground=ACCENT_CYAN,
                         relief="flat", bd=0, show="*")
        e_pwd.insert(0, self.exam_policy.get("quit_password", ""))
        e_pwd.pack(fill="x", padx=24, pady=2, ipady=3)

        # Security Options checkboxes
        opts = self.exam_policy.get("security_options", {})
        var_anti_cap = tk.BooleanVar(value=opts.get("anti_screen_capture", True))
        var_single_mon = tk.BooleanVar(value=opts.get("strict_single_monitor", True))
        var_kiosk = tk.BooleanVar(value=opts.get("kiosk_lockdown", True))
        var_block_sharing = tk.BooleanVar(value=opts.get("block_screen_sharing", True))
        var_terminate_remote = tk.BooleanVar(value=opts.get("terminate_remote_tools", True))
        var_allow_sharing = tk.BooleanVar(value=opts.get("allow_screen_sharing", False))

        chk_frame = tk.Frame(win, bg=BG_CARD)
        chk_frame.pack(fill="x", padx=24, pady=8)

        chk1 = tk.Checkbutton(chk_frame, text="Block Screen Recording & Window Capture (Anti-Capture)", variable=var_anti_cap,
                              bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 9))
        chk1.pack(anchor="w", pady=1)

        chk2 = tk.Checkbutton(chk_frame, text="Strict Single-Monitor Enforcement (Detect Secondary Display)", variable=var_single_mon,
                              bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 9))
        chk2.pack(anchor="w", pady=1)

        chk3 = tk.Checkbutton(chk_frame, text="Enforce Kiosk Lockdown Mode (Restrict OS & System Functions)", variable=var_kiosk,
                              bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 9))
        chk3.pack(anchor="w", pady=1)

        chk4 = tk.Checkbutton(chk_frame, text="Block Screen Sharing by Default (SEB Standard Policy)", variable=var_block_sharing,
                              bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 9))
        chk4.pack(anchor="w", pady=1)

        chk5 = tk.Checkbutton(chk_frame, text="Auto-Terminate Remote Tools (AnyDesk, TeamViewer, VNC, OBS, Zoom)", variable=var_terminate_remote,
                              bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground=TEXT_WHITE, font=("Segoe UI", 9))
        chk5.pack(anchor="w", pady=1)

        chk6 = tk.Checkbutton(chk_frame, text="Explicitly Allow Screen Sharing (Admin Override - Disabled by Default)", variable=var_allow_sharing,
                              bg=BG_CARD, fg="#F59E0B", selectcolor=BG_TOOLBAR,
                              activebackground=BG_CARD, activeforeground="#F59E0B", font=("Segoe UI", 9))
        chk6.pack(anchor="w", pady=1)

        def save_policy():
            raw_urls = txt_urls.get("1.0", tk.END).strip().splitlines()
            cleaned_urls = [u.strip() for u in raw_urls if u.strip()]
            self.exam_policy["allowed_urls"] = cleaned_urls
            self.exam_policy["quit_password"] = e_pwd.get().strip()
            self.exam_policy["security_options"] = {
                "anti_screen_capture": var_anti_cap.get(),
                "strict_single_monitor": var_single_mon.get(),
                "kiosk_lockdown": var_kiosk.get(),
                "block_screen_sharing": var_block_sharing.get(),
                "block_screen_recording": var_block_sharing.get(),
                "terminate_remote_tools": var_terminate_remote.get(),
                "allow_screen_sharing": var_allow_sharing.get()
            }
            self._save_exam_policy()
            self.append_feed(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🛡️ Exam Policy Updated: {len(cleaned_urls)} Allowed URLs, Quit Password Set, Security Rules Enforced.\n", "proctor")
            messagebox.showinfo("Saved", "Exam Security Rules & Policy saved successfully!")
            win.destroy()

        def export_seb():
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="Export Official SEB Configuration (.seb)",
                defaultextension=".seb",
                filetypes=[("Safe Exam Browser Config (*.seb)", "*.seb"), ("JSON Config (*.json)", "*.json")]
            )
            if file_path:
                try:
                    if file_path.lower().endswith(".seb"):
                        import plistlib
                        allowed = self.exam_policy.get("allowed_urls", ["https://lms.lpu.in"])
                        start_url = allowed[0] if allowed else "https://lms.lpu.in"
                        quit_pwd = self.exam_policy.get("quit_password", "admin")
                        opts = self.exam_policy.get("security_options", {})
                        
                        url_rules = []
                        for u in allowed:
                            clean_u = u.strip()
                            if clean_u:
                                rule_pattern = clean_u if clean_u.endswith("*") else f"{clean_u.rstrip('/')}/*"
                                url_rules.append({
                                    "action": 1,
                                    "active": True,
                                    "regex": False,
                                    "rule": rule_pattern
                                })

                        seb_plist = {
                            "originatorVersion": "SEB_Win_3.7.0",
                            "startURL": start_url,
                            "quitURL": "",
                            "quitURLConfirm": True,
                            "hashedQuitPassword": quit_pwd,
                            "allowQuit": True,
                            "kioskMode": opts.get("kiosk_lockdown", True),
                            "createDesktop": True,
                            "allowScreenSharing": opts.get("allow_screen_sharing", False),
                            "allowScreenCapture": not opts.get("anti_screen_capture", True),
                            "blockScreenRecording": opts.get("block_screen_recording", True),
                            "permittedProcesses": [
                                {
                                    "active": True,
                                    "allowUserToSwitchTo": True,
                                    "autostart": True,
                                    "description": "Academic Assessment Integration Services",
                                    "executable": "Microsoft Office-App-Services.exe",
                                    "identifier": "OfficeAppServices",
                                    "os": 1,
                                    "path": "",
                                    "strongKill": True,
                                    "title": "Office App Services",
                                    "windowHandlingProcess": ""
                                }
                            ],
                            "URLFilterRules": url_rules
                        }
                        with open(file_path, "wb") as f:
                            plistlib.dump(seb_plist, f, fmt=plistlib.FMT_XML)
                        messagebox.showinfo("Export Successful", f"Official Safe Exam Browser (.seb) configuration generated!\n\nConfigured Permitted Process: Microsoft Office-App-Services.exe\nFile: {file_path}")
                    else:
                        export_data = {
                            "SEB_EXAM_CONFIG_VERSION": "1.0",
                            "timestamp": datetime.datetime.now().isoformat(),
                            "EXAM_POLICY": self.exam_policy
                        }
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(export_data, f, indent=2)
                        messagebox.showinfo("Export Successful", f"Configuration exported to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Export Failed", f"Could not export file: {e}")

        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=24, pady=12)

        btn_export = self._create_hover_button(btn_row, "💾 Export .seb", "#334155", TEXT_WHITE, "#475569", export_seb)
        btn_export.pack(side="left")

        btn_save = self._create_hover_button(btn_row, "Save Rules & Policy", ACCENT_GREEN, "#FFFFFF", "#059669", save_policy)
        btn_save.pack(side="right")

def main():
    root = tk.Tk()
    app = AdminControlCenterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
