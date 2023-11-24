import argparse

from simpleemu.simpleudp import simpleudp
from simpleemu.simpletcp import simpletcp
from simpleemu.simplecoin import SimpleCOIN
from utils.packet import *
from utils.log import *

import time

# Network
serverAddressPort = ("10.0.0.30", 9999)
clientAddressPort = ("10.0.0.10", 9999)

# parse args
parser = argparse.ArgumentParser(description="Using TCP or UDP")
parser.add_argument("--protocol", "-p", type=str, choices=["tcp", "udp", "t", "u"], default="udp",
                    help="choosing protocol, tcp/t or udp/u(default udp)")
args = parser.parse_args()

# tcp/udp
if args.protocol in ["udp", "u"]:
    protocol = "udp"
    simple = simpleudp
    pro_num = 17
else:
    protocol = "tcp"
    simple = simpletcp
    simple.listen(serverAddressPort)
    pro_num = 6

# NetworkSetting
ifce_name, node_ip = simple.get_local_ifce_ip('10.0.')

# Simple coin
app = SimpleCOIN(ifce_name=ifce_name, n_func_process=1, lightweight_mode=True)

first = True
num_chunks = 0
cache_time = 0.0

@app.main()
def main(simplecoin: SimpleCOIN.IPC, af_packet: bytes):
    global num_chunks, cache_time, pro_num, first
    if first and pro_num == 6:
        conn, addr = simple.accept(serverAddressPort)
        first = False

    if pro_num == 17:
        packet = simple.parse_af_packet(af_packet)
        if packet['Protocol'] == pro_num and packet['IP_src'] != node_ip:
            chunk = packet['Chunk']
            header = int(chunk[0])
            if header == HEADER_DATA or header == HEADER_FINISH:
                if num_chunks == 0: cache_time = time.time()
                num_chunks = num_chunks + 1
                if header == HEADER_FINISH:
                        cache_time = time.time() - cache_time
                        print(f"num: {num_chunks} time: {cache_time}\nchunks/time = {num_chunks/cache_time}")
                        num_chunks = 0
                        cache_time = 0.0

    elif pro_num == 6:
        data = simple.recv(conn) 
        print(data)

app.run()