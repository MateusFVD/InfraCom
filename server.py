import socket
import os

# ----------definindo configurações-------------
HOST = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 1024

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print(f"Servidor UDP iniciado e escutando em {HOST}:{PORT}")

print("\nAguardando um cliente se conectar...")

try:
    file_bytes = b""

    file_name_bytes, client_address = server_socket.recvfrom(
        BUFFER_SIZE
    )  # recebe o nome do arquivo em bytes e o endereço de quem enviou (cliente)!! necessário para retornar o arquivo

    file_name = file_name_bytes.decode()  # decodificando para string
    server_file_name = (
        "server_" + file_name
    )  # cria o nome do arquivo que será salvo no servidor!

    print(f"Conexão recebida de: {client_address}")
    print(f"Nome do arquivo a ser recebido: '{file_name}'")
    print(f"Salvando como: '{server_file_name}'")

    with open(server_file_name, "wb") as f:
        print("Iniciando recepção do arquivo...")
        dcount = 0
        while True:
            # recebe um pedaço do arquivo
            data, _ = server_socket.recvfrom(BUFFER_SIZE)
            dcount += 1

            # verifica se recebemos o sinal de fim de arquivo do cliente
            if data == b"<END>":
                print("Sinal de <END> recebido. O arquivo foi completamente recebido.")
                dcount = 0
                break
            else:  # se não, salva o pedaço do arquivo na sequencia de bytes
                file_bytes += data

            # torna toda sequencia de bytes em um aquivo
            f.write(file_bytes)

    print("Arquivo salvo com sucesso no servidor.")

    # ========== PROCESSAR ARQUIVO RECEBIDO E ENVIAR PARA CLIENTE ==========
    
    # Processar arquivo recebido - enviar nome do arquivo processado para o cliente
    print(f"\nProcessando arquivo recebido...")
    print(f"Enviando nome do arquivo processado: '{server_file_name}' para o cliente")
    server_socket.sendto(server_file_name.encode(), client_address)
    
    # Enviar arquivo processado de volta para o cliente
    print("Iniciando envio do arquivo processado para o cliente...")
    with open(server_file_name, "rb") as f:
        dcount = 0
        while True:
            file_data = f.read(BUFFER_SIZE)  # Lê 1024 bytes do arquivo
            if not file_data:
                # Quando o arquivo é lido por completo, envia "<END>" para indicar o fim
                server_socket.sendto(b"<END>", client_address)
                print("Sinal de <END> enviado. Arquivo processado enviado completamente.")
                break
            server_socket.sendto(file_data, client_address)  # Envia partes do arquivo
            dcount += 1
            print(f"Enviando datagrama {dcount} para o cliente")
    
    print("Arquivo processado enviado com sucesso para o cliente!")

except Exception as e:
    print(f"Ocorreu um erro durante a recepção: {e}")
