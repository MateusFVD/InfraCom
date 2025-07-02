import socket
import os

HOST = "127.0.0.1"  #Endereço IP do servidor
PORT = 5000         #Porta do servidor
dest = (HOST, PORT)

#Cria um socket UDP (SOCK_DGRAM) usando IPv4 (AF_INET).
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#-------------ENVIO DO ARQUIVO -------------------------------------

file_src = "MonaLisa.jpg"  #Nome do arquivo a ser enviado

try:
    file_size = os.path.getsize(file_src)  #Obtém o tamanho do arquivo em bytes
    print(f"O tamanho do arquivo é : {file_size} bytes")

    #Converte o nome do arquivo para bytes e envia para o servidor.
    clientSocket.sendto(file_src.encode(), dest)

    # Usar o "with", abre o arquivo em modo de leitura e garante que será fechado automaticamente
    with open(file_src, "rb") as file:
        while True:
            file_data = file.read(1024)  #Lê 1024 bytes do arquivo
            if not file_data:
                #Quando o arquivo é lido por completo, envia "<END>" para indicar o fim.
                clientSocket.sendto(b"<END>", dest)
                break
            clientSocket.sendto(file_data, dest)  #Lê e envia partes do arquivo em segmentos de 1024 bytes.
    print("Arquivo enviado com sucesso.")
#Tratamento de erro e exceção
except fileNotFoundError:
    print(f"Erro: O arquivo {file_src} não foi encontrado.")
    clientSocket.close()
    exit() #Encerra o script se o arquivo não existir

#---------- RECEBENDO O ARQUIVO DE VOLTA ---------------------------

file_bytes = b""

#Recebe o nome do arquivo modificado de volta do servidor
file_name, clientAddress = clientSocket.recvfrom(1024)
file_name = file_name.decode()
file_name = "client_" + file_name
file = open(file_name, "wb")  #Abre um novo arquivo binário para escrita

dcount = 0  #Contador para contagem dos datagramas recebidos
while True:
    datagram, serverAddress = clientSocket.recvfrom(1024)  # Recebe um datagrama
    dcount += 1
    print(f"datagram {dcount} recebido do servidor ({clientAddress})")

    if datagram == b"<END>":  #Recebe os datagramas até encontrar o marcador "<END>".
        dcount = 0
        break
    else:
        file_bytes += datagram

print("devolucao finalizada.")

file.write(file_bytes)  #Escreve os bytes recebidos no arquivo
file.close()  #Fecha o arquivo
clientSocket.close()  #Fecha o socket do cliente
