# Module: server_chat.py
# Implements the server side of the chat system.

import socket
import datetime
from threading import Thread
from rdt_protocol import send_data, receive_data

# --- Server Configuration ---
HOST = "localhost"
MAIN_PORT = 12000
BUFFER_SIZE = 1024

# --- Data Structures for State Management ---
USER_REGISTRY = {}      # {username: (address, port)}
ACTIVE_SESSIONS = {}    # {username: {"expected_seq_num": int}}
FOLLOW_LISTS = {}       # {username: {set_of_followed_users}}
CHAT_GROUPS = {}        # {group_key: {"name": str, "owner": str, "members": {username: (addr,port)}}}

# --- Helper Functions ---
def get_user_by_address(address):
    """Finds a username based on their socket address."""
    return next((user for user, addr in USER_REGISTRY.items() if addr == address), None)

def group_key_exists(group_key):
    """Checks if a group key is already in use."""
    return group_key in CHAT_GROUPS

def get_group_id_by_name(group_name, username):
    """Finds a group's ID by its name, if the user is a member."""
    for group_id, group_info in CHAT_GROUPS.items():
        if group_info["name"] == group_name and username in group_info["members"]:
            return group_id
    return None

def send_response(sock, message, client_address):
    """Helper to send a response message back to the client."""
    response_addr = (client_address[0], client_address[1] + 1)
    send_data(sock, message, response_addr, {'num': 0})

# --- Command Handling Logic ---

def handle_login(sock, args, client_address):
    username = args[0]
    if username in ACTIVE_SESSIONS:
        send_response(sock, "Error: This username is already in use.", client_address)
    else:
        USER_REGISTRY[username] = client_address
        ACTIVE_SESSIONS[username] = {"expected_seq_num": 1}
        if username not in FOLLOW_LISTS:
            FOLLOW_LISTS[username] = set()
        send_response(sock, f"Login successful! Welcome, {username}.", client_address)

def handle_logout(sock, args, client_address):
    username = get_user_by_address(client_address)
    if username and username in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[username]
        send_response(sock, f"Logout successful. Goodbye, {username}.", client_address)
    else:
        send_response(sock, "Error: You are not logged in.", client_address)

def handle_follow(sock, args, client_address):
    requester = get_user_by_address(client_address)
    target = args[0]
    if target not in USER_REGISTRY:
        send_response(sock, f"Error: User [{target}] not found.", client_address)
    elif target in FOLLOW_LISTS.get(requester, set()):
        send_response(sock, f"You are already following user [{target}].", client_address)
    else:
        FOLLOW_LISTS[requester].add(target)
        send_response(sock, f"You are now following [{target}].", client_address)
        if target in ACTIVE_SESSIONS:
            target_addr = USER_REGISTRY[target]
            send_response(sock, f"Notification: [{requester}] has started following you.", target_addr)

def handle_unfollow(sock, args, client_address):
    requester = get_user_by_address(client_address)
    target = args[0]
    if target in FOLLOW_LISTS.get(requester, set()):
        FOLLOW_LISTS[requester].remove(target)
        send_response(sock, f"You have unfollowed [{target}].", client_address)
        if target in ACTIVE_SESSIONS:
            target_addr = USER_REGISTRY[target]
            send_response(sock, f"Notification: [{requester}] has unfollowed you.", target_addr)
    else:
        send_response(sock, f"You are not following user [{target}].", client_address)

def handle_create_group(sock, args, client_address):
    username = get_user_by_address(client_address)
    group_name, group_key = args[0], args[1]
    if group_key_exists(group_key):
        send_response(sock, f"Error: The group key [{group_key}] already exists.", client_address)
    else:
        CHAT_GROUPS[group_key] = {
            "name": group_name,
            "owner": username,
            "members": {username: client_address},
            "created_at": datetime.datetime.now()
        }
        send_response(sock, f"Group [{group_name}] created successfully!", client_address)

def handle_join_group(sock, args, client_address):
    username = get_user_by_address(client_address)
    group_name, group_key = args[0], args[1]
    group = CHAT_GROUPS.get(group_key)
    if group and group["name"] == group_name:
        if username in group["members"]:
             send_response(sock, f"You are already a member of group [{group_name}].", client_address)
             return
        group["members"][username] = client_address
        send_response(sock, f"You have joined the group [{group_name}].", client_address)
        # Notify other members
        for member, addr in group["members"].items():
            if member != username:
                send_response(sock, f"Notification: [{username}] has joined the group [{group_name}].", addr)
    else:
        send_response(sock, "Error: Invalid group name or key.", client_address)

def handle_leave_group(sock, args, client_address):
    username = get_user_by_address(client_address)
    group_name = args[0]
    group_id = get_group_id_by_name(group_name, username)
    if group_id:
        # Notify other members before removing the user
        for member, addr in CHAT_GROUPS[group_id]["members"].items():
            if member != username:
                send_response(sock, f"Notification: [{username}] has left the group [{group_name}].", addr)
        del CHAT_GROUPS[group_id]["members"][username]
        send_response(sock, f"You have left the group [{group_name}].", client_address)
    else:
        send_response(sock, f"Error: You are not in a group named [{group_name}].", client_address)

def handle_delete_group(sock, args, client_address):
    owner = get_user_by_address(client_address)
    group_name = args[0]
    group_id = get_group_id_by_name(group_name, owner)
    if group_id and CHAT_GROUPS[group_id]["owner"] == owner:
        members = CHAT_GROUPS[group_id]["members"].copy()
        del CHAT_GROUPS[group_id]
        send_response(sock, f"Group [{group_name}] was successfully deleted.", client_address)
        # Notify all former members
        for member, addr in members.items():
            if member != owner:
                send_response(sock, f"Notification: The group [{group_name}] has been deleted by its owner.", addr)
    elif not group_id:
        send_response(sock, f"Error: Group [{group_name}] not found.", client_address)
    else:
        send_response(sock, f"Error: You are not the owner of group [{group_name}].", client_address)


def handle_ban_user(sock, args, client_address):
    owner = get_user_by_address(client_address)
    user_to_ban, group_name = args[0], args[1]
    group_id = get_group_id_by_name(group_name, owner)
    if not group_id:
        send_response(sock, f"Error: You are not in group [{group_name}].", client_address)
        return
    
    group = CHAT_GROUPS[group_id]
    if group["owner"] != owner:
        send_response(sock, f"Error: You are not the owner of group [{group_name}].", client_address)
    elif user_to_ban not in group["members"]:
        send_response(sock, f"Error: User [{user_to_ban}] is not in group [{group_name}].", client_address)
    else:
        banned_user_addr = group["members"][user_to_ban]
        del group["members"][user_to_ban]
        send_response(sock, f"You have been banned from group [{group_name}] by the owner.", banned_user_addr)
        for member, addr in group["members"].items():
            send_response(sock, f"Notification: [{user_to_ban}] was banned from group [{group_name}].", addr)
        send_response(sock, f"User [{user_to_ban}] was successfully banned from [{group_name}].", client_address)


def handle_list_online_users(sock, args, client_address):
    if not ACTIVE_SESSIONS:
        send_response(sock, "No users are currently online.", client_address)
        return
    user_list = "Online Users:\n" + "\n".join(f"- {user}" for user in ACTIVE_SESSIONS)
    send_response(sock, user_list, client_address)

def handle_list_friends(sock, args, client_address):
    username = get_user_by_address(client_address)
    followed_list = FOLLOW_LISTS.get(username, set())
    if not followed_list:
        send_response(sock, "You are not following anyone.", client_address)
        return
    friend_list = "Followed Users:\n" + "\n".join(f"- {user}" for user in followed_list)
    send_response(sock, friend_list, client_address)

def handle_list_my_groups(sock, args, client_address):
    owner = get_user_by_address(client_address)
    owned_groups = [f"- {g['name']} (Key: {gid})" for gid, g in CHAT_GROUPS.items() if g['owner'] == owner]
    if not owned_groups:
        send_response(sock, "You have not created any groups.", client_address)
        return
    response = "Groups You Own:\n" + "\n".join(owned_groups)
    send_response(sock, response, client_address)

def handle_list_groups(sock, args, client_address):
    user = get_user_by_address(client_address)
    member_of_groups = [f"- {g['name']} (Owner: {g['owner']})" for gid, g in CHAT_GROUPS.items() if user in g['members']]
    if not member_of_groups:
        send_response(sock, "You are not a member of any groups.", client_address)
        return
    response = "Groups You Are In:\n" + "\n".join(member_of_groups)
    send_response(sock, response, client_address)


def handle_friend_chat(sock, args, client_address):
    sender = get_user_by_address(client_address)
    recipient, message = args[0], args[1]
    if recipient not in USER_REGISTRY:
        send_response(sock, f"Error: User [{recipient}] does not exist.", client_address)
    elif recipient not in FOLLOW_LISTS.get(sender, set()):
        send_response(sock, f"Error: [{recipient}] is not on your followed list.", client_address)
    elif recipient in ACTIVE_SESSIONS:
        recipient_addr = USER_REGISTRY[recipient]
        formatted_msg = f"(Private) {sender}: {message}"
        send_response(sock, formatted_msg, recipient_addr)
        send_response(sock, "Private message sent.", client_address)
    else:
        send_response(sock, f"Error: User [{recipient}] is offline.", client_address)

def handle_group_chat(sock, args, client_address):
    sender = get_user_by_address(client_address)
    group_name, group_key, message = args[0], args[1], args[2]
    group = CHAT_GROUPS.get(group_key)
    if group and group["name"] == group_name and sender in group["members"]:
        formatted_msg = f"({group_name}) {sender}: {message}"
        for member, addr in group["members"].items():
            if member != sender:
                send_response(sock, formatted_msg, addr)
        send_response(sock, "Message sent to the group.", client_address)
    else:
        send_response(sock, "Error: You are not a member of this group or the key is incorrect.", client_address)

# Maps command strings to handler functions
COMMAND_DISPATCHER = {
    'login': handle_login,
    'logout': handle_logout,
    'follow': handle_follow,
    'unfollow': handle_unfollow,
    'create_group': handle_create_group,
    'delete_group': handle_delete_group,
    'join': handle_join_group,
    'leave': handle_leave_group,
    'ban': handle_ban_user,
    'chat_friend': handle_friend_chat,
    'chat_group': handle_group_chat,
    'list:cinners': handle_list_online_users,
    'list:friends': handle_list_friends,
    'list:mygroups': handle_list_my_groups,
    'list:groups': handle_list_groups,
}

def handle_client_request(data, client_address, thread_port):
    """Function executed by a thread for each received request."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as thread_socket:
        thread_socket.bind((HOST, thread_port))

        user = get_user_by_address(client_address)
        expected_seq_num_tracker = {'num': ACTIVE_SESSIONS.get(user, {}).get("expected_seq_num", 0)}

        raw_command = receive_data(thread_socket, data, client_address, expected_seq_num_tracker)
        if not raw_command:
            return

        if user in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[user]["expected_seq_num"] = expected_seq_num_tracker['num']

        command_str = raw_command.decode('utf-8')
        parts = command_str.split(' ')
        command_name = parts[0]
        
        args = []
        if command_name == "chat_group" and len(parts) >= 4:
            args = [parts[1], parts[2], " ".join(parts[3:])]
        elif command_name == "chat_friend" and len(parts) >= 3:
            args = [parts[1], " ".join(parts[2:])]
        else:
            args = parts[1:]
        
        handler = COMMAND_DISPATCHER.get(command_name)
        if handler:
            handler(thread_socket, args, client_address)
        else:
            send_response(sock, f"Error: Unknown command '{command_name}'.", client_address)

def start_server():
    """Creates the main server socket and enters the listening loop."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as main_socket:
        main_socket.bind((HOST, MAIN_PORT))
        print(f"Chat server started at {HOST}:{MAIN_PORT}. Waiting for connections...")
        
        thread_port_counter = 0
        while True:
            try:
                data, client_address = main_socket.recvfrom(BUFFER_SIZE)
                thread_port_counter += 1
                new_thread_port = MAIN_PORT + thread_port_counter
                
                client_thread = Thread(target=handle_client_request, args=(data, client_address, new_thread_port))
                client_thread.start()
            except KeyboardInterrupt:
                print("\nServer is shutting down.")
                break

if __name__ == "__main__":
    start_server()