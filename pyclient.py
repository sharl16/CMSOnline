# Python/Unity Communication:

import UDPComms as U
import time
import threading

isRunning = False

sock = U.UDPComms(udpIP="127.0.0.1", portTX=8000, portRX=8001, enableRX=True, suppressWarnings=False)

def ReceiveDataContinuous():
    while True:
        received_data = sock.ReadReceivedData()
        if received_data:
            print(f"Received: {received_data}")
        time.sleep(0.01)

def SignalClient():
    print("Signaling Client session to Unity.")
    sock.SendData('Set session as client.')

isRunning = True

thread = threading.Thread(target=ReceiveDataContinuous)
thread.start()

SignalClient()

# ==========================================================

# Networking:

import socket
import threading
import time

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

peer_ip = "192.168.1.6"  
peer_port = 9000 

isConnected = False

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"{Fore.LIGHTBLUE_EX}Acting as Client!{Style.RESET_ALL}")

def ConnectToServer():
    print(f"Attempting to connect on: {Fore.CYAN}{peer_ip}:{peer_port}{Style.RESET_ALL}..")
    try:
        client_socket.connect((peer_ip, peer_port))
        isConnected = True
    except Exception as e:
        print(f"{Fore.YELLOW}Failed to connect to {peer_ip}:{peer_port} / Reason: {e}{Style.RESET_ALL}")
        prompt = input("Press (y) to retry connection.")
        if str.lower(prompt) == "y":
            ConnectToServer()
        else:
            quit()


def handle_server():
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print(f"{Fore.YELLOW}Server disconnected!{Style.RESET_ALL}")
                break
            decodedData = data.decode('utf-8')
            print(f"Received: {Fore.MAGENTA}{decodedData}{Style.RESET_ALL}")
            sock.SendData(decodedData)
        except Exception as e:
            print(f"{Fore.RED}{e}{Style.RESET_ALL}")
            break


ConnectToServer()

server_thread = threading.Thread(target=handle_server)
server_thread.daemon = True  
server_thread.start()

# if not isConnected:
#     quit()

while True:
    message = input(f"Connected to: {Fore.CYAN}{peer_ip}:{peer_port}{Style.RESET_ALL}  ")
    # if message.lower() == 'exit':
    #     break
    client_socket.sendall(message.encode('utf-8'))
    print(f"Sent: {Fore.MAGENTA}{message}{Style.RESET_ALL}")
    time.sleep(0.01)