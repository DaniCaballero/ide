# Autores: Emmanuel Bandres, 14-10071
#          Daniela Caballero, 14-10140

import subprocess, argparse, sys, time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monta los nodos con geth")
    parser.add_argument("-f", type=str, required=True, help="Archivo de datos de los nodos")

    args = parser.parse_args()

    with open(args.f, 'r') as f:
        lines = f.readlines()
        lines = [line.rstrip() for line in lines]

    port_dict = {}
    for line in lines:
        tmp = line.split()
        port_dict[tmp[0]] = tmp[1:]

    # link con el bloque genesis
    for loc in port_dict.keys():
         subprocess.Popen(['geth', 'init', '--datadir', f"./localidades/{loc}/nodo", './genesis.json'])
        
    time.sleep(5)

    for loc, ports in port_dict.items():
        subprocess.Popen(['geth', '--identity', f'{loc}', '--http', '--http.port', f'{ports[0]}',
                          '--http.corsdomain', "*", '--datadir', f'./localidades/{loc}/nodo',
                          '--port', f'{ports[1]}', '--nodiscover', '--http.api', 'db,eth,net,web3,personal,miner,admin',
                          '--networkid', '1900', '--allow-insecure-unlock'])
