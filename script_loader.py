from contract import Contract
from network import Network, Local_Network
from account import Account, Local_Account
import os, json

def load_project_data():
    with open("current_project_path.txt", "r") as f:
        project_path = rf"{f.readline()}"

    with open(os.path.join(project_path, "project_data.json"), "r") as f:
        data_json = json.load(f)

    return data_json

def instantiate_contract(data_json, contract_name, contract_version):
    contract_tmp = data_json["contracts"][contract_name][contract_version]

    contract = Contract(contract_tmp["name"], contract_tmp["abi"], contract_tmp["bytecode"])
    
    address = contract_tmp["address"]
    contract.address = address

    return contract

def get_network(network_name, data_json):
    network_json = data_json["networks"][network_name]

    if network_name == "local":
        network = Local_Network(network_json["name"], network_json["chain_id"], network_json["port"])
    else:
        network = Network(network_json["name"], network_json["chain_id"])
        network.project_path = network_json["project_path"]

    return network


def loader(contract_name, contract_version, network_name = "local"):
    accounts = []
    
    data_json = load_project_data()
    contract = instantiate_contract(data_json, contract_name, contract_version)
    network = get_network(network_name, data_json)

    if network_name == "local":
        accounts_tmp = data_json["accounts"]["local"]
        accounts = [Local_Account(acc["address"], acc["private_key"][2:]) for acc in accounts_tmp]
    else:
    
        accounts_tmp = data_json["accounts"]["persistent"]
        accounts = [Account(acc["alias"]) for acc in accounts_tmp]

        for account, account_dict in zip(accounts, accounts_tmp):
            account.address = account_dict["address"]
            account.project_path = account_dict["project_path"]

    return contract, network, accounts

