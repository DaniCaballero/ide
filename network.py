import os, subprocess, shutil
from web3 import Web3, HTTPProvider
from dotenv import load_dotenv

def init_ganache(state):
    ganache = shutil.which("ganache-cli")
    subprocess.Popen([ganache, "-d", "--account_keys_path", f"{os.path.join(state.project.path, 'keys.json')}"], stdout=subprocess.DEVNULL)
    network = Local_Network("local")
    w3 = network.connect_to_node()
    #chain_id = w3.eth.chain_id
    network.chain_id = 1337

    state.networks["local"] = network
    #print("CHAIN ID IS: ", chain_id)

    
class Local_Network:
    def __init__(self, name, chain_id=0,port="8545"):
        self.name = name
        self.chain_id = chain_id
        self.port = port

    def connect_to_node(self):
        w3 = Web3(HTTPProvider(f"http://127.0.0.1:{self.port}"))

        return w3

class Network:
    def __init__(self, name, chain_id, api_key="", project_path=""):
        self.name = name
        self.chain_id = 5
        self.nodes = []
        self.project_path = project_path

        if api_key != "":
            self.write_api_key_to_env(api_key, project_path) 

    def connect_to_node(self):
        api_key = self.load_api_key()
        url = f"https://{self.name}.infura.io/v3/{api_key}"
        w3 = Web3(HTTPProvider(url))

        return w3

    # proveedor de nodo tambien?
    def load_api_key(self):
        path = os.path.join(self.project_path, ".env")
        load_dotenv(path)

        return os.getenv(f"{self.name}_API_KEY")

    def write_api_key_to_env(self, api_key, project_path):
        env_line = f"export {self.name}_API_KEY={api_key}\n"
        path = os.path.join(project_path, ".env")

        with open(path, "a") as file:
            file.write(env_line)