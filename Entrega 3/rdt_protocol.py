# Module: rdt_protocol.py
# Responsible for the implementation of the reliable transport layer (RDT 3.0).

import socket

PACKET_SIZE = 1024  # Total size of the UDP datagram

def send_data(sock, message, destination_address, sequence_number_tracker):
    """
    Sends data reliably using the RDT 3.0 protocol.

    Args:
        sock (socket.socket): The sender's socket.
        message (str): The message to be sent.
        destination_address (tuple): The recipient's address (IP, port).
        sequence_number_tracker (dict): A dictionary to track the sequence number.
    """
    offset = 0
    delimiter = "::"
    header_size = len(f"{sequence_number_tracker['num']}{delimiter}")
    payload_size = PACKET_SIZE - header_size

    # Fragment the message into segments and send them one by one
    while offset < len(message):
        segment = message[offset : offset + payload_size]
        ack_confirmed = False

        # Build the datagram with the sequence number
        datagram = f"{sequence_number_tracker['num']}{delimiter}{segment}"
        
        # Send the datagram and wait for the ACK
        sock.sendto(datagram.encode('utf-8'), destination_address)

        while not ack_confirmed:
            try:
                ack_packet, _ = sock.recvfrom(PACKET_SIZE)
                # Check if the ACK corresponds to the sent sequence
                if ack_packet.decode('utf-8') == f"ACK{sequence_number_tracker['num']}":
                    ack_confirmed = True
                    # Alternate the sequence number (0 -> 1, 1 -> 0)
                    sequence_number_tracker['num'] = 1 - sequence_number_tracker['num']
                else:
                    # Incorrect ACK, resend the packet
                    sock.sendto(datagram.encode('utf-8'), destination_address)
            except socket.timeout:
                # Timeout: resend the packet
                sock.sendto(datagram.encode('utf-8'), destination_address)
            except ConnectionResetError:
                print("Warning: The connection was reset by the other side.")
                return

        offset += payload_size

def receive_data(sock, received_packet, sender_address, expected_sequence_tracker):
    """
    Receives data reliably using the RDT 3.0 protocol.

    Args:
        sock (socket.socket): The receiver's socket.
        received_packet (bytes): The received data packet.
        sender_address (tuple): The sender's address.
        expected_sequence_tracker (dict): Dictionary to track the expected sequence.

    Returns:
        bytes: The message content if the packet is received correctly, otherwise None.
    """
    try:
        if not received_packet:
            return None

        # Split the packet into the header (sequence number) and the payload
        delimiter = b"::"
        header, payload = received_packet.split(delimiter, 1)
        received_sequence_num = int(header.decode('utf-8'))

        # Compare the received sequence number with the expected one
        if received_sequence_num == expected_sequence_tracker['num']:
            # Correct sequence: send ACK and return the payload
            ack_msg = f"ACK{expected_sequence_tracker['num']}"
            sock.sendto(ack_msg.encode('utf-8'), sender_address)
            # Alternate the expected sequence number for the next packet
            expected_sequence_tracker['num'] = 1 - expected_sequence_tracker['num']
            return payload
        else:
            # Incorrect sequence (duplicate packet): resend ACK of the last correct sequence
            ack_msg = f"ACK{1 - expected_sequence_tracker['num']}"
            sock.sendto(ack_msg.encode('utf-8'), sender_address)
            return None  # Discard the out-of-order packet
            
    except (ValueError, IndexError):
        # Malformed packet, ignore
        return None
    except ConnectionResetError:
        print("Warning: The connection with the client has been terminated.")
        return None