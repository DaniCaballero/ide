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
    def __init__(self, alias, priv_key, project_path=""):
        self.alias = alias
        self.address = self.get_address_from_priv_key(priv_key)
        self.project_path = project_path
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


