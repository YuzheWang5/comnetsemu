import time
import argparse
import random

import os
import torch
from torch.serialization import load
from simpleemu.simpleudp import simpleudp
from simpleemu.simpletcp import simpletcp
from simpleemu.simplecoin import SimpleCOIN

from utils.log import *
from utils.packet import *

# parse args
parser = argparse.ArgumentParser(description="Using TCP or UDP")
parser.add_argument("--protocol", "-p", type=str, choices=["tcp", "udp", "t", "u"], default="udp",
                    help="choosing protocol, tcp/t or udp/u(default udp).")
args = parser.parse_args()

# tcp/udp
if args.protocol in ["udp", "u"]:
    protocol = "udp"
    simple = simpleudp
else:
    protocol = "tcp"
    simple = simpletcp

# network setting
ifce_name, node_ip = simple.get_local_ifce_ip('10.0')
log_file(ifce_name).debug(f"ifce_name = {ifce_name}, node_ip = {node_ip}")
app = SimpleCOIN(ifce_name=ifce_name, n_func_process=5, lightweight_mode=True)
serverAddressPort = ("10.0.0.30", 9999)
clientAddressPort = ("10.0.0.10", 9999)

# Generate a random number
random_number = random.randint(0, 100) # 0 ~ 100
print(f"Generated random number: {random_number}")

# Convert random number to bytes and send it to the server
random_number_bytes = str(random_number).encode() # Convert to bytes and encode it to string

#chunk_arr = chunk_handler.get_chunks_fc(random_number_bytes)
#print(f"chunk_arr: {len(chunk_arr)}") # 64
#for chunk in chunk_arr:
        # time.sleep(0.001)
simple.sendto(random_number_bytes, serverAddressPort) # Send to server

if protocol == "tcp":
    simple.close()