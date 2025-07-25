import socket
from rdt_protocol import RDT3_0_Receiver, RDT3_0_Sender

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1024

# Tamanho máximo de dados dentro de um pacote RDT, ajustado para o overhead do JSON
RDT_DATA_CHUNK_SIZE = BUFFER_SIZE - 40

def choose_file():
    print("Digite:\n 1 - para enviar um PDF\n 2 - para enviar uma imagem\n")

    file = input()

    if file == "1":
        return "teste.pdf"
    elif file == "2":
        return "MonaLisa.jpg"
    else:
        print("Erro: O arquivo não foi encontrado.")
        exit()


filename = choose_file()

# Cria um socket UDP (SOCK_DGRAM) usando IPv4 (AF_INET).
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Instancia as máquinas de estado RDT
# O cliente é primariamente um remetente no início, e depois um receptor

rdt_sender = RDT3_0_Sender(client_socket, SERVER_ADDRESS, timeout=1.0, loss_prob=0.1)
rdt_receiver = RDT3_0_Receiver(client_socket, SERVER_ADDRESS)
# -------------ENVIO DO ARQUIVO -------------------------------------

try:
    print(f"Enviando {filename} para o servidor")
    # Converte o nome do arquivo para bytes e envia para o servidor.
    client_socket.sendto(filename.encode(), SERVER_ADDRESS)

    # Usar o "with", abre o arquivo em modo de leitura e garante que será fechado automaticamente
    with open(filename, "rb") as f:
        while True:
            # Lê um espaço de dados para o RDT
            chunk = f.read(RDT_DATA_CHUNK_SIZE)
            if not chunk:
                # Envia um marcador de fim de transmissão
                rdt_sender.rdt_send(b"EOF_TRANSMISSION")
                break
            # Envia partes do arquivo usando o RDT sender
            rdt_sender.rdt_send(chunk)

    # ---------- RECEBENDO O ARQUIVO DE VOLTA ---------------------------

    # Recebe o nome do arquivo que o cliente vai receber de volta
    filename_recv, _ = client_socket.recvfrom(BUFFER_SIZE)
    client_filename = "client_" + filename_recv.decode()

    print(f"Recebendo {client_filename} do servidor")
    with open(client_filename, "ab") as f:
        while True:
            try:
                client_socket.settimeout(0.5) #Tempo limite para esperar por pacotes
                rcvpkt, server_address = client_socket.recvfrom(BUFFER_SIZE)
                data = rdt_receiver.rdt_rcv(rcvpkt)

                if data is not None:
                    if data == b"EOF_TRANSMISSION":
                        break
                    f.write(data)

            except socket.timeout:
                print("Cliente: Tempo limite para receber dados do servidor. Aguardando...")
                break
            except Exception as e:
                print(f"Erro durante recepção RDT no cliente: {e}")
                break

except FileNotFoundError:
    print(f"Erro: O arquivo {filename} não foi encontrado.")
    client_socket.close()
    exit()  # Encerra o script se o arquivo não existir

except Exception as e:
    print(f"Erro durante recebimento: {e}")

finally:
    client_socket.close()
