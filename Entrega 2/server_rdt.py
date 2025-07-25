import socket
from rdt_protocol import RDT3_0_Receiver, RDT3_0_Sender

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1000  # Reduzido para deixar espaço para cabeçalho RDT3.0

# criando o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# vinculando o servidor ao endereço especificado
server_socket.bind(SERVER_ADDRESS)

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")
print("Aguardando um cliente se conectar...")

try:
    # ========== RECEBENDO ARQUIVO DO CLIENTE ==========
    print("Servidor: Iniciando protocolo RDT3.0 para recepção")
    
    # Primeiro, vamos receber uma mensagem UDP normal para obter o endereço do cliente
    first_msg, client_address = server_socket.recvfrom(1024)
    print(f"Servidor: Cliente conectado de {client_address}")
    
    # Agora processa essa primeira mensagem e as próximas usando RDT3.0
    rdt_receiver = RDT3_0_Receiver(server_socket)
    
    # Processa a primeira mensagem (nome do arquivo)
    if rdt_receiver.has_seq(first_msg, 0):  # Esperamos que seja seq=0
        filename_data = rdt_receiver.extract_data(first_msg)
        filename = filename_data.decode()
        # Envia ACK
        ack_pkt = rdt_receiver.make_pkt(0, b'', 0)
        server_socket.sendto(ack_pkt, client_address)
        rdt_receiver.expected_seq = 1  # Próximo esperado é 1
        print(f"Servidor: Nome do arquivo recebido: {filename}")
    else:
        print("Servidor: Erro na primeira mensagem")
        exit()

    # cria o nome do arquivo que será salvo no servidor!
    server_filename = "server_" + filename

    print("Iniciando recepção do arquivo usando RDT3.0...")

    # cria um novo arquivo no modo "write binary" para escrever o arquivo recebido
    with open(server_filename, "wb") as f:
        while True:
            # recebe um pedaço do arquivo usando RDT3.0
            data = rdt_receiver.rdt_rcv(client_address)

            # se não receber dados do cliente, encerra o laço
            if not data or len(data) == 0:
                print("Servidor: Recebido pacote de finalização")
                break

            # adiciona a sequencia de bytes no arquivo
            f.write(data)
            print(f"Servidor: Recebido chunk de {len(data)} bytes")

    print("Arquivo recebido com sucesso pelo servidor usando RDT3.0.")

    # ========== PROCESSAR ARQUIVO RECEBIDO E ENVIAR PARA CLIENTE ==========
    print("Servidor: Iniciando envio")
    
    # Cria o sender RDT3.0
    rdt_sender = RDT3_0_Sender(server_socket, client_address)

    # Processar arquivo recebido - enviar nome do arquivo processado para o cliente
    print(f"Servidor: Enviando nome do arquivo: {server_filename}")
    rdt_sender.rdt_send(server_filename.encode())

    # Enviar arquivo processado de volta para o cliente
    print("Iniciando envio do arquivo processado para o cliente usando RDT3.0...")

    with open(server_filename, "rb") as f:
        while True:
            # Lê 1024 bytes do arquivo
            chunk = f.read(BUFFER_SIZE)
            
            # Se não ler dados do arquivo, envia pacote vazio e encerra o laço
            if not chunk:
                print("Servidor: Enviando pacote de finalização")
                rdt_sender.rdt_send(b'')  # Envia pacote vazio para sinalizar fim
                break
            
            # Envia partes do arquivo usando RDT3.0
            print(f"Servidor: Enviando chunk de {len(chunk)} bytes")
            rdt_sender.rdt_send(chunk)

    print("Arquivo processado enviado com sucesso para o cliente usando RDT3.0!")

    # Processar arquivo recebido - enviar nome do arquivo processado para o cliente
    print(f"Servidor: Enviando nome do arquivo: {server_filename}")
    rdt_sender.rdt_send(server_filename.encode())

    # Enviar arquivo processado de volta para o cliente
    print("Iniciando envio do arquivo processado para o cliente usando RDT3.0...")

    with open(server_filename, "rb") as f:
        while True:
            # Lê 1024 bytes do arquivo
            chunk = f.read(BUFFER_SIZE)
            
            # Se não ler dados do arquivo, envia pacote vazio e encerra o laço
            if not chunk:
                print("Servidor: Enviando pacote de finalização")
                rdt_sender.rdt_send(b'')  # Envia pacote vazio para sinalizar fim
                break
            
            # Envia partes do arquivo usando RDT3.0
            print(f"Servidor: Enviando chunk de {len(chunk)} bytes")
            rdt_sender.rdt_send(chunk)

    print("Arquivo processado enviado com sucesso para o cliente usando RDT3.0!")

except Exception as e:
    print(f"Ocorreu um erro durante a execução: {e}")
    import traceback
    traceback.print_exc()

finally:
    server_socket.close()
    print("Servidor: Socket fechado")
