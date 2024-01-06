import numpy as np
import argparse
from simpleemu.simpleudp import simpleudp
from simpleemu.simpletcp import simpletcp
from simpleemu.simplecoin import SimpleCOIN
from utils.packet import *
from utils.log import *
from joblib import load

def decode_packet_vnf_1(joined_string):
    """
    Decode the packet from string to numpy array[2 dimension]

    :param packet: the packet received from the server
    :return: the numpy array
    """
    if "#" in joined_string:
        csv_list = joined_string.split("#")
        print(csv_list)

        # if csv_list and len(csv_list[0]) != 16:
        #     return ''
        
        data = np.array([list(map(float, row.split(','))) for row in csv_list])
    else:
        data = [np.array([float(item) for item in joined_string.split(",")])]
        
    print("======================================")
    print(data)
    print("======================================")
    
    return data

def encode_packet_vnf_1(data):
    """
    Encode the packet from numpy array to string.
    `data` is a list of float numbers.
    """
    res_string = '#'.join([str(item) for item in data])
    return res_string


def decode_packet_vnf_2(joined_string):
    """
    Decode the packet from string to numpy array[1 dimension]

    """
    print(joined_string)
    if "#" in joined_string:
        data = [float(item) for item in joined_string.split("#")]
    else:
        data = [float(joined_string)]
    
    print("======================================")
    print(data)
    print("======================================")

    return data

def vnf_1_process(packet, model_weight):
    print("vnf 1 process")
    # print(packet['Chunk'])
    print("---------begin---------")
    res = []

    # get the csv data from packet
    joined_string = str(packet['Chunk'].decode())
    data = decode_packet_vnf_1(joined_string)

    if data[0].shape[0] != 16:
        return ''
    
    for csv_one_line in data:

        # just calculate one part, do the dot calculation
        res_one_line = np.dot(csv_one_line, model_weight)
        
        res.append(res_one_line)

    res_str = encode_packet_vnf_1(res)
    print("vnf1 result", res_str)
    return res_str
    

def vnf_2_process(packet, intercept):
    res = []

    # get the csv data from packet
    joined_string = str(packet['Chunk'].decode())
    
    if (joined_string == '0#0#0#0#0') or (joined_string == '0'):
        return ''
    
    data = decode_packet_vnf_2(joined_string)
    for res_temp in data:

        # just calculate one part, add with intercept
        res_temp += intercept
        res.append(res_temp)

    print("vnf2 result", res)
    res_str = encode_packet_vnf_1(res) # same to vnf 1 encode

    return res_str


def vnf_3_process(packet):
    res = []

    # get the csv data from packet
    joined_string = str(packet['Chunk'].decode())
    data = decode_packet_vnf_2(joined_string)
    for res_temp in data:

        # judege the value > ? <= 0
        result = 1 if res_temp > 0 else 0
        res.append(result)

    print("vnf3 result", res)
    res_str = encode_packet_vnf_1(res) # same to vnf 1 encode
    print("vnf3 result string", res_str)
    return res_str

def load_svm_model(path):
    global already_load_svm_model
    if not already_load_svm_model:
        # load the fitted model SVM
        svm = load(path)

        _weight = svm.coef_ # the weight vector of the svm model after fit
        _intercept = svm.intercept_ # the intercept of the svm model after fit

        print('weight:',_weight)
        print('intercept:',_intercept)
        already_load_svm_model = True

        return _weight, _intercept

# Network
serverAddressPort = ("10.0.0.30", 9999)
clientAddressPort = ("10.0.0.10", 9999)

# parse args
parser = argparse.ArgumentParser(description="Using TCP or UDP")
parser.add_argument("--protocol", "-p", type=str, choices=["tcp", "udp", "t", "u"], default="udp",
                    help="choosing protocol, tcp/t or udp/u(default udp)")
parser.add_argument("--num", "-n", type=int, choices=[1, 2, 3], default=1,
                    help="which number is this switch. 1, 2 or 3(default 1)")
args = parser.parse_args()

# tcp/udp
if args.protocol in ["udp", "u"]:
    protocol = "udp"
    simple = simpleudp
    pro_num = 17
else:
    protocol = "tcp"
    simple = simpletcp
    pro_num = 6

num = args.num # set the number of switch


# network setting
ifce_name, node_ip = simple.get_local_ifce_ip('10.0')
# already_load_svm_model = False
# _weight, _intercept = load_svm_model('./svm_model.joblib')
_weight = [
    4.46737612, -1.95081422, 18.29293572, -4.5986548, -15.89973802,
    4.45173662, -6.66900044, 11.41212648, 12.09920262, -27.9301321,
    -20.2555121, 5.15629297, -0.51542267, 39.2437361, 11.1431311,
    -13.25246067
]
_intercept = -0.39625843


# Simple coin
app = SimpleCOIN(ifce_name=ifce_name, n_func_process=1, lightweight_mode=True)

@app.main()
def main(simplecoin: SimpleCOIN.IPC, af_packet: bytes):
    global num
    global pro_num
    # the global variable for the svm model should only load once @todo MA
    global _weight
    global _intercept

    packet:dict = simple.parse_af_packet(af_packet)
    
    if packet['Protocol'] == pro_num and packet['IP_src'] != node_ip:
        if num == 1:
            res_str = vnf_1_process(packet, _weight)
        elif num == 2:
            res_str = vnf_2_process(packet, _intercept)
        elif num == 3:
            res_str = vnf_3_process(packet)
        else:
            print("Not set mode with 1,2,3. Normal forwarding.")
            exit()
        
        # make the chunk and re-gene the packet
        if res_str != '':
            data_bytes:bytes = str(res_str).encode()
            packet['Chunk']:dict = data_bytes # update the packet data
            af_packet_new:bytes = simple.recreate_af_packet_by_chunk(packet)

            simplecoin.forward(af_packet_new)

app.run()