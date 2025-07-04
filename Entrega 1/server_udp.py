import socket

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1024

# criando o socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# vinculando o servidor ao endereço especificado
server_socket.bind(SERVER_ADDRESS)

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")
print("Aguardando um cliente se conectar...")

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
            # recebe um pedaço do arquivo enviado pelo cliente
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)

            # se não receber dados do cliente, encerra o laço
            if not data:
                break

            # adiciona a sequencia de bytes no aquivo
            f.write(data)

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
