# 66011464 ราธา โรจน์รุจิพงศ์ sec17

import sys
import socket
import hashlib

Packet_size = 1450
Seq_size = 4
Hash_size = 32
Header_size = Seq_size + Hash_size
Payload_size = Packet_size - (Header_size)
Byte_order = 'big'
Timeout_duration = 1
Window_size = 10

class FileReceiverUDP:
    def __init__(self, server_ip, server_port: int):
        self.Server_ip = server_ip
        self.Server_port = server_port
        self.Server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Server_socket.bind((self.Server_ip, self.Server_port))
        self.Buffer = {}

    def receive_file(self):
        while True:
            try:
                Filename_received = False
                Expected_seq_num = 0
                File_name = None
                Client_address = None
                
                while not Filename_received:
                    Data, Client_address = self.Server_socket.recvfrom(Packet_size)
                    
                    if len(Data) < Header_size:
                        print("Received incomplete packet, ignoring...")
                        continue
                    
                    Header = Data[:Header_size]
                    Seq_number = int.from_bytes(Header[:Seq_size], Byte_order)
                    Received_checksum = Header[Seq_size:]
                    
                    Payload = Data[Header_size:]
                    Calculated_checksum = hashlib.sha256(Payload).digest()
                    
                    if Received_checksum == Calculated_checksum:
                        if Seq_number == 0:
                            File_name = Payload.decode("utf-8")
                            print(f"Receiving file: {File_name}")
                            Expected_seq_num = 0
                            Filename_received = True
                            self.Server_socket.sendto((0).to_bytes(Seq_size, Byte_order), Client_address)
                        else:
                            print(f"Expected sequence 0 for filename, got {Seq_number}, sending ACK 0")
                            self.Server_socket.sendto((0).to_bytes(Seq_size, Byte_order), Client_address)
                    else:
                        print("Checksum mismatch for filename packet, ignoring...")
                        
                with open(File_name, 'wb') as File:
                    Eof_received = False
                    
                    while not Eof_received:
                        Data, Addr = self.Server_socket.recvfrom(Packet_size)
                        
                        if len(Data) < Header_size:
                            print("Received an incomplete packet, ignoring...")
                            continue
                        
                        Header = Data[:Header_size]
                        Seq_number = int.from_bytes(Header[:Seq_size], Byte_order)
                        Received_checksum = Header[Seq_size:]
                        
                        Payload = Data[Header_size:]
                        Calculated_checksum = hashlib.sha256(Payload).digest()
                        
                        if Received_checksum == Calculated_checksum:
                            if len(Payload) == 0:
                                self.Server_socket.sendto(Seq_number.to_bytes(Seq_size, Byte_order), Addr)
                                Eof_received = True
                                continue
                            
                            if Seq_number >= Expected_seq_num:
                                self.Buffer[Seq_number] = Payload
                            else:
                                print(f"Duplicate packet {Seq_number}, already processed")
                            
                            while Expected_seq_num in self.Buffer:
                                File.write(self.Buffer[Expected_seq_num])
                                del self.Buffer[Expected_seq_num]
                                Expected_seq_num += 1
                            
                            Ack_num = Expected_seq_num - 1
                            self.Server_socket.sendto(Ack_num.to_bytes(Seq_size, Byte_order), Addr)
                        else:
                            print(f"Checksum mismatch for segment {Seq_number}, ignoring...")
                            Ack_num = Expected_seq_num - 1
                            if Ack_num >= 0:
                                self.Server_socket.sendto(Ack_num.to_bytes(Seq_size, Byte_order), Addr)
                                print(f"Resent ACK {Ack_num} after checksum failure")
                
                print(f"File {File_name} received successfully.")
                print(hashlib.sha256(open(File_name, 'rb').read()).hexdigest())
                self.Buffer.clear()
                return 0

            except Exception as e:
                print(f"Error: {e}")
            except KeyboardInterrupt:
                print("Server closed.")
                self.Server_socket.close()
                break

def execute():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port>")
        sys.exit(1)

    Server_ip = sys.argv[1]
    Server_port = int(sys.argv[2])
    Receiver = FileReceiverUDP(Server_ip, Server_port)
    
    print(f"Server is listening on {Server_ip}:{Server_port}")
    Receiver.receive_file()

if __name__ == '__main__':
    execute()
