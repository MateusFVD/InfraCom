# Module: client_chat.py
# Implements the client side of the chat system.

import socket
from threading import Thread, Event
from colorama import Fore, Style, init
from rdt_protocol import send_data, receive_data

# Initialize colorama
init(autoreset=True)

# --- Client Configuration ---
SERVER_HOST = "localhost"
SERVER_PORT = 12000
BUFFER_SIZE = 1024

# --- Client State ---
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind((SERVER_HOST, 0))
client_socket.settimeout(5.0)

CURRENT_USER = None
RDT_SEQ_TRACKER = {'num': 0}

# Events for thread synchronization
login_success_event = Event()
server_response_event = Event()

# --- Message Receiving Thread ---
def listen_for_server_messages():
    """Thread that waits for and processes messages received from the server."""
    listen_port = client_socket.getsockname()[1] + 1
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
        listen_socket.bind((SERVER_HOST, listen_port))
        
        while True:
            try:
                # *** BUG FIX ***: The sequence number tracker is now reset for each expected response.
                # This aligns the client's receiver logic with the server's stateless sender logic.
                expected_seq_num_tracker = {'num': 0}
                
                packet, server_address = listen_socket.recvfrom(BUFFER_SIZE)
                message_bytes = receive_data(listen_socket, packet, server_address, expected_seq_num_tracker)

                if message_bytes:
                    message = message_bytes.decode('utf-8')
                    # Clear previous line and print message
                    print(f"\r{' ' * 60}\r{Fore.LIGHTMAGENTA_EX}<< {message}{Style.RESET_ALL}")
                    
                    global CURRENT_USER
                    if "Login successful" in message:
                        try:
                            # Safely extract username, removing trailing period.
                            CURRENT_USER = message.split()[-1].replace('.', '')
                        except IndexError: pass
                        login_success_event.set()
                    elif "Logout successful" in message:
                        CURRENT_USER = None
                        RDT_SEQ_TRACKER['num'] = 0
                        server_response_event.set()
                    elif "Error: This username is already in use" in message:
                        RDT_SEQ_TRACKER['num'] = 0
                        login_success_event.set()
                    else:
                        server_response_event.set()

                    print(f"{Fore.CYAN}>> Enter a command: {Style.RESET_ALL}", end='', flush=True)

            except socket.timeout:
                continue # Ignore timeouts and keep listening
            except Exception:
                continue

# --- User Command Functions ---
def send_command_to_server(command_str):
    """Sends a formatted command to the server using RDT."""
    server_response_event.clear()
    send_data(client_socket, command_str, (SERVER_HOST, SERVER_PORT), RDT_SEQ_TRACKER)
    # Wait for the response event, which is set by the listener thread
    received = server_response_event.wait(timeout=5.0)
    if not received:
        print(Fore.RED + "No response from server; request may have timed out.")

def execute_login(args):
    global CURRENT_USER
    if CURRENT_USER:
        print(Fore.YELLOW + f"Warning: You are already logged in as {CURRENT_USER}.")
        return
    if len(args) != 1:
        print(Fore.RED + "Usage: login <username>")
        return
    
    print(Fore.BLUE + "Attempting to log in...")
    login_success_event.clear()
    command_str = f"login {args[0]}"
    send_data(client_socket, command_str, (SERVER_HOST, SERVER_PORT), RDT_SEQ_TRACKER)
    received = login_success_event.wait(timeout=5.0)
    if not received:
        print(Fore.RED + "Login request timed out.")


def execute_logout(args):
    if len(args) != 0:
        print(Fore.RED + "Usage: logout (no arguments)")
        return
    print(Fore.BLUE + "Disconnecting...")
    send_command_to_server("logout")

def execute_follow(args):
    if len(args) != 1:
        print(Fore.RED + "Usage: follow <username>")
        return
    if args[0] == CURRENT_USER:
        print(Fore.RED + "You cannot follow yourself.")
        return
    print(Fore.BLUE + f"Sending request to follow {args[0]}...")
    send_command_to_server(f"follow {args[0]}")

def execute_chat_friend(args):
    if len(args) < 2:
        print(Fore.RED + "Usage: chat_friend <username> <message>")
        return
    recipient = args[0]
    message = " ".join(args[1:])
    print(Fore.BLUE + f"Sending message to {recipient}...")
    send_command_to_server(f"chat_friend {recipient} {message}")

def execute_create_group(args):
    if len(args) != 2:
        print(Fore.RED + "Usage: create_group <group_name> <group_key>")
        return
    print(Fore.BLUE + f"Creating group {args[0]}...")
    send_command_to_server(f"create_group {args[0]} {args[1]}")

def execute_join_group(args):
    if len(args) != 2:
        print(Fore.RED + "Usage: join <group_name> <group_key>")
        return
    print(Fore.BLUE + f"Attempting to join group {args[0]}...")
    send_command_to_server(f"join {args[0]} {args[1]}")

def execute_group_chat(args):
    if len(args) < 3:
        print(Fore.RED + "Usage: chat_group <group_name> <group_key> <message>")
        return
    group_name, group_key = args[0], args[1]
    message = " ".join(args[2:])
    print(Fore.BLUE + f"Sending message to group {group_name}...")
    send_command_to_server(f"chat_group {group_name} {group_key} {message}")

# Maps input commands to functions
CLIENT_COMMAND_HANDLERS = {
    "login": execute_login,
    "logout": execute_logout,
    "follow": execute_follow,
    "unfollow": lambda args: send_command_to_server(f"unfollow {args[0]}"),
    "create_group": execute_create_group,
    "delete_group": lambda args: send_command_to_server(f"delete_group {args[0]}"),
    "join": execute_join_group,
    "leave": lambda args: send_command_to_server(f"leave {args[0]}"),
    "ban": lambda args: send_command_to_server(f"ban {args[0]} {args[1]}"),
    "chat_friend": execute_chat_friend,
    "chat_group": execute_group_chat,
    "list:cinners": lambda args: send_command_to_server("list:cinners"),
    "list:friends": lambda args: send_command_to_server("list:friends"),
    "list:mygroups": lambda args: send_command_to_server("list:mygroups"),
    "list:groups": lambda args: send_command_to_server("list:groups"),
}

def main_loop():
    """Main loop that captures user input and dispatches commands."""
    listen_thread = Thread(target=listen_for_server_messages, daemon=True)
    listen_thread.start()
    
    print(Fore.GREEN + "Welcome to the Chat Client! Use 'login <username>' to start.")
    
    while True:
        try:
            user_input = input(f"{Fore.CYAN}>> Enter a command: {Style.RESET_ALL}")
            parts = user_input.strip().split()
            if not parts:
                continue

            command_name = parts[0]
            args = parts[1:]
            
            if not CURRENT_USER and command_name != 'login':
                print(Fore.RED + "You need to be logged in. Use 'login <username>'.")
                continue

            handler = CLIENT_COMMAND_HANDLERS.get(command_name)
            if handler:
                handler(args)
            else:
                print(Fore.RED + f"Unknown command '{command_name}'.")

        except KeyboardInterrupt:
            print("\nExiting chat client. Goodbye!")
            break
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")

    client_socket.close()

if __name__ == "__main__":
    main_loop()