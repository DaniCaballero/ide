from solcx import compile_standard, install_solc, get_installed_solc_versions
from packaging.version import Version
from contract import Contract
from pathlib import Path
import json, os, operator, re
import tkinter as tk

COMPARE_METHODS = {"<" : operator.lt, ">" : operator.gt, "<=" : operator.le, ">=" : operator.ge, "^" : operator.eq}

#devolver tupla true con version que sirve o false con la version a instalar
def is_solc_version_installed(version, compare_functions):
    ver_list = get_installed_solc_versions()
    ver_list = [Version(f"{ver.major}.{ver.minor}.{ver.patch}") for ver in ver_list]

    if len(version) == 1:
        for ver in ver_list:
            if compare_functions[0](ver, Version(version[0])):
                return (True, ver)
    elif len(version) == 2:
        for ver in ver_list:
            if compare_functions[0](ver, Version(version[0])) and compare_functions[1](ver, Version(version[1])):
                return (True, ver)
    
    return (False, "")

def get_pragma_string(line):
    pragma_line = line.replace("pragma solidity", "")
    pragma_line = pragma_line.replace(";", "")

    return pragma_line.strip()

def regex_match(pragma_line):
    versions, compare_methods, symbols = [], [], []
    patterns = ['(>=|>).+(<=|<).+', '\^.+', '(<=|>=|<|>).+']

    for pattern in patterns:
        result = re.match(pattern, pragma_line)
        if result:
            if pattern == '\^.+':
                symbols = ['^']
            else:
                result_split = re.split(pattern, pragma_line)
                symbols = [symbol for symbol in result_split if symbol]

            for symbol in symbols:
                compare_methods.append(COMPARE_METHODS[symbol])
                pragma_line = pragma_line.replace(symbol, "")

            versions = pragma_line.split()
    return versions, compare_methods


def get_pragma_version(state, file_name):
    contracts_folder_path = os.path.join(state.project.path, "contracts")
    file_path =  os.path.join(contracts_folder_path, file_name)
    
    with open(file_path, "r") as file:
        for line in file:
            if "pragma" in line:
                pragma_line = line
                break
    
    pragma_line = get_pragma_string(pragma_line)
    pragma_versions, compare_methods = regex_match(pragma_line)

    return is_solc_version_installed(pragma_versions, compare_methods)

    
def get_import_files(state):
    contracts_folder_path = os.path.join(state.project.path, "contracts")
    files_paths = os.listdir(contracts_folder_path)
    files_names = [Path(file).name for file in files_paths]
    imports_list = []

    for file_path in files_paths:
        with open(file_path, "r") as file:
            for line in file:
                if "import" in line:
                    line_split = line.split(" ")
                    file_name = (line_split[1].split(";"))[0]
                    if file_name not in imports_list:
                        imports_list.append(Path(file_name).name)
        
    to_compile = list(set(files_names)^set(imports_list))

    return to_compile

def write_json(contract_tuple, state):
    path = os.path.join(state.project.path, "build")

    for json_file, contract_name in contract_tuple:
        file_path = os.path.join(path, Path(contract_name).stem)

        with open(file_path + ".json", 'w') as file:
            json.dump(json_file, file)

def compile_contract(state, version, file_name, overwrite):
    contracts_folder_path = os.path.join(state.project.path, "contracts")

    sol_args = {
        "language" : "Solidity",
        "sources" : {file_name: {'urls': [os.path.join(".", file_name)]}},
        "settings" : {
            "outputSelection" : {
                "*" : {"*" : ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },      
    }
    
    compiled_sol = compile_standard(sol_args, solc_version=version, base_path=contracts_folder_path, allow_paths=".")

    for contract_name in compiled_sol["contracts"][file_name].keys():
        bytecode = compiled_sol["contracts"][file_name][contract_name]["evm"]["bytecode"]["object"]
        abi = compiled_sol["contracts"][file_name][contract_name]["abi"]
        contract = Contract(contract_name, abi, bytecode)

        try:
            if overwrite:
                state.contracts[f"{contract_name}-{file_name}"][-1] = contract
            else:
                state.contracts[f"{contract_name}-{file_name}"].append(contract)
        except:
            state.contracts[f"{contract_name}-{file_name}"] = [contract]

    return compiled_sol

def compile(compile_all, state, file_name, overwrite):
    contracts_tuple = []
    ver_tuple = get_pragma_version(state, file_name)
    version = f"{ver_tuple[1].major}.{ver_tuple[1].minor}.{ver_tuple[1].micro}"
    
    if ver_tuple[0] == False:
        state.output.append(f"Installing solidity version {version}...\n")
        install_solc(version, show_progress=False)
        state.output.append(f"Installation complete!\n")
    if compile_all == False:
        try:
            compiled_sol = compile_contract(state, version, file_name, overwrite)
            contracts_tuple.append((compiled_sol, file_name))
        except Exception as e:
            state.output.append(f"{e.message}\n")
            return
    else:
        pass
        # compile everything in contracts folder. needs an order
    write_json(contracts_tuple, state)
    state.output.append(f"{file_name} contract successfully compiled\n")

