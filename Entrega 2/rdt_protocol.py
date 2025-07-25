import json
import socket
import time
import random
import base64

class RDT3_0_Receiver:
    def __init__(self, udp_socket, client_address):
        self.udp_socket = udp_socket
        self.client_address = client_address
        self.expected_sequence_number = 0 # O próximo número de sequência esperado

    def _make_pkt(self, seq_num, ack_type="ACK"):
        ack_packet = {
            "type": ack_type,
            "seq_num": seq_num
        }
        print(f"RDT Receiver: Criando pacote ACK (type={ack_type}, seq={seq_num}).")
        return json.dumps(ack_packet).encode()

    def _udt_send(self, packet):
        if self.client_address:
            self.udp_socket.sendto(packet, self.client_address)
            print(f"RDT Receiver: Enviado ACK via UDT (UDP) para {self.client_address}.")
        else:
            print("RDT Receiver: Não pode enviar ACK, endereço do cliente não definido.")

    def _extract(self, rcvpkt):
        try:
            packet_data = json.loads(rcvpkt.decode())
            print(f"RDT Receiver: Extraindo dados do pacote (seq={packet_data.get('seq_num')}).")
            # Decodifica o campo 'data' de base64 para bytes
            data_b64 = packet_data.get("data")
            if data_b64 is not None:
                data = base64.b64decode(data_b64)
            else:
                data = b''
            return packet_data.get("seq_num"), data
        except (json.JSONDecodeError, UnicodeDecodeError, base64.binascii.Error):
            print("RDT Receiver: Erro ao extrair dados: pacote corrompido ou formato inválido.")
            return None, None 

    def _has_seq(self, rcvpkt, expected_seq):
        try:
            packet_data = json.loads(rcvpkt.decode())
            has_expected_seq = packet_data.get("seq_num") == expected_seq
            print(f"RDT Receiver: Verificando número de sequência: Pacote tem seq={packet_data.get('seq_num')}, esperado={expected_seq}. Match: {has_expected_seq}.")
            return has_expected_seq
        except (json.JSONDecodeError, UnicodeDecodeError):
            print("RDT Receiver: Erro ao verificar número de sequência: pacote corrompido.")
            return False

    def rdt_rcv(self, rcvpkt):

        print(f"\n--- RDT Receiver: Pacote recebido via UDT. Esperando seq={self.expected_sequence_number} ---")

        if self.client_address is None:
            pass

        if self._has_seq(rcvpkt, self.expected_sequence_number):
            seq_num, data = self._extract(rcvpkt)
            print(f"RDT Receiver: Pacote com seq={seq_num} é o esperado. Enviando ACK e alternando sequência.")
            sndpkt = self._make_pkt(self.expected_sequence_number, "ACK")
            self._udt_send(sndpkt)
            self.expected_sequence_number = 1 - self.expected_sequence_number
            print(f"RDT Receiver: Dados entregues à camada superior. Próxima sequência esperada: {self.expected_sequence_number}.")
            return data
        else:
            print(f"RDT Receiver: Pacote com seq diferente do esperado. Reenviando ACK para a sequência anterior ({1 - self.expected_sequence_number}).")
            sndpkt = self._make_pkt(1 - self.expected_sequence_number, "ACK")
            self._udt_send(sndpkt)
            return None

class RDT3_0_Sender:
    def __init__(self, udp_socket, dest_address, timeout=1.0, loss_prob=0.1):
        self.udp_socket = udp_socket
        self.dest_address = dest_address
        self.timeout = timeout  # tempo limite para ACK
        self.loss_prob = loss_prob  # probabilidade de "perder" um pacote
        self.sequence_number = 0

    def _make_pkt(self, data):
        # Codifica os dados em base64 para garantir transmissão segura via JSON
        if isinstance(data, bytes):
            data_b64 = base64.b64encode(data).decode('ascii')
        else:
            data_b64 = base64.b64encode(data.encode()).decode('ascii')
        pkt = {
            "seq_num": self.sequence_number,
            "data": data_b64
        }
        print(f"RDT Sender: Criando pacote (seq={self.sequence_number}).")
        return json.dumps(pkt).encode()

    def _udt_send(self, packet):
        # Simula perda de pacote
        if random.random() < self.loss_prob:
            print(f"RDT Sender: Simulando PERDA do pacote seq={self.sequence_number}!")
            return  # Não envia o pacote
        self.udp_socket.sendto(packet, self.dest_address)
        print(f"RDT Sender: Pacote seq={self.sequence_number} enviado via UDT (UDP) para {self.dest_address}.")

    def _wait_for_ack(self):
        self.udp_socket.settimeout(self.timeout)
        end_time = time.time() + self.timeout
        while time.time() < end_time:
            try:
                ack_pkt, _ = self.udp_socket.recvfrom(65535)
                try:
                    ack_data = json.loads(ack_pkt.decode())
                except Exception as e:
                    print(f"RDT Sender: Pacote recebido não é JSON válido: {e}")
                    continue  # Ignora e espera próximo pacote
                print(f"RDT Sender: Pacote recebido para ACK: {ack_data}")
                if ack_data.get("type") != "ACK":
                    print("RDT Sender: Pacote recebido não é ACK, ignorando...")
                    continue  # Ignora e espera próximo pacote
                print(f"RDT Sender: ACK recebido (seq={ack_data.get('seq_num')}). Esperado seq={self.sequence_number}.")
                if ack_data.get("seq_num") == self.sequence_number:
                    return True
                else:
                    print(f"RDT Sender: ACK inválido ou duplicado. Esperado seq={self.sequence_number}.")
                    continue  # Ignora e espera próximo pacote
            except socket.timeout:
                print(f"RDT Sender: TIMEOUT esperando ACK do seq={self.sequence_number}!")
                return False
            except Exception as e:
                print(f"RDT Sender: Erro ao receber ACK: {e}")
                return False
        print(f"RDT Sender: TIMEOUT esperando ACK do seq={self.sequence_number} (loop)!")
        return False

    def rdt_send(self, data):
        pkt = self._make_pkt(data)
        while True:
            self._udt_send(pkt)
            ack_ok = self._wait_for_ack()
            if ack_ok:
                print(f"RDT Sender: ACK correto recebido. Alternando sequência.")
                self.sequence_number = 1 - self.sequence_number
                break
            else:
                print(f"RDT Sender: Retransmitindo pacote seq={self.sequence_number}...")
