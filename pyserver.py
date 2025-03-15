# Python / Unity Communication Logic:

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

def SignalServer():
    print("Signaling Server session to Unity.")
    sock.SendData('Set session as server.')

isRunning = True

thread = threading.Thread(target=ReceiveDataContinuous)
thread.start()

SignalServer()

# Server:

import socket
import configparser

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

# Initialization

colorama_init()

config = configparser.ConfigParser()
config.read('config.ini')

verbose = config.getboolean("Logging", "verbose")

hasPrintedNoConnections = False

if verbose:
    print(f"{Fore.CYAN}Verbose logging enabled.{Style.RESET_ALL}")

# Initialization: Server IP, Port

server_ip = config['Server'].get('server_address')
server_port = int(config['Server'].get('server_port'))

if not server_ip or not server_port:
    input(f"{Fore.RED}Invalid server IP or Port. Verify config.INI{Style.RESET_ALL}")
    exit()

print(f"Server address: {server_ip}")
print(f"Server port: {server_port}")

# Initialization: Server Socket, Clients Object, Communication Mode

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected_clients = []
connected_clients_status = connected_clients.copy()

communicationMode = config['Server'].get('communication_mode')

# Initialization: Security (Whitelist)

whitelist_enabled = config.getboolean("Security", "whitelist")
whitelisted_addresses = config.get("Security", "whitelisted_addresses").split(", ")
whitelisted_addresses = [ip.strip() for ip in whitelisted_addresses]

if whitelist_enabled:
    print(f"{Fore.CYAN}Whitelist is enabled!{Style.RESET_ALL}")
    print(f"Whitelisted IPs: {Fore.CYAN}{whitelisted_addresses}{Style.RESET_ALL}")
else:
    print(f"Whitelist is {Fore.LIGHTRED_EX}disabled!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Using a whitelist is strongly recommended. Running without one poses a significant security risk!{Style.RESET_ALL}")

print(f"{Fore.LIGHTBLUE_EX}Acting as Server!{Style.RESET_ALL}") # Successfully Initialized!

# Event Loop

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            decodedData = data.decode('utf-8')
            print(f"Received: {Fore.MAGENTA}{decodedData}{Style.RESET_ALL}")            
        except Exception as e:
            print(f"{Fore.RED}{e}{Style.RESET_ALL}")
            break

    client_socket.close()

def start_server():
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    print(f"Server listening on {Fore.CYAN}{server_ip}:{server_port}{Style.RESET_ALL}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_ip = client_address[0]
        if not client_ip in whitelisted_addresses:
            print(f"{Fore.YELLOW}IP: {client_address} is not in the whitelist. Terminating connection.{Style.RESET_ALL}")
            client_socket.close()
        else:
            print(f"Client: {Fore.CYAN}{client_address}{Style.RESET_ALL} is now connected to server.")
            connected_clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

server_thread = threading.Thread(target=start_server)
server_thread.start()

def sendToClients(message):
    for client in connected_clients:    
        try:
             client.send(message.encode('utf-8'))
             print(f"Sent: {Fore.MAGENTA}{message}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Exception: {e}{Style.RESET_ALL}")

if communicationMode == 'MANUAL':
    print(f"{Fore.LIGHTRED_EX}MANUAL communication mode is ON. You can bypass the event loop and send packets directly.{Style.RESET_ALL}")

print("===============================")

while True:
    if connected_clients_status != connected_clients:
        print(f"Updated clients list: {connected_clients}")
        connected_clients_status = connected_clients.copy()
        print("===============================")

    if communicationMode == 'MANUAL':
        message = input(f"Send a message to every client:{Fore.LIGHTBLACK_EX}  ")
        sendToClients(message)
    if not connected_clients and not hasPrintedNoConnections:
        print(f"{Fore.YELLOW}No clients are currently connected.{Style.RESET_ALL}")
        hasPrintedNoConnections = True
    # time.sleep(5)
    # sendToClients("Set Player1 GameObject Position to: 100, 100, 100")
    time.sleep(0.01)