import sys

# importing necessary module directories
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/bluno_beetle')
sys.path.append('/home/kenneth/Desktop/CG4002/scripts/helper')

from bluno_beetle import BlunoBeetle
from bluno_beetle_game_state import BlunoBeetleGameState
from bluno_beetle_udp import BlunoBeetleUDP
from _socket import SHUT_RDWR
from collections import deque

#import asyncio
import constant
import socket
import threading
import traceback
import time

"""
import asyncio
import websockets
import time

SERVER_ADDRESS = "ws://localhost:8080"
BUFFER_SIZE = 1024
DATA_TO_SEND = b'x' * 20 * 16 # 1 MB of data

class WebSocketClient:
     async def send_message(self, message):
         async with websockets.connect(SERVER_ADDRESS) as websocket:
             print(f'Sending message: {message}'.ljust(40))
             await websocket.send(message)
             response = await websocket.recv()
             print(f'Response received: {response}'.ljust(40))

 async def main():
     client = WebSocketClient()
     while True:
         data = input("Message: ")
         await client.send_message(data)

 if __name__ == '__main__':
     asyncio.run(main())

async def start_client():
    async with websockets.connect(SERVER_ADDRESS) as websocket:
        res = []
        print('Client connected. Sending data...')

        for i in range(21):
            start_time = time.time()

            # Send the data to the server in chunks
            total_sent = 0
            while total_sent < len(DATA_TO_SEND):
                try:
                    # data = DATA_TO_SEND[total_sent:]
                    data = input("Input: ")
                    sent = await websocket.send(data)
                except websockets.exceptions.ConnectionClosedError:
                    print('Server closed the connection prematurely.')
                    return

                if not sent:
                    break
                total_sent += sent

            # Wait for the server to send the data back
            received_data = b''
            while len(received_data) < len(DATA_TO_SEND):
                data = await websocket.recv()
                if not data:
                    break
                received_data += data

            end_time = time.time()

            # Calculate the time taken to send and receive the data
            time_taken = end_time - start_time
            res.append(time_taken)

        print('Average Data sent and received in {:.4f} seconds.'.format(sum(res) / len(res)))

asyncio.run(start_client())

class WebSocketClient:
    def __init__(self, host_name, port_num):
        self.server_address = f"ws://{host_name}:{port_num}"

        # self.lock = asyncio.Lock()

        self.ble_packet = BLEPacket()

    async def send(self):
        async with websockets.connect(self.server_address) as websocket:
            print('Connected to Ultra96')
            while True:
                try:
                    sent = await websocket.send("Hello".encode())
                except websockets.exceptions.ConnectionClosedError:
                    print('Server closed the connection prematurely.')
                    return

    async def receive_packet(self):
        message = await self.websocket.recv()
        self.ble_packet.unpack(message)
        print("CRC: ", self.packer.get_crc())

    async def run(self):
        await self.send()
"""

class Controller(threading.Thread):
    def __init__(self, params):
        super().__init__()
        """
        # Create a TCP/IP socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.client_socket = client_socket
        self.connection = client_socket.connect(("localhost" , 8080))
        self.secret_key = None
        self.secret_key_bytes = None
        """
        # Flags
        self.shutdown = threading.Event()
        
        self.beetles = [
                BlunoBeetleGameState(params[0]), 
                BlunoBeetleGameState(params[1]), 
                BlunoBeetleUDP(params[2])
            ]
        
        # For statistics calculation
        self.start_time = 0
        self.prev_time = 0
        self.prev_processed_bit_count = 0
        self.current_data_rate = 0

        #self.data = b''

        #self.client = Client()

    def setup(self):
        print('Setting up Secret Key')
        print('Default Secret Key: chrisisdabest123')

        secret_key = 'chrisisdabest123'

        self.secret_key = secret_key
        self.secret_key_bytes = bytes(str(secret_key), encoding='utf-8')

    def close_connection(self):
        self.connection.shutdown(SHUT_RDWR)
        self.connection.close()
        self.shutdown.set()
        self.client_socket.close()

        print("Shutting Down Connection")
    
    def receive_game_state(self):
        while not self.shutdown.is_set():
            message = self.client_socket.recv(128)
            if len(message) > 0:
                print(message)

    def run_threads(self):
        # create thread for printing statistics
        print_thread = threading.Thread(target=self.print_statistics, args=())
        #receive_thread = threading.Thread(target=self.receive_game_state, args=()) 
        for i in range(18):
            print()

        self.start_time = time.perf_counter()

        #self.client.start()

        for beetle in self.beetles:
            beetle.start()

        print_thread.start()
        #receive_thread.start()
    
    # run() function invoked by thread.start()
    def run(self):
        #self.setup()
        self.run_threads()
        """
        while not self.shutdown.is_set():
            try:
                #data = input("Enter char: ")

                if not BlunoBeetle.packet_queue:
                    continue
                
                data = BlunoBeetle.packet_queue.popleft()
                #print(data)
                self.client_socket.send(data)
            except Exception as _:
                # traceback.print_exc()
                #self.close_connection()
                continue
        """
    # prints beetle data and statistics to std output
    def print_statistics(self):
        while True:
            for i in range(18):
                print(constant.LINE_UP, end="")

            print("***********************************************************************************************************")
            processed_bit_count = 0
            fragmented_packet_count = 0
            for beetle in self.beetles:
                processed_bit_count += beetle.get_processed_bit_count()
                fragmented_packet_count += beetle.get_fragmented_packet_count()
                beetle.print_beetle_info()

            print("Statistics".ljust(80))
            current_time = time.perf_counter()
            if current_time - self.prev_time >= 1:
                self.current_data_rate = ((processed_bit_count - self.prev_processed_bit_count) / 1000) / (current_time - self.prev_time)
                self.prev_time = current_time
                self.prev_processed_bit_count = processed_bit_count
            print("Current data rate: {} kbps".ljust(80).format(self.current_data_rate))
            print("Average Data rate: {} kbps".ljust(80).format(
                (processed_bit_count / 1000) / (current_time - self.start_time)
            ))
            print("No. of fragmented packets: {}".ljust(80).format(fragmented_packet_count))
            print("************************************************************************************************************")

if __name__ == '__main__':
    #client = WebSocketClient("localhost", 8080)
    #asyncio.run(client.run())
    controller = Controller([
        [0, 1, constant.P1_IR_TRANSMITTER],     # P1 gun (IR transmitter)
        #[0, 2, constant.P2_IR_RECEIVER],        # P2 vest (IR receiver)
        [0, 2, constant.P1_IR_RECEIVER],        # P1 vest (IR receiver)
        [0, 3, constant.P1_IMU_SENSOR],         # P1 glove (IMU and flex sensors)
        #[1, 4, constant.P2_IR_TRANSMITTER],     # P2 gun (IR transmitter)
        #[1, 5, constant.P2_IR_RECEIVER],        # P2 vest (IR receiver)
        #[1, 6, constant.P2_IMU_SENSOR]          # P2 glove (IMU and flex sensors)
    ])
    controller.start()
