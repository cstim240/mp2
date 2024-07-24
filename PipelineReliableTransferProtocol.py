import socket 
import threading
import time

# Constants for protocol
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12000
BUFFER_SIZE = 1024
CONGESTION_WINDOW_INIT_SIZE = 1
FLOW_CONTROL_WINDOW_SIZE = 5 
#this is the maximum number of packets that can be sent without receiving an ack

# Simulated network params
RTT = 0.1 # round trip time in seconds

class PipelinedReliableTransferProtocolServer:
    # Constructor for the server
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # Create a TCP/IP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        # Listen for incoming connections
        self.socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

    # Function to handle a client
    def handle_client(self, client_socket, address):
        congestion_window = CONGESTION_WINDOW_INIT_SIZE
        ack_num = 0

        while True: # Loop to keep the connection open
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if not message: 
                break # If no message is received, break
            print(f"Received message from {address}: {message}")

            # Simulate ACK and flow control window update 
            time.sleep(RTT) #simulate delay for receiving ACK

            client_socket.send(f"ACK: {ack_num}".encode('utf-8')) #send ACK for received packet
            ack_num += 1 #increment ACK number for next packet
            # Adjust congestion window size for congestion control (simplified)
            congestion_window = min(congestion_window + 1, FLOW_CONTROL_WINDOW_SIZE)
        client_socket.close()

    # Function to start the server
    def start(self):
        while True: 
            client_socket, address = self.socket.accept()
            print(f"Connection from {address}")
            # Create a new thread to handle the client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            client_thread.start()

if __name__ == "__main__":
    server = PipelinedReliableTransferProtocolServer(SERVER_HOST, SERVER_PORT)
    server.start()


# Mechanisms of this protocol:

# Connection-oriented -
# The server uses TCP/IP sockets, which are connection-oriented.
# Inspect line 22: self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM), 
# where SOCK_STREAM specifies a TCP socket.

# Reliable -
# ACK: the server sends an acknowledgement for each recevied packed
# Inspect line 42: client_socket.send(f"ACK: {ack_num}".encode('utf-8')). 
# This ensures the sender/client knows that the packet was received. 
# The Loop for Connection in handle_client keeps the connection open to continuously receive 
# and acknowledge messages, ensuring reliable data transfer until the connection is explicitly closed.

# Pipelined -
# Continuous data flow: The server does not wait for an acknowledgement of one packet before sending
# the next packet. This is implied by the continuous loops of receiving and ACKing
# packets before proceeding. This allows for multiple pakets to be "in flight" at the same time, 
# characteristic of a pipelined protocol.

# Flow Control -
# Inspect line 45: congestion_window = min(congestion_window + 1, FLOW_CONTROL_WINDOW_SIZE).
# Window Size: The constant FLOW_CONTROL_WINDOW_SIZE specifies the maximum number of packets
# that can be sent without receivig an acknowledgement. Although the code does not explicitly 
# limit the sending of packets based on this window (since it's a server-side implementation
# focusing on receiving data), the concept is present and would be applied on the client-side to 
# prevent overflowing the server's buffer.

# Congestion Control -
# Congestion Window Adjustment: The server simulates basic congestion control by adjusting the
# congestion_window variable, see line 45 (congestion_window = min(congestion_window + 1, FLOW_CONTROL_WINDOW_SIZE)).
# After each ACK, the congestion window is incremented by 1, up to the limit set by FLOW_CONTROL_WINDOW_SIZE.
# This simple approach mimics the behaviour of increasing the congestion dinwo in response to successful 
# transmission, although real-world protocols would decrease the window upon detecting congestion signals (ie. packet loss or timeouts)



