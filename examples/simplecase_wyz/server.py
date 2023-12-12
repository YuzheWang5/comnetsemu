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
args = parser.parse_args() # to parse command line arguments to determine which protocol to use

# tcp/udp, tcp is not supported yet
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

# Simple coin, setup network interface and process
app = SimpleCOIN(ifce_name=ifce_name, n_func_process=1, lightweight_mode=True)

first = True

@app.main() # main function
def main(simplecoin: SimpleCOIN.IPC, af_packet: bytes):
    global pro_num, first
    if first and pro_num == 6:
        conn, addr = simple.accept(serverAddressPort)
        first = False

    if pro_num == 17:  # UDP
        packet = simple.parse_af_packet(af_packet)
        if packet['Protocol'] == pro_num and packet['IP_src'] != node_ip: # if the packet is UDP and not from the server
            data = packet['Data']
            try:
                random_number = int(data.decode())
                print(f"The final result: {random_number}")
            except ValueError:
                print("Received data is not a valid integer.")

    elif pro_num == 6:  # TCP
        data = simple.recv(conn)
        print(data)

app.run()