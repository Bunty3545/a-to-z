"""
Quick Test Launcher for Uni One - Device Verification Popup
Double-click or run this file to test the UI without admin restrictions.
"""
import sys
import os

# Set working directory to script location
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Import and invoke the auth popup directly
from Microsoft_Office_App_Services import show_auth_popup

print("Launching 'Uni One - Device Verification' popup...")
success = show_auth_popup()
print(f"Verification outcome: {success}")

