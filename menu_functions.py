from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QTextEdit
from project import Project, Editor
from pathlib import Path
from compile import compile
import threading, subprocess, shutil, os
from dialogs import Compile_Dialog, Add_Account_Dialog, Add_Node_Dialog, Deploy_Dialog, IPFS_Token_Dialog
from account import Account, add_local_accounts
from network import Network, init_ganache
from ipfs import IPFS
from contract import find_replace_split

def create_menu_option(option_name, label_list, command_list, shortcut_list, menu, window):
    menu_item = menu.addMenu(option_name)
    
    for label, command, shortcut in zip(label_list, command_list, shortcut_list):
        menu_item_action = QAction(label, window)
        menu_item_action.triggered.connect(command)

        if shortcut != "":
            menu_item_action.setShortcut(shortcut)

        menu_item.addAction(menu_item_action)
    
def lambda_func(function_name, *arguments):
    return lambda : function_name(*arguments)


def compile_file(state):
    dlg = Compile_Dialog()
    try:
        contracts_folder_path = os.path.join(state.project.path, "contracts")
        files_paths = os.listdir(contracts_folder_path)
        only_files = [f for f in files_paths if os.path.isfile(os.path.join(contracts_folder_path, f))]
        dlg.set_files(only_files)
    except:
        dlg.set_files([])

    if dlg.exec():
        file_name = dlg.get_file()
        overwrite = dlg.overwrite_btn.isChecked()

        if file_name != "":
            compile_all = False
            threading.Thread(target=compile, args=(compile_all, state, file_name, overwrite)).start()
            

def add_account(state):
    dlg = Add_Account_Dialog(state)
    if dlg.exec():
        name = dlg.get_account_name()
        key = dlg.get_priv_key()
        acc = Account(name, key, state.project.path)

        if "persistent" in state.accounts.keys():
            state.accounts["persistent"][name] = acc
        else:
            state.accounts["persistent"] = {}
            state.accounts["persistent"][name] = acc

        if state.functions_widget.select_network.currentText() != "local":
            state.functions_widget.update_accounts("persistent")
            
        state.output.append(f'Account "{acc.alias}" added\n')

        state.save_to_json()

def generate_account(state):
    pass

def add_node_provider(state):
    dlg = Add_Node_Dialog()
    if dlg.exec():
        network_name = dlg.get_network()
        network_key = dlg.get_key()
        net = Network(network_name, 2, network_key, state.project.path)
        state.networks[network_name] = net
        state.output.append(f'Node provider for "{network_name} network" added\n')
        state.functions_widget.update_networks()

        state.save_to_json()

def deploy_contract(state):
    dlg = Deploy_Dialog(state)
    dlg.contract_signal.connect(lambda x : dlg.set_versions(state.test(x)))
    try:
        dlg.set_combo_contracts(state.contracts.keys())
        dlg.set_combo_networks(state.networks.keys())
        dlg.set_accounts(state.accounts["local"].keys())
    except:
        dlg.set_combo_contracts([])
        dlg.set_combo_networks([])
        dlg.set_accounts([])

    if dlg.exec():
        try:
            contract_name = dlg.get_contract()
            version = dlg.get_version()
            contract = state.contracts[contract_name][version]
            constructor_args = find_replace_split(dlg.constructor_args.text())
            
            network_name = dlg.get_network()
            network = state.networks[network_name]
            account_name = dlg.get_account()
            #account = state.accounts[account_name]
            if network_name == "local":
                account = state.accounts["local"][account_name]
            else:
                account = state.accounts["persistent"][account_name]

            w3 = network.connect_to_node()

            _, tx_receipt = contract.deploy(network, w3, account, constructor_args)

            link = network.get_link("address", tx_receipt.contractAddress)
            state.output.add_to_output(tx_receipt.contractAddress, True, False, link)
            # chequear si el thread finalizo bien primero
            state.functions_widget.insert_function(state, contract)

            state.save_to_json()
            #threading.Thread(target=deploy_thread, args=(state, contract, network, w3, account, constructor_args,)).start()
        except Exception as e:
            state.add_to_output(e)

def add_token_id(state):
    dlg = IPFS_Token_Dialog(state)
    if dlg.exec():
        token_id = dlg.get_ipfs_token()
        ipfs = IPFS(token_id)
        state.ipfs = ipfs
        state.output.append(f"Web3Storage token id added")

