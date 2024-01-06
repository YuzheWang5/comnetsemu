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

# def self_score (y_pred, y_test):
#     # calculate the accuracy
#     score = 0
#     for i in range(len(y_pred)):
#         if y_pred[i] == y_test[i]:
#             score += 1
#     score /= len(y_pred)
#     score *= 100
#     return score

def contains_non_zero_one(numbers):
    for num in numbers:
        if num != 0 and num != 1:
            return True
    return False

@app.main() # main function
def main(simplecoin: SimpleCOIN.IPC, af_packet: bytes):
    global pro_num, first
    if first and pro_num == 6:
        conn, addr = simple.accept(serverAddressPort)
        first = False

    if pro_num == 17:
        packet = simple.parse_af_packet(af_packet)
        if packet['Protocol'] == pro_num and packet['IP_src'] != node_ip: # if the packet is UDP and not from the server
            
            joined_string = str(packet['Chunk'].decode())
            
            print(f"joined_string: {joined_string}")

            if "#" in joined_string:
                split_list = joined_string.split('#')
                split_list = [float(i) for i in split_list]
            else:
                split_list = [float(joined_string)]
            
            if contains_non_zero_one(split_list):
                return

            # 因为client目前只导入了其中一个csv文件，因此其中预测所有正确结果理论上为0
            zero_count = split_list.count(0) # 计算列表中0的数量
            total_count = len(split_list) # 计算列表的总长度
            # 计算比值
            ratio = zero_count / total_count * 100 if total_count > 0 else 0

            print(f"The current SCORE: {ratio} %")

    elif pro_num == 6:
        data = simple.recv(conn)
        print(data)

app.run()