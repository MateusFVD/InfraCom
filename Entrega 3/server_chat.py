import socket
import threading
from rdt_protocol import RDT3_0_Sender, RDT3_0_Receiver
from datetime import datetime

# dicionario para guarda a lista de usuarios
clients = {} 

# dicionário para guardar o estado RDT de cada cliente: {(ip, port): expected_seq_num}
client_rdt_state = {}

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

    expected_seq = client_rdt_state.get(address, 0)
    
    receiver_tool = RDT3_0_Receiver(sock) # usamos a classe como uma ferramenta sem estado aqui

    # o pacote recebido tem a sequência que estávamos esperando para este cliente?
    if receiver_tool.has_seq(packet, expected_seq):
        # se sim, processa o pacote
        message_bytes = receiver_tool.extract_data(packet)
        message = message_bytes.decode()
        
        # envia o ACK correto
        ack_packet = receiver_tool.make_pkt(expected_seq, b'')
        sock.sendto(ack_packet, address)
        
        # ATUALIZA A MEMÓRIA: Agora vamos esperar o próximo número de sequência
        client_rdt_state[address] = 1 - expected_seq
        
    else: # se o pacote for duplicado ou fora de ordem
        # descobre qual era o ACK anterior
        wrong_seq = receiver_tool.extract_seq(packet)
        ack_to_resend = 1 - expected_seq
        # reenvia o último ACK correto para ajudar o cliente a se resincronizar
        ack_packet = receiver_tool.make_pkt(ack_to_resend, b'')
        sock.sendto(ack_packet, address)
        print(f"Recebido pacote fora de ordem de {address} (seq={wrong_seq}, esperava={expected_seq}). Reenviando ACK {ack_to_resend}.")
        return # para de processar esta mensagem duplicada

    if "hi, meu nome eh " in message:

        # extrai o nome do user
        username = message.split("hi, meu nome eh ")[1].strip()

        # bloqueia o dicionario
        with clients_lock:

            # verificando se o nome já está em uso
            if username in clients:

                print(f"Tentativa de conexão com nome duplicado: {username}")
                error_message = "ERRO: Nome de usuário já existe. Tente outro."

                sender = RDT3_0_Sender(sock, address)
                sender.rdt_send(error_message.encode())
                return 
            
            clients[username] = address
            print(f"Usuário '{username}' conectado de {address}")

        broadcast_message(f"SERVER_INFO:{username} entrou na sala.", sock, origin_address=address) # O 'origin_address' evita que a mensagem seja enviada de volta para quem acabou de entrar


    else:

        send_username = None

        with clients_lock:
            # Procura no dicionário qual usuário tem o endereço do remetente
            for name, addr in clients.items():
                if addr == address:
                    sender_username = name
                    break
        
        if send_username:

            timestamp = datetime.now().strftime("%H:%M:%S %d/%m/%Y") # pegando data e hora formatada
            formatted_message = f"{address[0]}:{address[1]}/~{sender_username}: {message} {timestamp}"

            print(f"Retransmitindo mensagem de {sender_username}")
            broadcast_message(formatted_message, sock, origin_address=address)


# envia uma mensagem para todos os clientes conectados
def broadcast_message(message, sock, origin_address=None):

    with clients_lock:
        for username, address in clients.copy().items():

            if address == origin_address:
                continue

            try:

                sender = RDT3_0_Sender(sock, address)
                sender.rdt_send(message.encode())

                print(f"Enviando broadcast para {username}@{address}")

            except Exception as e:
                print(f"Erro ao enviar broadcast para {username}: {e}")

while True:
    
    try:

        # pegar os dados e o endereço de quem enviou
        raw_packet, client_address = server_socket.recvfrom(1024)

        # usando uma thread para liberar o loop principal para receber a próxima mensagem imediatamente
        handle_message(raw_packet, client_address, server_socket)
    
    except Exception as e:
        print(f"Erro no loop principal: {e}")



