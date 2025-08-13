# modulo: server_chat.py
# implementa o lado do servidor do chat de sala unica.

import socket
import datetime
from threading import Thread
from rdt_protocol import send_data, receive_data

# --- configuracao do servidor ---
HOST = "localhost"
MAIN_PORT = 12000
BUFFER_SIZE = 1024

# --- estruturas de dados para gerenciamento de estado ---
ACTIVE_USERS = {}       # {username: {"addr": (ip, port), "seq_num": int}}
FRIEND_LISTS = {}     # {user1: {friend1, friend2}, user2: {friend3}}
BAN_VOTES = {}        # {target_user: {"voters": {user1, user2}, "required": int}}

# --- funcoes auxiliares ---
def get_user_by_address(address):
    """encontra um nome de usuario com base em seu endereco."""
    for user, data in ACTIVE_USERS.items():
        if data["addr"] == address:
            return user
    return None

def send_response(sock, message, client_address):
    """envia uma resposta para um cliente especifico."""
    response_addr = (client_address[0], client_address[1] + 1)
    send_data(sock, message, response_addr, {'num': 0})

def broadcast_message(sock, message, sender_name=None):
    """envia uma mensagem para todos os usuarios conectados."""
    server_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    
    for user, data in ACTIVE_USERS.items():
        # se um remetente e especificado, nao envia de volta para ele
        if sender_name and sender_name == user:
            continue

        # personaliza a mensagem se for de um amigo
        final_message = message
        if sender_name and sender_name in FRIEND_LISTS.get(user, set()):
            # adiciona a tag [amigo] conforme requisito
            parts = message.split(":", 2)
            final_message = f"{parts[0]}:[ amigo ] {parts[1]}: {parts[2]}"
        
        send_response(sock, final_message, data["addr"])

# --- logica de tratamento de comandos ---
def handle_connect(sock, command_parts, client_address):
    username = " ".join(command_parts[4:])
    if username in ACTIVE_USERS:
        send_response(sock, f"erro: nome de usuario '{username}' ja esta em uso.", client_address)
    else:
        ACTIVE_USERS[username] = {"addr": client_address, "seq_num": 1}
        FRIEND_LISTS[username] = set()
        send_response(sock, f"conexao aceita: {username}", client_address)
        broadcast_message(sock, f"servidor: {username} entrou na sala.", sender_name=username)

def handle_disconnect(sock, username, client_address):
    if username in ACTIVE_USERS:
        del ACTIVE_USERS[username]
        # limpa listas de amigos que continham o usuario
        for user in FRIEND_LISTS:
            FRIEND_LISTS[user].discard(username)
        send_response(sock, "voce foi desconectado.", client_address)
        broadcast_message(sock, f"servidor: {username} saiu da sala.")

def handle_list_users(sock, client_address):
    user_list = "usuarios conectados:\n" + "\n".join(f"- {user}" for user in ACTIVE_USERS)
    send_response(sock, user_list, client_address)

def handle_list_friends(sock, username, client_address):
    friends = FRIEND_LISTS.get(username, set())
    if not friends:
        send_response(sock, "voce nao tem amigos na sua lista.", client_address)
    else:
        friend_list = "sua lista de amigos:\n" + "\n".join(f"- {friend}" for friend in friends)
        send_response(sock, friend_list, client_address)

def handle_add_friend(sock, username, args, client_address):
    friend_to_add = args[0]
    if friend_to_add not in ACTIVE_USERS:
        send_response(sock, f"erro: usuario '{friend_to_add}' nao encontrado ou offline.", client_address)
    elif friend_to_add == username:
        send_response(sock, "erro: voce nao pode adicionar a si mesmo.", client_address)
    else:
        FRIEND_LISTS[username].add(friend_to_add)
        send_response(sock, f"voce adicionou '{friend_to_add}' a sua lista de amigos.", client_address)

def handle_remove_friend(sock, username, args, client_address):
    friend_to_remove = args[0]
    if friend_to_remove in FRIEND_LISTS.get(username, set()):
        FRIEND_LISTS[username].remove(friend_to_remove)
        send_response(sock, f"voce removeu '{friend_to_remove}' da sua lista de amigos.", client_address)
    else:
        send_response(sock, f"erro: '{friend_to_remove}' nao esta na sua lista de amigos.", client_address)

def handle_ban(sock, voter, args, client_address):
    target_user = args[0]
    if target_user not in ACTIVE_USERS:
        send_response(sock, f"erro: usuario '{target_user}' nao esta na sala.", client_address)
        return
    
    required_votes = (len(ACTIVE_USERS) // 2) + 1

    # inicia uma nova votacao se nao existir
    if target_user not in BAN_VOTES:
        BAN_VOTES[target_user] = {"voters": set(), "required": required_votes}
    
    # adiciona voto
    BAN_VOTES[target_user]["voters"].add(voter)
    current_votes = len(BAN_VOTES[target_user]["voters"])

    # notifica a todos sobre o status da votacao
    broadcast_message(sock, f"servidor: votacao para banir [{target_user}] - votos: {current_votes}/{required_votes}.")

    # verifica se o banimento foi atingido
    if current_votes >= required_votes:
        broadcast_message(sock, f"servidor: [{target_user}] foi banido da sala por votacao.")
        target_address = ACTIVE_USERS[target_user]["addr"]
        handle_disconnect(sock, target_user, target_address)
        del BAN_VOTES[target_user]

def handle_chat_message(sock, username, message, client_address):
    user_ip, user_port = client_address
    server_time = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    # formato: <IP>:<PORTA>/~<nome_usuario>: <mensagem> <hora-data>
    formatted_message = f"{user_ip}:{user_port}/~{username}: {message} {server_time}"
    broadcast_message(sock, formatted_message, sender_name=username)

# --- thread de tratamento de cliente ---
def handle_client_request(data, client_address, thread_port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as thread_socket:
        thread_socket.bind((HOST, thread_port))

        username = get_user_by_address(client_address)
        expected_seq_num = ACTIVE_USERS.get(username, {}).get("seq_num", 0)
        
        raw_command = receive_data(thread_socket, data, client_address, {'num': expected_seq_num})
        if not raw_command:
            return

        if username in ACTIVE_USERS:
            ACTIVE_USERS[username]["seq_num"] = 1 - expected_seq_num

        command_str = raw_command.decode('utf-8')
        parts = command_str.split(' ')
        command = parts[0].lower()

        # tratamento de comandos
        if command_str.lower().startswith("hi, meu nome eh"):
            handle_connect(thread_socket, parts, client_address)
        elif not username:
            send_response(thread_socket, "erro: comando invalido. conecte-se primeiro.", client_address)
        elif command == "bye":
            handle_disconnect(thread_socket, username, client_address)
        elif command == "list":
            handle_list_users(thread_socket, client_address)
        elif command == "mylist":
            handle_list_friends(thread_socket, username, client_address)
        elif command == "addtomylist" and len(parts) > 1:
            handle_add_friend(thread_socket, username, parts[1:], client_address)
        elif command == "rmvfrommylist" and len(parts) > 1:
            handle_remove_friend(thread_socket, username, parts[1:], client_address)
        elif command == "ban" and len(parts) > 1:
            handle_ban(thread_socket, username, parts[1:], client_address)
        else:
            # se nao for um comando, e uma mensagem de chat
            handle_chat_message(thread_socket, username, command_str, client_address)

def start_server():
    """cria o socket principal do servidor e entra no loop de escuta."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as main_socket:
        main_socket.bind((HOST, MAIN_PORT))
        print(f"servidor de chat iniciado em {HOST}:{MAIN_PORT}. aguardando conexoes...")
        
        thread_port_counter = 0
        while True:
            try:
                data, client_address = main_socket.recvfrom(BUFFER_SIZE)
                thread_port_counter += 1
                new_thread_port = MAIN_PORT + thread_port_counter
                
                client_thread = Thread(target=handle_client_request, args=(data, client_address, new_thread_port), daemon=True)
                client_thread.start()
            except KeyboardInterrupt:
                print("\nservidor esta desligando.")
                break

if __name__ == "__main__":
    start_server()