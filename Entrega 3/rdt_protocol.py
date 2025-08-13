# modulo: rdt_protocol.py
# responsavel pela implementacao da camada de transporte confiavel (rdt 3.0).

import socket

PACKET_SIZE = 1024  # tamanho total do datagrama udp

def send_data(sock, message, destination_address, sequence_number_tracker):
    """
    envia dados de forma confiavel usando o protocolo rdt 3.0.

    args:
        sock (socket.socket): o socket do remetente.
        message (str): a mensagem a ser enviada.
        destination_address (tuple): o endereco do destinatario (ip, porta).
        sequence_number_tracker (dict): um dicionario para rastrear o numero de sequencia.
    """
    offset = 0
    delimiter = "::"
    header_size = len(f"{sequence_number_tracker['num']}{delimiter}")
    payload_size = PACKET_SIZE - header_size

    # fragmenta a mensagem em segmentos e os envia um por um
    while offset < len(message):
        segment = message[offset : offset + payload_size]
        ack_confirmed = False

        # constroi o datagrama com o numero de sequencia
        datagram = f"{sequence_number_tracker['num']}{delimiter}{segment}"
        
        # envia o datagrama e espera pelo ack
        sock.sendto(datagram.encode('utf-8'), destination_address)

        while not ack_confirmed:
            try:
                ack_packet, _ = sock.recvfrom(PACKET_SIZE)
                # verifica se o ack corresponde a sequencia enviada
                if ack_packet.decode('utf-8') == f"ACK{sequence_number_tracker['num']}":
                    ack_confirmed = True
                    # alterna o numero de sequencia (0 -> 1, 1 -> 0)
                    sequence_number_tracker['num'] = 1 - sequence_number_tracker['num']
                else:
                    # ack incorreto, reenvia o pacote
                    sock.sendto(datagram.encode('utf-8'), destination_address)
            except socket.timeout:
                # timeout: reenvia o pacote
                sock.sendto(datagram.encode('utf-8'), destination_address)
            except ConnectionResetError:
                print("aviso: a conexao foi resetada pelo outro lado.")
                return

        offset += payload_size

def receive_data(sock, received_packet, sender_address, expected_sequence_tracker):
    """
    recebe dados de forma confiavel usando o protocolo rdt 3.0.

    args:
        sock (socket.socket): o socket do receptor.
        received_packet (bytes): o pacote de dados recebido.
        sender_address (tuple): o endereco do remetente.
        expected_sequence_tracker (dict): dicionario para rastrear a sequencia esperada.

    returns:
        bytes: o conteudo da mensagem se o pacote for recebido corretamente, caso contrario none.
    """
    try:
        if not received_packet:
            return None

        # divide o pacote no cabecalho (numero de sequencia) e na carga util
        delimiter = b"::"
        header, payload = received_packet.split(delimiter, 1)
        received_sequence_num = int(header.decode('utf-8'))

        # compara o numero de sequencia recebido com o esperado
        if received_sequence_num == expected_sequence_tracker['num']:
            # sequencia correta: envia ack e retorna a carga util
            ack_msg = f"ACK{expected_sequence_tracker['num']}"
            sock.sendto(ack_msg.encode('utf-8'), sender_address)
            # alterna o numero de sequencia esperado para o proximo pacote
            expected_sequence_tracker['num'] = 1 - expected_sequence_tracker['num']
            return payload
        else:
            # sequencia incorreta (pacote duplicado): reenvia o ack da ultima sequencia correta
            ack_msg = f"ACK{1 - expected_sequence_tracker['num']}"
            sock.sendto(ack_msg.encode('utf-8'), sender_address)
            return None  # descarta o pacote fora de ordem
            
    except (ValueError, IndexError):
        # pacote malformado, ignora
        return None
    except ConnectionResetError:
        print("aviso: a conexao com o cliente foi encerrada.")
        return None