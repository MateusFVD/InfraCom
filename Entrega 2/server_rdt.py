import socket
from rdt_protocol import RDT3_0_Receiver, RDT3_0_Sender

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1024

# Tamanho máximo de dados dentro de um pacote RDT, ajustado para o overhead do JSON
RDT_DATA_CHUNK_SIZE = BUFFER_SIZE - 40

# criando o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# vinculando o servidor ao endereço especificado
server_socket.bind(SERVER_ADDRESS)

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")
print("Aguardando um cliente se conectar...")

try:
    # ========== RECEBENDO ARQUIVO DO CLIENTE ========== 

    # recebe o nome do arquivo em bytes e o endereço de quem enviou (cliente)
    filename, client_address = server_socket.recvfrom(BUFFER_SIZE)
    server_filename = "server_" + filename.decode()

    # Agora crie o receiver com o endereço correto
    rdt_receiver = RDT3_0_Receiver(server_socket, client_address)

    print("Iniciando recepção do arquivo...")

    with open(server_filename, "ab") as f:
        while True:
            try:
                server_socket.settimeout(1.0) # Tempo limite para esperar por pacotes
                data_rcv_raw, client_address_rcv = server_socket.recvfrom(BUFFER_SIZE)
                received_data = rdt_receiver.rdt_rcv(data_rcv_raw)
                if received_data is not None:
                    if received_data == b"EOF_TRANSMISSION":
                        print("Fim da transmissão do arquivo do cliente.")
                        break
                    f.write(received_data)
            except socket.timeout:
                print("Servidor: Tempo limite para receber dados do cliente. Aguardando...")
                continue
            except Exception as e:
                print(f"Erro durante recepção RDT no servidor: {e}")
                break

    print("Arquivo recebido com sucesso pelo servidor.")

    # ========== PROCESSAR ARQUIVO RECEBIDO E ENVIAR PARA CLIENTE ========== 

    # Enviar nome do arquivo processado para o cliente
    server_socket.sendto(server_filename.encode(), client_address)

    print("Iniciando envio do arquivo processado para o cliente...")

    rdt_sender = RDT3_0_Sender(server_socket, client_address, timeout=1.0, loss_prob=0.1)
    with open(server_filename, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                rdt_sender.rdt_send(b"EOF_TRANSMISSION")
                break
            rdt_sender.rdt_send(chunk)

    print("Arquivo processado enviado com sucesso para o cliente!")

except Exception as e:
    print(f"Ocorreu um erro durante a execução: {e}")
