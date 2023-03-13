from ..contract import Contract
import os, json

def loader(contract_name, contract_version, network_name = ""):
    
    with open("../current_project_path.txt", "r") as f:
        project_path = f.readline()

    with open(os.path.join(project_path, "contracts.json"), "r") as f:
        contracts_json = json.load(f)

    contract_tmp = contracts_json[contract_name][contract_version]

    abi = contract_tmp["abi"]
    bytecode = contract_tmp["bytecode"]
    name = contract_tmp["name"]
    address = contract_tmp["address"]

    contract = Contract(name, abi, bytecode)
    contract.address = address

    return contract

