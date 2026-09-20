# 66011464 ราธา โรจน์รุจิพงศ์ sec17

import os
import sys
import socket
import hashlib
import time

Packet_size = 1450
Seq_size = 4
Hash_size = 32
Header_size = Seq_size + Hash_size
Payload_size = Packet_size - Header_size
Byte_order = 'big'
Timeout_duration = 1

class FileSenderUDP:
    def __init__(self, server_address, server_port: int):
        self.Server_address = server_address
        self.Server_port = server_port
        self.Udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Udp_socket.settimeout(Timeout_duration)

    def split_data(self, content: bytes):
        return [content[i:i + Payload_size] for i in range(0, len(content), Payload_size)]

    def send_chunks(self, content: bytes):
        Fragments = self.split_data(content)
        Base_index = 0
        Next_index = 0
        Sliding_window = {}
        
        while Base_index < len(Fragments):
            if Next_index % 10 == 0:
                print(f"Sending segments {Next_index} to {min(Base_index + 10, len(Fragments)) - 1}")
            
            while Next_index < len(Fragments) and Next_index < Base_index + 10:
                Segment = Fragments[Next_index]
                Segment_hash = hashlib.sha256(Segment).digest()
                Header = Next_index.to_bytes(Seq_size, Byte_order) + Segment_hash
                Packet = Header + Segment
                self.Udp_socket.sendto(Packet, (self.Server_address, self.Server_port))
                Sliding_window[Next_index] = (Packet, time.time(), Segment)
                Next_index += 1
            
            try:
                Ack_data, _ = self.Udp_socket.recvfrom(Seq_size)
                Received_ack = int.from_bytes(Ack_data, Byte_order)
                print(f"ACK received for segment {Received_ack}")
                
                if Received_ack >= Base_index:
                    for Seq in list(Sliding_window.keys()):
                        if Seq <= Received_ack:
                            del Sliding_window[Seq]
                    Base_index = Received_ack + 1
                
                elif Received_ack < Base_index:
                    Rollback_index = Received_ack + 1
                    if Rollback_index < Next_index:
                        Next_index = Rollback_index
                        for Retry_seq in range(Rollback_index, min(Base_index + 10, len(Fragments))):
                            if Retry_seq not in Sliding_window:
                                Retry_segment = Fragments[Retry_seq]
                                Retry_hash = hashlib.sha256(Retry_segment).digest()
                                Retry_header = Retry_seq.to_bytes(Seq_size, Byte_order) + Retry_hash
                                Retry_packet = Retry_header + Retry_segment
                                Sliding_window[Retry_seq] = (Retry_packet, time.time(), Retry_segment)
            except socket.timeout:
                Current_time = time.time()
                for Seq, (Pkt, Last_attempt, Original_segment) in list(Sliding_window.items()):
                    if Current_time - Last_attempt > Timeout_duration:
                        Hash_value = hashlib.sha256(Original_segment).digest()
                        Header = Seq.to_bytes(Seq_size, Byte_order) + Hash_value
                        Retry_packet = Header + Original_segment
                        self.Udp_socket.sendto(Retry_packet, (self.Server_address, self.Server_port))
                        Sliding_window[Seq] = (Retry_packet, Current_time, Original_segment)
        return Next_index

    def send_end_signal(self, sequence_number):
        Eof_packet = sequence_number.to_bytes(Seq_size, Byte_order) + hashlib.sha256(b'').digest() + b''
        Retries = 0
        Max_retries = 5
        
        while Retries < Max_retries:
            self.Udp_socket.sendto(Eof_packet, (self.Server_address, self.Server_port))
            try:
                Ack_data, _ = self.Udp_socket.recvfrom(Seq_size)
                Received_ack = int.from_bytes(Ack_data, Byte_order)
                if Received_ack == sequence_number:
                    print("EOF confirmed.")
                    return True
                else:
                    print("Unexpected ACK for EOF, retrying...")
            except socket.timeout:
                print("EOF timeout, retrying...")
            Retries += 1
        print("Failed to confirm EOF after max retries.")
        return False

    def transmit_file(self, file_path: str):
        File_name = os.path.basename(file_path).encode("utf-8")
        print(f"Transmitting filename: {File_name.decode('utf-8')}")
        Final_sequence = self.send_chunks(File_name)
        Start_time = time.time()
        
        with open(file_path, 'rb') as File:
            File_data = File.read()
            print(f"Sending file content ({len(File_data)} bytes)")
            Final_sequence = self.send_chunks(File_data)
        
        print("Sending EOF signal...")
        if self.send_end_signal(Final_sequence):
            print("File transmission successful.")
            print(hashlib.sha256(open(file_path, 'rb').read()).hexdigest())
        else:
            print("File transmission encountered errors.")
        
        Duration = time.time() - Start_time
        print(f"Total time taken: {Duration:.2f} seconds")
        self.Udp_socket.close()

def execute():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <file_path> <server_ip> <server_port>")
        sys.exit(1)
    
    File_location = sys.argv[1]
    Server_ip = sys.argv[2]
    Server_port = int(sys.argv[3])
    
    Sender = FileSenderUDP(Server_ip, Server_port)
    Sender.transmit_file(File_location)
    return 0

if __name__ == "__main__":
    execute()
