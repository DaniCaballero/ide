import os
from dotenv import load_dotenv
import web3, os, json

def add_local_accounts(state):
    #accounts = []
    keys_path = os.path.join(state.project.path, "keys.json")

    with open(keys_path, "r") as file:
        keys_info = json.load(file)

    addr_keys = keys_info["private_keys"]
    state.accounts["local"] = {}

    for key in addr_keys.keys():
        #accounts.append(Local_Account(key, addr_keys[key]))
        state.accounts["local"][key] = Local_Account(key, addr_keys[key])
        
    #state.accounts["local"] = accounts

class Local_Account:
    def __init__(self, address, private_key):
        self.alias = address
        self.address = web3.Web3.toChecksumAddress(address)
        self.private_key = "".join(("0x", private_key))

    def sign_transaction(self, node, tx):
        signed_tx = node.eth.account.sign_transaction(tx, private_key=self.private_key)

        return signed_tx
    

class Account:
    def __init__(self, alias, priv_key="", project_path=""):
        self.alias = alias
        self.address = ""
        self.project_path = project_path

        if priv_key != "":
            
            if priv_key.startswith("0x") == False:
                priv_key = "".join(("0x", priv_key))

            self.address = web3.eth.Account.from_key(priv_key).address
            self.write_priv_key_to_env(priv_key, project_path)

    def load_private_key(self):
        path = os.path.join(self.project_path, ".env")
        load_dotenv(path)

        return os.getenv(f"{self.alias}_PRIVATE_KEY")

    def get_address_from_priv_key(self, priv_key):
        account = web3.eth.Account.from_key(priv_key)

        return account.address

    def write_priv_key_to_env(self, priv_key, project_path):
        env_line = f'export {self.alias}_PRIVATE_KEY={priv_key}\n'
        path = os.path.join(project_path, ".env")

        with open(path, "a") as file:
            file.write(env_line)

    def sign_transaction(self, node, tx):
        priv_key = self.load_private_key()
        signed_tx = node.eth.account.sign_transaction(tx, private_key=priv_key)

        return signed_tx

class Test_Account:
    def __init__(self, alias, private_key):
        self.alias = alias
        self.private_key = private_key
        self.address = self.get_address_from_priv_key(private_key)

    def sign_transaction(self, node, tx):
        signed_tx = node.eth.account.sign_transaction(tx, private_key=self.private_key)

        return signed_tx

    def get_address_from_priv_key(self, priv_key):
        account = web3.eth.Account.from_key(priv_key)

        return account.address
    
class Local_Network:
    def __init__(self, name, chain_id=0,port="8545"):
        self.name = name
        self.chain_id = chain_id
        self.port = port

    def connect_to_node(self):
        w3 = web3.Web3(web3.Web3.HTTPProvider(f"http://127.0.0.1:{self.port}"))

        return w3
    
    def get_link(self, hash_type, hash):
        return ""

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
        w3 = web3.Web3(web3.Web3.HTTPProvider(url))

        return w3
    
    def get_link(self, hash_type, hash):
        if self.name == "mainnet":
            url = f"https://goerli.etherscan.io/{hash_type}/{hash}"
        else:
            url = f"https://{self.name}.etherscan.io/{hash_type}/{hash}"

        return url

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


def _sign_and_send_tx(tx, account, w3):
        signed_tx = account.sign_transaction(w3, tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)  
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return tx_receipt

class Contract: 
    def __init__(self, name, abi, bytecode):
        self.name = name
        self.abi = abi
        self.bytecode = bytecode
        self.address = {}

    def __str__(self):
        return f"{self.name}"

    # def _sign_and_send_tx(self, tx, account, w3):
    #     signed_tx = account.sign_transaction(w3, tx)
    #     tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)  
    #     tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    #     return tx_receipt

    def deploy(self, network, w3, account, constructor_args, msg_value = 0, nonce  = None):
        _, type_list = self.get_function_visibility_input_types("constructor")
        #casted_args = cast_web3_types(type_list, constructor_args)
        contract = w3.eth.contract(abi=self.abi, bytecode=self.bytecode)

        if nonce == None:
            nonce = w3.eth.getTransactionCount(account.address)

        tx = contract.constructor(*constructor_args).build_transaction(
            {"gasPrice": w3.eth.gas_price,"from" : account.address, "chainId" : network.chain_id, "nonce" : nonce, "value" : msg_value})
        
        tx_receipt = _sign_and_send_tx(tx, account, w3)
        self.address[network.chain_id] = tx_receipt.contractAddress

        return True, tx_receipt

    def contract_interaction(self, network, w3, account, function_name, args_list, msg_value = 0, nonce = None):
        visibility, type_list = self.get_function_visibility_input_types(function_name)
        #casted_args = cast_web3_types(type_list, args_list)

        if nonce == None:
            nonce = w3.eth.getTransactionCount(account.address)
    
        contract_instance = self.get_instance(w3, network)

        tx = {"chainId" : network.chain_id, "from" : account.address, "nonce" : nonce, "gasPrice" : w3.eth.gas_price, "value" : msg_value}

        try:
            if visibility == "view" or visibility == "pure":
                value = contract_instance.functions[function_name](*args_list).call({"from" : account.address})
                return True, value

            else:
                tx = contract_instance.functions[function_name](*args_list).build_transaction(tx)
                tx_receipt = _sign_and_send_tx(tx, account, w3)

                return True, tx_receipt
                
        except Exception as e:
            return False, e

    def get_instance(self, w3, network):
        address = self.address[network.chain_id]
        #print(address)
        contract_instance = w3.eth.contract(address=address, abi=self.abi)

        return contract_instance

    def get_functions(self):
        function_list = [item for item in self.abi if item["type"]=="function"]

        return function_list

    def get_function_visibility_input_types(self, function_name):
        visibility, input_types = None, []

        if function_name == "constructor":
            constructor = self.get_constructor()
            if constructor != []:
                visibility = constructor["stateMutability"]
                input_types = [input["type"] for input in constructor["inputs"]]
        else:
            for function in self.get_functions():
                if function["name"] == function_name:
                    visibility = function["stateMutability"]
                    input_types = [input["type"] for input in function["inputs"]]
                    break

        return visibility, input_types


    def get_constructor(self):
        try:
            constructor = [item for item in self.abi if item["type"]=="constructor"]
            #input_types = [input["type"] for input in constructor["inputs"]]
            #input = [item for item in constructor[0]["inputs"]]
            #print("iput types",input_types)
            return constructor[0]
        except:
            return []