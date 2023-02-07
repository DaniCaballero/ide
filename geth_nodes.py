import subprocess, sys, time, os
import socket
from contextlib import closing
from web3 import Web3

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
        print("peers", len(node.geth.admin.peers()))


def next_free_port(port, max_port=65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError('no free ports')

def get_ports(number_of_nodes):
    ports_dict = {i : [] for i in range(number_of_nodes)}
    port = 8000

    for i in range(number_of_nodes):
        for j in range(3):
            free_port = next_free_port(port)
            ports_dict[i].append(free_port)
            port = free_port + 1

    return ports_dict

def init_geth_nodes(number_of_nodes, nodes_path, miner):

    for i in range(number_of_nodes):
        os.mkdir(os.path.join(nodes_path, f"node{i}"))
    
    port_dict = get_ports(number_of_nodes)

    

    # link con el bloque genesis
    for i in range(number_of_nodes):
        subprocess.Popen(['geth', '--datadir', os.path.join(nodes_path, f"node{i}"), 'init', os.path.join(nodes_path, 'genesis.json')])

    time.sleep(5)

    subprocess.Popen(['geth', '--datadir', os.path.join(nodes_path, "node0"),'--password', os.path.join(nodes_path, "pwd.txt"),'account', 'import', os.path.join(nodes_path, "key.txt")])

    time.sleep(2)

    pids = []

    for i, ports in port_dict.items():
        if i == 0:
            process =subprocess.Popen(['geth', '--identity', f'{i}', '--http', '--http.port', f'{ports[0]}',
                        '--authrpc.port', f"{ports[1]}",'--http.corsdomain', "*", '--datadir', os.path.join(nodes_path, f"node{i}"),
                        '--port', f'{ports[2]}', '--nodiscover','--networkid', '1325', '--http.api', 'eth,net,web3,personal,miner,admin',
                        '--allow-insecure-unlock', '--ipcdisable', '--nat', 'any', '--syncmode', 'full', '--unlock', f"{miner.address}", '--password', os.path.join(nodes_path, "pwd.txt"), '--mine', '--verbosity', "5"])
        else:
            process =subprocess.Popen(['geth', '--identity', f'{i}', '--http', '--http.port', f'{ports[0]}',
                            '--authrpc.port', f"{ports[1]}",'--http.corsdomain', "*", '--datadir', os.path.join(nodes_path, f"node{i}"),
                            '--port', f'{ports[2]}', '--nodiscover','--networkid', '1325', '--http.api', 'eth,net,web3,personal,miner,admin',
                            '--allow-insecure-unlock', '--ipcdisable', '--nat', 'any', '--syncmode', 'full', '--verbosity', "5"])

        pids.append(process.pid)

    http_ports = [ports[0] for ports in port_dict.values()]
    print("HTTP PORTS:", http_ports)


    return http_ports, pids

