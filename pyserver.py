import time
import threading

import socket
import configparser

import logging

# Initialization (shared)

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

import UDPComms as U

colorama_init()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.debug(f"Logger active with level: {logging.getLevelName(logger.level)}")

config = configparser.ConfigParser()
config.read('config.ini')

verbose = config.getboolean("Logging", "verbose")

hasPrintedNoConnections = False

if verbose:
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
    logger.debug(f"{Fore.CYAN}Verbose [DEBUG] logging enabled. Detailed messages will now be shown.{Style.RESET_ALL}")

# Python / Unity Communication Logic:

isRunning = False

sock = U.UDPComms(udpIP="127.0.0.1", portTX=8000, portRX=8001, enableRX=True, suppressWarnings=False)

def ReceiveDataContinuous():
    while True:
        received_data = sock.ReadReceivedData()
        if received_data:
            print(f"Received: {received_data}")
            handle_udp_data(received_data)
        time.sleep(0.01)

def SignalServer():
    logger.debug("Signaling Server session to Unity.")
    sock.SendData('Set session as server.')

isRunning = True

thread = threading.Thread(target=ReceiveDataContinuous)
thread.start()

SignalServer()

# Server:

# Initialization: Server IP, Port

server_ip = config['Server'].get('server_address')
server_port = int(config['Server'].get('server_port'))

if not server_ip or not server_port:
    input(f"{Fore.RED}Invalid server IP or Port. Verify config.INI{Style.RESET_ALL}")
    exit()

logger.info(f"Server address: {Fore.CYAN}{server_ip}{Style.RESET_ALL}")
logger.info(f"Server port: {Fore.CYAN}{server_port}{Style.RESET_ALL}")

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
    logger.info(f"{Fore.CYAN}Whitelist is enabled!{Style.RESET_ALL}")
    logger.debug(f"Whitelisted IPs: {Fore.CYAN}{whitelisted_addresses}{Style.RESET_ALL}")
else:
    logger.info(f"Whitelist is {Fore.LIGHTRED_EX}disabled!{Style.RESET_ALL}")
    logger.warning(f"{Fore.YELLOW}Using a whitelist is strongly recommended. Running without one poses a significant security risk!{Style.RESET_ALL}")

logger.info(f"{Fore.LIGHTBLUE_EX}Acting as Server!{Style.RESET_ALL}") # Successfully Initialized!

# Event Loop

def start_server():
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)
    logger.info(f"Server listening on {Fore.CYAN}{server_ip}:{server_port}{Style.RESET_ALL}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_ip = client_address[0]
        if not client_ip in whitelisted_addresses:
            logger.warning(f"{Fore.YELLOW}IP: {client_address} is not in the whitelist. Terminating connection.{Style.RESET_ALL}")
            client_socket.close()
        else:
            logger.info(f"Client: {Fore.CYAN}{client_address}{Style.RESET_ALL} is now connected to server.")
            connected_clients.append(client_socket)
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

server_thread = threading.Thread(target=start_server)
server_thread.start()

def handle_udp_data(data):
    opcode = data[:4]
    logger.debug(f"Decoded opcode: {opcode}")
    if opcode == "0002":
        # Host position moved
        position = data[5:]
        logger.info(f"Set Host Position: {position}")
        sendToClients(f"0004:{position}")
        sock.SendData(f"0004:{position}")

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            decodedData = data.decode('utf-8') 
            logger.info(f"Received: {Fore.MAGENTA}{decodedData}{Style.RESET_ALL}")        
        except Exception as e:
            logger.error(f"{Fore.RED}{e}{Style.RESET_ALL}")
            break

    client_socket.close()

def sendToClients(message):
    for client in connected_clients:    
        try:
             client.send(message.encode('utf-8'))
             logger.info(f"Sent: {Fore.MAGENTA}{message}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}Exception: {e}{Style.RESET_ALL}")

if communicationMode == 'MANUAL':
    logger.info(f"{Fore.LIGHTRED_EX}MANUAL communication mode is ON. You can bypass the event loop and send packets directly.{Style.RESET_ALL}")

print("===============================")

if communicationMode == 'MANUAL':
    while True:
        if connected_clients_status != connected_clients:
            logger.debug(f"Updated clients list: {connected_clients}")
            connected_clients_status = connected_clients.copy()
            print("===============================")

        if communicationMode == 'MANUAL':
            message = input(f"Send a message to every client:{Fore.LIGHTBLACK_EX}  ")
            sendToClients(message)
        if not connected_clients and not hasPrintedNoConnections:
            logger.warning(f"{Fore.YELLOW}No clients are currently connected.{Style.RESET_ALL}")
            hasPrintedNoConnections = True
        time.sleep(0.01)