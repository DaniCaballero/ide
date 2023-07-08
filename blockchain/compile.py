from solcx import compile_files, install_solc, get_installed_solc_versions, get_installable_solc_versions
from packaging.version import Version
from .contract import Contract
from pathlib import Path
import json, os, operator, re


def custom_compare(version0, version1):
    if version0.major == version1.major and version0.minor == version1.minor:
        if version0.micro >= version1.micro:
            return True
    
    return False

COMPARE_METHODS = {"<" : operator.lt, ">" : operator.gt, "<=" : operator.le, ">=" : operator.ge, "^" : custom_compare, "==" : operator.eq}

def compare_with_installable_solc_versions(version, compare_functions):
    installable_versions = get_installable_solc_versions()
    version_list = [Version(f"{ver.major}.{ver.minor}.{ver.patch}") for ver in installable_versions]

    for ver in version_list:
        if compare_functions[0](ver, Version(version[0])) and compare_functions[1](ver, Version(version[1])):
            return (False, ver)

    return False, version[0]

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

        return compare_with_installable_solc_versions(version, compare_functions)
    
    return (False, Version(version[0]))

def get_pragma_string(line):
    pragma_line = line.replace("pragma solidity", "")
    pragma_line = pragma_line.replace(";", "")

    return pragma_line.strip()

def regex_match(pragma_line):
    versions, compare_methods, symbols = [], [], []
    patterns = ['(>=|>)\d+\.\d+\.\d+\s?(<=|<)\d+\.\d+\.\d+', '\^\d+\.\d+\.\d+', '(<=|>=|<|>)\d+\.\d+\.\d+', '\d+\.\d+\.\d+']

    for pattern in patterns:
        result = re.match(pattern, pragma_line)
        if result:
            if pattern == '\^\d+\.\d+\.\d+':
                symbols = ['^']

            elif pattern == '\d+\.\d+\.\d+':
                symbols = ['==']
            else:
                result_split = re.split(pattern, pragma_line)
                symbols = [symbol for symbol in result_split if symbol]

            for symbol in symbols:
                compare_methods.append(COMPARE_METHODS[symbol])
                if symbol != "==":
                    pragma_line = pragma_line.replace(symbol, "")

            versions = pragma_line.split()
    return versions, compare_methods


def get_pragma_version(state, file_name):
    contracts_folder_path = os.path.join(state.project.path, "contracts")
    file_path =  os.path.join(contracts_folder_path, file_name)

    try:
        with open(file_path, "r") as file:
            for line in file:
                if "pragma" in line:
                    pragma_line = line
                    break

        pragma_line = get_pragma_string(pragma_line)
        pragma_versions, compare_methods = regex_match(pragma_line)
        print("pragma version ", pragma_versions)

        return is_solc_version_installed(pragma_versions, compare_methods)
    except:
        raise RuntimeError("Solidity version not found")

    
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
    print("file name ", file_name)
    contracts_folder_path = os.path.join(state.project.path, "contracts")
    
    compiled_sol = compile_files(
        source_files=[os.path.join(contracts_folder_path, file_name)], 
        solc_version=version,
        output_values=["abi", "bin"], 
        allow_paths=contracts_folder_path)

    for contract in compiled_sol.keys():
        contract_path = contract.split(":")

        if Path(contract_path[-2]).name == file_name:
            
            contract_name = contract_path[-1]
            bytecode = compiled_sol[contract]["bin"]
            abi = compiled_sol[contract]["abi"]
            contract = Contract(f"{contract_name}-{file_name}", abi, bytecode)

            try:
                if overwrite:
                    state.contracts[f"{contract_name}-{file_name}"][-1] = contract
                else:
                    state.contracts[f"{contract_name}-{file_name}"].append(contract)
            except:
                state.contracts[f"{contract_name}-{file_name}"] = [contract]

    state.save_to_json()

    return compiled_sol

def compile(compile_all, state, file_name, overwrite):
    contracts_tuple = []

    try:
        ver_tuple = get_pragma_version(state, file_name)
        print("VERSION TUPLE IS: ", ver_tuple)
        version = f"{ver_tuple[1].major}.{ver_tuple[1].minor}.{ver_tuple[1].micro}"
        
        if ver_tuple[0] == False:
            state.output.append(f"Installing solidity version {version}...\n")
            install_solc(version, show_progress=False)
            state.output.append(f"Installation complete!\n")
        if compile_all == False:
            compiled_sol = compile_contract(state, version, file_name, overwrite)
            contracts_tuple.append((compiled_sol, file_name))
        else:
            pass

        # compile everything in contracts folder. needs an order
        write_json(contracts_tuple, state)
        state.output.append(f"{file_name} contract successfully compiled\n")

    except Exception as e:
        state.output.append(f"{e}\n")
        return



