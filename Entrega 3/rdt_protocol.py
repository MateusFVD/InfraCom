import socket
import time
import struct
import random 

# --- Simulação do canal não confiável ---
LOSS_PROBABILITY = 0.005  # 0.5% de chance de perda de pacote

def udt_send_with_loss(socket_obj, packet, address):
    """Função para simular perda de pacotes"""
    if random.random() < LOSS_PROBABILITY:
        print(f"Simulação de perda: Pacote perdido")
    else:
        socket_obj.sendto(packet, address)

class RDT3_0_Sender:
    def __init__(self, socket_obj, server_address, timeout=2.0):
        self.socket = socket_obj
        self.server_address = server_address
        self.timeout = timeout
        self.sndpkt = None
        self.seq_num = 0  # Inicia com número de sequência 0
        self.timer_start = None
        
    def make_pkt(self, seq, data):
        """Cria um pacote com número de sequência e dados"""
        if len(data) > 1023:  # Limita o tamanho dos dados
            data = data[:1023]
        return struct.pack('!B', seq) + data
    
    def extract_seq(self, pkt):
        """Extrai o número de sequência do pacote"""
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def has_seq(self, pkt, expected_seq):
        """Verifica se o pacote tem o número de sequência esperado"""
        return self.extract_seq(pkt) == expected_seq
    
    def start_timer(self):
        """Inicia o timer para retransmissão"""
        self.timer_start = time.time()
    
    def stop_timer(self):
        """Para o timer"""
        self.timer_start = None
    
    def is_timeout(self):
        """Verifica se ocorreu timeout"""
        return self.timer_start is not None and (time.time() - self.timer_start) >= self.timeout
    
    def rdt_send(self, data):
        """Implementação do protocolo RDT 3.0 para envio de dados"""
        print(f"RDT3.0 Sender: Enviando dados com seq={self.seq_num}")
        
        # Cria o pacote
        self.sndpkt = self.make_pkt(self.seq_num, data)
        
        # Envia o pacote (com possível perda simulada)
        udt_send_with_loss(self.socket, self.sndpkt, self.server_address)
        self.start_timer()
        
        # Espera pelo ACK correto
        while True:
            try:
                self.socket.settimeout(0.1)  # Timeout curto para verificação periódica
                rcvpkt, addr = self.socket.recvfrom(1024)

                # Ignora pacotes de outros remetentes
                if addr != self.server_address:
                    continue
                
                print(f"Sender: ACK recebido de {addr}")
                
                # Verifica se é o ACK esperado
                if self.has_seq(rcvpkt, self.seq_num):
                    print(f"Sender: ACK correto para seq={self.seq_num}")
                    self.stop_timer()
                    self.seq_num = 1 - self.seq_num  # Alterna o número de sequência
                    break
                    
            except socket.timeout:
                if self.is_timeout():
                    print(f"RDT3.0 Sender: Timeout! Reenviando pacote seq={self.seq_num}")
                    udt_send_with_loss(self.socket, self.sndpkt, self.server_address)
                    self.start_timer()
                continue
            finally:
                self.socket.settimeout(None)

class RDT3_0_Receiver:
    def __init__(self, socket_obj):
        self.socket = socket_obj
        self.expected_seq = 0  # Inicia esperando sequência 0
        
    def make_pkt(self, seq, data=b''):
        """Cria um pacote ACK"""
        return struct.pack('!B', seq) + data
    
    def extract_seq(self, pkt):
        """Extrai o número de sequência do pacote"""
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def extract_data(self, pkt):
        """Extrai os dados do pacote"""
        return pkt[1:] if len(pkt) >= 1 else b''
    
    def has_seq(self, pkt, expected_seq):
        """Verifica se o pacote tem o número de sequência esperado"""
        return self.extract_seq(pkt) == expected_seq
    
    def rdt_rcv(self, client_address=None):
        while True:
            try:
                self.socket.settimeout(1.0)  # Aumenta o timeout
                rcvpkt, addr = self.socket.recvfrom(1024)
                
                if client_address and addr != client_address:
                    continue
                
                received_seq = self.extract_seq(rcvpkt)
                print(f"Receiver: Pacote recebido seq={received_seq}, esperava={self.expected_seq}")
                
                if received_seq == self.expected_seq:
                    data = self.extract_data(rcvpkt)
                    ack_pkt = self.make_pkt(self.expected_seq)
                    udt_send_with_loss(self.socket, ack_pkt, addr)
                    self.expected_seq = 1 - self.expected_seq
                    return data
                else:
                    # Envia ACK para o número de sequência que está esperando
                    ack_pkt = self.make_pkt(1 - self.expected_seq)
                    udt_send_with_loss(self.socket, ack_pkt, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receiver error: {str(e)}")
                raise