"""
Audit Logging & Activity Tracker Module
---------------------------------------
Provides structured, asynchronous activity tracking and audit logging
for authorized user sessions.

Logs operational events (logins, feature invocations, timestamps, 
and session metrics) and transmits real-time alerts + question screenshots
to Telegram Bot and Admin Control Center.
"""

import os
import sys
import time
import json
import uuid
import datetime
import threading
import queue
import socket
import base64
import io
import requests

UDP_PORT = 54321

class AuditLogger:
    def __init__(self, webhook_url=None, api_server_url="http://localhost:4000/api/events", local_log_path=None):
        """
        Initializes the audit logger.
        :param webhook_url: Optional remote webhook endpoint (e.g. Discord/Slack/Telegram).
        :param api_server_url: Backend Node.js / Express REST ingestion endpoint.
        :param local_log_path: Optional path for storing structured JSON logs locally.
        """
        self.webhook_url = webhook_url
        self.api_server_url = api_server_url
        self.auth_token = "uni-audit-secret-token-2026"
        
        # Dual logging paths for absolute reliability
        self.local_log_path = local_log_path or os.path.join(
            os.environ.get("TEMP", os.path.dirname(os.path.abspath(__file__))),
            "app_audit_trail.jsonl"
        )
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.secondary_log_path = os.path.join(base_dir, "app_audit_trail.jsonl")

        self.session_id = str(uuid.uuid4())[:8]
        self.user_reg = None
        self.user_name = None
        self.is_verified = False
        
        # Counters for session question stats
        self.total_solves = 0
        self.mcq_solves = 0
        self.code_solves = 0

        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        
        # UDP socket for real-time local GUI communication (<1ms latency)
        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Start background worker to ensure non-blocking operation
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def start_session(self, reg_no, user_name="Authorized User", is_verified=True, expiry_date="", days_left=None):
        """Initializes tracking for a verified user session."""
        self.user_reg = str(reg_no)
        self.user_name = user_name
        self.is_verified = is_verified
        self.log_event("SESSION_START", {
            "status": "Authenticated" if is_verified else "Unverified",
            "is_verified": is_verified,
            "expiry_date": expiry_date,
            "days_left": days_left,
            "device": os.environ.get("COMPUTERNAME", "Unknown"),
            "os_user": os.environ.get("USERNAME", "Unknown")
        })

    def log_event(self, action_name, details=None):
        """
        Queues an action/event for logging.
        :param action_name: High-level event identifier (e.g., 'MCQ_SOLVE', 'CODE_SOLVE')
        :param details: Dictionary of metadata or status attributes.
        """
        det = dict(details or {})
        
        # Track stats
        if action_name == "MCQ_SOLVE":
            self.mcq_solves += 1
            self.total_solves += 1
        elif action_name == "CODE_SOLVE":
            self.code_solves += 1
            self.total_solves += 1

        det["total_solved"] = self.total_solves
        det["mcq_solved"] = self.mcq_solves
        det["code_solved"] = self.code_solves
        det["is_verified"] = self.is_verified

        event_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "session_id": self.session_id,
            "reg_no": self.user_reg or "UNVERIFIED",
            "user_name": self.user_name or "Unknown",
            "action": action_name,
            "details": det
        }
        self.queue.put(event_record)

    def _get_telegram_config(self):
        try:
            candidates = []
            if getattr(sys, 'frozen', False):
                candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "admin_config.json"))
            if '__file__' in globals():
                candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_config.json"))
            candidates.append(os.path.join(os.getcwd(), "admin_config.json"))
            for p in candidates:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as cf:
                        return json.load(cf).get("TELEGRAM", {})
        except Exception:
            pass
        return {}

    def _process_queue(self):
        """Background thread worker that flushes queued events."""
        while not self._stop_event.is_set():
            try:
                event = self.queue.get(timeout=1.0)
            except queue.Empty:
                continue

            det = event.get("details", {})
            screenshot_b64 = det.pop("screenshot_b64", None)  # Extract image so disk logs don't get bloated

            # 1. Write to local structured JSON Lines files (dual locations for safety)
            raw_json = json.dumps(event)
            for path in [self.local_log_path, self.secondary_log_path]:
                try:
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(raw_json + "\n")
                except Exception:
                    pass

            # 2. Instant UDP Broadcast to Admin Desktop Dashboard (<1ms latency)
            try:
                self._udp_sock.sendto(raw_json.encode('utf-8'), ('127.0.0.1', UDP_PORT))
            except Exception:
                pass

            # 3. Dispatch to Node.js / Express Telemetry Backend if available
            if self.api_server_url:
                try:
                    payload = {
                        "userId": event.get("reg_no"),
                        "userName": event.get("user_name"),
                        "sessionId": event.get("session_id"),
                        "action": event.get("action"),
                        "status": event.get("status", "SUCCESS"),
                        "timestamp": event.get("timestamp"),
                        "details": det
                    }
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.auth_token}"
                    }
                    requests.post(self.api_server_url, json=payload, headers=headers, timeout=1.5)
                except Exception:
                    pass

            # 4. Telegram Bot Notification Dispatcher (Messages + Screenshots + Metrics)
            try:
                tg_cfg = self._get_telegram_config()
                bot_token = tg_cfg.get("bot_token")
                chat_id = tg_cfg.get("chat_id")
                if bot_token and chat_id and tg_cfg.get("enabled", True):
                    act = event.get("action", "")
                    u_name = event.get("user_name", "")
                    u_reg = event.get("reg_no", "")
                    is_v = "✅ Verified Student" if det.get("is_verified", False) else "❌ Unverified"
                    tot = det.get("total_solved", self.total_solves)
                    mcq_tot = det.get("mcq_solved", self.mcq_solves)
                    code_tot = det.get("code_solved", self.code_solves)

                    caption = None
                    if act == "MCQ_SOLVE":
                        caption = (
                            f"⚡ *[MCQ SOLVE ALERT]*\n"
                            f"👤 *Student:* {u_name} (`{u_reg}`)\n"
                            f"🛡️ *Status:* {is_v}\n"
                            f"🎯 *Correct Option:* `[ {det.get('answer','?')} ]`\n"
                            f"📊 *Progress:* Question #{det.get('query_num','?')}\n"
                            f"📈 *Solved Stats:* Total: `{tot}` | MCQ: `{mcq_tot}` | Code: `{code_tot}`\n"
                            f"⏳ *Queries Left:* {det.get('queries_left','?')}"
                        )
                    elif act == "CODE_SOLVE":
                        caption = (
                            f"💻 *[CODE PROBLEM SOLVED - READY]*\n"
                            f"👤 *Student:* {u_name} (`{u_reg}`)\n"
                            f"🛡️ *Status:* {is_v}\n"
                            f"📏 *Code Size:* `{det.get('chars','?')}` characters\n"
                            f"📊 *Progress:* Question #{det.get('query_num','?')}\n"
                            f"📈 *Solved Stats:* Total: `{tot}` | MCQ: `{mcq_tot}` | Code: `{code_tot}`\n"
                            f"⏳ *Queries Left:* {det.get('queries_left','?')}\n"
                            f"⌨️ *Action:* Ghost Typing armed. Final HD Screenshot will be sent upon full typing & run completion!"
                        )
                    elif act == "CODE_RUN_COMPLETE":
                        caption = (
                            f"🎯 *[CODE FULLY TYPED & RUN COMPLETED]*\n"
                            f"👤 *Student:* {u_name} (`{u_reg}`)\n"
                            f"🛡️ *Status:* {is_v}\n"
                            f"💻 *State:* Code 100% Typed & Executed on Screen! ✅\n"
                            f"📏 *Code Size:* `{det.get('chars','?')}` characters\n"
                            f"📊 *Progress:* Question #{det.get('query_num','?')}\n"
                            f"📈 *Solved Stats:* Total: `{tot}` | MCQ: `{mcq_tot}` | Code: `{code_tot}`\n"
                            f"⏳ *Queries Left:* {det.get('queries_left','?')}"
                        )
                    elif act == "PROCTOR_ALERT":
                        msg = (
                            f"🚨 *[EXAM INTEGRITY VIOLATION ALERT]*\n"
                            f"👤 *Student:* {u_name} (`{u_reg}`)\n"
                            f"🛡️ *Status:* {is_v}\n"
                            f"⚠️ *Violation:* `{det.get('violation', 'Unauthorized Material / Outside Screen')}`\n"
                            f"🖥️ *Details:* `{det.get('info', 'Screen focus change or multi-monitor')}`"
                        )
                        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        requests.post(tg_url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=4)
                    elif act == "SESSION_START":
                        days_txt = f"{det.get('days_left')} days" if det.get("days_left") is not None else "Active"
                        msg = (
                            f"🟢 *[STUDENT SESSION STARTED]*\n"
                            f"👤 *Student:* {u_name} (`{u_reg}`)\n"
                            f"🛡️ *Verification:* {is_v}\n"
                            f"📅 *Validity:* `{days_txt}` (Until {det.get('expiry_date', 'N/A')})\n"
                            f"🖥️ *Device:* `{det.get('device','?')}`\n"
                            f"👤 *Windows User:* `{det.get('os_user','?')}`"
                        )
                        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        requests.post(tg_url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=4)

                    # Send Photo with Caption if screenshot available!
                    if caption:
                        if screenshot_b64:
                            try:
                                img_bytes = base64.b64decode(screenshot_b64)
                                photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                                files = {"photo": ("question_screenshot.jpg", io.BytesIO(img_bytes), "image/jpeg")}
                                data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
                                r = requests.post(photo_url, data=data, files=files, timeout=7)
                                if r.status_code != 200:
                                    # Fallback to plain text message if photo upload hits payload limits
                                    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                    requests.post(tg_url, json={"chat_id": chat_id, "text": caption, "parse_mode": "Markdown"}, timeout=4)
                            except Exception:
                                tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                requests.post(tg_url, json={"chat_id": chat_id, "text": caption, "parse_mode": "Markdown"}, timeout=4)
                        else:
                            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            requests.post(tg_url, json={"chat_id": chat_id, "text": caption, "parse_mode": "Markdown"}, timeout=4)

            except Exception:
                pass

            # 5. Dispatch to remote webhook if configured
            if self.webhook_url:
                try:
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "content": f"📋 **[AUDIT EVENT]** User `{event['reg_no']}` ({event['user_name']}) | Action: `{event['action']}`",
                        "embeds": [{
                            "title": f"Action: {event['action']}",
                            "timestamp": event["timestamp"],
                            "fields": [
                                {"name": "Registration No", "value": str(event["reg_no"]), "inline": True},
                                {"name": "User Name", "value": str(event["user_name"]), "inline": True},
                                {"name": "Session ID", "value": event["session_id"], "inline": True},
                                {"name": "Details", "value": json.dumps(det, indent=2)}
                            ]
                        }]
                    }
                    requests.post(self.webhook_url, json=payload, headers=headers, timeout=4)
                except Exception:
                    pass

            self.queue.task_done()

    def end_session(self, reason="Application Exited"):
        """Logs session termination and gracefully flushes queue."""
        self.log_event("SESSION_END", {"reason": reason})
        time.sleep(0.5)

# Global singleton instance
audit_tracker = AuditLogger()
