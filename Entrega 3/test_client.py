import socket
import threading
from rdt_protocol import RDT3_0_Sender, RDT3_0_Receiver
import sys
import time

# Configurações do servidor
HOST = "127.0.0.1"  # IP do servidor
PORT = 5000         # Porta do servidor
SERVER_ADDR = (HOST, PORT)

# --- Função para receber mensagens em uma thread separada ---
def receive_messages():
    while True:
        try:
            message = receiver.rdt_rcv()
            if message:
                decoded = message.decode()
                if decoded and not decoded.startswith("ACK"):
                    # Exibe apenas a mensagem formatada (ignora mensagens de controle)
                    if not decoded.startswith("SERVER_INFO:"):
                        print(decoded)
                    else:
                        print(decoded.split("SERVER_INFO:")[1])
        except Exception as e:
            print(f"Erro na thread de recebimento: {str(e)}")
            break
        

# --- Ponto de entrada do programa ---
if __name__ == "__main__":
    # 1. Pede o nome do usuário
    username = input("Digite seu nome de usuário: ").strip()

    # 2. Cria o socket UDP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 3. Inicializa o sender e receiver RDT
    sender = RDT3_0_Sender(client_socket, SERVER_ADDR)
    receiver = RDT3_0_Receiver(client_socket)

    # 4. Envia a mensagem de conexão ao servidor
    connect_msg = f"hi, meu nome eh {username}"
    print(f"[CONEXÃO] Conectando como '{username}'...")
    sender.rdt_send(connect_msg.encode())

    # 5. Inicia uma thread para receber mensagens do servidor
    threading.Thread(target=receive_messages, daemon=True).start()

    # 6. Loop principal para enviar mensagens
    print("[CHAT] Conectado! Digite mensagens (ou 'bye' para sair):")
    while True:
        try:
            # Lê uma mensagem do teclado
            msg = input().strip()
            
            if not msg:
                continue  # Ignora mensagens vazias

            # Envia a mensagem usando RDT
            sender.rdt_send(msg.encode())

            time.sleep(0.1)
            
            # Se digitou 'bye', encerra o cliente
            if msg.lower() == "bye":
                print("[CHAT] Saindo...")
                client_socket.close()
                sys.exit(0)

        except KeyboardInterrupt:
            print("\n[CHAT] Encerrando cliente...")
            client_socket.close()
            sys.exit(0)
        except Exception as e:
            print(f"[ERRO] Falha ao enviar mensagem: {e}")