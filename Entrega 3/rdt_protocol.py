import socket
import time
import struct
import random 

# --- Simulação do canal não confiável ---
LOSS_PROBABILITY = 0.005

def udt_send_with_loss( socket_obj, packet, address):
    if random.random() < LOSS_PROBABILITY:
        print(f"Simulação de perda: Pacote perdido")
        # Não fazemos nada, o pacote simplesmente não é enviado
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
        # Formato: seq_num (1 byte) + data
        # Limita dados a 1023 bytes para deixar espaço para cabeçalho
        if len(data) > 1023:
            data = data[:1023]
        pkt = struct.pack('!B', seq) + data
        return pkt
    
    def extract_seq(self, pkt):
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def has_seq(self, pkt, expected_seq):
        seq = self.extract_seq(pkt)
        return seq == expected_seq
    
    def start_timer(self):
        self.timer_start = time.time()
    
    def stop_timer(self):
        self.timer_start = None
    
    def is_timeout(self):
        if self.timer_start is None:
            return False
        return (time.time() - self.timer_start) >= self.timeout
    
    def rdt_send(self, data):
        print(f"RDT3.0 Sender: Enviando dados com seq={self.seq_num}")
        
        # Estado: Esperar chamada 0 de cima (ou 1 de cima)
        # make_pkt(seq_num, data)
        self.sndpkt = self.make_pkt(self.seq_num, data)
        
        # udt_send(sndpkt)
        #self.socket.sendto(self.sndpkt, self.server_address)
        udt_send_with_loss(self.socket, self.sndpkt, self.server_address)
        
        # start_timer
        self.start_timer()
        
        # Estado: Esperar ACK
        while True:
            try:
                # Configura timeout no socket
                self.socket.settimeout(0.1)  # Timeout curto para verificar periodicamente
                
                # rdt_rcv(rcvpkt)
                rcvpkt, addr = self.socket.recvfrom(1024)

                if addr != self.server_address:
                    print(f"Sender: Recebido pacote do endereço errado {addr}, ignorando.")
                    continue
                
                print(f"Sender: ACK recebido de {addr}")
                
                # Verifica se é ACK correto (sem corrupt/notcorrupt - assumimos UDP checksum)
                if self.has_seq(rcvpkt, self.seq_num):
                    print(f"Sender: ACK correto para seq={self.seq_num}")
                    # stop_timer
                    self.stop_timer()
                    # Alterna número de sequência
                    self.seq_num = 1 - self.seq_num
                    break
                else:
                    print(f"Sender: ACK incorreto, esperando seq={self.seq_num}")
                    # Continua esperando ACK correto
                    
            except socket.timeout:
                # Verifica se houve timeout
                if self.is_timeout():
                    print(f"RDT3.0 Sender: Timeout! Reenviando pacote seq={self.seq_num}")
                    # Reenvia o pacote
                    #self.socket.sendto(self.sndpkt, self.server_address)
                    udt_send_with_loss(self.socket, self.sndpkt, self.server_address)
                    # Reinicia o timer
                    self.start_timer()
                # Continua o loop
                continue
        
        # Restaura socket para modo bloqueante
        self.socket.settimeout(None)

class RDT3_0_Receiver:
    def __init__(self, socket_obj):
        self.socket = socket_obj
        self.expected_seq = 0  # Inicia esperando sequência 0
        self.sndpkt = None
        
    def make_pkt(self, seq, data=b''):
        # Formato: seq_num (1 byte) + data
        pkt = struct.pack('!B', seq) + data
        return pkt
    
    def extract_seq(self, pkt):
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def extract_data(self, pkt):
        if len(pkt) < 1:
            return b''
        return pkt[1:]  # Pula seq_num (1 byte)
    
    def has_seq(self, pkt, expected_seq):
        seq = self.extract_seq(pkt)
        return seq == expected_seq
    
    def deliver_data(self, data):
        return data
    
    def rdt_rcv(self, client_address=None):
        while True:
            print(f"Receiver: Esperando pacote seq={self.expected_seq}")
            
            # Estado: Esperar 0 de baixo (ou 1 de baixo)
            # rdt_rcv(rcvpkt)
            rcvpkt, addr = self.socket.recvfrom(1024)
            
            # Se client_address não foi fornecido, usa o endereço de quem enviou
            if client_address is None:
                client_address = addr
            
            print(f"Receiver: Pacote recebido de {addr}")
            
            # Verifica se é o pacote esperado (sem corrupt/notcorrupt - assumimos UDP checksum)
            if self.has_seq(rcvpkt, self.expected_seq):
                print(f"Receiver: Pacote correto seq={self.expected_seq}")
                
                # extract(rcvpkt, data)
                data = self.extract_data(rcvpkt)
                
                # deliver_data(data)
                delivered_data = self.deliver_data(data)
                
                # sndpkt = make_pkt(ACK, expected_seq)
                self.sndpkt = self.make_pkt(self.expected_seq, b'')
                
                # udt_send(sndpkt)
                #self.socket.sendto(self.sndpkt, client_address)
                udt_send_with_loss(self.socket, self.sndpkt, client_address)
                print(f"Receiver: ACK enviado para seq={self.expected_seq}")
                
                # Alterna número de sequência esperado
                self.expected_seq = 1 - self.expected_seq
                
                return delivered_data
                
            else:
                print(f"Receiver: Pacote incorreto, esperava seq={self.expected_seq}")
                
                # sndpkt = make_pkt(ACK, 1-expected_seq)
                wrong_seq = 1 - self.expected_seq
                self.sndpkt = self.make_pkt(wrong_seq, b'')
                
                # udt_send(sndpkt)
                #self.socket.sendto(self.sndpkt, client_address)
                udt_send_with_loss(self.socket, self.sndpkt, client_address)
                print(f"Receiver: ACK reenviado para seq={wrong_seq}")
                
                # Continua esperando o pacote correto
                continue
