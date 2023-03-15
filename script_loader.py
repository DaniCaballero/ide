from contract import Contract
from network import Network, Local_Network
from account import Account, Local_Account
import os, json

def loader(contract_name, contract_version, network_name = "local"):
    accounts = []
    
    with open("current_project_path.txt", "r") as f:
        project_path = rf"{f.readline()}"

    with open(os.path.join(project_path, "project_data.json"), "r") as f:
        data_json = json.load(f)

    contract_tmp = data_json["contracts"][contract_name][contract_version]

    abi = contract_tmp["abi"]
    bytecode = contract_tmp["bytecode"]
    name = contract_tmp["name"]
    address = contract_tmp["address"]

    contract = Contract(name, abi, bytecode)
    contract.address = address

    if network_name == "local":
        network_json = data_json["networks"][network_name]
        network = Local_Network("ganache", project_path, network_json["chain_id"], network_json["port"])

        accounts_tmp = data_json["accounts"]["local"]
        accounts = [Local_Account(acc["address"], acc["private_key"][2:]) for acc in accounts_tmp]
    else:
        network = None
        accounts = None

    return contract, network, accounts

