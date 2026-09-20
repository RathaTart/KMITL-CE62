#!/usr/bin/env python3
import os
import sys
import socket
import hashlib
import time

PKT_SIZE = 1450
SEQ_LEN = 4
HASH_LEN = 32
HDR_LEN = SEQ_LEN + HASH_LEN
PL_SIZE = PKT_SIZE - HDR_LEN
ORDER = 'big'
TIMEOUT_VAL = 1

class UDPClient:
    def __init__(self, srv_ip, srv_port: int):
        self.srv_ip = srv_ip
        self.srv_port = srv_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(TIMEOUT_VAL)

    def chunkify(self, data: bytes):
        return [data[i:i + PL_SIZE] for i in range(0, len(data), PL_SIZE)]

    def transmit_data(self, data: bytes):
        segments = self.chunkify(data)
        base_idx = 0
        next_seq = 0
        window = {}
        while base_idx < len(segments):
            if next_seq % 10 == 0:
                print(f"Sending segments {next_seq} to {min(base_idx + 10, len(segments)) - 1}")
            while next_seq < len(segments) and next_seq < base_idx + 10:
                seg = segments[next_seq]
                hash_val = hashlib.sha256(seg).digest()
                hdr = next_seq.to_bytes(SEQ_LEN, ORDER) + hash_val
                pkt = hdr + seg
                self.sock.sendto(pkt, (self.srv_ip, self.srv_port))
                window[next_seq] = (pkt, time.time(), seg)
                next_seq += 1
            try:
                ack, _ = self.sock.recvfrom(SEQ_LEN)
                ack_num = int.from_bytes(ack, ORDER)
                print(f"ACK received for segment {ack_num}")
                if ack_num >= base_idx:
                    for seq in list(window.keys()):
                        if seq <= ack_num:
                            del window[seq]
                    base_idx = ack_num + 1
                elif ack_num < base_idx:
                    if base_idx - ack_num > 1:
                        rollback = ack_num + 1
                        if rollback < next_seq:
                            next_seq = rollback
                            for seq_fix in range(rollback, min(base_idx + 10, len(segments))):
                                if seq_fix not in window:
                                    seg = segments[seq_fix]
                                    hash_val = hashlib.sha256(seg).digest()
                                    hdr = seq_fix.to_bytes(SEQ_LEN, ORDER) + hash_val
                                    pkt = hdr + seg
                                    window[seq_fix] = (pkt, time.time(), seg)
            except socket.timeout:
                cur_time = time.time()
                for seq, (pkt, last_time, orig) in list(window.items()):
                    if cur_time - last_time > TIMEOUT_VAL:
                        hash_val = hashlib.sha256(orig).digest()
                        hdr = seq.to_bytes(SEQ_LEN, ORDER) + hash_val
                        new_pkt = hdr + orig
                        self.sock.sendto(new_pkt, (self.srv_ip, self.srv_port))
                        window[seq] = (new_pkt, cur_time, orig)
        return next_seq

    def transmit_eof(self, seq_num):
        eof_pkt = seq_num.to_bytes(SEQ_LEN, ORDER) + hashlib.sha256(b'').digest() + b''
        attempts = 0
        max_attempts = 5
        while attempts < max_attempts:
            self.sock.sendto(eof_pkt, (self.srv_ip, self.srv_port))
            try:
                ack, _ = self.sock.recvfrom(SEQ_LEN)
                ack_num = int.from_bytes(ack, ORDER)
                if ack_num == seq_num:
                    print("EOF confirmed.")
                    return True
                else:
                    print("Unexpected ACK for EOF, retrying...")
            except socket.timeout:
                print("EOF timeout, retrying...")
            attempts += 1
        print("Failed to confirm EOF after max retries.")
        return False

    def send_file(self, file_path: str):
        fname = os.path.basename(file_path).encode("utf-8")
        print(f"Transmitting filename: {fname.decode('utf-8')}")
        last_seq = self.transmit_data(fname)
        start_time = time.time()
        with open(file_path, 'rb') as f:
            content = f.read()
            print(f"Transmitting file data ({len(content)} bytes)")
            last_seq = self.transmit_data(content)
        print("Transmitting EOF...")
        if self.transmit_eof(last_seq):
            print("File sent successfully.")
            print(hashlib.sha256(open(file_path, 'rb').read()).hexdigest())
        else:
            print("File transmission encountered errors.")
        elapsed = time.time() - start_time
        print(f"Elapsed time: {elapsed:.2f} seconds")
        self.sock.close()

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <file_path> <server_ip> <server_port>")
        sys.exit(1)
    file_path = sys.argv[1]
    srv_ip = sys.argv[2]
    srv_port = int(sys.argv[3])
    client = UDPClient(srv_ip, srv_port)
    client.send_file(file_path)
    return 0

if __name__ == "__main__":
    main()
