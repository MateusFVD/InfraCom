import socket
import threading
from rdt_protocol import RDT3_0_Sender, RDT3_0_Receiver
from datetime import datetime

# dicionario para guarda a lista de usuarios
clients = {} 

# dicionário para guardar o estado RDT de cada cliente: {(ip, port): expected_seq_num}
client_rdt_state = {}

client_senders = {}

# proteger o acesso ao dicionário, evitar mais de uma thread mexendo ao mesmo tempo
clients_lock = threading.Lock() 


HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

# BUFFER_SIZE = 1023  # Reservando apenas 1 byte para o número de sequência

# criando o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# vinculando o servidor ao endereço especificado
server_socket.bind(SERVER_ADDRESS)

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")
print("Aguardando um cliente se conectar...")

def handle_message(packet, address, sock):

    # pega o próximo número de sequência esperado para este endereço.

    with clients_lock:
        expected_seq = client_rdt_state.get(address, 0)
    
    receiver_tool = RDT3_0_Receiver(sock) # usamos a classe como uma ferramenta sem estado aqui

    received_seq = receiver_tool.extract_seq(packet)
    # o pacote recebido tem a sequência que estávamos esperando para este cliente?
    if received_seq == expected_seq:
        message_bytes = receiver_tool.extract_data(packet)
        message = message_bytes.decode()
        
        # envia o ACK correto
        ack_packet = receiver_tool.make_pkt(expected_seq, b'')
        sock.sendto(ack_packet, address)
        
        # ATUALIZA A MEMÓRIA: Agora vamos esperar o próximo número de sequência
        with clients_lock:
            client_rdt_state[address] = 1 - expected_seq
        
        process_client_message(message, address, sock)

    else: # se o pacote for duplicado ou fora de ordem
        ack_to_resend = 1 - expected_seq
        ack_packet = receiver_tool.make_pkt(ack_to_resend, b'')
        sock.sendto(ack_packet, address)
        print(f"Pacote fora de ordem de {address} (seq={received_seq}, esperava={expected_seq}). Reenviando ACK {ack_to_resend}.")

        
def process_client_message(message, address, sock):        
    if "hi, meu nome eh " in message:
        username = message.split("hi, meu nome eh ")[1].strip()
        
        with clients_lock:
            if username in [name for name, addr in clients.values()]:
                error_message = "ERRO: Nome de usuário já existe. Tente outro."
                temp_sender = RDT3_0_Sender(sock, address)
                temp_sender.rdt_send(error_message.encode())
                return 
            

            clients[address] = (username, address)
            # client_rdt_state[address] = 0

            client_senders[address] = RDT3_0_Sender(sock, address)

            print(f"Usuário '{username}' conectado de {address}")

        # Formata corretamente a mensagem de entrada
        broadcast_message(f"SERVER_INFO:{username} entrou na sala.", sock, origin_address=address)

    elif "bye" in message:
        with clients_lock:
            if address in clients:
                username, _ = clients[address]
                del clients[address]
                
                # limpa o estado RDT do cliente que saiu
                if address in client_rdt_state:
                    del client_rdt_state[address]
                if address in client_senders:
                    del client_senders[address]
                    
                broadcast_message(f"SERVER_INFO:{username} saiu da sala.", sock)
                print(f"Usuário '{username}' desconectado")

    else:
        sender_username = None
        with clients_lock:
            if address in clients:
                sender_username, _ = clients[address]
        
        if sender_username:
            # formata a mensagem 
            timestamp = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            formatted_message = f"{address[0]}:{address[1]}/~{sender_username}: {message} {timestamp}"
            
            print(f"Retransmitindo mensagem de {sender_username}")
            # envia a mensagem para todos, exceto o remetente original 
            broadcast_message(formatted_message, sock, origin_address=address)
            
# envia uma mensagem para todos os clientes conectados
def broadcast_message(message, sock, origin_address=None):
    with clients_lock:
        clients_copy = clients.copy()
        # Prepara a mensagem uma única vez
        message_bytes = message.encode()
        
        for address, (username, _) in clients_copy.items():
            if address == origin_address:
                continue
            
            try:
                # Usa a instância de Sender persistente do cliente
                sender = client_senders.get(address)
                if sender:
                    print(f"Enviando broadcast para {username}@{address}")
                    sender.rdt_send(message_bytes)
                else:
                    print(f"ERRO: Não foi encontrado um sender RDT para {username}@{address}")
            except Exception as e:
                print(f"Erro ao enviar broadcast para {username}: {e}")

while True:
    
    try:

        # pegar os dados e o endereço de quem enviou
        raw_packet, client_address = server_socket.recvfrom(1024)
        threading.Thread(target=handle_message, args=(raw_packet, client_address, server_socket), daemon=True).start()
        # usando uma thread para liberar o loop principal para receber a próxima mensagem imediatamente
        # handle_message(raw_packet, client_address, server_socket)
    
    except Exception as e:
        print(f"Erro no loop principal: {e}")

