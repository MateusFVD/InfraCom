import json

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
            return packet_data.get("seq_num"), packet_data.get("data").encode()
        except (json.JSONDecodeError, UnicodeDecodeError):
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
            sndpkt = self._make_pkt(self.expected_sequence_number, "ACK")
            self._udt_send(sndpkt)
            self.expected_sequence_number = 1 - self.expected_sequence_number
            print(f"RDT Receiver: Dados entregues à camada superior. Próxima sequência esperada: {self.expected_sequence_number}.")
            return data
        else:
            sndpkt = self._make_pkt(1 - self.expected_sequence_number, "ACK")
            self._udt_send(sndpkt)
            print(f"RDT Receiver: Reenviado ACK para a sequência anterior ({1 - self.expected_sequence_number}).")
            return None
