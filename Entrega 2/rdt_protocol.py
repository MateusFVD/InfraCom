import socket
import threading
import time
import struct

class RDT3_0_Sender:
    def __init__(self, socket_obj, server_address, timeout=2.0):
        self.socket = socket_obj
        self.server_address = server_address
        self.timeout = timeout
        self.sndpkt = None
        self.seq_num = 0  # Inicia com número de sequência 0
        self.timer = None
        
    def make_pkt(self, seq, data, checksum=0):
        """Criando um pacote com número de sequência, dados e checksum"""
        # Formato: seq_num (1 byte) + checksum (4 bytes) + data
        # Limita dados a 1000 bytes para deixar espaço para cabeçalho
        if len(data) > 1000:
            data = data[:1000]
        pkt = struct.pack('!BI', seq, checksum) + data
        return pkt
    
    def extract_seq(self, pkt):
        """Extraindo o número de sequência do pacote"""
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def has_seq(self, pkt, expected_seq):
        """Verificando se o pacote tem o número de sequência esperado"""
        seq = self.extract_seq(pkt)
        return seq == expected_seq
    
    def start_timer(self):
        """Iniciando o timer para timeout"""
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self.timeout_handler)
        self.timer.start()
    
    def stop_timer(self):
        """Parando o timer"""
        if self.timer:
            self.timer.cancel()
            self.timer = None
    
    def timeout_handler(self):
        """Manipulador de timeout - reenviando o pacote"""
        print(f"RDT3.0 Sender: Timeout! Reenviando pacote seq={self.seq_num}")
        self.socket.sendto(self.sndpkt, self.server_address)
        self.start_timer()
    
    def rdt_send(self, data):
        """Método principal para envio confiável de dados, com timeout"""
        print(f"Sender: Enviando dados com seq={self.seq_num}")
        
        # Estado: Esperar chamada 0 de cima (ou 1 de cima)
        # make_pkt(seq_num, data, checksum)
        self.sndpkt = self.make_pkt(self.seq_num, data, 0)
        
        # udt_send(sndpkt)
        self.socket.sendto(self.sndpkt, self.server_address)
        
        # start_timer
        self.start_timer()
        
        # Estado: Esperar ACK
        while True:
            try:
                # Configura timeout no socket para poder detectar timeout
                self.socket.settimeout(0.5)  # Timeout curto para verificar se timer expirou
                
                # rdt_rcv(rcvpkt)
                rcvpkt, addr = self.socket.recvfrom(1024)
                
                print(f"Sender: ACK recebido de {addr}")
                
                # Verifica se é ACK correto
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
                # Continua o loop - timer pode ter expirado
                continue
        
        # Restaura socket para modo bloqueante
        self.socket.settimeout(None)

class RDT3_0_Receiver:
    def __init__(self, socket_obj):
        self.socket = socket_obj
        self.expected_seq = 0  # Inicia esperando sequência 0
        self.sndpkt = None
        
    def make_pkt(self, seq, data=b'', checksum=0):
        """Cria um pacote ACK com número de sequência"""
        # Formato: seq_num (1 byte) + checksum (4 bytes) + data
        pkt = struct.pack('!BI', seq, checksum) + data
        return pkt
    
    def extract_seq(self, pkt):
        """Extrai o número de sequência do pacote"""
        if len(pkt) < 1:
            return -1
        return struct.unpack('!B', pkt[:1])[0]
    
    def extract_data(self, pkt):
        """Extrai os dados do pacote"""
        if len(pkt) < 5:
            return b''
        return pkt[5:]  # Pula seq_num (1 byte) + checksum (4 bytes)
    
    def has_seq(self, pkt, expected_seq):
        """Verifica se o pacote tem o número de sequência esperado"""
        seq = self.extract_seq(pkt)
        return seq == expected_seq
    
    def deliver_data(self, data):
        """Entrega os dados para a camada superior"""
        return data
    
    def rdt_rcv(self, client_address=None):
        """Método principal para recepção confiável de dados"""
        while True:
            print(f"Receiver: Esperando pacote seq={self.expected_seq}")
            
            # Estado: Esperar 0 de baixo (ou 1 de baixo)
            # rdt_rcv(rcvpkt)
            rcvpkt, addr = self.socket.recvfrom(1024)
            
            # Se client_address não foi fornecido, usa o endereço de quem enviou
            if client_address is None:
                client_address = addr
            
            print(f"Receiver: Pacote recebido de {addr}")
            
            # Verifica se é o pacote esperado e não corrompido
            if self.has_seq(rcvpkt, self.expected_seq):
                print(f"Receiver: Pacote correto seq={self.expected_seq}")
                
                # extract(rcvpkt, data)
                data = self.extract_data(rcvpkt)
                
                # deliver_data(data)
                delivered_data = self.deliver_data(data)
                
                # sndpkt = make_pkt(ACK, expected_seq, checksum)
                self.sndpkt = self.make_pkt(self.expected_seq, b'', 0)
                
                # udt_send(sndpkt)
                self.socket.sendto(self.sndpkt, client_address)
                print(f"Receiver: ACK enviado para seq={self.expected_seq}")
                
                # Alterna número de sequência esperado
                self.expected_seq = 1 - self.expected_seq
                
                return delivered_data
                
            else:
                print(f"Receiver: Pacote incorreto, esperava seq={self.expected_seq}")
                
                # sndpkt = make_pkt(ACK, 1-expected_seq, checksum)
                wrong_seq = 1 - self.expected_seq
                self.sndpkt = self.make_pkt(wrong_seq, b'', 0)
                
                # udt_send(sndpkt)
                self.socket.sendto(self.sndpkt, client_address)
                print(f"Receiver: ACK reenviado para seq={wrong_seq}")
                
                # Continua esperando o pacote correto
                continue
