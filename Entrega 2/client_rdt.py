import socket
from rdt_protocol import RDT3_0_Sender, RDT3_0_Receiver

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1023  # Reservando apenas 1 byte para o número de sequência


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

# -------------ENVIO DO ARQUIVO USANDO RDT3.0 -------------------------------------

try:
    print(f"RDT3.0 Cliente: Iniciando protocolo RDT3.0 para envio")
    
    # Cria o sender RDT3.0
    rdt_sender = RDT3_0_Sender(client_socket, SERVER_ADDRESS)
    
    print(f"Enviando {filename} para o servidor usando RDT3.0")
    
    # Envia o nome do arquivo usando RDT3.0
    print(f"RDT3.0 Cliente: Enviando nome do arquivo: {filename}")
    rdt_sender.rdt_send(filename.encode())

    # Usar o "with", abre o arquivo em modo de leitura e garante que será fechado automaticamente
    with open(filename, "rb") as f:
        while True:
            # Lê 1024 bytes do arquivo
            chunk = f.read(BUFFER_SIZE)
            
            # Se não ler dados do arquivo, envia pacote vazio e encerra o laço
            if not chunk:
                print("RDT3.0 Cliente: Enviando pacote de finalização")
                rdt_sender.rdt_send(b'')  # Envia pacote vazio para sinalizar fim
                break
            
            # Envia partes do arquivo usando RDT3.0
            print(f"RDT3.0 Cliente: Enviando chunk de {len(chunk)} bytes")
            rdt_sender.rdt_send(chunk)

    print("RDT3.0 Cliente: Arquivo enviado com sucesso usando RDT3.0")

    # ---------- RECEBENDO O ARQUIVO DE VOLTA USANDO RDT3.0 ---------------------------
    print("RDT3.0 Cliente: Iniciando recepção usando RDT3.0")
    
    # Cria o receiver RDT3.0
    rdt_receiver = RDT3_0_Receiver(client_socket)

    # Recebe o nome do arquivo que o servidor vai enviar usando RDT3.0
    filename_data = rdt_receiver.rdt_rcv(SERVER_ADDRESS)
    received_filename = filename_data.decode()
    
    print(f"RDT3.0 Cliente: Nome do arquivo recebido: {received_filename}")

    # cria o nome do arquivo que será salvo no cliente!
    client_filename = "client_" + received_filename

    print(f"Recebendo {client_filename} do servidor usando RDT3.0")
    
    # cria um novo arquivo no modo "write binary" para escrever o arquivo recebido
    with open(client_filename, "wb") as f:
        while True:
            # recebe um pedaço do arquivo usando RDT3.0
            data = rdt_receiver.rdt_rcv(SERVER_ADDRESS)

            # se não receber dados do servidor, encerra o laço
            if not data or len(data) == 0:
                print("RDT3.0 Cliente: Recebido pacote de finalização")
                break

            # adiciona a sequencia de bytes no arquivo
            f.write(data)
            print(f"RDT3.0 Cliente: Recebido chunk de {len(data)} bytes")

    print("RDT3.0 Cliente: Arquivo recebido com sucesso usando RDT3.0!")

except FileNotFoundError:
    print(f"Erro: O arquivo {filename} não foi encontrado.")
    client_socket.close()
    exit()  # Encerra o script se o arquivo não existir

except Exception as e:
    print(f"Erro durante execução: {e}")
    import traceback
    traceback.print_exc()

finally:
    client_socket.close()
    print("RDT3.0 Cliente: Socket fechado")
