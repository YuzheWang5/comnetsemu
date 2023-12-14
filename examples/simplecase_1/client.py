import time
import argparse

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

batch = 64
in_chs = 65536
chunk_gap = 0.001

dummy_input = torch.randint(0, 255, [batch, int(in_chs)], dtype=torch.float32)

chunk_arr = chunk_handler.get_chunks_fc(dummy_input)
print(f"chunk_arr: {len(chunk_arr)}")
for chunk in chunk_arr:
        time.sleep(chunk_gap)
        simple.sendto(chunk, serverAddressPort)

if protocol == "tcp":   
    simple.close()
