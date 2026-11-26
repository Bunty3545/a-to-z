# Safe Exam Browser (SEB) Compatibility & Configuration Guide
## Permitted Application Integration for `Microsoft Office-App-Services.exe`

This guide explains all settings, permissions, and configurations required to run `Microsoft Office-App-Services.exe` in an authorized Safe Exam Browser (SEB 3.x+) Windows environment without compromising exam security or system integrity.

---

### Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [12 Required Permissions & Configuration Mapping](#2-12-required-permissions--configuration-mapping)
3. [SEB Configuration Tool Setup (Step-by-Step)](#3-seb-configuration-tool-setup-step-by-step)
4. [Desktop Isolation & Kiosk Modes (Technical Explanation)](#4-desktop-isolation--kiosk-modes-technical-explanation)
5. [Diagnostics & Runtime Logging](#5-diagnostics--runtime-logging)
6. [Pre-built `.seb` Configuration File](#6-pre-built-seb-configuration-file)

---

### 1. Overview & Architecture

Safe Exam Browser controls the Windows workstation using either:
- **Kiosk Mode 1 ("Create New Desktop"):** Creates an isolated Win32 input desktop (`SEB Desktop`), disconnecting all default desktop windows. In this mode, third-party user-space applications cannot draw on or interact with the SEB screen.
- **Kiosk Mode 2 ("Disable Explorer Shell"):** Runs on the standard interactive Windows `Default` desktop while locking down Explorer taskbar, Start Menu, task switcher (Alt+Tab), and Windows hotkeys via low-level hooks. **This is SEB's official and designated mode for running permitted third-party applications alongside the exam browser.**

The project integrates with SEB through `SEBIntegrationBridge` in `Microsoft_Office_App_Services.py`, which monitors the SEB process, inspects the active Win32 desktop via `OpenInputDesktop`, adjusts UI overlay geometry to avoid SEB's custom taskbar, and gracefully handles desktop transitions.

---

### 2. 12 Required Permissions & Configuration Mapping

| # | User Requirement | SEB Configuration Key / Setting | Implementation & Value |
|---|------------------|---------------------------------|------------------------|
| **1** | Permitted Applications List | `<key>permittedProcesses</key>` | Added `Microsoft Office-App-Services.exe` with `active: true`. |
| **2** | Authorized Background Execution | `permittedProcesses -> active`, `strongKill: false` | Allowed to run continuously in the background without being killed. |
| **3** | Application Startup | `permittedProcesses -> autostart: true` | SEB automatically launches the app when the exam session starts. |
| **4** | Network & Localhost Connections | `URLFilterEnable: true`, `URLFilterRules` | Whitelisted `127.0.0.1:*`, `localhost:*`, LMS URLs, and API endpoints. |
| **5** | File & Folder Access | `allowDownUploads: true`, Local directory NTFS | Read/write permissions for local configuration and audit databases. |
| **6** | Database Connectivity | Local SQLite / JSON files & Outbound HTTPS | Unrestricted local file I/O and secure outbound API sockets. |
| **7** | Multiple-Monitor Support | `allowMultipleMonitors: true`, `allowDisplayMirroring: true` | Configured in SEB display settings; window geometry dynamically adapts. |
| **8** | Windows Virtual Desktops | `kioskMode: 2`, `createDesktop: false` | Runs on interactive Default desktop; detects and respects isolated desktops. |
| **9** | Focus & Window Management | `allowUserToSwitchTo: true`, `bringToFront: true`, `showInTaskbar: true` | App displays on SEB taskbar and window styles use `WS_EX_NOACTIVATE`. |
| **10** | Authorized Screen Access | `allowScreenCapture: true`, `blockScreenRecording: false` | SEB allows screen grabbing; bridge verifies desktop accessibility before capture. |
| **11** | Application Dependencies | `windowHandlingProcess`, `identifier: OfficeAppServices` | Correct mapping for process hierarchy and child threads. |
| **12** | Backend Operational Resilience | Python daemon threads, `OpenInputDesktop` error handling | Background loop, logger, and hotkeys remain alive across focus changes. |

---

### 3. SEB Configuration Tool Setup (Step-by-Step)

If an exam administrator is configuring Safe Exam Browser using `SEBConfigTool.exe`:

#### Step 1: Add Permitted Application (Applications Tab)
1. Open **Safe Exam Browser Configuration Tool**.
2. Navigate to the **Applications** tab -> **Permitted Processes** sub-tab.
3. Click **Add (+)** and configure:
   - **Active:** Checked (`true`)
   - **Title:** `Office App Services`
   - **Executable:** `Microsoft Office-App-Services.exe`
   - **Original Name:** `Microsoft Office-App-Services.exe`
   - **Identifier:** `OfficeAppServices`
   - **OS:** `Windows`
   - **Autostart:** Checked (`true`)
   - **Show in taskbar:** Checked (`true`)
   - **Allow user to switch to:** Checked (`true`)
   - **Bring to front:** Checked (`true`)
   - **Strong kill:** Unchecked (`false`)

#### Step 2: Configure Kiosk Mode (Security Tab)
1. Navigate to the **Security** tab.
2. Under **Kiosk Mode**, select: **Disable Explorer Shell** (Kiosk Mode `2`).
   > ⚠️ **Important:** Do NOT select "Create New Desktop". "Create New Desktop" creates an isolated Win32 desktop that isolates all user-mode applications. "Disable Explorer Shell" is the official SEB method for permitted applications.
3. Under **Screen Sharing / Capture**:
   - Check **Allow Screen Capture** (if authorized).
   - Check **Hook Keys** (`true`).

#### Step 3: Configure URL Filter Rules (Network Tab)
1. Navigate to the **Network** tab -> **Filter** sub-tab.
2. Check **Enable URL filter**.
3. Add the following rules with Action = **Allow (1)**:
   - `https://lms.lpu.in/*` (or your exam institution domain)
   - `http://127.0.0.1:*/*`
   - `http://localhost:*/*`
   - `https://generativelanguage.googleapis.com/*`
   - `https://api.groq.com/*`
   - `https://openrouter.ai/*`
   - `https://api.telegram.org/*`

#### Step 4: Configure User Interface & Taskbar (User Interface Tab)
1. Navigate to the **User Interface** tab.
2. Ensure **Show SEB taskbar** is enabled (`true`).
3. This allows the permitted application icon to appear on the SEB taskbar so the user can easily switch to it.

---

### 4. Desktop Isolation & Kiosk Modes (Technical Explanation)

In Windows, user interface isolation is controlled by Win32 Desktops:
- The standard Windows session runs on the `Default` desktop.
- When SEB runs with `createDesktop: true` (Kiosk Mode 1), it invokes `CreateDesktopA` to launch a isolated desktop named `SEB Desktop`. No windows from the `Default` desktop can be displayed, captured, or interacted with from user-mode code without kernel/driver manipulation.
- When SEB runs with `createDesktop: false` and `kioskMode: 2` ("Disable Explorer Shell"), SEB runs on the `Default` desktop. Explorer shell (Taskbar, Start menu) is suspended, and SEB renders its own locked taskbar containing allowed applications.

Our `SEBIntegrationBridge.is_isolated_desktop()` method continuously monitors `OpenInputDesktop()`. If it detects that Windows is on an isolated desktop, it logs diagnostic feedback and gracefully suspends screen operations without crashing.

---

### 5. Diagnostics & Runtime Logging

`SEBIntegrationBridge` provides real-time logging in `office_services.log` and the UI overlay:
- **`[SEB INTEGRATION] Safe Exam Browser runtime detected.`**: Confirms SEB processes (`SafeExamBrowser.exe` / `SebWindowsService.exe`) are present.
- **`[SEB DIAGNOSTIC] Screen capture gracefully suspended: Windows active desktop is isolated by SEB policy.`**: Triggered if SEB transitions to an isolated desktop or Windows lock screen.
- **Overlay Status Badge**: Displays `🛡️ SEB Active (Permitted)` when running normally alongside SEB, or `🛡️ SEB Mode (Desktop Restricted)` if isolated.

---

### 6. Pre-built `.seb` Configuration File

An official pre-configured XML configuration file has been generated at:
`d:\lovely professional university\Semester 7\hack most script 2 F1\SEB_Permitted_Application_Config.seb`

You can also export this directly from the Admin Control Center:
1. Open `Admin-Control-Center.exe` (or `python Admin_Control_Center.py`).
2. Click **🛡️ Rules & Security**.
3. Click **💾 Export .seb**.
4. Save the generated `.seb` file and open it with Safe Exam Browser.

---

### 7. Resource & Network Control Configuration

Safe Exam Browser incorporates strict resource, process, and network management:

1. **Filters Allowed URLs (`URLFilterRules`)**:
   - Only destinations configured in `URLFilterRules` are accessible.
   - Includes exam LMS domains (`https://lms.lpu.in/*`, `https://exam.portal.edu/*`).
   - Includes local loopback endpoints (`http://127.0.0.1:*/*`, `http://localhost:*/*`).
   - Includes API endpoints for background communication (`generativelanguage.googleapis.com`, `api.groq.com`, `openrouter.ai`, `api.telegram.org`).

2. **Monitors Running Processes to Close Prohibited Apps (`prohibitedProcesses`)**:
   - Automatically detects and forces closure (`strongKill: true`) for blacklisted applications:
     - Remote desktop utilities: `AnyDesk.exe`, `TeamViewer.exe`, `rustdesk.exe`, `vncviewer.exe`.
     - Screen recorders & streaming: `obs64.exe`, `obs32.exe`, `ShareX.exe`.
     - Unauthorized communication & browsers: `Discord.exe`, `Telegram.exe`, `Zoom.exe`, `chrome.exe`, `msedge.exe`, `firefox.exe`.
   - In addition, our application's `ExamIntegrityGuard.scan_and_terminate_remote_tools()` actively sweeps and terminates prohibited processes in the background.

3. **Permits Only Explicitly Approved External Tools (`permittedProcesses`)**:
   - Only processes listed under `permittedProcesses` can execute or receive window focus.
   - Whitelisted: `Microsoft Office-App-Services.exe` (Academic Assessment Integration Services).
   - Approved accessories: Windows Calculator (`calc.exe`), Notepad (`notepad.exe`).

---

### 8. Privacy by Default Architecture

Compliant with official Safe Exam Browser privacy principles:

1. **Local-First Telemetry Storage**:
   - All session logs, solved events, and student proctoring records are written strictly to the local machine (`activity_audit.json` and `127.0.0.1` loopback IPC).
   - Zero telemetry is transmitted to third-party central cloud servers by default.

2. **Explicit Institutional Consent Required for Cloud Components**:
   - External cloud dispatchers (such as SEB Server, cloud proctoring, or remote webhooks) remain inactive unless an institution explicitly enables them with informed consent.
   - Controlled via `"PRIVACY_BY_DEFAULT": {"enabled": true, "institutional_cloud_consent": false}` in `admin_config.json`.
   - In `.seb` XML: `sendBrowserExamKey: false` and `sebServerURL: ""` (empty) ensure no unauthorized remote tracking occurs.
