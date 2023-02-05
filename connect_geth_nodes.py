from pathlib import Path
from web3 import Web3
import time

def connect_to_peer(nodes):

    for i in range(len(nodes)-1):
        enode = nodes[i+1].geth.admin.node_info()['enode']
        nodes[i].geth.admin.add_peer(enode)

def connect_nodes(http_ports):
    node_list = []

    for http_port in http_ports:
        node = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{http_port}"))
        node_list.append(node)
    
    connect_to_peer(node_list)

    for node in node_list:
        print(len(node.geth.admin.peers()))

