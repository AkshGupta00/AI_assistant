import os
import pyautogui
import winreg
from pathlib import Path
import subprocess
import spacy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import pygetwindow as gw
import ctypes

nlp = spacy.load("en_core_web_sm")

"""opening of an application"""


def find_application(app_name):
    """Search for an application in Start Menu, Windows Registry, Program Files, and UWP Apps."""

    app_name_lower = app_name.lower()

    # 1️⃣ Search in Start Menu Shortcuts
    start_menu_paths = [
        Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
        Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")),
    ]

    for path in start_menu_paths:
        if path.exists():
            for shortcut in path.glob("**/*.lnk"):
                if app_name_lower in shortcut.stem.lower():
                    return str(shortcut)  # Return the shortcut path

    # 2️⃣ Search in Registry for Installed Applications
    registry_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for reg_path in registry_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            app_display_name, _ = winreg.QueryValueEx(
                                subkey, "DisplayName"
                            )
                            if (
                                app_display_name
                                and app_name_lower in app_display_name.lower()
                            ):
                                try:
                                    install_location, _ = winreg.QueryValueEx(
                                        subkey, "InstallLocation"
                                    )
                                    if install_location:
                                        exe_path = Path(install_location) / (
                                            app_display_name + ".exe"
                                        )
                                        if exe_path.exists():
                                            return str(exe_path)
                                except FileNotFoundError:
                                    continue
                    except FileNotFoundError:
                        continue
        except FileNotFoundError:
            continue

    # 3️⃣ Search in Program Files (Traditional Software Installations)
    program_files_paths = [Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")]

    for base_path in program_files_paths:
        if base_path.exists():
            for folder in base_path.iterdir():
                if folder.is_dir() and app_name_lower in folder.name.lower():
                    for file in folder.glob("*.exe"):
                        if app_name_lower in file.stem.lower():
                            return str(file)

    # 4️⃣ Search in UWP Apps (Microsoft Store Apps)
    try:
        command = f'Get-StartApps | Where-Object {{$_.Name -like "*{app_name}*"}} | Select-Object -ExpandProperty AppID'
        result = subprocess.run(
            ["powershell", "-Command", command], capture_output=True, text=True
        )

        app_id = result.stdout.strip()
        if app_id:
            return f"UWP App ID: {app_id}"  # Store the App ID instead of the path
    except Exception as e:
        pass

    return None  # App not found


def extract_app_name(command):
    """Extracts the most likely application name using NLP."""
    doc = nlp(command.lower())

    # Custom mappings for well-known applications
    app_mappings = {
        "edge": "msedge",
        "word": "winword",
        "powerpoint": "powerpnt",
        "excel": "excel",
        "chrome": "chrome",
        "notepad": "notepad",
        "vs code": "Code",
        "vscode": "Code",
        "epic": "EpicGamesLauncher",
        "epic games": "EpicGamesLauncher",
        "steam": "steam",
        "calculator": "calc",
        "cmd": "cmd",
        "terminal": "wt",  # Windows Terminal
    }

    # 1️⃣ Check if a known application is mentioned in the command
    for token in doc:
        if token.text in app_mappings:
            return app_mappings[token.text]  # Return mapped app name

    # 2️⃣ Check for noun chunks (handles multi-word app names like "epic games")
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if chunk_text in app_mappings:
            return app_mappings[chunk_text]

    # 3️⃣ Extract the first noun or proper noun as the app name
    for token in doc:
        if token.pos_ in ["PROPN", "NOUN"]:  # Proper noun or noun
            return token.text

    # 4️⃣ Try extracting words after verbs (open, launch, start, run)
    verbs = {"open", "launch", "start", "run"}
    words = [token.text for token in doc]

    for i, word in enumerate(words):
        if word in verbs and i + 1 < len(words):
            possible_name = " ".join(words[i + 1 :])  # Everything after the verb
            return app_mappings.get(possible_name, possible_name)  # Map if available

    return None  # Return None if no app name is found


# No suitable word found


SYSTEM_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "settings": "start ms-settings:",
    "control panel": "control",
    "file explorer": "explorer.exe",
    "word": r"C:\\Program Files\\Microsoft Office\\root\\Office16\WINWORD.EXE",  # Adjust path if needed
    "excel": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE",
    "powerpoint": r"C:\\Program Files\\Microsoft Office\\root\\Office16\\POWERPNT.EXE",
    "edge": "msedge.exe",
    "chrome": "chrome.exe",
}


def open_application(command):
    """Find and open an application."""
    app_name = extract_app_name(command)
    app_path = find_application(app_name)

    if app_path:
        if "UWP App ID" in app_path:
            app_id = app_path.replace("UWP App ID: ", "")
            subprocess.run(
                ["cmd", "/c", "start", f"shell:AppsFolder\\{app_id}"], check=True
            )
        else:
            subprocess.Popen(app_path, shell=True)
        return True
    return False


"""closing application"""


def close_active_window():
    """Closes the currently active window."""
    pyautogui.hotkey("alt", "f4")


def close_application(command):
    """Closes an application using Taskkill command."""
    app_name = extract_app_name(command)
    if not app_name:
        return "Couldn't identify the application to close."

    try:
        subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Closed {app_name}."
    except subprocess.CalledProcessError:
        return f"Failed to close {app_name}. It might not be running."


def close_window_by_title(title):
    """Closes a window by its title if it's open."""
    windows = gw.getWindowsWithTitle(title)
    if windows:
        windows[0].close()
        print(f"Closed window: {title}")
    else:
        print("Window not found.")


"""Adjust Volume and brightness"""


def set_volume(level):
    """Sets system volume to specified level (0-100)."""
    volume_percent = max(0, min(100, level))  # Clamp between 0-100

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))

    volume.SetMasterVolumeLevelScalar(volume_percent / 100, None)


# Adjust Brightness
def set_brightness(level):
    """Sets screen brightness to specified level (0-100)."""
    brightness_percent = max(0, min(100, level))  # Clamp between 0-100
    sbc.set_brightness(brightness_percent)


# Get Current Volume
def get_current_volume():
    """Returns the current system volume."""
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return int(volume.GetMasterVolumeLevelScalar() * 100)


# Get Current Brightness
def get_current_brightness():
    """Returns the current screen brightness as an integer."""
    brightness = sbc.get_brightness(display=0)  # Adjust display index if needed
    return (
        brightness[0] if isinstance(brightness, list) else brightness
    )  # Extract first element if list


"""system lock, restart, shutdown, and sleep commands"""


def shutdown():
    os.system("shutdown /s /t 0")


def restart():
    os.system("shutdown /r /t 0")


def logout():
    """Logs out the current user."""
    ctypes.windll.user32.LockWorkStation()


def sleep_computer():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


"""Process Command"""


# Extract Command Intent
def extract_intent(command):
    """Uses NLP to detect the type of command and value."""
    doc = nlp(command.lower())
    for token in doc:
        if any(token.lemma_ in ["open", "launch", "start"] for token in doc):
            return "open", None
        if any(
            token.lemma_ in ["force", "kill", "end", "immediately"] for token in doc
        ):
            return "close", "force"
        if any(
            token.lemma_ in ["close", "exit", "quit", "terminate", "stop"]
            for token in doc
        ):
            return "close", None
        if token.lemma_ in ["increase", "decrease", "raise", "lower", "reduce"]:
            return "adjust", token.lemma_
        if token.lemma_ in ["set", "change"]:
            return "set", None
        if any(token.lemma_ in ["shutdown", "power", "turn"] for token in doc) and any(
            word.text in ["PC", "computer", "system"] for word in doc
        ):
            return "shutdown", None
        if any(token.lemma_ in ["lock", "secure"] for token in doc):
            return "logout", None
        if any(token.lemma_ in ["restart", "reboot"] for token in doc):
            return "restart", None
        if any(
            token.lemma_ in ["sleep", "hibernate", "suspend", "standby"]
            for token in doc
        ):
            return "sleep", None
    return None, None


# Extract Numeric Value
def extract_number(command):
    """Extracts numeric values from command."""
    doc = nlp(command.lower())
    for token in doc:
        if token.like_num:  # Detects numbers like 10, 50, 100
            return int(token.text)
    return None


def process_basic_sys_command(command):
    intent, action = extract_intent(command)
    level = extract_number(command)

    if intent == "open":
        open_application(command)
        return True,"opning application"
    elif intent == "close" and action == "force":
        close_application(command)
        return True,"closing application"
    elif "close active window" in command or "close this window" in command:
        close_active_window()
        return True,"closing active window"
    elif intent == "close" and action == None:
        title = command.replace("close", "").replace("window", "").strip()
        close_window_by_title(title)
        return True,"closing window"
    elif intent == "shutdown":
        shutdown()
        return True,"shuting down"
    elif intent == "restart":
        restart()
        return True,"restarting"
    elif intent == "logout":
        logout()
        return True,"loging out"
    elif intent == "sleep":
        sleep_computer()
        return True,"going to sleep"
    elif "volume" in command:
        if intent == "set" and level is not None:
            set_volume(level)
            return True,f"seting volume to {level}"
        elif action == "increase":
            set_volume(min(100, get_current_volume() + 10))  # Increase by 10%
            return True ,"increasing volume by 10"
        elif action == "decrease":
            set_volume(max(0, get_current_volume() - 10))  # Decrease by 10%
            return True, "decreasing volume by 10"
    elif "brightness" in command:
        if intent == "set" and level is not None:
            set_brightness(level)
            return True ,f"seting brightness to {level}"
        elif action == "increase":
            set_brightness(min(100, get_current_brightness() + 10))
            return True ,"increasing brightness by 10"
        elif action == "decrease":
            set_brightness(max(0, get_current_brightness() - 10))
            return True, "decreasing brightness by 10"
    return False ,"something went wrong"

