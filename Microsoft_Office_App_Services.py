"""
Microsoft Office App Services - AI Exam Assistant v2.0
Disguised as Microsoft Office background service.
"""

import os
import sys
import time
import json
import re
import math
import threading
import queue
import ctypes
import base64
import io
import hashlib
import datetime
import requests
import uuid
from ctypes import wintypes
import tkinter as tk
from PIL import Image, ImageGrab
from pynput import keyboard as kb_module, mouse as mouse_module
from pynput.keyboard import Controller as KbController, Key
from pynput.mouse import Controller as MouseCtrl, Button
try:
    import pynput._util.win32 as uwin32
except Exception:
    uwin32 = None

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

# =====================================================
# PATHS & CONFIG (100% STEALTH - ZERO FILES IN APP FOLDER)
# =====================================================
TEMP_DIR = os.environ.get("TEMP", os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(TEMP_DIR, "ms_office_service.log")
AUTH_DONE_FILE = os.path.join(TEMP_DIR, ".ms_office_auth")

AUTH_RESULT = {
    "success": False,
    "reg_no": "",
    "user_name": "",
    "expiry_date": "",
    "days_left": 0,
    "hwid": ""
}

def log(msg):
    try:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass



# =====================================================
# STEP 2: ZERO-LEVEL ACCESS (NO ADMIN PRIVILEGES REQUIRED)
# =====================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def ensure_single_instance():
    """
    Zero-Level Access Single Instance Lock.
    Runs seamlessly under Standard User, Guest, or Admin accounts with 0 UAC prompts!
    Does NOT require administrator elevation.
    """
    if is_admin():
        log("Running with Administrator privileges.")
    else:
        log("Running in Zero-Admin / Standard User mode (No UAC required).")

    MUTEX_NAME = "MsOfficeAppServices_AI_SingleInstance"
    _k32 = ctypes.windll.kernel32
    _mutex = _k32.CreateMutexW(None, True, MUTEX_NAME)
    if _k32.GetLastError() == 183:
        log("Already running. Exiting duplicate instance.")
        sys.exit(0)
    return _mutex


if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')

# =====================================================
# API CONFIGURATIONS (Loaded from api_config.json with fallback)
# =====================================================
API_CONFIG_FILENAME = "api_config.json"

# Default fallback values (used if api_config.json is missing or incomplete)
GEMINI_API_KEYS = [
    "AQ.Ab8RN6JiV1Rtcc6biyx_jGTmCnmy4K1Uvl5JPibWcJrReOKZrw"
]
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-1.5-pro"
]

GROQ_API_KEYS = ["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"]
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.2-11b-vision-preview", "mixtral-8x7b-32768"]

# Master 8-key pool for load-balancing and unstoppable fallback
MASTER_GROQ_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

OPENAI_API_KEYS = []
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o"]

OPENROUTER_API_KEYS = ["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"]
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS = [
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "openrouter/auto"
]

CEREBRAS_API_KEYS = ["csk-w4m5r664cd6wfnmhfr9mrccn8ymt26xm232vr9mmey2cfjje"]
CEREBRAS_ENDPOINT = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODELS = ["llama-3.3-70b", "llama3.1-8b"]

ZAI_API_KEYS = ["703cf9a14a8642ee9c617caf65e030eb.AIiOekT1Zcyw0LcJ"]
ZAI_ENDPOINTS = [
    "https://api.z.ai/api/paas/v4/chat/completions",
    "https://open.bigmodel.cn/api/paas/v4/chat/completions"
]
ZAI_MODELS = ["glm-4.5-air", "glm-5.3-flash", "glm-4.5", "glm-5"]

def get_config_file_path():
    """Finds api_config.json in the exe directory, script directory, or working folder."""
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), API_CONFIG_FILENAME))
    if '__file__' in globals():
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), API_CONFIG_FILENAME))
    candidates.append(os.path.join(os.getcwd(), API_CONFIG_FILENAME))
    candidates.append(os.path.join(TEMP_DIR, API_CONFIG_FILENAME))
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0] if candidates else API_CONFIG_FILENAME

def _normalize_user_keys(raw_cfg):
    """
    Normalizes user keys from simple, easy-to-understand formats:
    Example 1:
        {"api_key_1": "gsk_...", "api_key_2": "AQ.Ab8...", "api_key_3": "...", "limit": 100}
    Example 2:
        {"gemini_key": "AQ.Ab8...", "groq_key": "gsk_...", "limit": 100}
    Example 3:
        {"api_keys": ["key1", "key2", "key3", "key4", "key5"], "limit": 100}
    Example 4:
        {"GEMINI": {"api_keys": [...]}, "GROQ": {"api_keys": [...]}}
    Supports batched 5-question round-robin rotation across api_key_1 .. api_key_20!
    """
    if not isinstance(raw_cfg, dict):
        return {}
    out = {}
    ordered_keys = []

    # 1. Preserve existing nested provider dicts
    for prov in ["GEMINI", "GROQ", "OPENAI", "OPENROUTER", "CEREBRAS", "ZAI"]:
        if prov in raw_cfg and isinstance(raw_cfg[prov], dict):
            out[prov] = dict(raw_cfg[prov])
            for k in raw_cfg[prov].get("api_keys", []):
                if isinstance(k, str) and k.strip() and k.strip() not in ordered_keys:
                    ordered_keys.append(k.strip())
        elif prov.lower() in raw_cfg and isinstance(raw_cfg[prov.lower()], dict):
            out[prov] = dict(raw_cfg[prov.lower()])
            for k in raw_cfg[prov.lower()].get("api_keys", []):
                if isinstance(k, str) and k.strip() and k.strip() not in ordered_keys:
                    ordered_keys.append(k.strip())

    # 2. Extract numbered keys (api_key_1 .. api_key_20, key_1 .. key_20, etc.)
    direct_keys = []
    for i in range(1, 21):
        for pattern in [f"api_key_{i}", f"key_{i}", f"key{i}", f"apikey_{i}", f"api_key{i}"]:
            if pattern in raw_cfg and isinstance(raw_cfg[pattern], str):
                direct_keys.append((None, raw_cfg[pattern]))
                break

    if "primary_key" in raw_cfg and isinstance(raw_cfg["primary_key"], str):
        direct_keys.append((None, raw_cfg["primary_key"]))
    if "backup_key" in raw_cfg and isinstance(raw_cfg["backup_key"], str):
        direct_keys.append((None, raw_cfg["backup_key"]))
    if "secondary_key" in raw_cfg and isinstance(raw_cfg["secondary_key"], str):
        direct_keys.append((None, raw_cfg["secondary_key"]))

    if "openai_key" in raw_cfg and isinstance(raw_cfg["openai_key"], str):
        direct_keys.append(("OPENAI", raw_cfg["openai_key"]))
    if "gemini_key" in raw_cfg and isinstance(raw_cfg["gemini_key"], str):
        direct_keys.append(("GEMINI", raw_cfg["gemini_key"]))
    if "groq_key" in raw_cfg and isinstance(raw_cfg["groq_key"], str):
        direct_keys.append(("GROQ", raw_cfg["groq_key"]))
    if "openrouter_key" in raw_cfg and isinstance(raw_cfg["openrouter_key"], str):
        direct_keys.append(("OPENROUTER", raw_cfg["openrouter_key"]))
    if "cerebras_key" in raw_cfg and isinstance(raw_cfg["cerebras_key"], str):
        direct_keys.append(("CEREBRAS", raw_cfg["cerebras_key"]))

    if "api_keys" in raw_cfg:
        if isinstance(raw_cfg["api_keys"], list):
            for k in raw_cfg["api_keys"]:
                if isinstance(k, str):
                    direct_keys.append((None, k))
        elif isinstance(raw_cfg["api_keys"], dict):
            for p, v in raw_cfg["api_keys"].items():
                pu = p.upper()
                if isinstance(v, list):
                    out[pu] = {"api_keys": v}
                    for k in v:
                        if isinstance(k, str) and k.strip() and k.strip() not in ordered_keys:
                            ordered_keys.append(k.strip())
                elif isinstance(v, str):
                    out[pu] = {"api_keys": [v]}
                    if v.strip() and v.strip() not in ordered_keys:
                        ordered_keys.append(v.strip())

    for forced_prov, k in direct_keys:
        k = k.strip()
        if not k:
            continue
        if k not in ordered_keys:
            ordered_keys.append(k)
        prov = forced_prov
        if not prov:
            if k.startswith("sk-proj-") or k.startswith("sk-admin-"):
                prov = "OPENAI"
            elif k.startswith("gsk_"):
                prov = "GROQ"
            elif k.startswith("csk-"):
                prov = "CEREBRAS"
            elif k.startswith("sk-or-"):
                prov = "OPENROUTER"
            elif k.startswith("AIza") or k.startswith("AQ."):
                prov = "GEMINI"
            elif "." in k and len(k) > 30:
                prov = "ZAI"
            else:
                prov = "GROQ"
        if prov not in out:
            out[prov] = {"api_keys": []}
        if "api_keys" not in out[prov]:
            out[prov]["api_keys"] = []
        if k not in out[prov]["api_keys"]:
            out[prov]["api_keys"].append(k)

    out["_ORDERED_KEYS"] = ordered_keys
    return out

# =====================================================
# 5-QUESTION BATCHED ROUND-ROBIN KEY ROTATION ENGINE
# =====================================================
KEY_ROTATION_BATCH_SIZE = 5
ACTIVE_ORDERED_KEYS = []

def get_rotating_key_order(key_list, batch_size=KEY_ROTATION_BATCH_SIZE, reg_no=None):
    """
    Batched 5-Question Round Robin Key Rotation:
    - Key 1 handles Questions 1-5 (indices 0..4)
    - Key 2 handles Questions 6-10 (indices 5..9)
    - Key 3 handles Questions 11-15 (indices 10..14)
    - Key 4 handles Questions 16-20 (indices 15..19)
    - Key 5 handles Questions 21-25 (indices 20..24)
    - Loops seamlessly back to Key 1 for Questions 26-30!
    Returns the rotated list with the scheduled primary key at index 0,
    followed by the remaining keys for immediate rate-limit/error failover.
    """
    if not key_list:
        return []
    cleaned = [k for k in key_list if isinstance(k, str) and k.strip()]
    if len(cleaned) <= 1:
        return cleaned

    q_count = get_query_count(reg_no)
    target_idx = (q_count // max(1, batch_size)) % len(cleaned)
    # Primary rotated key comes first, remaining keys act as immediate fallback
    return cleaned[target_idx:] + cleaned[:target_idx]

def get_key_rotation_status(reg_no=None):
    """
    Returns current rotation status dictionary:
    e.g. {'key_index': 1, 'total_keys': 5, 'batch_question': 3, 'batch_size': 5}
    """
    total = len(ACTIVE_ORDERED_KEYS) if ACTIVE_ORDERED_KEYS else 1
    q_count = get_query_count(reg_no)
    key_idx = (q_count // KEY_ROTATION_BATCH_SIZE) % max(1, total)
    batch_q = (q_count % KEY_ROTATION_BATCH_SIZE) + 1
    return {
        "key_index": key_idx + 1,
        "total_keys": total,
        "batch_question": batch_q,
        "batch_size": KEY_ROTATION_BATCH_SIZE,
        "query_count": q_count
    }

def load_api_config(user_reg=None):
    """
    Dynamically loads API keys and models from api_config.json.
    Supports PER-REGISTRATION NUMBER key assignment!
    If user_reg has dedicated API keys in api_config.json (under USER_KEYS)
    or in users.json (under api_keys, api_key_1, api_key_2), only that user's private keys will be used.
    This guarantees that one user's exhausted quota NEVER affects another user!
    """
    global GEMINI_API_KEYS, GEMINI_MODELS
    global GROQ_API_KEYS, GROQ_ENDPOINT, GROQ_MODELS
    global OPENAI_API_KEYS
    global OPENROUTER_API_KEYS, OPENROUTER_ENDPOINT, OPENROUTER_MODELS
    global CEREBRAS_API_KEYS, CEREBRAS_ENDPOINT, CEREBRAS_MODELS
    global ZAI_API_KEYS, ZAI_ENDPOINTS, ZAI_MODELS
    global ACTIVE_ORDERED_KEYS

    # Auto-detect registration from active session if not passed
    if not user_reg and 'AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict) and AUTH_RESULT.get("reg_no"):
        user_reg = str(AUTH_RESULT["reg_no"]).strip()

    config_path = get_config_file_path()
    cfg_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg_data = json.load(f)
        except Exception as e:
            log(f"[CONFIG] Error loading {config_path}: {e}")

    # 1. PRIORITY 1: Online GitHub Gist (Single Source of Truth)
    user_cfg = None
    if user_reg and 'get_allowed_users' in globals():
        try:
            all_users = get_allowed_users()
            if user_reg in all_users:
                user_cfg = _normalize_user_keys(all_users[user_reg])
                if user_cfg:
                    log(f"[CONFIG] Live Gist: Active dedicated keys loaded from GitHub Gist for Reg: {user_reg}")
        except Exception as e:
            log(f"[CONFIG] Error loading user keys from Gist: {e}")

    # 2. PRIORITY 2: Local api_config.json fallback
    if not user_cfg and user_reg and "USER_KEYS" in cfg_data and user_reg in cfg_data["USER_KEYS"]:
        user_cfg = _normalize_user_keys(cfg_data["USER_KEYS"][user_reg])
        log(f"[CONFIG] Fallback: Active dedicated keys from api_config.json for Reg: {user_reg}")

    # 3. PRIORITY 3: Embedded Code Database (Guaranteed offline / standalone)
    if user_reg and 'ALLOWED_REGISTRATIONS' in globals() and user_reg in ALLOWED_REGISTRATIONS:
        code_cfg = _normalize_user_keys(ALLOWED_REGISTRATIONS[user_reg])
        if not user_cfg:
            user_cfg = code_cfg
            log(f"[CONFIG] Embedded: Dedicated keys loaded from compiled code for Reg: {user_reg}")
        else:
            # Merge any embedded keys so student always has their keys available
            for p, pdata in code_cfg.items():
                if p not in user_cfg:
                    user_cfg[p] = pdata
                elif isinstance(pdata, dict) and "api_keys" in pdata:
                    for k in pdata.get("api_keys", []):
                        if k not in user_cfg[p].get("api_keys", []):
                            user_cfg[p]["api_keys"].append(k)

    def _clean_keys(klist):
        if not klist:
            return []
        if isinstance(klist, str):
            klist = [klist]
        cleaned = []
        for k in klist:
            if isinstance(k, str) and k.strip():
                ks = k.strip()
                ku = ks.upper()
                if not (ku.startswith("PASTE_") or ku.startswith("YOUR_") or "SAMPLE" in ku or "DUMMY" in ku):
                    cleaned.append(ks)
        return cleaned

    is_owner = (user_reg == "12303979") or ('AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict) and AUTH_RESULT.get("role") == "Owner")

    # PER-REGISTRATION KEY MANAGEMENT + MASTER FAILSAFE POOL:
    # Student's dedicated keys are given highest priority.
    # However, to guarantee 100% uptime and prevent exam failures, the master pool of active Groq keys
    # is attached as fallback if the student's key is missing, hits rate-limits (429), or expires!
    if not is_owner and user_reg:
        source = {}
        for prov in ["GEMINI", "GROQ", "OPENAI", "OPENROUTER", "CEREBRAS", "ZAI"]:
            if prov in cfg_data and isinstance(cfg_data[prov], dict):
                source[prov] = {
                    "models": cfg_data[prov].get("models", []),
                    "endpoint": cfg_data[prov].get("endpoint", ""),
                    "endpoints": cfg_data[prov].get("endpoints", [])
                }
        if user_cfg:
            for provider, p_data in user_cfg.items():
                pu = provider.upper()
                if pu not in source:
                    source[pu] = {}
                source[pu]["api_keys"] = _clean_keys(p_data.get("api_keys", []))
    else:
        # Owner account: can use base config and owner keys
        source = dict(cfg_data)
        if user_cfg:
            for provider, p_data in user_cfg.items():
                pu = provider.upper()
                if pu in source and isinstance(source[pu], dict):
                    merged = dict(source[pu])
                    merged.update(p_data)
                    source[pu] = merged
                else:
                    source[pu] = p_data

    # Populate globals strictly with cleaned, valid keys
    OPENAI_API_KEYS = _clean_keys(source.get("OPENAI", {}).get("api_keys", []))
    if "OPENAI" in source and source["OPENAI"].get("models"):
        OPENAI_MODELS = source["OPENAI"]["models"]

    GEMINI_API_KEYS = _clean_keys(source.get("GEMINI", {}).get("api_keys", []))
    if "GEMINI" in source and source["GEMINI"].get("models"):
        GEMINI_MODELS = source["GEMINI"]["models"]

    GROQ_API_KEYS = _clean_keys(source.get("GROQ", {}).get("api_keys", []))
    if "GROQ" in source:
        GROQ_ENDPOINT = source["GROQ"].get("endpoint", GROQ_ENDPOINT)
        if source["GROQ"].get("models"):
            GROQ_MODELS = source["GROQ"]["models"]

    # Failsafe fallback: Append master Groq keys so queries NEVER fail even if student keys run out
    for mk in MASTER_GROQ_KEYS:
        if mk not in GROQ_API_KEYS:
            GROQ_API_KEYS.append(mk)

    OPENROUTER_API_KEYS = _clean_keys(source.get("OPENROUTER", {}).get("api_keys", []))
    if "OPENROUTER" in source:
        OPENROUTER_ENDPOINT = source["OPENROUTER"].get("endpoint", OPENROUTER_ENDPOINT)
        if source["OPENROUTER"].get("models"):
            OPENROUTER_MODELS = source["OPENROUTER"]["models"]

    CEREBRAS_API_KEYS = _clean_keys(source.get("CEREBRAS", {}).get("api_keys", []))
    if "CEREBRAS" in source:
        CEREBRAS_ENDPOINT = source["CEREBRAS"].get("endpoint", CEREBRAS_ENDPOINT)
        if source["CEREBRAS"].get("models"):
            CEREBRAS_MODELS = source["CEREBRAS"]["models"]

    ZAI_API_KEYS = _clean_keys(source.get("ZAI", {}).get("api_keys", []))
    if "ZAI" in source:
        if source["ZAI"].get("endpoints"):
            ZAI_ENDPOINTS = source["ZAI"]["endpoints"]
        if source["ZAI"].get("models"):
            ZAI_MODELS = source["ZAI"]["models"]

    # Collect ACTIVE_ORDERED_KEYS for batched round-robin rotation
    ordered = []
    if user_cfg and "_ORDERED_KEYS" in user_cfg:
        ordered = _clean_keys(user_cfg["_ORDERED_KEYS"])
    if not ordered:
        for prov_keys in [OPENAI_API_KEYS, GEMINI_API_KEYS, GROQ_API_KEYS, OPENROUTER_API_KEYS, CEREBRAS_API_KEYS, ZAI_API_KEYS]:
            for k in prov_keys:
                if k not in ordered and k not in MASTER_GROQ_KEYS:
                    ordered.append(k)
    ACTIVE_ORDERED_KEYS = ordered

    return True

# Initial load at startup
load_api_config()


# =====================================================
# SECURE EXAM KIOSK & OS RESTRICTION GUARD
# =====================================================
IS_KIOSK_LOCKED = False

def check_kiosk_lockdown_status(reg_no=None):
    """
    Checks if Admin has enabled Secure Exam Lockdown for this student.
    Restricts access to the operating system, other applications, and unauthorized system switching.
    """
    global IS_KIOSK_LOCKED
    if not reg_no and 'AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict):
        reg_no = AUTH_RESULT.get("reg_no")
    reg_no = str(reg_no or "").strip()
    if not reg_no:
        return False
    try:
        users = get_allowed_users(force_network=False)
        if reg_no in users and users[reg_no].get("lockdown_mode"):
            IS_KIOSK_LOCKED = True
            return True
    except Exception:
        pass
    IS_KIOSK_LOCKED = False
    return False

def is_exam_lockdown_active():
    return IS_KIOSK_LOCKED

# =====================================================
# EXAM INTEGRITY GUARD (ANTI-CAPTURE, MULTI-MONITOR & FOCUS)
# =====================================================
class ExamIntegrityGuard:
    """
REMOTE_SHARING_PROCESSES = {
    "anydesk.exe": "AnyDesk Remote Desktop",
    "teamviewer.exe": "TeamViewer",
    "tv_w32.exe": "TeamViewer Host",
    "ultraviewer.exe": "UltraViewer",
    "rustdesk.exe": "RustDesk Remote Access",
    "vncviewer.exe": "VNC Viewer",
    "winvnc.exe": "VNC Server",
    "tightvnc.exe": "TightVNC",
    "zoom.exe": "Zoom Meetings & Screen Sharing",
    "discord.exe": "Discord Screen Stream",
    "obs64.exe": "OBS Studio (Screen Recording/Sharing)",
    "obs32.exe": "OBS Studio (Screen Recording/Sharing)",
    "sharex.exe": "ShareX Screen Capture",
    "snippingtool.exe": "Snipping Tool",
    "snipaste.exe": "Snipaste Capture",
    "lightshot.exe": "Lightshot Screen Tool",
    "parsec.exe": "Parsec Gaming/Remote Share",
    "chrome_remote_desktop.exe": "Chrome Remote Desktop"
}


    Prevents test-takers from viewing unauthorized materials, getting outside help,
    or recording / sharing the screen.
    """
    @staticmethod
    def enable_anti_screen_capture(hwnd):
        """
        Blocks screen capture, OBS, Discord, TeamViewer, and screen recorders.
        Uses WDA_EXCLUDEFROMCAPTURE (0x00000011).
        """
        try:
            return user32.SetWindowDisplayAffinity(hwnd, 0x00000011) != 0
        except Exception:
            return False

    @staticmethod
    def detect_multiple_monitors():
        """
        Detects if test-taker has connected a second screen / projector
        to view unauthorized materials or get outside help.
        """
        try:
            SM_CMONITORS = 80
            count = user32.GetSystemMetrics(SM_CMONITORS)
            return (count > 1), count
        except Exception:
            return False, 1

    @staticmethod
    def get_foreground_window_title():
        """Returns the title of the currently focused window."""
        try:
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
        except Exception:
            return ""

    @staticmethod
    def scan_and_terminate_remote_tools():
        """
        SEB Core Integrity Principle:
        Detects and terminates unauthorized background remote-access tools
        (AnyDesk, TeamViewer, VNC, OBS, Zoom, Discord) and screen-sharing utilities.
        """
        try:
            policy = get_exam_policy()
            opts = policy.get("security_options", {})
            if not opts.get("terminate_remote_tools", True) and not opts.get("block_screen_sharing", True):
                return []
            
            # If screen sharing is explicitly allowed by Administrator override, don't terminate
            if opts.get("allow_screen_sharing", False):
                return []

            terminated = []
            try:
                import psutil
                for proc in psutil.process_iter(['name']):
                    try:
                        pname = (proc.info.get('name') or '').lower()
                        if pname in REMOTE_SHARING_PROCESSES:
                            desc = REMOTE_SHARING_PROCESSES[pname]
                            proc.kill()
                            terminated.append((pname, desc))
                    except Exception:
                        pass
            except Exception:
                import subprocess
                for pname, desc in REMOTE_SHARING_PROCESSES.items():
                    res = subprocess.run(f"taskkill /F /IM {pname}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if res.returncode == 0:
                        terminated.append((pname, desc))
            
            if terminated:
                names = ", ".join([f"{n} ({d})" for n, d in terminated])
                log(f"[SEB INTEGRITY] Blocked & Terminated remote sharing process: {names}")
                try:
                    import activity_logger
                    activity_logger.log_proctor_alert(f"SEB Rule Violation: Unauthorized screen-sharing / remote tool terminated: {names}")
                except Exception:
                    pass
            return terminated
        except Exception as e:
            log(f"Error in remote tool scanner: {e}")
            return []

    @staticmethod
    def verify_window_policy():
        """Checks multi-monitor, remote tools, and foreground window against exam security policy."""
        try:
            policy = get_exam_policy()
            opts = policy.get("security_options", {})
            
            # 1. Multi-monitor check
            if opts.get("strict_single_monitor", True):
                has_multi, count = ExamIntegrityGuard.detect_multiple_monitors()
                if has_multi:
                    try:
                        import activity_logger
                        activity_logger.log_proctor_alert(f"Multiple display violation detected: {count} monitors connected!")
                    except Exception:
                        pass
            
            # 2. Window / URL verification
            allowed = policy.get("allowed_urls", [])
            if allowed:
                title = ExamIntegrityGuard.get_foreground_window_title()
                if title:
                    blocked_apps = ["Discord", "Telegram", "WhatsApp", "Cheat Engine", "TeamViewer", "AnyDesk", "OBS"]
                    for app in blocked_apps:
                        if app.lower() in title.lower():
                            try:
                                import activity_logger
                                activity_logger.log_proctor_alert(f"Unauthorized application focused: '{title}'")
                            except Exception:
                                pass
                            break
            
            # 3. Screen sharing & remote tools termination (SEB Core Rule)
            ExamIntegrityGuard.scan_and_terminate_remote_tools()
        except Exception:
            pass

def get_exam_policy():
    """Reads EXAM_POLICY from admin_config.json if present."""
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "admin_config.json"))
    if '__file__' in globals():
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_config.json"))
    candidates.append(os.path.join(os.getcwd(), "admin_config.json"))
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f).get("EXAM_POLICY", {})
            except Exception:
                pass
    return {}

def prompt_admin_quit_password(parent=None):
    """
    Prompts for Administrator Quit Password if configured in admin_config.json.
    Returns True if allowed to exit, False if denied.
    """
    try:
        policy = get_exam_policy()
        quit_pwd = policy.get("quit_password", "")
        if not quit_pwd:
            return True
        
        dialog = tk.Toplevel(parent) if parent else tk.Tk()
        dialog.title("🔒 Administrator Quit Password Required")
        dialog.geometry("380x190")
        dialog.configure(bg="#0F172A")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        
        dialog.update_idletasks()
        x = (SCREEN_W - 380) // 2
        y = (SCREEN_H - 190) // 2
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="Exam Session Locked", font=("Segoe UI", 12, "bold"), fg="#EF4444", bg="#0F172A").pack(pady=(15, 4))
        tk.Label(dialog, text="Enter Administrator Quit Password to exit:", font=("Segoe UI", 9), fg="#94A3B8", bg="#0F172A").pack(pady=(0, 10))
        
        pwd_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=pwd_var, show="*", font=("Segoe UI", 11), bg="#1E293B", fg="#F8FAFC", insertbackground="#38BDF8", bd=0, relief="flat", justify="center")
        entry.pack(fill="x", padx=40, ipady=4)
        entry.focus_set()
        
        status_lbl = tk.Label(dialog, text="", font=("Segoe UI", 8), fg="#EF4444", bg="#0F172A")
        status_lbl.pack(pady=4)
        
        result = {"authorized": False}
        
        def try_unlock(*_):
            if pwd_var.get() == quit_pwd:
                result["authorized"] = True
                dialog.destroy()
            else:
                status_lbl.config(text="❌ Invalid Administrator Quit Password")
                try:
                    import activity_logger
                    activity_logger.log_proctor_alert("Unauthorized quit attempt blocked: Invalid Quit Password entered.")
                except Exception:
                    pass
        
        entry.bind("<Return>", try_unlock)
        btn_frame = tk.Frame(dialog, bg="#0F172A")
        btn_frame.pack(pady=6)
        
        btn_ok = tk.Button(btn_frame, text="Unlock & Exit", font=("Segoe UI", 9, "bold"), bg="#DC2626", fg="#FFFFFF", activebackground="#B91C1C", bd=0, padx=14, pady=4, cursor="hand2", command=try_unlock)
        btn_ok.pack(side="left", padx=5)
        
        btn_cancel = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 9), bg="#334155", fg="#FFFFFF", activebackground="#475569", bd=0, padx=14, pady=4, cursor="hand2", command=dialog.destroy)
        btn_cancel.pack(side="left", padx=5)
        
        if not parent:
            dialog.mainloop()
        else:
            dialog.grab_set()
            dialog.wait_window()
        return result["authorized"]
    except Exception as e:
        log(f"Error checking quit password: {e}")
        return True


# =====================================================
# WIN32 CONSTANTS & SETUP
# =====================================================
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
IDC_CROSS = 32515
IDC_NORMAL = 32512

SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)

# =====================================================
# QUERY COUNTER & PER-REGISTRATION USAGE LIMITS (Default 100)
# =====================================================
DEFAULT_QUERY_LIMIT = 100
USAGE_FILE = os.path.join(TEMP_DIR, ".ms_query_usage.json")

def _load_all_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_all_usage(usage_dict):
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(usage_dict, f, indent=2)
    except Exception:
        pass

def get_user_query_limit(reg_no=None):
    """
    Returns the configured query limit for the given registration number.
    Checks api_config.json ('USER_LIMITS'), then users.json/Gist ('query_limit' or 'limit').
    Default is 100. Returns -1 for unlimited.
    """
    if not reg_no and 'AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict):
        reg_no = AUTH_RESULT.get("reg_no")
    reg_no = str(reg_no or "").strip()

    # Owner account is always unlimited (-1)
    if reg_no == "12303979" or ('AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict) and AUTH_RESULT.get("role") == "Owner"):
        return -1

    # 1. PRIORITY 1: Online GitHub Gist (Single Source of Truth)
    if 'get_allowed_users' in globals() and reg_no:
        try:
            all_users = get_allowed_users()
            if reg_no in all_users:
                uinfo = all_users[reg_no]
                if uinfo.get("role") == "Owner":
                    return -1
                for lf in ["limit", "query_limit", "tokens", "token_limit"]:
                    if lf in uinfo and uinfo[lf] is not None:
                        return int(uinfo[lf])
        except Exception:
            pass

    # 2. PRIORITY 2: Local api_config.json fallback
    cfg_path = get_config_file_path()
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                if "USER_KEYS" in cdata and reg_no in cdata["USER_KEYS"] and isinstance(cdata["USER_KEYS"][reg_no], dict):
                    uk = cdata["USER_KEYS"][reg_no]
                    for lf in ["limit", "query_limit", "tokens", "token_limit"]:
                        if lf in uk and uk[lf] is not None:
                            return int(uk[lf])
                if "USER_LIMITS" in cdata and reg_no in cdata["USER_LIMITS"]:
                    return int(cdata["USER_LIMITS"][reg_no])
                if "DEFAULT_QUERY_LIMIT" in cdata:
                    return int(cdata["DEFAULT_QUERY_LIMIT"])
        except Exception:
            pass

    return DEFAULT_QUERY_LIMIT

def get_query_count(reg_no=None):
    """Returns number of queries already used by this registration number."""
    if not reg_no and 'AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict):
        reg_no = AUTH_RESULT.get("reg_no")
    reg_no = str(reg_no or "default").strip()
    usage = _load_all_usage()
    return usage.get(reg_no, 0)

def increment_query(reg_no=None):
    """Increments the query count persistently for the active user."""
    if not reg_no and 'AUTH_RESULT' in globals() and isinstance(AUTH_RESULT, dict):
        reg_no = AUTH_RESULT.get("reg_no")
    reg_no = str(reg_no or "default").strip()
    usage = _load_all_usage()
    current = usage.get(reg_no, 0) + 1
    usage[reg_no] = current
    _save_all_usage(usage)
    return current

def get_queries_left(reg_no=None):
    limit = get_user_query_limit(reg_no)
    if limit == -1:
        return 999999
    used = get_query_count(reg_no)
    return max(0, limit - used)

def can_execute_query(reg_no=None):
    limit = get_user_query_limit(reg_no)
    if limit == -1:
        return True
    used = get_query_count(reg_no)
    return used < limit

def get_queries_display_str(reg_no=None):
    """Formats string for Shift+F overlay: e.g. '87 left (13/100)' or 'Unlimited ∞'"""
    limit = get_user_query_limit(reg_no)
    if limit == -1:
        return "Unlimited ∞"
    used = get_query_count(reg_no)
    left = max(0, limit - used)
    if left == 0:
        return f"0 / {limit} (Limit Reached)"
    return f"{left} left ({used}/{limit})"

def queries_remaining():
    return get_queries_left()


# =====================================================
# ALLOWED REGISTRATIONS & 7-DAY EXPIRY DATABASE
# =====================================================
# Predefined dictionary of allowed users:
# Format: "REGISTRATION_NUMBER": {"name": "User Name", "expiry_date": "YYYY-MM-DD", "role": "Role"}
ALLOWED_REGISTRATIONS = {
    # Primary Owner / Prashant (Offline emergency fallback - Unlimited)
    "12303979": {
        "name": "Bunty Sharma",
        "expiry_date": "2026-12-31",
        "role": "Owner",
        "limit": -1,
        "active": True
    },
    "12301121": {
        "name": "Student 01",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "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",
        "api_key_2": "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"
    },
    "12301122": {
        "name": "Student A",
        "expiry_date": "2026-11-22",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "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",
        "api_key_2": "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"
    },
    "12301123": {
        "name": "Student 03",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6IQiIVZEvSR2ejHYK4izpP58w7iJvk5DqAAq_noEDwwDQ",
        "api_key_2": "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"
    },
    "12301124": {
        "name": "Student 04",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JiV1Rtcc6biyx_jGTmCnmy4K1Uvl5JPibWcJrReOKZrw",
        "api_key_2": "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"
    },
    "12301125": {
        "name": "Student 05",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JfQ-VqdXueecSNj_2xFCnNsQBAP7FU-AnIdsLedcIb5Q",
        "api_key_2": "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"
    },
    "12301126": {
        "name": "Student 06",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6IQiIVZEvSR2ejHYK4izpP58w7iJvk5DqAAq_noEDwwDQ",
        "api_key_2": "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"
    },
    "12301127": {
        "name": "Student 07",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JiV1Rtcc6biyx_jGTmCnmy4K1Uvl5JPibWcJrReOKZrw",
        "api_key_2": "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"
    },
    "12301128": {
        "name": "Student 08",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JfQ-VqdXueecSNj_2xFCnNsQBAP7FU-AnIdsLedcIb5Q",
        "api_key_2": "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"
    },
    "12301129": {
        "name": "Student 09",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6IQiIVZEvSR2ejHYK4izpP58w7iJvk5DqAAq_noEDwwDQ",
        "api_key_2": "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"
    },
    "12301130": {
        "name": "Student 10",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JiV1Rtcc6biyx_jGTmCnmy4K1Uvl5JPibWcJrReOKZrw",
        "api_key_2": "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"
    },
    "12301131": {
        "name": "Student 11",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JfQ-VqdXueecSNj_2xFCnNsQBAP7FU-AnIdsLedcIb5Q",
        "api_key_2": "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"
    },
    "12301132": {
        "name": "Student 12",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6IQiIVZEvSR2ejHYK4izpP58w7iJvk5DqAAq_noEDwwDQ",
        "api_key_2": "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"
    },
    "12301133": {
        "name": "Student 13",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JiV1Rtcc6biyx_jGTmCnmy4K1Uvl5JPibWcJrReOKZrw",
        "api_key_2": "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"
    },
    "12301134": {
        "name": "Student 14",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6JfQ-VqdXueecSNj_2xFCnNsQBAP7FU-AnIdsLedcIb5Q",
        "api_key_2": "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"
    },
    "12301135": {
        "name": "Student 15",
        "expiry_date": "2026-12-31",
        "role": "Student",
        "limit": 100,
        "active": True,
        "hwid": "",
        "api_key_1": "AQ.Ab8RN6IQiIVZEvSR2ejHYK4izpP58w7iJvk5DqAAq_noEDwwDQ",
        "api_key_2": "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"
    }
}

AUTH_RESULT = {
    "success": False,
    "reg_no": "",
    "user_name": "",
    "expiry_date": "",
    "days_left": 0,
    "hwid": ""
}

ONLINE_USERS_URL = "https://gist.githubusercontent.com/Bunty3545/ce59887c21712333b29126d54c104675/raw/gistfile1.txt"

def get_hwid():
    """
    Generates a unique, stable 64-character SHA-256 Device Hardware ID (HWID).
    Combines Windows MachineGuid and Network Node UUID.
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        raw = f"{guid}:{uuid.getnode()}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()
    except Exception:
        raw = f"{uuid.getnode()}:{os.environ.get('COMPUTERNAME', 'SYSTEM')}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

_LAST_GIST_DATA = {}
_LAST_GIST_FETCH_TIME = 0

def get_allowed_users(force_network=False):
    """
    Online GitHub Gist + Local users.json dynamic sync!
    Local changes made by Admin in users.json take immediate effect.
    RAM Cache (15s) makes Shift+F and local checks instant (<1ms)!
    """
    global _LAST_GIST_DATA, _LAST_GIST_FETCH_TIME
    now = time.time()
    if not force_network and _LAST_GIST_DATA and (now - _LAST_GIST_FETCH_TIME < 15):
        return _LAST_GIST_DATA

    # 1. Base hardcoded allowed
    combined = dict(ALLOWED_REGISTRATIONS)

    # 2. PRIORITY 1: Online GitHub Gist (Direct Live Source with anti-cache headers)
    online_success = False
    try:
        url = f"{ONLINE_USERS_URL}?_t={int(now * 1000)}"
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            online_data = resp.json()
            if isinstance(online_data, dict) and online_data:
                combined.update(online_data)
                _LAST_GIST_DATA = dict(combined)
                _LAST_GIST_FETCH_TIME = now
                online_success = True
    except Exception as e:
        log(f"[AUTH] Online Gist sync error, falling back: {e}")

    # If temporary network glitch, use last known good Gist data:
    if not online_success and _LAST_GIST_DATA:
        combined.update(_LAST_GIST_DATA)

    # 3. PRIORITY 2: Local users.json (Admin Control Center & local overrides)
    if getattr(sys, 'frozen', False):
        base_folder = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_folder = os.path.dirname(os.path.abspath(__file__))
    local_users_file = os.path.join(base_folder, "users.json")
    if not os.path.exists(local_users_file):
        local_users_file = os.path.join(os.getcwd(), "users.json")

    if os.path.exists(local_users_file):
        try:
            with open(local_users_file, "r", encoding="utf-8") as f:
                local_data = json.load(f)
                if isinstance(local_data, dict) and local_data:
                    combined.update(local_data)
                    log(f"[AUTH] Synced {len(local_data)} users from local users.json.")
        except Exception as e:
            log(f"[AUTH] Error reading local users.json: {e}")

    _LAST_GIST_DATA = combined
    _LAST_GIST_FETCH_TIME = now
    return combined

def verify_registration(reg_no, hwid=None):
    """
    Verifies Registration Number / Access Token, device HWID, and expiry status.
    Returns: (is_valid, message, user_info)
    """
    reg_no = str(reg_no).strip()
    if not reg_no:
        return False, "Please enter your Registration No / Access Token.", None

    users = get_allowed_users()

    # Match against allowed registrations
    if reg_no not in users:
        return False, "❌ Invalid Registration Number / Access Token.\nAccess Denied.", None

    user_info = users[reg_no]
    name = user_info.get("name", "User")
    expiry_str = user_info.get("expiry_date", "")

    # Real-time remote deactivation check
    if user_info.get("active") is False or user_info.get("status") == "blocked" or user_info.get("enabled") is False:
        return False, "❌ Access has been deactivated by Admin.", user_info

    if user_info.get("limit") == 0 or user_info.get("query_limit") == 0:
        return False, "❌ Query limit reached or disabled by Admin.", user_info

    # Optional HWID lock verification if specified in user record
    registered_hwid = user_info.get("hwid")
    if registered_hwid and hwid:
        if str(registered_hwid).strip().lower() != str(hwid).strip().lower():
            return False, "❌ Device mismatch! This token is locked to another HWID.", user_info

    if not expiry_str:
        return False, "❌ Expiration date not set for this account.", None

    try:
        expiry_date = datetime.date.fromisoformat(expiry_str)
        today = datetime.date.today()
        if today > expiry_date:
            return False, f"❌ Access Expired on {expiry_str}!\nPlease contact Admin to renew access.", user_info

        days_left = (expiry_date - today).days
        return True, f"✅ Verified! Welcome, {name}.\nAccess Valid: {days_left} day(s) remaining (until {expiry_str}).", user_info
    except Exception as e:
        log(f"Date check error: {e}")
        return False, "❌ Error verifying expiration date.", None


def show_auth_popup():
    """
    Uni One - Device Verification UI
    Displays the Device Hardware ID (HWID), Registration No / Access Token input,
    and actions to 'Verify Launch' or 'Copy HWID'.
    Clean, professional Dim White (soft slate-silver) theme matching official system dialogs.
    """
    current_hwid = get_hwid()

    root = tk.Tk()
    root.title("Uni One - Device Verification")
    root.wm_attributes("-topmost", True)
    root.config(bg="#F8FAFC")
    root.resizable(False, False)

    w, h = 490, 280
    x = (SCREEN_W - w) // 2
    y = (SCREEN_H - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    cf = tk.Frame(root, bg="#F8FAFC", padx=22, pady=16)
    cf.pack(fill="both", expand=True)

    # 1. HWID Label
    tk.Label(cf, text="Your Device Hardware ID (HWID):", bg="#F8FAFC",
             fg="#1E293B", font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x", pady=(0, 4))

    # HWID Display Entry (Readonly)
    hwid_frame = tk.Frame(cf, bg="#EEF2F6", highlightthickness=1, highlightbackground="#CBD5E1")
    hwid_frame.pack(fill="x", pady=(0, 10))

    hwid_var = tk.StringVar(value=current_hwid)
    hwid_entry = tk.Entry(hwid_frame, textvariable=hwid_var, bg="#EEF2F6", fg="#475569",
                          font=("Segoe UI", 9), bd=0, relief="flat", state="readonly",
                          readonlybackground="#EEF2F6")
    hwid_entry.pack(fill="x", padx=8, pady=6)

    # 2. Registration / Access Token Label
    tk.Label(cf, text="Enter Your Registration No / Access Token:", bg="#F8FAFC",
             fg="#1E293B", font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x", pady=(0, 4))

    # Pre-fill last saved registration number if available
    saved_reg = ""
    if os.path.exists(AUTH_DONE_FILE):
        try:
            with open(AUTH_DONE_FILE, "r", encoding="utf-8") as f:
                saved_content = f.read().strip()
                if saved_content.isdigit():
                    saved_reg = saved_content
                else:
                    data = json.loads(saved_content)
                    saved_reg = data.get("reg_no", "")
        except Exception:
            pass

    reg_frame = tk.Frame(cf, bg="#FFFFFF", highlightthickness=1, highlightbackground="#0284C7")
    reg_frame.pack(fill="x", pady=(0, 8))

    entry_var = tk.StringVar(value=saved_reg)
    entry = tk.Entry(reg_frame, textvariable=entry_var, bg="#FFFFFF", fg="#0F172A",
                     font=("Segoe UI", 11, "bold"), bd=0, insertbackground="#0284C7",
                     relief="flat")
    entry.pack(fill="x", padx=8, pady=6)
    entry.focus()
    if saved_reg:
        entry.select_range(0, tk.END)

    status_lbl = tk.Label(cf, text="", bg="#F8FAFC", fg="#DC2626", font=("Segoe UI", 8), wraplength=450)
    status_lbl.pack(pady=(0, 8))

    def on_close():
        if prompt_admin_quit_password(root):
            try:
                root.destroy()
            except Exception:
                pass
            os._exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.bind("<Alt-Shift-KeyPress-T>", lambda e: on_close())
    root.bind("<Alt-Shift-KeyPress-t>", lambda e: on_close())
    root.bind("<Alt-Shift-KeyPress-X>", lambda e: on_close())
    root.bind("<Alt-Shift-KeyPress-x>", lambda e: on_close())
    root.bind("<Escape>", lambda e: on_close())

    def copy_hwid():
        win_set_clipboard(current_hwid)
        status_lbl.config(text="✅ HWID copied to clipboard!", fg="#0284C7")

    def submit(*_):
        val = entry_var.get().strip()
        status_lbl.config(text="Verifying device HWID & registration...", fg="#0284C7")
        root.update_idletasks()
        ok, msg, info = verify_registration(val, hwid=current_hwid)
        if ok:
            name = info.get("name", "User")
            exp = info.get("expiry_date", "")
            today = datetime.date.today()
            days = (datetime.date.fromisoformat(exp) - today).days if exp else 0

            AUTH_RESULT["success"] = True
            AUTH_RESULT["reg_no"] = val
            AUTH_RESULT["user_name"] = name
            AUTH_RESULT["expiry_date"] = exp
            AUTH_RESULT["days_left"] = days
            AUTH_RESULT["hwid"] = current_hwid

            # Load dedicated API keys specifically for this registration number
            load_api_config(user_reg=val)

            status_lbl.config(text=msg, fg="#16A34A")
            try:
                with open(AUTH_DONE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"reg_no": val, "name": name, "expiry": exp, "hwid": current_hwid}, f)
            except Exception:
                pass

            # Audit tracking integration
            try:
                from activity_logger import audit_tracker
                audit_tracker.start_session(reg_no=val, user_name=name, is_verified=True, expiry_date=exp, days_left=days)
            except Exception:
                pass

            root.after(1000, root.destroy)
        else:
            status_lbl.config(text=msg, fg="#DC2626")

    # Button Row: Verify Launch & Copy HWID
    btn_row = tk.Frame(cf, bg="#F8FAFC")
    btn_row.pack(fill="x", pady=(2, 0))

    btn_verify = tk.Button(btn_row, text="Verify Launch", bg="#0284C7", fg="#FFFFFF",
                           activebackground="#0369A1", activeforeground="#FFFFFF",
                           font=("Segoe UI", 10, "bold"), relief="flat", bd=0, padx=22, pady=6, cursor="hand2", command=submit)
    btn_verify.pack(side="left", expand=True, padx=(10, 8))

    btn_copy = tk.Button(btn_row, text="Copy HWID", bg="#FFFFFF", fg="#334155",
                         activebackground="#F1F5F9", activeforeground="#0F172A",
                         font=("Segoe UI", 10), relief="flat", bd=0, padx=22, pady=6, cursor="hand2",
                         highlightthickness=1, highlightbackground="#CBD5E1", command=copy_hwid)
    btn_copy.pack(side="right", expand=True, padx=(8, 10))

    entry.bind("<Return>", submit)
    root.bind("<Escape>", lambda e: on_close())

    root.mainloop()
    return AUTH_RESULT["success"]

# =====================================================
# SCREEN CAPTURE
# =====================================================
def capture_screen_b64(region=None, max_width=None, quality=92):
    """
    Ultra-Sharp High-Definition Screen Capture.
    Preserves 100% crystal-clear font text, code tokens, and MCQ options for AI and Telegram.
    Uses high-precision LANCZOS anti-aliasing filter and Quality 92 compression.
    """
    try:
        img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        # Only resize if max_width is specified and image is wider
        if max_width and img.width > max_width:
            target_w = max_width
            target_h = max(1, int(img.height * (target_w / img.width)))
            resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
            img = img.resize((target_w, target_h), resample_filter)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        err_msg = str(e).lower()
        if "screen grab failed" in err_msg or "handle is invalid" in err_msg:
            log(f"[SEB LIFECYCLE] Screen capture paused during desktop transition or lock: {e}")
        else:
            log(f"Screenshot error: {e}")
        return None

# =====================================================
# CURSOR UTILS
# =====================================================
def smooth_move(tx, ty, ms=400):
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    sx, sy = pt.x, pt.y
    tx = max(10, min(SCREEN_W - 10, tx))
    ty = max(10, min(SCREEN_H - 10, ty))
    steps = 25
    for i in range(1, steps + 1):
        t = i / steps
        st = t * t * (3 - 2 * t)
        user32.SetCursorPos(int(sx + (tx - sx) * st), int(sy + (ty - sy) * st))
        time.sleep((ms / 1000.0) / steps)
    user32.SetCursorPos(int(tx), int(ty))

def move_cursor_for_mcq(answer):
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    cx, cy = pt.x, pt.y
    dist = 260
    targets = {
        'A': (cx, cy - dist),           # UP
        'B': (cx + dist, cy),           # RIGHT
        'C': (cx, cy + dist),           # DOWN
        'D': (cx - dist, cy),           # LEFT
        'E': (SCREEN_W // 2, SCREEN_H // 2)
    }
    tx, ty = targets.get(answer.upper(), (cx, cy))
    smooth_move(tx, ty, ms=500)
    direction = {'A': 'UP', 'B': 'RIGHT', 'C': 'DOWN', 'D': 'LEFT', 'E': 'CENTER'}
    log(f"[MCQ] Answer: {answer} -> Cursor moved {direction.get(answer.upper(), '?')}")

def set_crosshair_cursor():
    try:
        h = user32.LoadCursorW(0, IDC_CROSS)
        user32.SetSystemCursor(h, IDC_NORMAL)
    except Exception:
        pass

def restore_cursor():
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)
    except Exception:
        pass

def win_set_clipboard(text):
    try:
        if not text:
            return
        OpenClipboard = user32.OpenClipboard
        EmptyClipboard = user32.EmptyClipboard
        SetClipboardData = user32.SetClipboardData
        CloseClipboard = user32.CloseClipboard
        CF_UNICODETEXT = 13
        GlobalAlloc = kernel32.GlobalAlloc
        GlobalLock = kernel32.GlobalLock
        GlobalUnlock = kernel32.GlobalUnlock
        GMEM_MOVEABLE = 0x0002

        if OpenClipboard(None):
            try:
                EmptyClipboard()
                data = text.encode('utf-16le') + b'\x00\x00'
                h_mem = GlobalAlloc(GMEM_MOVEABLE, len(data))
                if h_mem:
                    p_mem = GlobalLock(h_mem)
                    if p_mem:
                        ctypes.memmove(p_mem, data, len(data))
                        GlobalUnlock(h_mem)
                        SetClipboardData(CF_UNICODETEXT, h_mem)
            finally:
                CloseClipboard()
    except Exception as e:
        log(f"Clipboard error: {e}")

# =====================================================
# AI BACKENDS (OpenAI -> Gemini -> Groq -> OpenRouter -> Cerebras -> Z.AI)
# =====================================================
def _query_openai(prompt, images_b64, system):
    if not OPENAI_API_KEYS:
        return None
    for key in get_rotating_key_order(OPENAI_API_KEYS):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        for model in OPENAI_MODELS:
            try:
                messages = [{"role": "system", "content": system}]
                if images_b64:
                    content = [{"type": "text", "text": "Solve from screenshot(s)."}]
                    for img in images_b64:
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "user", "content": prompt or "Solve."})
                r = requests.post(OPENAI_ENDPOINT,
                                  json={"model": model, "messages": messages, "temperature": 0.2},
                                  headers=headers, timeout=12)
                if r.status_code == 200:
                    text = r.json()["choices"][0]["message"]["content"]
                    log(f"OpenAI OK ({model})")
                    return text
                else:
                    log(f"OpenAI HTTP {r.status_code}: {r.text[:120]}")
            except Exception as e:
                log(f"OpenAI {model}: {e}")
    return None

def _query_gemini(prompt, images_b64, system):
    valid_keys = [k for k in GEMINI_API_KEYS if k and len(k.strip()) >= 20 and not (k.upper().startswith("PASTE_") or k.upper().startswith("YOUR_"))]
    if not valid_keys:
        return None
    if images_b64:
        parts = [{"inlineData": {"mimeType": "image/jpeg", "data": img}} for img in images_b64]
        parts.append({"text": f"{system}\n\nSolve from the screenshot(s) above."})
    else:
        parts = [{"text": f"{system}\n\n{prompt}"}]
    payload = {"contents": [{"parts": parts}]}
    headers = {"Content-Type": "application/json"}
    for key in get_rotating_key_order(valid_keys):
        for model in GEMINI_MODELS:
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                    json=payload, headers=headers, timeout=6)
                if r.status_code == 200:
                    candidates = r.json().get("candidates", [])
                    if candidates:
                        text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])).strip()
                        if text:
                            log(f"Gemini OK ({model})")
                            return text
                else:
                    log(f"Gemini HTTP {r.status_code} ({model}): {r.text[:120]}")
            except Exception as e:
                log(f"Gemini {model}: {e}")
    return None

def _query_groq(prompt, images_b64, system):
    for key in get_rotating_key_order(GROQ_API_KEYS):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        models_to_try = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"] if images_b64 else GROQ_MODELS
        for model in models_to_try:
            try:
                messages = [{"role": "system", "content": system}]
                if images_b64:
                    content = [{"type": "text", "text": "Solve from screenshot(s)."}]
                    for img in images_b64:
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "user", "content": prompt or "Solve."})
                r = requests.post(GROQ_ENDPOINT,
                                  json={"model": model, "messages": messages, "temperature": 0.2},
                                  headers=headers, timeout=8)
                if r.status_code == 200:
                    text = r.json()["choices"][0]["message"]["content"]
                    log(f"Groq OK ({model})")
                    return text
                elif r.status_code == 429:
                    log(f"Groq 429 on key ... switching to next key")
                    break
                else:
                    log(f"Groq HTTP {r.status_code} ({model}): {r.text[:120]}")
            except Exception as e:
                log(f"Groq {model}: {e}")
    return None

def _query_openrouter(prompt, images_b64, system):
    for key in get_rotating_key_order(OPENROUTER_API_KEYS):
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Office Services"
        }
        for model in OPENROUTER_MODELS:
            try:
                messages = [{"role": "system", "content": system}]
                if images_b64:
                    content = [{"type": "text", "text": "Solve from screenshot(s)."}]
                    for img in images_b64:
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                    messages.append({"role": "user", "content": content})
                else:
                    messages.append({"role": "user", "content": prompt or "Solve."})
                r = requests.post(OPENROUTER_ENDPOINT,
                                  json={"model": model, "messages": messages, "temperature": 0.2},
                                  headers=headers, timeout=10)
                if r.status_code == 200:
                    choices = r.json().get("choices", [])
                    if choices:
                        text = choices[0]["message"]["content"]
                        if text:
                            log(f"OpenRouter OK ({model})")
                            return text
            except Exception as e:
                log(f"OpenRouter {model}: {e}")
    return None

def _query_cerebras(prompt, images_b64, system):
    for key in get_rotating_key_order(CEREBRAS_API_KEYS):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        for model in CEREBRAS_MODELS:
            try:
                messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt or "Solve."}]
                r = requests.post(CEREBRAS_ENDPOINT,
                                  json={"model": model, "messages": messages, "temperature": 0.2},
                                  headers=headers, timeout=8)
                if r.status_code == 200:
                    log(f"Cerebras OK ({model})")
                    return r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                log(f"Cerebras {model}: {e}")
    return None

def _query_zai(prompt, images_b64, system):
    for key in get_rotating_key_order(ZAI_API_KEYS):
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        for ep in ZAI_ENDPOINTS:
            for model in ZAI_MODELS:
                try:
                    if images_b64:
                        content = [{"type": "text", "text": "Solve from screenshot(s)."}]
                        for img in images_b64:
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
                        user_msg = content
                    else:
                        user_msg = prompt or "Solve."
                    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_msg}]
                    r = requests.post(ep, json={"model": model, "messages": messages, "temperature": 0.2},
                                      headers=headers, timeout=10)
                    if r.status_code == 200:
                        log(f"Z.AI OK ({model})")
                        return r.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    log(f"Z.AI {model}: {e}")
    return None

def query_ai(prompt=None, images_b64=None, mode="code"):
    load_api_config()
    total_keys = len(OPENAI_API_KEYS) + len(GEMINI_API_KEYS) + len(GROQ_API_KEYS) + len(OPENROUTER_API_KEYS) + len(CEREBRAS_API_KEYS) + len(ZAI_API_KEYS)
    if total_keys == 0:
        log("[API] No dedicated API key found for this Registration Number. Query rejected.")
        return "ERROR_NO_API_KEY"
    if mode == "mcq":
        system = (
            "You are an expert MCQ solver with 100% accuracy.\n"
            "Analyze the question carefully from text or screenshot.\n"
            "Do NOT write explanation or working.\n"
            "Output ONLY on the last line: CORRECT_OPTION: X\n"
            "where X is A, B, C, D, or E."
        )
    else:
        system = (
            "You are an elite competitive programmer solving an online exam.\n"
            "Detect the programming language from the screenshot (C++/Java/Python, default C++).\n"
            "Write ONLY pure executable code. No markdown fences (no ```). No comments. No explanation.\n"
            "CRITICAL COMPILER FORMATTING RULES:\n"
            "1. Write clean, normal compiler code exactly as written in an IDE (VS Code / CLion).\n"
            "2. Every single statement ending with a semicolon ';' MUST immediately go to the next line. NEVER put multiple statements on one line.\n"
            "3. Every '{' MUST be followed by a newline and indented by 4 spaces.\n"
            "4. Every '}' MUST be on its own line.\n"
            "If MCQ, output on last line: CORRECT_OPTION: X"
        )
    # Batched round-robin provider prioritization based on active ordered keys
    backends = [_query_openai, _query_gemini, _query_groq, _query_openrouter, _query_cerebras, _query_zai]
    if ACTIVE_ORDERED_KEYS:
        rotated_all = get_rotating_key_order(ACTIVE_ORDERED_KEYS)
        if rotated_all:
            primary_k = rotated_all[0]
            if primary_k.startswith('sk-proj-') or primary_k.startswith('sk-admin-'):
                pref = _query_openai
            elif primary_k.startswith('AIza') or primary_k.startswith('AQ.'):
                pref = _query_gemini
            elif primary_k.startswith('csk-'):
                pref = _query_cerebras
            elif primary_k.startswith('sk-or-'):
                pref = _query_openrouter
            elif '.' in primary_k and len(primary_k) > 30:
                pref = _query_zai
            else:
                pref = _query_groq
            backends = [pref] + [b for b in backends if b != pref]

    for fn in backends:
        try:
            result = fn(prompt, images_b64, system)
            if result:
                return result
        except Exception as e:
            log(f"Backend error: {e}")
    return None

def format_compiler_code(raw_code):
    if not raw_code:
        return ""
    if "CORRECT OPTION:" in raw_code or "MCQ ANSWER" in raw_code:
        return raw_code
    code = raw_code.replace('\r\n', '\n').replace('\r', '\n')
    lines = []
    for line in code.split('\n'):
        sub_lines = []
        curr = []
        in_str = False
        str_char = None
        paren_depth = 0

        for i, char in enumerate(line):
            curr.append(char)
            if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                if in_str and char == str_char:
                    in_str = False
                elif not in_str:
                    in_str = True
                    str_char = char
            elif not in_str:
                if char in ('(', '[', '{'):
                    paren_depth += 1
                elif char in (')', ']', '}'):
                    paren_depth = max(0, paren_depth - 1)
                elif char == ';' and paren_depth == 0:
                    # Statement terminator outside any parens/for loop
                    rest = line[i+1:].strip()
                    if rest and not rest.startswith('//') and not rest.startswith('/*'):
                        sub_lines.append("".join(curr).strip())
                        curr = []
        if curr:
            sub_lines.append("".join(curr).strip())
        for sl in sub_lines:
            if sl:
                lines.append(sl)

    expanded_lines = []
    for line in lines:
        s = line.strip()
        if '{' in s and not s.startswith('#') and not s.endswith('{'):
            parts = re.split(r'(\{)', s)
            combined = ""
            for p in parts:
                if p == '{':
                    combined += '{\n'
                else:
                    combined += p
            for l in combined.split('\n'):
                if l.strip():
                    expanded_lines.append(l.strip())
        else:
            expanded_lines.append(s)

    formatted = []
    indent_level = 0
    INDENT = "  "  # 2 spaces to eliminate wasted left space
    for line in expanded_lines:
        s = line.strip()
        if not s:
            formatted.append("")
            continue
        if s.startswith('#') or s.startswith('package ') or s.startswith('import '):
            formatted.append(s)
            continue
        if s.startswith('}'):
            indent_level = max(0, indent_level - 1)
        if s in ('public:', 'private:', 'protected:') or s.startswith('case ') or s == 'default:':
            current_indent = max(0, indent_level - 1)
        else:
            current_indent = indent_level
        formatted.append((INDENT * current_indent) + s)
        if s.endswith('{'):
            indent_level += 1
        elif not s.startswith('}') and (s.count('}') > s.count('{')):
            indent_level = max(0, indent_level - (s.count('}') - s.count('{')))

    return "\n".join(formatted).strip()

def sanitize_mcq(raw):
    if not raw:
        return "?"
    text = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL).strip()
    matches = re.findall(
        r'(?:CORRECT[_\s]+OPTION|FINAL[_\s]+ANSWER|ANSWER)\s*[:=]?\s*[*_`\(\[]*([A-E])',
        text, re.IGNORECASE)
    if matches:
        return matches[-1].upper()
    m = re.match(r'^[*_`\(\[]*([A-E])[*_`\)\]\.]?\s*$', text.strip(), re.IGNORECASE)
    if m:
        return m.group(1).upper()
    for line in reversed([l.strip() for l in text.splitlines() if l.strip()]):
        m = re.search(r'\b([A-E])\b', line)
        if m:
            return m.group(1).upper()
    return "?"

def sanitize_code(raw):
    if not raw:
        return ""
    text = re.sub(r'<thought>.*?</thought>', '', raw, flags=re.DOTALL).strip()
    matches = re.findall(r"```[a-zA-Z0-9_-]*\n?(.*?)\n?```", text, re.DOTALL)
    if matches:
        raw_code = "\n\n".join(matches).strip()
    else:
        lines = [l for l in text.split('\n') if not l.strip().startswith('```')]
        raw_code = '\n'.join(lines).strip()
    return format_compiler_code(raw_code)

# =====================================================
# SHAKE DETECTOR (MCQ Method A - vertical shake)
# =====================================================
class ShakeDetector:
    def __init__(self, window_sec=2.0, min_changes=4, threshold=28):
        self.window = window_sec
        self.min_changes = min_changes
        self.threshold = threshold
        self._positions = []
        self._lock = threading.Lock()

    def update(self, x, y):
        now = time.time()
        with self._lock:
            self._positions.append((now, y))
            cutoff = now - self.window
            self._positions = [(t, p) for t, p in self._positions if t >= cutoff]
            if len(self._positions) < 6:
                return False
            changes = 0
            last_dir = 0
            for i in range(1, len(self._positions)):
                dy = self._positions[i][1] - self._positions[i-1][1]
                if abs(dy) >= self.threshold:
                    curr_dir = 1 if dy > 0 else -1
                    if curr_dir != last_dir and last_dir != 0:
                        changes += 1
                    last_dir = curr_dir
            if changes >= self.min_changes:
                self._positions.clear()
                return True
        return False

# =====================================================
# CORNER HOVER DETECTOR (MCQ Method B - 3x bottom-right)
# =====================================================
class CornerHoverDetector:
    def __init__(self, zone=70, window_sec=3.5):
        self.zone = zone
        self.window = window_sec
        self._entries = []
        self._in_zone = False
        self._lock = threading.Lock()

    def update(self, x, y):
        in_corner = (x >= SCREEN_W - self.zone and y >= SCREEN_H - self.zone)
        now = time.time()
        triggered = False
        with self._lock:
            if in_corner and not self._in_zone:
                self._in_zone = True
                self._entries.append(now)
                self._entries = [t for t in self._entries if now - t <= self.window]
                if len(self._entries) >= 3:
                    self._entries.clear()
                    triggered = True
            elif not in_corner:
                self._in_zone = False
        return triggered

# =====================================================
# GHOST TYPER (F11 / Alt+1 / Alt+U)
# =====================================================
def tokenize_code_for_ghost(code_text):
    clean_code = code_text.replace('\r\n', '\n').replace('\r', '\n').strip()
    lines = clean_code.splitlines()
    tokens = []
    for line_idx, line in enumerate(lines):
        # Web code editors (Monaco/Ace/LeetCode/exam portals) automatically
        # insert indentation when Enter is pressed.
        # Stripping leading spaces prevents cascading double-indentation!
        stripped = line.strip()
        if not stripped:
            tokens.append('\n')
            continue
        for ch in stripped:
            tokens.append(ch)
        if line_idx < len(lines) - 1:
            tokens.append('\n')
    return tokens if tokens else list(clean_code)

class GhostTyper:
    def __init__(self, on_complete=None):
        self.kb = KbController()
        self.armed = False         # True when interactive ghost typing is ON
        self.is_loaded = False     # True when tokens are loaded in memory
        self.tokens = []           # List of individual characters
        self.index = 0             # Current position in tokens
        self.on_complete = on_complete
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        threading.Thread(target=self._worker, daemon=True).start()

    @property
    def active(self):
        return self.armed

    @active.setter
    def active(self, val):
        self.armed = bool(val)

    def load(self, code):
        with self._lock:
            self.tokens = tokenize_code_for_ghost(code)
            self.index = 0
            self.is_loaded = bool(self.tokens)
            self.armed = False  # Ready, but NOT active until user presses F11!
            with self._queue.mutex:
                self._queue.queue.clear()
        log(f"Ghost typer loaded: {len(self.tokens)} characters ready. Press F11 to start interactive typing.")

    def start(self):
        with self._lock:
            if not self.tokens:
                return
            if self.index >= len(self.tokens):
                self.index = 0
            self.armed = True
            with self._queue.mutex:
                self._queue.queue.clear()
        log(f"Ghost typer ON: resuming from character {self.index}/{len(self.tokens)}.")

    def stop(self):
        with self._lock:
            self.armed = False
            with self._queue.mutex:
                self._queue.queue.clear()
        log(f"Ghost typer OFF/paused at character {self.index}/{len(self.tokens)}.")

    def clear(self):
        with self._lock:
            self.armed = False
            self.is_loaded = False
            self.tokens = []
            self.index = 0
            with self._queue.mutex:
                self._queue.queue.clear()
        log("Ghost typer buffer cleared.")

    def trigger_next_char(self):
        with self._lock:
            if not self.armed or self.index >= len(self.tokens):
                return

            ch = self.tokens[self.index]
            self.index += 1
            self._queue.put(ch)

            if self.index >= len(self.tokens):
                self.armed = False
                log("Ghost typer: 100% complete! End of code reached.")
                if self.on_complete:
                    try:
                        self.on_complete()
                    except Exception:
                        pass

    def _worker(self):
        while True:
            ch = self._queue.get()
            try:
                self.kb.type(ch)
            except Exception as e:
                log(f"Typing error for '{ch}': {e}")
            if ch == '\n':
                time.sleep(0.04)  # 40ms pause on newline so web editor auto-indent completes
            self._queue.task_done()

    @property
    def is_complete(self):
        return self.index >= len(self.tokens) if self.tokens else False

# =====================================================
# SIDE OVERLAY UI (Shift+F to toggle)
# =====================================================

# =====================================================
# SAFE EXAM BROWSER (SEB) INTEGRATION & COEXISTENCE BRIDGE
# =====================================================
class SEBIntegrationBridge:
    """
    Manages supported coexistence with Safe Exam Browser (SEB)
    when running as an administrator-approved Permitted Application.
    """
    _seb_cached_state = None
    _last_check = 0

    @classmethod
    def is_seb_present(cls):
        """Checks if SafeExamBrowser.exe or SebWindowsService.exe is currently active."""
        now = time.time()
        if cls._seb_cached_state is not None and (now - cls._last_check < 4):
            return cls._seb_cached_state
        cls._last_check = now
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                pname = (proc.info.get('name') or '').lower()
                if pname in ('safeexambrowser.exe', 'sebwindowsservice.exe', 'seb.exe'):
                    if cls._seb_cached_state is not True:
                        log("[SEB INTEGRATION] Safe Exam Browser runtime detected. Operating under Permitted Application parameters.")
                    cls._seb_cached_state = True
                    return True
        except Exception:
            pass
        cls._seb_cached_state = False
        return False

    @classmethod
    def get_status_summary(cls):
        if cls.is_seb_present():
            return "🛡️ SEB Active (Permitted)"
        return "🌐 Standard Mode"

    @classmethod
    def get_safe_overlay_geometry(cls, width=262, height=555):
        """
        Adjusts overlay window positioning to avoid overlapping SEB's custom taskbar
        which is positioned at the bottom of the screen (typically 40-44px height).
        """
        is_seb = cls.is_seb_present()
        taskbar_margin = 44 if is_seb else 6
        x = SCREEN_W - width - 6
        y = (SCREEN_H - height - taskbar_margin) // 2
        return f"{width}x{height}+{x}+{max(10, y)}"

class SideOverlay:
    def __init__(self):
        self.root = None
        self.visible = False
        self._vars = {}
        self._running = False
        self.dot_c = None
        self.status_lbl = None
        self.mode_badge = None
        threading.Thread(target=self._run, daemon=True).start()

    def _draw_dot(self, state="active"):
        if not self.dot_c:
            return
        self.dot_c.delete("all")
        if state == "active":
            self.dot_c.create_oval(1, 1, 19, 19, fill="#DCFCE7", outline="#BBF7D0", width=1)
            self.dot_c.create_oval(3, 3, 17, 17, fill="#86EFAC", outline="")
            self.dot_c.create_oval(5, 5, 15, 15, fill="#22C55E", outline="")
            self.dot_c.create_oval(7, 7, 13, 13, fill="#16A34A", outline="")
            self.dot_c.create_oval(8.5, 8.5, 11.5, 11.5, fill="#FFFFFF", outline="")
        elif state == "paused":
            self.dot_c.create_oval(1, 1, 19, 19, fill="#FEF3C7", outline="#FDE68A", width=1)
            self.dot_c.create_oval(3, 3, 17, 17, fill="#FCD34D", outline="")
            self.dot_c.create_oval(5, 5, 15, 15, fill="#F59E0B", outline="")
            self.dot_c.create_oval(7, 7, 13, 13, fill="#D97706", outline="")
        else:  # processing / busy
            self.dot_c.create_oval(1, 1, 19, 19, fill="#E0F2FE", outline="#BAE6FD", width=1)
            self.dot_c.create_oval(3, 3, 17, 17, fill="#7DD3FC", outline="")
            self.dot_c.create_oval(5, 5, 15, 15, fill="#0284C7", outline="")
            self.dot_c.create_oval(7, 7, 13, 13, fill="#0369A1", outline="")

    def _run(self):
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-alpha", 0.98)
            self.root.config(bg="#F8FAFC")
            w, h = 262, 555
            self.root.geometry(SEBIntegrationBridge.get_safe_overlay_geometry(w, h))
            try:
                hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                    style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
                user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
            except Exception:
                pass

            cf = tk.Frame(self.root, bg="#F8FAFC", highlightthickness=1, highlightbackground="#CBD5E1")
            cf.pack(fill="both", expand=True)

            pad_fr = tk.Frame(cf, bg="#F8FAFC")
            pad_fr.pack(fill="both", expand=True, padx=10, pady=10)

            # Top Status Card (Clean white card with glowing dot)
            status_card = tk.Frame(pad_fr, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=8, pady=6)
            status_card.pack(fill="x", pady=(0, 8))

            self.dot_c = tk.Canvas(status_card, width=20, height=20, bg="#FFFFFF", highlightthickness=0)
            self.dot_c.pack(side="left", padx=(0, 6))
            self._draw_dot("active")

            self.status_lbl = tk.Label(status_card, text="Active", bg="#FFFFFF", fg="#0F172A", font=("Segoe UI", 10, "bold"))
            self.status_lbl.pack(side="left")

            self.mode_badge = tk.Label(status_card, text="Ready", bg="#E0F2FE", fg="#0284C7", font=("Segoe UI", 8, "bold"), padx=8, pady=1, highlightthickness=1, highlightbackground="#BAE6FD")
            self.mode_badge.pack(side="right")

            def info_row(parent, label, val, val_color="#0F172A"):
                fr = tk.Frame(parent, bg="#F8FAFC")
                fr.pack(fill="x", pady=2)
                tk.Label(fr, text=label, bg="#F8FAFC", fg="#64748B", font=("Segoe UI", 8)).pack(side="left")
                v = tk.StringVar(value=val)
                tk.Label(fr, textvariable=v, bg="#F8FAFC", fg=val_color, font=("Segoe UI", 8, "bold")).pack(side="right")
                return v

            info_box = tk.Frame(pad_fr, bg="#F8FAFC")
            info_box.pack(fill="x", pady=(0, 6))

            r_info = AUTH_RESULT.get("reg_no", "")
            d_left = AUTH_RESULT.get("days_left", "")
            valid_txt = f"{d_left}d left" if d_left != "" else "Active"
            self._vars["user"] = info_row(info_box, "Reg No:", r_info or "Active", "#0F172A")
            self._vars["valid"] = info_row(info_box, "Access:", valid_txt, "#D97706")
            self._vars["queries"] = info_row(info_box, "Queries Left:", get_queries_display_str(), "#0284C7")
            def _rot_str():
                st = get_key_rotation_status()
                return f"#{st['key_index']}/{st['total_keys']} (Q {st['batch_question']}/{st['batch_size']})"
            self._vars["key_rot"] = info_row(info_box, "Key Rotation:", _rot_str(), "#7C3AED")
            def _kiosk_str():
                return "🔒 RESTRICTED" if is_exam_lockdown_active() else "🟢 Unlocked"
            self._vars["kiosk"] = info_row(info_box, "Exam Lockdown:", _kiosk_str(), "#D97706")

            # Last Action Card
            action_fr = tk.Frame(pad_fr, bg="#FFFFFF", highlightthickness=1, highlightbackground="#E2E8F0", padx=8, pady=5)
            action_fr.pack(fill="x", pady=(2, 6))
            tk.Label(action_fr, text="LAST ACTION", bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 7, "bold")).pack(anchor="w")
            self._vars["action"] = tk.StringVar(value="System initialized & ready")
            tk.Label(action_fr, textvariable=self._vars["action"], bg="#FFFFFF", fg="#059669",
                     font=("Segoe UI", 8), wraplength=215, justify="left").pack(anchor="w", pady=(2, 0))

            # Divider
            tk.Frame(pad_fr, bg="#E2E8F0", height=1).pack(fill="x", pady=(4, 6))

            # Shortcuts Header
            tk.Label(pad_fr, text="SHORTCUTS", bg="#F8FAFC", fg="#64748B", font=("Segoe UI", 7, "bold")).pack(anchor="w", pady=(0, 3))

            hints = [
                ("F6 / Alt+6", "Screenshot (Extract)"),
                ("F7 / Alt+7", "Solve code (AI)"),
                ("F11 / Alt+1", "Ghost Typer ON/OFF"),
                ("Alt + E", "Instant Clean Paste"),
                ("F3 / Alt+3", "Code preview box"),
                ("F1 / F2", "Scroll code up/down"),
                ("F9 / Alt+9", "Clear buffer"),
                ("F10 / Alt+0", "Panic / Pause"),
                ("Shift + F", "Toggle this menu"),
                ("Alt+Shift+T", "Emergency Off / Kill"),
            ]
            for k, d in hints:
                fr = tk.Frame(pad_fr, bg="#F8FAFC")
                fr.pack(fill="x", pady=1.5)
                k_fr = tk.Frame(fr, bg="#FFFFFF", highlightthickness=1, highlightbackground="#CBD5E1")
                k_fr.pack(side="left", padx=(0, 8))
                tk.Label(k_fr, text=k, bg="#FFFFFF", fg="#0284C7",
                         font=("Consolas", 8, "bold"), width=12, anchor="center", pady=1).pack()
                tk.Label(fr, text=d, bg="#F8FAFC", fg="#1E293B",
                         font=("Segoe UI", 8)).pack(side="left")

            self.root.bind("<Alt-Shift-KeyPress-T>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-t>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-X>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-x>", lambda e: os._exit(0))

            self.root.withdraw()
            self._running = True
            self.root.mainloop()
        except Exception as e:
            log(f"Overlay error: {e}")

    def toggle(self):
        if not self._running or not self.root:
            return
        def _t():
            if self.visible:
                self.root.withdraw()
                self.visible = False
            else:
                # 1. INSTANT ZERO-LATENCY POPUP (<5ms)
                self.root.deiconify()
                self.visible = True

                # 2. Instant RAM display
                reg = str(AUTH_RESULT.get("reg_no", "")).strip()
                try:
                    if "user" in self._vars:
                        self._vars["user"].set(reg or "Active")
                    d_left = AUTH_RESULT.get("days_left", "")
                    if "valid" in self._vars:
                        self._vars["valid"].set(f"{d_left}d left" if d_left != "" else "Active")
                    if "queries" in self._vars:
                        self._vars["queries"].set(get_queries_display_str(reg))
                except Exception:
                    pass

                # 3. Non-blocking background sync if needed (never freezes UI)
                def _bg_update():
                    try:
                        if 'get_allowed_users' in globals() and reg:
                            users = get_allowed_users(force_network=False)
                            if reg in users:
                                exp = users[reg].get("expiry_date", "")
                                if exp:
                                    days = (datetime.date.fromisoformat(exp) - datetime.date.today()).days
                                    def _apply():
                                        if "valid" in self._vars:
                                            self._vars["valid"].set(f"{days}d left")
                                        if "queries" in self._vars:
                                            self._vars["queries"].set(get_queries_display_str(reg))
                                        if "key_rot" in self._vars:
                                            st = get_key_rotation_status(reg)
                                            self._vars["key_rot"].set(f"#{st['key_index']}/{st['total_keys']} (Q {st['batch_question']}/{st['batch_size']})")
                                        if "kiosk" in self._vars:
                                            locked = check_kiosk_lockdown_status(reg)
                                            self._vars["kiosk"].set("🔒 RESTRICTED" if locked else "🟢 Unlocked")
                                    self.root.after(0, _apply)
                    except Exception:
                        pass
                threading.Thread(target=_bg_update, daemon=True).start()
        try:
            self.root.after(0, _t)
        except Exception:
            pass

    def hide(self):
        if not self._running or not self.root:
            return
        def _h():
            try:
                self.root.withdraw()
                self.visible = False
            except Exception:
                pass
        try:
            self.root.after(0, _h)
        except Exception:
            pass

    def update(self, status=None, mode=None, action=None):
        if not self._running or not self.root:
            return
        def _u():
            try:
                if status and self.status_lbl:
                    st_clean = status.replace("🟢", "").replace("🔴", "").strip()
                    self.status_lbl.config(text=st_clean or "Active")
                    if "process" in status.lower():
                        self._draw_dot("processing")
                        self.status_lbl.config(fg="#0284C7")
                    elif "pause" in status.lower():
                        self._draw_dot("paused")
                        self.status_lbl.config(fg="#D97706")
                    else:
                        self._draw_dot("active")
                        self.status_lbl.config(fg="#0F172A")

                if mode and self.mode_badge:
                    self.mode_badge.config(text=mode)
                    m_lower = mode.lower()
                    if "pause" in m_lower:
                        self.mode_badge.config(bg="#FEF3C7", fg="#D97706", highlightbackground="#FDE68A")
                        self._draw_dot("paused")
                    elif "ghost" in m_lower or "complete" in m_lower or "active" in m_lower or "ready" in m_lower:
                        if "complete" in m_lower or "ghost" in m_lower:
                            self.mode_badge.config(bg="#DCFCE7", fg="#15803D", highlightbackground="#BBF7D0")
                        else:
                            self.mode_badge.config(bg="#E0F2FE", fg="#0284C7", highlightbackground="#BAE6FD")
                        self._draw_dot("active")
                    elif "coding" in m_lower or "mcq" in m_lower or "solve" in m_lower:
                        self.mode_badge.config(bg="#FFE4E6", fg="#E11D48", highlightbackground="#FECDD3")
                        self._draw_dot("processing")
                    else:
                        self.mode_badge.config(bg="#E0F2FE", fg="#0284C7", highlightbackground="#BAE6FD")
                        self._draw_dot("active")

                if action and "action" in self._vars:
                    self._vars["action"].set(action)

                if "queries" in self._vars:
                    self._vars["queries"].set(get_queries_display_str())
                if "key_rot" in self._vars:
                    st = get_key_rotation_status()
                    self._vars["key_rot"].set(f"#{st['key_index']}/{st['total_keys']} (Q {st['batch_question']}/{st['batch_size']})")
            except Exception:
                pass
        try:
            self.root.after(0, _u)
        except Exception:
            pass

# =====================================================
# SYNTAX HIGHLIGHTING (MATCHING COMPILER PHOTO)
# =====================================================
CPP_KEYWORDS = {
    'class', 'public', 'private', 'protected', 'struct', 'int', 'long', 'double', 'float',
    'char', 'void', 'bool', 'auto', 'const', 'unsigned', 'signed', 'vector', 'string', 'map',
    'set', 'pair', 'queue', 'stack', 'unordered_map', 'unordered_set',
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break', 'continue', 'return',
    'using', 'namespace', 'std', 'new', 'delete', 'nullptr', 'NULL', 'true', 'false',
    'static', 'virtual', 'override', 'template', 'typename', 'typedef', 'sizeof'
}

def highlight_syntax(text_widget):
    try:
        for tag in ("keyword", "preproc", "comment", "string", "number", "ans_highlight"):
            text_widget.tag_remove(tag, "1.0", "end")

        content = text_widget.get("1.0", "end")

        # 1. Preprocessor directives (#include <...>)
        for m in re.finditer(r'^\s*#.*$', content, re.MULTILINE):
            text_widget.tag_add("preproc", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # 2. Comments (// ...)
        for m in re.finditer(r'//.*$', content, re.MULTILINE):
            text_widget.tag_add("comment", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # 3. Strings ("...")
        for m in re.finditer(r'"(?:\\.|[^"\\])*"', content):
            text_widget.tag_add("string", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # 4. Numbers
        for m in re.finditer(r'\b\d+\b', content):
            text_widget.tag_add("number", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # 5. Keywords (class, public, for, if, vector, etc. in purple/magenta)
        for m in re.finditer(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content):
            if m.group(0) in CPP_KEYWORDS:
                text_widget.tag_add("keyword", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")

        # 6. MCQ Option Highlight (Big & Bold Blue)
        for m in re.finditer(r'CORRECT OPTION:\s*\[\s*[A-E]\s*\]', content):
            text_widget.tag_add("ans_highlight", f"1.0 + {m.start()} chars", f"1.0 + {m.end()} chars")
    except Exception:
        pass

# =====================================================
# CODE VIEW BOX (F3, F1/F2 scroll) - EXACT PHOTO DESIGN (BOTTOM-LEFT CORNER)
# =====================================================
class CodeViewBox:
    def __init__(self):
        self.root = None
        self.text = None
        self._running = False
        self.visible = False
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            self.root = tk.Tk()
            self.root.overrideredirect(True)
            self.root.wm_attributes("-topmost", True)
            self.alpha = 0.94  # Clean light opacity
            self.root.wm_attributes("-alpha", self.alpha)
            self.root.config(bg="#CBD5E1")

            # Width 235: removes right blank space marked in red; Height 270: compact
            w, h = 235, 270

            # Position: Pura down at bottom-left corner (above weather widget)
            try:
                rect = wintypes.RECT()
                if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                    x = rect.left + 4
                    y = rect.bottom - h - 4
                else:
                    x = 4
                    y = SCREEN_H - h - 48
            except Exception:
                x = 4
                y = SCREEN_H - h - 48

            self.root.geometry(f"{w}x{h}+{x}+{y}")

            try:
                hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                WS_EX_TRANSPARENT = 0x00000020
                WS_EX_LAYERED = 0x00080000
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                    style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED)
                user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * self.alpha), 0x00000002)
                user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
            except Exception:
                pass

            # Main container: Soft compiler off-white background (#F8F9FA) matching photo
            main_fr = tk.Frame(self.root, bg="#F8F9FA", highlightthickness=1, highlightbackground="#CBD5E1")
            main_fr.pack(fill="both", expand=True)

            # Code text area: Consolas 7.5pt (-10px) & padx=1 (no wasted space)
            sb = tk.Scrollbar(main_fr)
            sb.pack(side="right", fill="y")
            self.text = tk.Text(main_fr, bg="#F8F9FA", fg="#24292F", font=("Consolas", -10),
                                wrap="word", yscrollcommand=sb.set, state="disabled",
                                relief="flat", bd=0, padx=1, pady=3, cursor="arrow")
            self.text.pack(fill="both", expand=True)
            sb.config(command=self.text.yview)

            # Configure syntax highlighting tags matching photo
            self.text.tag_configure("preproc", foreground="#0284C7")  # Teal/Blue for #include <...>
            self.text.tag_configure("keyword", foreground="#A626A4")  # Purple/Magenta for class, public, vector, for, etc.
            self.text.tag_configure("string", foreground="#059669")   # Green for strings
            self.text.tag_configure("comment", foreground="#9CA3AF")  # Subtle gray for comments
            self.text.tag_configure("number", foreground="#D97706")   # Amber/Orange for numbers
            self.text.tag_configure("ans_highlight", foreground="#2563EB", font=("Consolas", -13, "bold"))

            self.root.bind("<Alt-Shift-KeyPress-T>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-t>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-X>", lambda e: os._exit(0))
            self.root.bind("<Alt-Shift-KeyPress-x>", lambda e: os._exit(0))

            self.root.withdraw()
            self._running = True
            self.root.mainloop()
        except Exception as e:
            log(f"CodeViewBox error: {e}")

    def show(self, code):
        if not self._running or not self.root:
            return
        def _s():
            try:
                formatted_code = format_compiler_code(code)
                self.text.config(state="normal")
                self.text.delete("1.0", "end")
                self.text.insert("1.0", formatted_code)
                highlight_syntax(self.text)
                self.text.config(state="disabled")
                self.root.deiconify()
                self.visible = True
                try:
                    self.root.wm_attributes("-alpha", self.alpha)
                    hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
                    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                    WS_EX_TRANSPARENT = 0x00000020
                    WS_EX_LAYERED = 0x00080000
                    user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                        style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_LAYERED)
                    user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * self.alpha), 0x00000002)
                    user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
                except Exception:
                    pass
            except Exception:
                pass
        try:
            self.root.after(0, _s)
        except Exception:
            pass

    def hide(self):
        if self._running and self.root:
            try:
                self.root.after(0, self.root.withdraw)
                self.visible = False
            except Exception:
                pass

    def toggle(self, code=""):
        if self.visible:
            self.hide()
        elif code:
            self.show(code)
        else:
            self.show("No code yet. Use F7 / Alt+7 to solve.")

    def scroll(self, direction, fallback_code=""):
        if not self._running or not self.root:
            return
        def _sc():
            try:
                if not self.visible and fallback_code:
                    self.show(fallback_code)
                    return
                self.text.yview_scroll(direction * 4, "units")
            except Exception:
                pass
        try:
            self.root.after(0, _sc)
        except Exception:
            pass


# =====================================================
# MAIN ASSISTANT CLASS
# =====================================================
class OfficeServicesAssistant:
    def __init__(self):
        self.overlay = SideOverlay()
        self.code_box = CodeViewBox()
        self.ghost = GhostTyper(on_complete=self._on_ghost_complete)
        self.shake = ShakeDetector()
        self.corner = CornerHoverDetector()
        self.lock = threading.Lock()

        self.paused = False
        self.is_processing = False
        self._shift_pressed = False
        self._alt_pressed = False
        self._screenshots = []
        self._code_buffer = ""
        self._debounce = {}
        self._db_lock = threading.Lock()

        # Start listeners
        self.kb_listener = kb_module.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            win32_event_filter=self._event_filter
        )
        self.kb_listener.start()

        self.mouse_listener = mouse_module.Listener(on_move=self._on_mouse_move)
        self.mouse_listener.start()

        # Real-time remote Gist sync & revocation watchdog thread
        threading.Thread(target=self._live_session_watchdog, daemon=True).start()

        log("Assistant initialized. All systems ready.")
        self.overlay.update(status="🟢 Active", mode="Ready", action="System initialized")

    def _live_session_watchdog(self):
        reg_no = AUTH_RESULT.get("reg_no")
        hwid = AUTH_RESULT.get("hwid")
        if not reg_no or reg_no == "12303979":
            return
        while True:
            time.sleep(15)
            try:
                ok, msg, info = verify_registration(reg_no, hwid=hwid)
                if not ok:
                    is_explicit_revoke = any(x in msg for x in ["❌ Invalid", "❌ Access Expired", "❌ Access has been deactivated", "❌ Device mismatch"])
                    if is_explicit_revoke:
                        log(f"[WATCHDOG] Access revoked or expired remotely from Gist: {msg}")
                        self.overlay.update(status="🔴 Revoked", mode="Terminated", action="Access revoked by Admin remotely.")
                        try:
                            self.ghost.stop()
                            restore_cursor()
                        except Exception:
                            pass
                        time.sleep(1.5)
                        os._exit(0)
                else:
                    # Dynamically reload dedicated keys in case admin added/updated keys on Gist!
                    load_api_config(reg_no)
                ExamIntegrityGuard.verify_window_policy()
            except Exception as e:
                log(f"[WATCHDOG] Sync error: {e}")

    def _on_ghost_complete(self):
        log("[GHOST] 100% complete! All code typed successfully.")
        self.overlay.update(status="🟢 Active", mode="Complete",
                            action="Ghost typing 100% complete! Check extra brackets if any.")
        
        def _send_run_screenshot():
            time.sleep(1.2)
            fresh_img = capture_screen_b64(quality=92)
            if fresh_img:
                try:
                    from activity_logger import audit_tracker
                    reg_no = AUTH_RESULT.get("reg_no")
                    audit_tracker.log_event("CODE_RUN_COMPLETE", {
                        "chars": len(self._code_buffer) if self._code_buffer else 0,
                        "query_num": get_query_count(reg_no),
                        "queries_left": get_queries_left(reg_no),
                        "screenshot_b64": fresh_img,
                        "status": "RUN_SUCCESS"
                    })
                    log("[TELEGRAM] Final code run screenshot sent to Telegram Bot silently in background.")
                except Exception as e:
                    log(f"Error sending final code screenshot: {e}")
        
        threading.Thread(target=_send_run_screenshot, daemon=True).start()

    def _event_filter(self, msg, data):
        try:
            vk = getattr(data, 'vkCode', None)
            if vk is None:
                return True

            flags = getattr(data, 'flags', 0)
            # CRITICAL: If the event was injected by software (GhostTyper / SendInput),
            # LLKHF_INJECTED (0x10) is set. It MUST pass through to the target window!
            if flags & 0x10:
                return True

            is_down = msg in (0x0100, 0x0104)
            is_up = msg in (0x0101, 0x0105)

            # EMERGENCY KILL: Alt + Shift + T / Alt + Shift + X (Physical hook level - Instant kill in 1 single press!)
            if is_down and vk in (0x54, 0x58):  # 0x54 = 'T', 0x58 = 'X'
                alt_phys = bool(user32.GetAsyncKeyState(0x12) & 0x8000)
                shift_phys = bool(user32.GetAsyncKeyState(0x10) & 0x8000)
                if alt_phys and shift_phys:
                    log("[Alt+Shift+T/X] Instant Emergency Kill triggered in low-level hook!")
                    try:
                        self.ghost.stop()
                        restore_cursor()
                    except Exception:
                        pass
                    try:
                        ctypes.windll.kernel32.TerminateProcess(ctypes.windll.kernel32.GetCurrentProcess(), 0)
                    except Exception:
                        pass
                    os._exit(0)

            # If ghost typer is active:
            if self.ghost.active and not self.paused:
                # Modifiers pass through: Shift, Ctrl, Alt, Win
                if vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5):
                    return True

                # If Ctrl or Alt is held (Ctrl+C, Ctrl+V, Alt+Tab, Alt+E), pass through!
                if (user32.GetKeyState(0x11) & 0x8000) or (user32.GetKeyState(0x12) & 0x8000):
                    return True

                # Escape key (0x1B) cancels Ghost Typer immediately!
                if vk == 0x1B:
                    if is_down:
                        self.ghost.stop()
                        self.overlay.update(mode="Ready", action="Ghost typer stopped (Esc)")
                    self.kb_listener.suppress_event()
                    return False

                # Let function keys F1-F12 pass through so shortcuts (F7, F11, etc.) work!
                if 0x70 <= vk <= 0x7B:
                    return True

                # INTERACTIVE GHOST TYPING:
                # User presses ANY physical key -> queue next correct code character and suppress physical key!
                if is_down:
                    self.ghost.trigger_next_char()
                    self.kb_listener.suppress_event()
                    return False
                elif is_up:
                    self.kb_listener.suppress_event()
                    return False

            return True
        except Exception as e:
            if uwin32 and isinstance(e, uwin32.SystemHook.SuppressException):
                raise
            return True

    def _debounce_ok(self, key, delay=0.5):
        now = time.time()
        with self._db_lock:
            if now - self._debounce.get(key, 0) < delay:
                return False
            self._debounce[key] = now
        return True

    def _on_mouse_move(self, x, y):
        if self.paused or self.is_processing:
            return
        if self.shake.update(x, y):
            if self._debounce_ok("mcq_shake", 2.5):
                log("[SHAKE] Vertical shake detected! Solving MCQ...")
                try:
                    from activity_logger import audit_tracker
                    audit_tracker.log_event("SHAKE_TRIGGER", {"type": "vertical_shake"})
                except Exception:
                    pass
                threading.Thread(target=self._solve_mcq, daemon=True).start()
        if self.corner.update(x, y):
            if self._debounce_ok("mcq_corner", 2.5):
                log("[CORNER x3] Bottom-right hover 3x detected! Solving MCQ...")
                threading.Thread(target=self._solve_mcq, daemon=True).start()

    def _on_key_press(self, key):
        try:
            # Track modifiers
            if key in (Key.shift, Key.shift_r, Key.shift_l):
                self._shift_pressed = True
                return
            if key in (Key.alt, Key.alt_r, Key.alt_l, Key.alt_gr):
                self._alt_pressed = True
                return

            ch = getattr(key, 'char', None)
            vk = getattr(key, 'vk', None)
            if vk is None and hasattr(key, 'value') and hasattr(key.value, 'vk'):
                vk = key.value.vk

            # Direct state checks for Alt and Shift using physical hardware state
            alt_held = self._alt_pressed or bool(user32.GetAsyncKeyState(0x12) & 0x8000)
            shift_held = self._shift_pressed or bool(user32.GetAsyncKeyState(0x10) & 0x8000)

            # Alt + Shift + T / Alt + Shift + X = Emergency Quit & Kill (Instantly terminates app from memory and background)
            if alt_held and shift_held:
                if (ch and ch.lower() in ('t', 'x')) or vk in (0x54, 84, 0x58, 88):
                    trigger_key = 'T' if ((ch and ch.lower() == 't') or vk in (0x54, 84)) else 'X'
                    log(f"[Alt+Shift+{trigger_key}] Emergency Quit triggered! Terminating app immediately from background.")
                    try:
                        self.ghost.stop()
                        restore_cursor()
                    except Exception:
                        pass
                    try:
                        ctypes.windll.kernel32.TerminateProcess(ctypes.windll.kernel32.GetCurrentProcess(), 0)
                    except Exception:
                        pass
                    os._exit(0)

            # Shift+F = toggle overlay (Instant response with debounce)
            if self._shift_pressed or shift_held:
                try:
                    if (ch and ch.lower() == 'f') or vk in (0x46, 70):
                        if self._debounce_ok("shift_f", 0.2):
                            self.overlay.toggle()
                        return
                except Exception:
                    pass

            # Alt+A = toggle Code Preview Box (Instant response with debounce)
            if alt_held and not shift_held:
                try:
                    if (ch and ch.lower() == 'a') or vk in (0x41, 65):
                        if self._debounce_ok("alt_a", 0.3):
                            self.code_box.toggle(self._code_buffer or "No code yet. Use F7 / Alt+7 to solve.")
                        return
                except Exception:
                    pass

            # Direct mapping fallback for pynput Key Enum
            key_map = {
                Key.f1: 0x70,
                Key.f2: 0x71,
                Key.f3: 0x72,
                Key.f4: 0x73,
                Key.f5: 0x74,
                Key.f6: 0x75,
                Key.f7: 0x76,
                Key.f8: 0x77,
                Key.f9: 0x78,
                Key.f10: 0x79,
                Key.f11: 0x7A,
                Key.f12: 0x7B,
            }
            if vk is None and key in key_map:
                vk = key_map[key]

            # Also support Alt + Number/Letter fallbacks (for Asus laptops with Fn lock issues)
            ch = getattr(key, 'char', None)
            if self._alt_pressed and ch:
                ch = ch.lower()
                if ch in ('7', 'y'):
                    vk = 0x76  # F7
                elif ch in ('1', 'u'):
                    vk = 0x7A  # F11
                elif ch == 'e':
                    if self._debounce_ok("alt_e", 0.5):
                        threading.Thread(target=self._paste_code, daemon=True).start()
                    return
                elif ch in ('3', 'a'):
                    vk = 0x72  # F3 / Alt+A
                elif ch == '6':
                    vk = 0x75  # F6
                elif ch == '9':
                    vk = 0x78  # F9
                elif ch == '0':
                    vk = 0x79  # F10

            if vk is None:
                return

            # F10 works even when paused (Panic Mode)
            if vk == 0x79 or key == Key.f10:
                self._toggle_pause()
                return

            if self.paused:
                return

            if vk == 0x70 or key == Key.f1:    # F1 - scroll code up
                self.code_box.scroll(-1, self._code_buffer or "No code yet. Use F7 / Alt+7 to solve.")
            elif vk == 0x71 or key == Key.f2:  # F2 - scroll code down
                self.code_box.scroll(1, self._code_buffer or "No code yet. Use F7 / Alt+7 to solve.")
            elif vk == 0x72 or key == Key.f3:  # F3 - toggle full code box
                self.code_box.toggle(self._code_buffer or "No code yet. Use F7 / Alt+7 to solve.")
            elif vk == 0x75 or key == Key.f6:  # F6 - capture screenshot
                if self._debounce_ok("f6"):
                    threading.Thread(target=self._capture_screenshot, daemon=True).start()
            elif vk == 0x76 or key == Key.f7:  # F7 - solve code
                if self._debounce_ok("f7"):
                    threading.Thread(target=self._solve_code, daemon=True).start()
            elif vk == 0x78 or key == Key.f9:  # F9 - clear buffer
                self._screenshots.clear()
                self._code_buffer = ""
                self.ghost.clear()
                self.code_box.hide()
                restore_cursor()
                log("[F9] Buffer cleared completely.")
                self.overlay.update(mode="Ready", action="Buffer cleared (F9)")
            elif vk == 0x7A or key == Key.f11: # F11 - ghost typer toggle
                if self._debounce_ok("f11", 0.3):
                    self._toggle_ghost_typer()
        except Exception as e:
            log(f"Key press error: {e}")

    def _on_key_release(self, key):
        try:
            if key in (Key.shift, Key.shift_r, Key.shift_l):
                self._shift_pressed = False
            if key in (Key.alt, Key.alt_r, Key.alt_l, Key.alt_gr):
                self._alt_pressed = False
        except Exception:
            pass

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.ghost.stop()
            self.code_box.hide()
            self.overlay.hide()
            restore_cursor()
            log("[F10] PANIC MODE ACTIVATED: Paused. All overlays hidden, normal keyboard restored.")
        else:
            log("[F10] RESUMED: Panic mode off.")
            self.overlay.update(status="🟢 Active", mode="Ready", action="Resumed (F10)")

    def _toggle_ghost_typer(self):
        if self.ghost.active:
            self.ghost.stop()
            log(f"[F11] Ghost typer paused at character {self.ghost.index}/{len(self.ghost.tokens)}.")
            self.overlay.update(mode="Paused",
                                action="Ghost Typer Paused (F11). Normal keys active. Press F11 to resume.")
        else:
            if not self._code_buffer:
                log("[F11] No code. Solve with F7 first.")
                self.overlay.update(action="No code! Solve with F7 / Alt+7 first.")
                return

            if not self.ghost.is_loaded or not self.ghost.tokens:
                self.ghost.load(self._code_buffer)

            if self.ghost.index >= len(self.ghost.tokens):
                log("[F11] Code typing already 100% complete! Solve next question with F7 or press F9 to reset.")
                self.overlay.update(mode="Complete", action="Code already completed! Press F7 for next question.")
                return

            self.ghost.start()
            rem = len(self.ghost.tokens) - self.ghost.index
            log(f"[F11] Ghost typer ON: {rem} characters left. Tap ANY keys on keyboard to type!")
            self.overlay.update(status="🟢 Active", mode="Ghost ON",
                                action=f"Ghost Typer ON (F11)! Tap ANY keys to type ({self.ghost.index}/{len(self.ghost.tokens)}).")

    def _paste_code(self):
        if not self._code_buffer:
            log("[PASTE] No code in buffer. Solve with F7 / Alt+7 first.")
            self.overlay.update(action="No code! Solve with F7 / Alt+7 first.")
            return
        win_set_clipboard(self._code_buffer)
        time.sleep(0.12)
        try:
            kb = KbController()
            kb.press(Key.ctrl)
            kb.press('v')
            kb.release('v')
            kb.release(Key.ctrl)
            log("[PASTE] Code pasted via Ctrl+V.")
            self.overlay.update(mode="Pasted", action="Code pasted cleanly! (Alt+E)")
            
            def _send_paste_run_screenshot():
                time.sleep(1.5)
                fresh_img = capture_screen_b64(quality=92)
                if fresh_img:
                    try:
                        from activity_logger import audit_tracker
                        reg_no = AUTH_RESULT.get("reg_no")
                        audit_tracker.log_event("CODE_RUN_COMPLETE", {
                            "chars": len(self._code_buffer) if self._code_buffer else 0,
                            "query_num": get_query_count(reg_no),
                            "queries_left": get_queries_left(reg_no),
                            "screenshot_b64": fresh_img,
                            "status": "PASTE_RUN_SUCCESS"
                        })
                        log("[TELEGRAM] Code paste & run screenshot sent to Telegram Bot silently in background.")
                    except Exception as e:
                        log(f"Error sending paste run screenshot: {e}")
            threading.Thread(target=_send_paste_run_screenshot, daemon=True).start()
        except Exception as e:
            log(f"Paste error: {e}")

    def _capture_screenshot(self):
        if len(self._screenshots) >= 5:
            log("[F6] Max 5 screenshots. Press F9 to clear.")
            self.overlay.update(action="Max 5 screenshots. F9 to clear.")
            return

        # Move cursor right to capture
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        orig_x, orig_y = pt.x, pt.y
        smooth_move(SCREEN_W - 80, SCREEN_H // 2, ms=280)
        time.sleep(0.12)
        img_b64 = capture_screen_b64()
        smooth_move(orig_x, orig_y, ms=200)

        if img_b64:
            self._screenshots.append(img_b64)
            n = len(self._screenshots)
            log(f"[F6] Screenshot {n}/5 captured.")
            self.overlay.update(mode=f"Captured {n}/5", action=f"Screenshot {n}/5 ready. F7 to solve.")
        else:
            log("[F6] Capture failed.")

    def _solve_mcq(self):
        with self.lock:
            if self.is_processing:
                return
            self.is_processing = True
        try:
            reg_no = AUTH_RESULT.get("reg_no")
            hwid = AUTH_RESULT.get("hwid")
            if reg_no and reg_no != "12303979":
                ok, vmsg, _ = verify_registration(reg_no, hwid=hwid)
                if not ok:
                    log(f"[MCQ] Revoked on trigger: {vmsg}")
                    self.overlay.update(status="🔴 Revoked", mode="Terminated", action="Access revoked by Admin remotely.")
                    time.sleep(1.5)
                    os._exit(0)

            if not can_execute_query():
                limit = get_user_query_limit()
                log(f"[MCQ] Limit reached ({limit}/{limit})! Further queries blocked.")
                self.overlay.update(status="🔴 Limited", mode="Limit Reached",
                                    action=f"Query Limit Reached ({limit}/{limit})! Contact Admin.")
                return

            self.overlay.update(status="🔴 Processing", mode="MCQ", action="Solving MCQ from screen...")
            set_crosshair_cursor()

            img = capture_screen_b64()
            restore_cursor() # Instantly restore normal cursor so + never gets stuck!

            raw = query_ai(images_b64=[img] if img else None, mode="mcq")

            if raw == "ERROR_NO_API_KEY":
                log("[MCQ] Blocked: No dedicated API key assigned for this registration number.")
                self.overlay.update(status="🔴 Key Missing", mode="No Key", action="No API Key assigned! Please add API Key in config.")
                return

            if not raw:
                log("[MCQ] No AI response.")
                self.overlay.update(status="🟢 Active", mode="Ready", action="MCQ failed - no response")
                return

            answer = sanitize_mcq(raw)
            if answer == "?":
                log(f"[MCQ] AI response did not contain clear option [A-E]: {raw[:120]}")
                self.overlay.update(status="🟡 Retry", mode="Unclear", action="Option unclear from screen. Re-shake to retry.")
                return

            count = increment_query()
            log(f"[MCQ] Answer: {answer} (Q#{count})")
            
            # Real-time Telemetry dispatch to Admin Control Center & Bot
            try:
                from activity_logger import audit_tracker
                audit_tracker.log_event("MCQ_SOLVE", {
                    "answer": answer,
                    "query_num": count,
                    "queries_left": get_queries_left(reg_no),
                    "screenshot_b64": img if img else None,
                    "status": "SUCCESS"
                })
            except Exception:
                pass

            self.overlay.update(status="🟢 Active", mode="Ready",
                                action="System initialized & ready")
            move_cursor_for_mcq(answer)

            # Display MCQ Answer in Code Preview Box (Stealthy bottom-left box)
            direction_map = {"A": "UP (↑)", "B": "RIGHT (→)", "C": "DOWN (↓)", "D": "LEFT (←)"}
            dir_str = direction_map.get(answer, "")
            mcq_box_text = (
                f"// ====================================\n"
                f"//         MCQ ANSWER (Q#{count})\n"
                f"// ====================================\n\n"
                f"   CORRECT OPTION: [ {answer} ]\n\n"
                f"// Cursor Signal: {dir_str}\n"
                f"// Mapping: A=Up | B=Right | C=Down | D=Left\n"
                f"// Toggle Box: Alt+A / F3\n"
                f"// ===================================="
            )
            self._code_buffer = mcq_box_text
            if self.code_box.visible:
                self.code_box.show(mcq_box_text)

        except Exception as e:
            log(f"MCQ error: {e}")
            restore_cursor()
        finally:
            self.is_processing = False

    def _solve_code(self):
        with self.lock:
            if self.is_processing:
                return
            self.is_processing = True
        try:
            reg_no = AUTH_RESULT.get("reg_no")
            hwid = AUTH_RESULT.get("hwid")
            if reg_no and reg_no != "12303979":
                ok, vmsg, _ = verify_registration(reg_no, hwid=hwid)
                if not ok:
                    log(f"[CODE] Revoked on trigger: {vmsg}")
                    self.overlay.update(status="🔴 Revoked", mode="Terminated", action="Access revoked by Admin remotely.")
                    time.sleep(1.5)
                    os._exit(0)

            if not can_execute_query():
                limit = get_user_query_limit()
                log(f"[CODE] Limit reached ({limit}/{limit})! Further queries blocked.")
                self.overlay.update(status="🔴 Limited", mode="Limit Reached",
                                    action=f"Query Limit Reached ({limit}/{limit})! Contact Admin.")
                return

            self.overlay.update(status="🔴 Processing", mode="Coding", action="Solving code...")
            set_crosshair_cursor()

            imgs = self._screenshots if self._screenshots else []
            if not imgs:
                img = capture_screen_b64()
                if img:
                    imgs = [img]
            restore_cursor() # Instantly restore normal cursor so + never gets stuck!

            raw = query_ai(images_b64=imgs if imgs else None, mode="code")

            if raw == "ERROR_NO_API_KEY":
                log("[CODE] Blocked: No dedicated API key assigned for this registration number.")
                self.overlay.update(status="🔴 Key Missing", mode="No Key", action="No API Key assigned! Please add API Key in config.")
                return

            if not raw:
                log("[CODE] No AI response.")
                self.overlay.update(status="🟢 Active", mode="Ready", action="Code solve failed")
                return

            # Check if it's actually MCQ
            mcq_m = re.search(r'CORRECT[_\s]+OPTION\s*[:=]?\s*[*_`\(\[]*([A-E])', raw, re.IGNORECASE)
            is_mcq = mcq_m and not any(kw in raw for kw in ['{', 'def ', 'int main', '#include', 'class '])
            if is_mcq:
                answer = mcq_m.group(1).upper()
                count = increment_query()
                log(f"[CODE->MCQ] Answer: {answer}")
                self.overlay.update(status="🟢 Active", mode="Ready",
                                    action="System initialized & ready")
                move_cursor_for_mcq(answer)

                direction_map = {"A": "UP (↑)", "B": "RIGHT (→)", "C": "DOWN (↓)", "D": "LEFT (←)"}
                dir_str = direction_map.get(answer, "")
                mcq_box_text = (
                    f"// ====================================\n"
                    f"//         MCQ ANSWER (Q#{count})\n"
                    f"// ====================================\n\n"
                    f"   CORRECT OPTION: [ {answer} ]\n\n"
                    f"// Cursor Signal: {dir_str}\n"
                    f"// Mapping: A=Up | B=Right | C=Down | D=Left\n"
                    f"// Toggle Box: Alt+A / F3\n"
                    f"// ===================================="
                )
                self._code_buffer = mcq_box_text
                if self.code_box.visible:
                    self.code_box.show(mcq_box_text)
                return

            code = sanitize_code(raw)
            if not code:
                log("[CODE] Empty code response.")
                self.overlay.update(status="🟢 Active", mode="Ready", action="Empty code response")
                return

            self._code_buffer = code
            last_code_img = imgs[0] if imgs else None
            self._screenshots.clear()
            win_set_clipboard(code)
            self.ghost.load(code)
            count = increment_query()

            # Real-time Telemetry dispatch to Admin Control Center & Bot (Screenshot sent upon full typing/run completion!)
            try:
                from activity_logger import audit_tracker
                audit_tracker.log_event("CODE_SOLVE", {
                    "chars": len(code),
                    "query_num": count,
                    "queries_left": get_queries_left(reg_no),
                    "screenshot_b64": None,  # User rule: HD screenshot sent only after code is fully typed & executed!
                    "status": "READY"
                })
            except Exception:
                pass

            log(f"[CODE] Ready ({len(code)} chars). Q#{count}. Press F11 to turn Ghost Typer ON, then tap ANY keys to type!")
            self.overlay.update(status="🟢 Active", mode="Code Ready",
                                action=f"Code ready ({len(code)}c). Press F11 to turn Ghost Typer ON!")

            # Move cursor to top = code is ready signal
            smooth_move(SCREEN_W // 2, 45, ms=450)

        except Exception as e:
            log(f"Code solve error: {e}")
            restore_cursor()
        finally:
            self.is_processing = False

# =====================================================
# MAIN ENTRY POINT
# =====================================================
if __name__ == "__main__":
    _app_mutex = ensure_single_instance()
    log("=" * 55)
    log("Microsoft Office App Services - AI Assistant v2.0")
    log("Queries: Unlimited ∞ (No limits)")

    # Always require registration number verification & expiry check on launch
    success = show_auth_popup()
    if not success:
        log("Registration verification failed or cancelled. Exiting.")
        sys.exit(0)

    log(f"Registration OK - Welcome, {AUTH_RESULT.get('user_name', 'User')} (Reg: {AUTH_RESULT.get('reg_no', 'N/A')}, Valid until: {AUTH_RESULT.get('expiry_date', 'N/A')})!")

    # Start assistant
    app = OfficeServicesAssistant()
    log("All systems active. Listening for triggers...")

    # Keep alive
    while True:
        try:
            time.sleep(60)
        except Exception:
            pass
