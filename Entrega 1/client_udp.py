import socket

HOST = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = (HOST, PORT)

BUFFER_SIZE = 1024


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

# -------------ENVIO DO ARQUIVO -------------------------------------

try:
    print(f"Enviando {filename} para o servidor")
    # Converte o nome do arquivo para bytes e envia para o servidor.
    client_socket.sendto(filename.encode(), SERVER_ADDRESS)

    # Usar o "with", abre o arquivo em modo de leitura e garante que será fechado automaticamente
    with open(filename, "rb") as f:
        while True:
            # Lê 1024 bytes do arquivo
            chunk = f.read(BUFFER_SIZE)
            # Envia partes do arquivo em segmentos de 1024 bytes.
            client_socket.sendto(chunk, SERVER_ADDRESS)

            # Se não ler dados do arquivo, encerra o laço
            if not chunk:
                break

    # ---------- RECEBENDO O ARQUIVO DE VOLTA ---------------------------

    # Recebe o nome do arquivo que o cliente vai enviar
    filename, _ = client_socket.recvfrom(BUFFER_SIZE)

    # cria o nome do arquivo que será salvo no cliente!
    client_filename = "client_" + filename.decode()

    print(f"Recebendo {client_filename} do servidor")
    # cria um novo arquivo no modo "append" para adicionar cada pedaço de arquivo recebido ao novo arquivo criado
    with open(client_filename, "ab") as f:
        while True:
            # recebe um pedaço do arquivo enviado pelo servidor
            data, _ = client_socket.recvfrom(BUFFER_SIZE)

            # se não receber dados do cliente, encerra o laço
            if not data:
                break

            # adiciona a sequencia de bytes no aquivo
            f.write(data)

except FileNotFoundError:
    print(f"Erro: O arquivo {filename} não foi encontrado.")
    client_socket.close()
    exit()  # Encerra o script se o arquivo não existir

except Exception as e:
    print(f"Erro durante recebimento: {e}")

finally:
    client_socket.close()
