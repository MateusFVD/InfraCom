import socket
from rdt_protocol import RDT3_0_Receiver

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1024

# Tamanho máximo de dados dentro de um pacote RDT, ajustado para o overhead do JSON
RDT_DATA_CHUNK_SIZE = BUFFER_SIZE - 50

# criando o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# vinculando o servidor ao endereço especificado
server_socket.bind(SERVER_ADDRESS)

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")
print("Aguardando um cliente se conectar...")

# Instancia as máquinas de estado RDT
# O servidor é primariamente um receptor no início, e depois um remetente
# O client_address será atualizado quando o primeiro pacote do cliente chegar
rdt_receiver = RDT3_0_Receiver(server_socket, None)

try:
    # ========== RECEBENDO ARQUIVO DO CLIENTE ==========

    # recebe o nome do arquivo em bytes e o endereço de quem enviou (cliente)!! necessário para retornar o arquivo
    filename, client_address = server_socket.recvfrom(BUFFER_SIZE)

    # cria o nome do arquivo que será salvo no servidor!
    server_filename = "server_" + filename.decode()

    print("Iniciando recepção do arquivo...")

    # cria um novo arquivo no modo "append" para adicionar cada pedaço de arquivo recebido ao novo arquivo criado
    with open(server_filename, "ab") as f:
        while True:
            try:
                server_socket.settimeout(1.0) # Tempo limite para esperar por pacotes
                data_rcv_raw, client_address_rcv = server_socket.recvfrom(BUFFER_SIZE)

                # Processa o pacote recebido com o RDT receiver
                received_data = rdt_receiver.rdt_rcv(data_rcv_raw)

                if received_data is not None:
                    if received_data == b"EOF_TRANSMISSION":
                        print("Fim da transmissão do arquivo do cliente.")
                        break
                    f.write(received_data)
                # Se received_data for None, significa que o pacote foi corrompido ou duplicado,
                # e o ACK apropriado já foi reenviado pelo rdt_receiver.
                # Não fazemos nada, apenas esperamos o próximo pacote ou retransmissão.

            except socket.timeout:
                print("Servidor: Tempo limite para receber dados do cliente. Aguardando...")
                # O servidor deve continuar esperando até receber o EOF ou um tempo muito longo se esgotar.
                continue
            except Exception as e:
                print(f"Erro durante recepção RDT no servidor: {e}")
                break # Sai do loop em caso de erro

    print("Arquivo recebido com sucesso pelo servidor.")

    # ========== PROCESSAR ARQUIVO RECEBIDO E ENVIAR PARA CLIENTE ==========

    # Processar arquivo recebido - enviar nome do arquivo processado para o cliente
    server_socket.sendto(server_filename.encode(), client_address)

    # Enviar arquivo processado de volta para o cliente
    print("Iniciando envio do arquivo processado para o cliente...")

    with open(server_filename, "rb") as f:
        while True:
            # Lê 1024 bytes do arquivo
            chunk = f.read(BUFFER_SIZE)
            # Envia partes do arquivo em segmentos de 1024 bytes.
            server_socket.sendto(chunk, client_address)

            # Se não ler dados do arquivo, encerra o laço
            if not chunk:
                break

    print("Arquivo processado enviado com sucesso para o cliente!")

except Exception as e:
    print(f"Ocorreu um erro durante a execução: {e}")
