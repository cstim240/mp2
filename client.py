import socket
import random
import threading

LOSS_PROBABILITY = 0.0
ERROR_PROBABILITY = 0.0
WINDOW_SIZE = 5
TIMEOUT = 1 

class Packet:
    def __init__(self, seq_num, ack_num, data, packet_type='data'):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data = data
        self.packet_type = packet_type # 'data' or 'error'
        self.checksum = self.calculate_checksum()

    def calculate_checksum(self):
        return sum(bytearray(self.data, 'utf-8')) % 256

    def has_errors(self):
        return self.calculate_checksum() != self.checksum

#added a packet_type attribute to distinguish between data and error packets
def packet_to_bytes(packet):
    return (f"{packet.seq_num}:{packet.ack_num}:{packet.checksum}:{packet.packet_type}:{packet.data}").encode('utf-8')


def bytes_to_packet(data):
    seq_num, ack_num, checksum, packet_type, payload = data.decode('utf-8').split(':', 4) #from 3 to 4
    packet = Packet(int(seq_num), int(ack_num), payload, packet_type)
    packet.checksum = int(checksum)
    return packet

def corrupt_data(data):
    if len(data) == 0:
        return data # No corruption if data is empty
    corrupted_data = list(data)
    index = random.randint(0, len(corrupted_data) - 1)
    corrupted_data[index] = chr(ord(corrupted_data[index]) ^ 0xFF)  # Flip a random bit
    return ''.join(corrupted_data)

def udt_send(packet, sock, addr):
    if random.random() < LOSS_PROBABILITY:
        print("Packet lost")
        return
    if random.random() < ERROR_PROBABILITY:
        packet.data = corrupt_data(packet.data)
        # modification - added a packet_type attribute to distinguish between data and error packets
        # this way the client can handle error packets appropriately when they are received
        error_packet = Packet(packet.seq_num, packet.ack_num, "Error: Data corrupted", 'error')
        sock.sendto(packet_to_bytes(error_packet), addr)
        return #end of mod
    sock.sendto(packet_to_bytes(packet), addr)

def udt_receive(sock):
    try:
        data, addr = sock.recvfrom(1024)
        if random.random() < LOSS_PROBABILITY:
            print("ACK lost")
            return None, addr
        return bytes_to_packet(data), addr
    except socket.timeout:
        return None, None

def rdt_send(sock, addr, data):
    window = []
    base = 0
    next_seq_num = 0
    lock = threading.Lock()
    timer = None

    #Congestion control vars
    cwnd = 1
    ssthresh = 64
    dup_ack_count = 0

    def start_timer():
        nonlocal timer
        timer = threading.Timer(TIMEOUT, timeout_handler)
        timer.start()

    def stop_timer():
        nonlocal timer
        if timer:
            timer.cancel()
            timer = None

    def timeout_handler():
        nonlocal base, cwnd, ssthresh
        with lock:
            ssthresh = max(cwnd // 2, 1) # Set ssthresh to half of cwnd
            cwnd = 1
            base = next_seq_num # Reset base to next_seq_num
            for packet in window:
                udt_send(packet, sock, addr)
            start_timer()

    while base < len(data):
        # Slow start
        while next_seq_num < base + min(cwnd, WINDOW_SIZE) and next_seq_num < len(data):
            packet = Packet(next_seq_num, 0, data[next_seq_num])
            udt_send(packet, sock, addr)
            window.append(packet)
            if base == next_seq_num:
                start_timer()
            next_seq_num += 1

        ack_packet, _ = udt_receive(sock)
        if ack_packet and not ack_packet.has_errors():
            with lock:
                if ack_packet.ack_num >= base:
                    base = ack_packet.ack_num + 1
                    window = window[base - next_seq_num:]
                    if base == next_seq_num:
                        stop_timer()
                    else:
                        start_timer()
                    if cwnd < ssthresh:
                        cwnd += 1 # Slow start
                    else:
                        cwnd += 1 / cwnd # Congestion avoidance
                    dup_ack_count = 0
                elif ack_packet.ack_num == base - 1:
                    dup_ack_count += 1
                    if dup_ack_count == 3: # Fast retransmit on 3 duplicate ACKs
                        ssthresh = max(cwnd // 2, 1)
                        cwnd = ssthresh + 3
                        udt_send(window[0], sock, addr)
                
    stop_timer()

def rdt_receive(sock):
    expected_seq_num = 0
    received_data = []

    while True:
        packet, addr = udt_receive(sock)
        if packet and not packet.has_errors():
            if packet.seq_num == expected_seq_num:
                print(f"Received: {packet.data}")
                received_data.append(packet.data)
                ack_packet = Packet(0, packet.seq_num, "")
                udt_send(ack_packet, sock, addr)
                expected_seq_num += 1
            else:
                ack_packet = Packet(0, expected_seq_num - 1, "")
                udt_send(ack_packet, sock, addr)

        if packet and packet.data == "END":
            break

    return received_data

if __name__ == "__main__":
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 10000)
    client_sock.settimeout(TIMEOUT)

    print("Client is sending data...")

    data = ["Message 1", "Message 2", "Message 3", "END"]
    rdt_send(client_sock, server_address, data)

    response = rdt_receive(client_sock)
    print("Received response:", response)
    
    complete_message = rdt_receive(client_sock)
    print("Received complete message:", complete_message)
