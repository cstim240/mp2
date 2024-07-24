import socket 
import threading
import time


# Constants for protocol
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12000
BUFFER_SIZE = 1024
CONGESTION_WINDOW_INIT_SIZE = 1
FLOW_CONTROL_WINDOW_SIZE = 5 #sample max window size

# Simulated network params
RTT = 0.1 # RTT in sec

class PipelinedReliableTransferProtocolClient:
    # Constructor for client
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port)) # Connect to server
        print(f"Client connected to server on {self.host}:{self.port}")
        self.base = 0 # Base sequence number
        self.next_seq_num = 0
        self.window_size = FLOW_CONTROL_WINDOW_SIZE
        self.congestion_window = CONGESTION_WINDOW_INIT_SIZE
        self.lock = threading.Lock() # Lock for thread safety
        self.ack_event = threading.Event() # Event to signal ACK received
        self.timeout_interval = RTT
    
    # Function to send a message
    def send_packet(self, data):
        # self.lock is used to ensure that only one thread can access the shared variables at a time
        with self.lock: 
            # if the window is not full, send the packet
            if self.next_seq_num < self.base + min(self.window_size, self.congestion_window):
                message = f"{self.next_seq_num}: {data}"
                self.socket.send(message.encode('utf-8'))
                print(f"Sent: {message}")
                self.next_seq_num += 1
            else:
                print("Window full, waiting for ACK...")

    # Function to handle ACKs
    def handle_ack(self):
        while True:
            try: 
                # Receive ACK message from serverr
                ack_message = self.socket.recv(BUFFER_SIZE).decode('utf-8')
                print(f"ACK received: {ack_message}")

                # Extract ACK number from received message
                #assumming ACK format is "ACK: <ack_num>"
                ack_num_str = ack_message.split(":")[1].strip()
                ack_num = int(ack_num_str) # this triggers ValueError if ack_num_str is not an integer

                #Update the client's state based on the received ACK
                with self.lock: 
                    # if self.base means that the ACK number is within the window and the packet has been received
                    if self.base <= ack_num < self.next_seq_num:
                        self.base = ack_num + 1
                        self.congestion_window = min(self.congestion_window + 1, FLOW_CONTROL_WINDOW_SIZE)
                        self.ack_event.set() # Signal that an ACK has been received
                        self.ack_event.clear() # Clear the event after processing the ACK
            except ValueError:
                print(f"Error: Received invalid ACK message - '{ack_message}'")

    # Function to start the client
    def start(self, data):
        threading.Thread(target=self.handle_ack).start() # Start the ACK handling thread
        for message in data:
            self.send_packet(message)
            self.ack_event.wait(self.timeout_interval) # Wait for ACK or timeout

if __name__ == "__main__":
    client = PipelinedReliableTransferProtocolClient(SERVER_HOST, SERVER_PORT)
    messages = ["Message 1", "Message 2", "Message 3", "Message 4", "Message 5"]
    client.start(messages)

