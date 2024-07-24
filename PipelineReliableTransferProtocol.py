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


