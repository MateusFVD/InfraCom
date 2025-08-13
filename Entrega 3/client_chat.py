import socket
from threading import Thread, Event
from colorama import Fore, Style, init
from rdt_protocol import send_data, receive_data

# inicializa o colorama
init(autoreset=True)

# configuracao do cliente
SERVER_HOST = "localhost"
SERVER_PORT = 5000
BUFFER_SIZE = 1024

# estado do cliente
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind((SERVER_HOST, 0))
client_socket.settimeout(5.0)

CURRENT_USER = None
RDT_SEQ_TRACKER = {'num': 0}

# evento para sincronizacao
server_response_event = Event()

# thread de recebimento de mensagens
def listen_for_server_messages():
    # thread que aguarda e processa mensagens recebidas do servidor.
    listen_port = client_socket.getsockname()[1] + 1
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listen_socket:
        listen_socket.bind((SERVER_HOST, listen_port))
        
        while True:
            try:
                expected_seq_num_tracker = {'num': 0}
                packet, server_address = listen_socket.recvfrom(BUFFER_SIZE)
                message_bytes = receive_data(listen_socket, packet, server_address, expected_seq_num_tracker)

                if message_bytes:
                    message = message_bytes.decode('utf-8')
                    # limpa a linha anterior e imprime a mensagem
                    print(f"\r{' ' * 80}\r{Fore.LIGHTMAGENTA_EX}<< {message}{Style.RESET_ALL}")
                    
                    global CURRENT_USER
                    if message.startswith("conexao aceita"):
                        CURRENT_USER = message.split(":")[-1].strip()
                        server_response_event.set()
                    elif message.startswith("erro: nome de usuario"):
                        server_response_event.set()
                    elif "voce foi desconectado" in message:
                        CURRENT_USER = None
                        RDT_SEQ_TRACKER['num'] = 0
                        server_response_event.set()

                    print(f"{Fore.CYAN}>> {Style.RESET_ALL}", end='', flush=True)

            except socket.timeout:
                continue
            except Exception:
                continue

#  envio de comandos/mensagens  
def send_to_server(message_str):
    """envia uma mensagem ou comando para o servidor usando rdt."""
    send_data(client_socket, message_str, (SERVER_HOST, SERVER_PORT), RDT_SEQ_TRACKER)

# loop principal do cliente     
def main_loop():
    # loop principal que captura a entrada do usuario e envia para o servidor
    listen_thread = Thread(target=listen_for_server_messages, daemon=True)
    listen_thread.start()
    
    print(Fore.GREEN + "bem-vindo ao chat de infracom!")
    print(Fore.GREEN + "para se conectar, use: " + Fore.YELLOW + "hi, meu nome eh <seu_nome>")
    
    while True:
        try:
            user_input = input(f"{Fore.CYAN}>> {Style.RESET_ALL}")
            if not user_input:
                continue

            parts = user_input.strip().split()
            command = parts[0].lower()

            # verifica se o usuario esta tentando se conectar
            if user_input.lower().startswith("hi, meu nome eh"):
                if CURRENT_USER:
                    print(Fore.YELLOW + f"aviso: voce ja esta conectado como {CURRENT_USER}.")
                    continue
                server_response_event.clear()
                send_to_server(user_input)
                # aguarda confirmacao de login do servidor
                received = server_response_event.wait(timeout=5.0)
                if not received:
                    print(Fore.RED + "o servidor nao respondeu ao pedido de conexao.")
            
            # verifica se o usuario esta logado para outros comandos
            elif not CURRENT_USER:
                print(Fore.RED + "voce precisa se conectar primeiro. use: hi, meu nome eh <seu_nome>")
                continue
            
            # comandos que exigem login
            elif command in ["bye", "list", "mylist", "addtomylist", "rmvfrommylist", "ban"]:
                 send_to_server(user_input)
            
            # se nao for um comando conhecido, e uma mensagem de chat
            else:
                send_to_server(user_input)

        except KeyboardInterrupt:
            if CURRENT_USER:
                send_to_server("bye")
            print("\nsaindo do cliente de chat. adeus!")
            break
        except Exception as e:
            print(Fore.RED + f"ocorreu um erro: {e}")

    client_socket.close()

if __name__ == "__main__":
    main_loop()