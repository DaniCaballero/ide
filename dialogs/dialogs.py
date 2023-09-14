from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox, QLineEdit, QWidget,
                             QHBoxLayout, QFrame, QToolButton, QPushButton, QTreeView, QSizePolicy, QFileDialog, 
                             QErrorMessage, QGraphicsDropShadowEffect, QCheckBox, QDoubleSpinBox, QMenu, QListView, QApplication, QHeaderView, QScrollArea)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFileSystemModel, QRgba64, QDragEnterEvent, QDragLeaveEvent
from PyQt6.QtCore import QSize, Qt, QDir, pyqtSignal, QThread, QItemSelectionModel
from PyQt6 import uic, QtWidgets
import os, threading, decimal, shutil, pickle, copy, json
from pathlib import Path
from .collapsible import CollapsibleBox
from blockchain.contract import find_replace_split
from blockchain.account import Account
from project.project import Editor, Select_Accounts_Model, Rols_Model
from tests.test import Sequence, Random, File, Prev_Output, Test, Instruction, Worker, List_Arg, Argument, ResultsModel, Time_Arg
import blocksmith, web3


def get_button_box(dialog_obj):
    QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    buttonBox = QDialogButtonBox(QBtn)
    buttonBox.accepted.connect(dialog_obj.accept)
    buttonBox.rejected.connect(dialog_obj.reject)

    return buttonBox

def add_widgets_to_layout(layout, widget_list):
    for widget in widget_list:
        layout.addWidget(widget)

class Create_Project_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('./ui/Qt/Create_Project_Dialog.ui', self)

        self.project_name.textChanged.connect(self.enable_disable_buttons)
        self.project_path.textChanged.connect(self.enable_disable_buttons)
        self.browse_btn.clicked.connect(self.get_path)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def get_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")

        self.project_path.setText(path)

    def enable_disable_buttons(self):
        project_name = self.project_name.text().strip()
        path = self.project_path.text()

        if Path(path).exists() and path != "" and project_name != "" and " " not in project_name:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def accept(self):
        path = self.project_path.text()
        project_name = self.project_name.text()

        if Path(os.path.join(path, project_name)).exists():
            error_message = QErrorMessage(self)
            error_message.showMessage("Folder already exists")
            return

        return super().accept()

class Compile_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = parent
        uic.loadUi("./ui/Qt/Compile_Dialog.ui", self)
        self.setWindowTitle("Compile options")

        self.select_file.currentIndexChanged.connect(self.set_enabled_button)
        self.overwrite_btn.setChecked(True)

    def set_files(self, files_names):
        self.select_file.addItems(files_names)
        self.set_enabled_button()

    def get_file(self):
        return self.select_file.currentText()

    def set_enabled_button(self):
        if self.select_file.currentText() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

# net list, account list and contract name
class Deploy_Dialog(QDialog):
    contract_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/Deploy_Dialog.ui", self)
        self.setWindowTitle("Deploy options")

        self.select_contract.currentIndexChanged.connect(self.set_button_enabled)
        self.select_contract.currentIndexChanged.connect(self.request_versions)

        self.select_network.currentIndexChanged.connect(self.update_accounts)
        self.select_network.currentIndexChanged.connect(self.set_button_enabled)

        self.select_account.currentIndexChanged.connect(self.set_button_enabled)

    def set_combo_contracts(self, contract_names):
        self.select_contract.addItems(contract_names)
        self.set_button_enabled()

    def get_contract(self):
        return self.select_contract.currentText()

    def get_version(self):
        return self.select_version.currentIndex()

    def set_combo_networks(self, network_names):
        self.select_network.addItems(network_names)
        self.set_button_enabled()

    def get_network(self):
        return self.select_network.currentText()

    def set_accounts(self, account_names):
        self.select_account.addItems(account_names)
        self.set_button_enabled()

    def get_account(self):
        return self.select_account.currentText()

    def request_versions(self, index):
        contract = self.select_contract.currentText()
        self.contract_signal.emit(contract)

    def set_versions(self, versions):
        self.select_version.clear()

        self.select_version.addItems([f"v{i}" for i in range(versions)])

    def set_button_enabled(self):
        if self.select_contract.currentText() != "" and self.select_network.currentText() != "" and self.select_account.currentText() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def update_accounts(self):
        names = []
        network = self.select_network.currentText()

        if network == "local":
            names = self.parent().accounts["local"].keys()
        else:
            names = self.parent().accounts["persistent"].keys()
        
        self.select_account.clear()
        self.select_account.addItems(names)

class Add_Account_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/Add_Account.ui",self)

        self.setWindowTitle("Add account")

        #self.name_label = QLabel("Account name: ")
        #self.name_input = QLineEdit(self)
        self.name_input.textChanged.connect(self.set_enabled_button)

        #self.key_label = QLabel("Private key: ")
        #self.key_input = QLineEdit(self)
        self.key_input.textChanged.connect(self.set_enabled_button)

        #self.button_box = get_button_box(self)

        #self.layout = QVBoxLayout()
        #add_widgets_to_layout(self.layout, [self.name_label, self.name_input, self.key_label, self.key_input, self.button_box])
        #self.setLayout(self.layout)

    def get_account_name(self):
        return self.name_input.text()

    def get_priv_key(self):
        return self.key_input.text()

    def set_enabled_button(self):
        if self.name_input.text() != "" and self.key_input.text() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def accept(self) -> None:

        try:
            priv_key = self.key_input.text()
            address = web3.eth.Account.from_key(priv_key).address
        except:
            error_message = QErrorMessage(self)
            error_message.showMessage("Not a valid private key")
            return

        return super().accept()

class New_Account(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        uic.loadUi("./ui/Qt/NewAccount.ui", self)
        self.main_window = main_window

        self.copy_btn.setIcon(QIcon("./ui/Icons/copy.png"))

        self.name_edit.textChanged.connect(self.enable_disable_accept)
        self.copy_btn.clicked.connect(self.copy_address)

    def copy_address(self):
        address = self.address_edit.text()

        QApplication.clipboard().setText(address)

    def enable_disable_accept(self):
        name = self.name_edit.text()
        accounts = self.main_window.accounts

        try:
            keys = accounts["persistent"].keys()
        except:
            keys = []
        
        if name != "" and name not in keys:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def accept(self):
        name = self.name_edit.text()
        path = self.main_window.project.path

        try:
            kg = blocksmith.KeyGenerator()
            priv_key = kg.generate_key()

            new_account = Account(name, priv_key, path)

            self.address_edit.clear()
            self.address_edit.setText(new_account.address)

            try:
                self.main_window.accounts["persistent"][name] = new_account
            except:
                self.main_window.accounts["persistent"] = {}
                self.main_window.accounts["persistent"][name] = new_account

            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        except:
            error_message = QErrorMessage(self)
            error_message.showMessage("Couldn't create new account")
    
class Add_Node_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/Node_Provider_Dialog.ui", self)
        self.setWindowTitle("Node Provider Dialog")

        networks = ["mainnet", "goerli", "sepolia"]

        self.select_network.addItems(networks)
        self.select_network.currentIndexChanged.connect(self.set_enabled_button)
        self.key_input.textChanged.connect(self.set_enabled_button)

    def get_network(self):
        return self.select_network.currentText()

    def get_key(self):
        return self.key_input.text()

    def set_enabled_button(self):
        if self.select_network.currentText() != "" and self.key_input.text() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def accept(self) -> None:

        try:
            network = self.select_network.currentText()
            key = self.key_input.text()

            w3 = web3.Web3(web3.Web3.HTTPProvider(f"https://{network}.infura.io/v3/{key}"))
            version = w3.net.version
            print(version)
        except:
            error_message = QErrorMessage(self)
            error_message.showMessage("Not a valid Infura Api Key")
            return
        
        return super().accept()
    
class Select_Script(QDialog):
    def __init__(self, scripts, parent=None):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/Select_Script_Dlg.ui", self)

        self.comboBox.addItems(scripts) 

class Left_Widget(QFrame):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.project_button = QToolButton(self)

        self.setStyleSheet("background-color: #3f5c73;")
        
        self.project_button.setIcon(QIcon("./ui/Icons/file-and-folder-white.png"))
        self.project_button.setIconSize(QSize(30,30))
        self.project_button.setStyleSheet("border: none;")
        
        self.function_button = QToolButton(self)
        self.function_button.setIcon(QIcon("./ui/Icons/smart-contracts-white.png"))
        self.function_button.setIconSize(QSize(30,30))
        self.function_button.setStyleSheet("border: none;")

        self.layout.addWidget(self.project_button)
        self.layout.addWidget(self.function_button)

        self.setLayout(self.layout)
        self.setFixedWidth(50)

class Functions_Layout(QScrollArea):
    function_signal = pyqtSignal(str, bool, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = parent
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ebf0f4"))
        self.setPalette(palette)
        content = QWidget()
        content.setPalette(palette)
        self.setWidget(content)
        self.setWidgetResizable(True)

        layout_label = QLabel("CONTRACT FUNCTIONS")
        layout_label.setStyleSheet("background-color: #3f5c73; color: white; padding: 5px 0; font-weight: bold;")
        layout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        select_network_layout = QHBoxLayout()
        select_network_label = QLabel("Network:")
        self.select_network = QComboBox(self)
        self.select_network.addItems(self.app.networks.keys())
        #add_widgets_to_layout(select_layout, [select_account_label, self.select_account])
        select_network_layout.addWidget(select_network_label, 30)
        select_network_layout.addWidget(self.select_network, 70)
        select_network_layout.setContentsMargins(10,0,10,0)
        self.select_network.currentIndexChanged.connect(self.update_accounts)

        select_layout = QHBoxLayout()
        select_account_label = QLabel("Account:")
        self.select_account = QComboBox(self)
        self.select_account.setMinimumWidth(self.width())

        self.copy_account_btn = QPushButton()
        self.copy_account_btn.setIcon(QIcon("./ui/Icons/copy.png"))
        self.copy_account_btn.clicked.connect(self.copy_account)
        #self.select_account.addItems(self.app.accounts.keys())
        #add_widgets_to_layout(select_layout, [select_account_label, self.select_account])
        select_layout.addWidget(select_account_label, 30)
        select_layout.addWidget(self.select_account, 60)
        select_layout.addWidget(self.copy_account_btn, 10)
        select_layout.setContentsMargins(10,0,10,0)

        ether_layout = QHBoxLayout()
        #msg_value_label = QLabel("Send ether:")
        self.msg_value = QDoubleSpinBox()
        self.msg_value.setMaximum(1000000000000000000)
        #self.msg_value.setPlaceholderText("ether amount")
        self.select_wei = QComboBox()
        self.select_wei.addItems(["wei", "gwei", "ether"])
        ether_layout.addWidget(self.msg_value, 70)
        ether_layout.addWidget(self.select_wei, 30)
        ether_layout.setContentsMargins(10,0,10,0)
        #add_widgets_to_layout(msg_layout, [msg_value_label, self.msg_value])

        self.layout = QVBoxLayout(content)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #add_widgets_to_layout(self.layout, [self.select_account, self.msg_value])
        self.layout.addWidget(layout_label)
        self.layout.addSpacing(15)
        self.layout.addLayout(select_network_layout)
        self.layout.addLayout(select_layout)
        self.layout.addLayout(ether_layout)
        self.layout.addSpacing(70)
        self.layout.setContentsMargins(0,0,0,0)
        #self.layout.addStretch()
        #self.setLayout(self.layout)

    def copy_account(self):

        try:
            address = self.app.accounts["persistent"][self.select_account.currentText()].address
        except:
            address = self.select_account.currentText()

        QApplication.clipboard().setText(address)

    def update_networks(self):
        self.select_network.clear()
        self.select_network.addItems(self.app.networks.keys())

    def update_accounts(self, network):
        names = []
        network = self.select_network.currentText()

        try:
            if network == "local":
                names = self.app.accounts["local"].keys()
            else:
                #names = [acc.address for acc in self.app.accounts["persistent"].values()]
                names = self.app.accounts["persistent"].keys()
        except:
            names = []
        
        self.select_account.clear()
        self.select_account.addItems(names)
        
    def insert_function(self, state, contract):
        box = CollapsibleBox(contract.name)
        box_layout = QVBoxLayout()

        for func in contract.get_functions():
            #print("function", func)
            func_layout = QHBoxLayout()
            btn = QPushButton(func["name"])
            input_types = [input["type"] for input in func["inputs"]]
            if input_types != []:
                input_str = ",".join(input_types)
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(input_str)
                btn.clicked.connect(lambda checked, func=func, input_types=input_types, line_edit=line_edit: self.interact_with_contract(contract, func["name"],
                find_replace_split(line_edit.text())))
                add_widgets_to_layout(func_layout, [btn, line_edit])
            else:
                btn.clicked.connect(lambda checked, func=func: self.interact_with_contract(contract, func["name"],
                []))
                add_widgets_to_layout(func_layout, [btn])

            box_layout.addLayout(func_layout)

        box.setContentLayout(box_layout)
        self.layout.addWidget(box)
    
    def interact_with_contract(self, contract, function_name, arg_list):
        network_name = self.select_network.currentText()
        network = self.app.networks[network_name]
        w3 = network.connect_to_node()
        msg_value = self.msg_value.value() 
        wei = self.select_wei.currentText()
        msg_value = web3.Web3.toWei(decimal.Decimal(msg_value), wei)

        if network_name == "local":
            account = self.app.accounts["local"][self.select_account.currentText()]
        else:
            account = self.app.accounts["persistent"][self.select_account.currentText()]

        #threading.Thread(target=contract_interaction, args=(network, w3, account,*args,)).start()
        # try:
        #     _, result = contract.contract_interaction(network, w3, account, *args, msg_value)
        # except Exception as e:
        #     result = e

        self.th = interactThread(False, contract, [network, w3, account, function_name, arg_list, msg_value])
        self.th.finished.connect(lambda result: self.interact_finished_slot(result, account.address, contract.name, function_name))
        self.th.start()
        #print("type of result ", type(result).__name__)

    def interact_finished_slot(self, result, address, contract_name, function_name):
        if type(result).__name__ == 'AttributeDict':
            result = web3.Web3.toJSON(result)
            result = json.loads(result)
            result = json.dumps(result, indent=1)
            #print(result)

        tx_msg = f"Transaction sent by <b><a style='color : green' href=''>{address}</a></b> invoking method <b><a style='color : blue' href=''>{function_name}</a></b> of contract <b><a style='color : red' href=''>{contract_name}</a></b>:"
        self.function_signal.emit(tx_msg, False, False)
        self.function_signal.emit(str(result), False, True)

class interactThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, deploy, contract, params, parent = None):
        super().__init__(parent)
        self._deploy = deploy
        self._contract = contract
        self._paraams = params

    def run(self):
        try:
            if self._deploy == True:
                _ ,value = self._contract.deploy(*(self._paraams))
            else:  
                _ ,value = self._contract.contract_interaction(*(self._paraams))
        except Exception as e:
            value = e

        self.finished.emit(value)

class Project_Widget(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent 
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ebf0f4"))
        self.setContentsMargins(0,0,0,0)
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        layout_label = QLabel("PROJECT FOLDERS")
        layout_label.setStyleSheet("background-color: #3f5c73; color: white; padding: 5px 0; font-weight: bold;")
        layout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(layout_label)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.layout)

    def add_tree_view(self, project_path):
        self.model = QFileSystemModel()
        self.model.setRootPath(project_path)

        self.model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(project_path))
        self.tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.tree_view.setStyleSheet("background-color : #ebf0f4;"
                                    "border-style: none;")

        self.tree_view.setIndentation(10)
        self.tree_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tree_view.clicked.connect(self.tree_view_clicked)

        # hide header info except file name
        self.tree_view.setHeaderHidden(True)
        for i in range(1, self.tree_view.model().columnCount()):
            self.tree_view.setColumnHidden(i, True)
        
        self.layout.addWidget(self.tree_view)
    
    def tree_view_clicked(self, index):
        path = self.model.filePath(index)
        p = Path(path)
        self.parent.add_new_tab(p)

class IPFS_Token_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/IPFS_Provider_Dialog.ui", self)
        self.setWindowTitle("Add W3Storage Token")

        self.line_edit.textChanged.connect(self.set_enabled_button)

    def get_ipfs_token(self):
        return self.line_edit.text()

    def set_enabled_button(self):
        if self.line_edit.text() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

class Add_Files_IPFS(QDialog):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        uic.loadUi("./ui/Qt/Add_Files_IPFS.ui", self)

        self.project_path = project_path

        self.name.textChanged.connect(self.enable_disable_buttons)
        self.source.textChanged.connect(self.enable_disable_buttons)
        self.single_file_radio.toggled.connect(self.enable_disable_buttons)
        self.all_files_radio.toggled.connect(self.enable_disable_buttons)

        self.browse_btn.clicked.connect(self.get_path)

    def get_path(self):
        path = ""
        
        if self.single_file_radio.isChecked():
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        elif self.all_files_radio.isChecked():
            path = QFileDialog.getExistingDirectory(self, "Select Directory")

        self.source.setText(path)

    def enable_disable_buttons(self):
        path = self.source.text()
        name = self.name.text()
        enabled = False

        if self.single_file_radio.isChecked():
            if Path(path).is_file():
                enabled = True

        elif self.all_files_radio.isChecked():
            if Path(path).is_dir():
                enabled = True

        if name == "" or Path(os.path.join(self.project_path, "IPFS", f"{name}.txt")).exists():
            enabled = False

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(enabled)

    def get_input(self):
        if self.single_file_radio.isChecked():
            multiple_files = False

        elif self.all_files_radio.isChecked():
            multiple_files = True

        path = self.source.text()
        name = self.name.text()

        return multiple_files, path, name






