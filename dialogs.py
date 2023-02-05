from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox, QLineEdit, QWidget,
                             QHBoxLayout, QFrame, QToolButton, QPushButton, QTreeView, QSizePolicy, QFileDialog, QErrorMessage)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFileSystemModel
from PyQt6.QtCore import QSize, Qt, QDir, pyqtSignal
from PyQt6 import uic
import os, threading
from pathlib import Path
from collapsible import CollapsibleBox
from interact import contract_interaction
from project import Editor
from test import Sequence, Random, File, Test, Instruction

def get_button_box(dialog_obj):
    QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    buttonBox = QDialogButtonBox(QBtn)
    buttonBox.accepted.connect(dialog_obj.accept)
    buttonBox.rejected.connect(dialog_obj.reject)

    return buttonBox

def add_widgets_to_layout(layout, widget_list):
    for widget in widget_list:
        layout.addWidget(widget)

class Compile_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = parent
        self.setWindowTitle("Compile options")

        self.button_box = get_button_box(self)

        self.select_file = QComboBox(self)
        self.select_file.currentIndexChanged.connect(self.set_enabled_button)

        self.layout = QVBoxLayout()
        msg = QLabel("Select a file to compile")
        add_widgets_to_layout(self.layout, [msg, self.select_file, self.button_box])
        self.setLayout(self.layout)

    def set_files(self, files_names):
        self.select_file.addItems(files_names)
        self.set_enabled_button()

    def get_file(self):
        return self.select_file.currentText()

    def set_enabled_button(self):
        if self.select_file.currentText() != "":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

# net list, account list and contract name
class Deploy_Dialog(QDialog):
    contract_signal = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Deploy options")

        self.button_box = get_button_box(self)

        self.select_contract = QComboBox(self)
        self.select_contract.currentIndexChanged.connect(self.set_button_enabled)
        self.select_contract.currentIndexChanged.connect(self.request_versions)

        self.select_version = QComboBox()

        self.constructor_args = QLineEdit(self)
        # constructor could or could not have arguments
        #self.constructor_args.textChanged.connect(self.set_button_enabled)

        self.select_network = QComboBox(self)
        self.select_network.currentIndexChanged.connect(self.update_accounts)
        self.select_network.currentIndexChanged.connect(self.set_button_enabled)

        self.select_account = QComboBox(self)
        self.select_account.currentIndexChanged.connect(self.set_button_enabled)

        self.layout = QVBoxLayout()
        add_widgets_to_layout(self.layout, [self.select_contract, self.select_version, self.constructor_args, self.select_network, self.select_account, self.button_box])
        self.setLayout(self.layout)

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
        ver_list = []

        for i in range(versions):
            ver_list.append(f"v{i}")

        self.select_version.addItems(ver_list)

    def set_button_enabled(self):
        if self.select_contract.currentText() != "" and self.select_network.currentText() != "" and self.select_account.currentText() != "":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

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

        self.setWindowTitle("Add account")

        self.name_label = QLabel("Account name: ")
        self.name_input = QLineEdit(self)
        self.name_input.textChanged.connect(self.set_enabled_button)

        self.key_label = QLabel("Private key: ")
        self.key_input = QLineEdit(self)
        self.key_input.textChanged.connect(self.set_enabled_button)

        self.button_box = get_button_box(self)

        self.layout = QVBoxLayout()
        add_widgets_to_layout(self.layout, [self.name_label, self.name_input, self.key_label, self.key_input, self.button_box])
        self.setLayout(self.layout)

    def get_account_name(self):
        return self.name_input.text()

    def get_priv_key(self):
        return self.key_input.text()

    def set_enabled_button(self):
        if self.name_input.text() != "" and self.key_input.text() != "":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    
class Add_Node_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add account")

        networks = ["mainnet", "goerli", "sepolia"]
        self.select_network = QComboBox(self)
        self.select_network.addItems(networks)
        self.select_network.currentIndexChanged.connect(self.set_enabled_button)

        self.key_label = QLabel("Api Key: ")
        self.key_input = QLineEdit(self)
        self.key_input.textChanged.connect(self.set_enabled_button)

        self.button_box = get_button_box(self)

        self.layout = QVBoxLayout()
        add_widgets_to_layout(self.layout, [self.select_network, self.key_label, self.key_input, self.button_box])
        self.setLayout(self.layout)

    def get_network(self):
        return self.select_network.currentText()

    def get_key(self):
        return self.key_input.text()

    def set_enabled_button(self):
        if self.select_network.currentText() != "" and self.key_input.text() != "":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

class Left_Widget(QFrame):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.project_button = QToolButton(self)
        
        self.project_button.setIcon(QIcon("./file-and-folder.png"))
        self.project_button.setIconSize(QSize(30,30))
        
        self.function_button = QToolButton(self)
        self.function_button.setIcon(QIcon("./smart-contracts.png"))
        self.function_button.setIconSize(QSize(30,30))

        self.layout.addWidget(self.project_button)
        self.layout.addWidget(self.function_button)

        self.setLayout(self.layout)
        self.setFixedWidth(50)

class Functions_Layout(QWidget):
    function_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = parent
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#D4DFEC'))
        self.setPalette(palette)

        select_network_layout = QHBoxLayout()
        select_network_label = QLabel("Network:")
        self.select_network = QComboBox(self)
        self.select_network.addItems(self.app.networks.keys())
        #add_widgets_to_layout(select_layout, [select_account_label, self.select_account])
        select_network_layout.addWidget(select_network_label, 30)
        select_network_layout.addWidget(self.select_network, 70)
        self.select_network.currentIndexChanged.connect(self.update_accounts)

        select_layout = QHBoxLayout()
        select_account_label = QLabel("Account:")
        self.select_account = QComboBox(self)
        #self.select_account.addItems(self.app.accounts.keys())
        #add_widgets_to_layout(select_layout, [select_account_label, self.select_account])
        select_layout.addWidget(select_account_label, 30)
        select_layout.addWidget(self.select_account, 70)

        #msg_layout = QHBoxLayout()
        #msg_value_label = QLabel("Send ether:")
        self.msg_value = QLineEdit(self)
        self.msg_value.setPlaceholderText("ether amount")
        #add_widgets_to_layout(msg_layout, [msg_value_label, self.msg_value])

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #add_widgets_to_layout(self.layout, [self.select_account, self.msg_value])
        self.layout.addLayout(select_network_layout)
        self.layout.addLayout(select_layout)
        self.layout.addWidget(self.msg_value)
        self.layout.setContentsMargins(5,5,5,10)
        self.setLayout(self.layout)

    def update_networks(self):
        self.select_network.clear()
        self.select_network.addItems(self.app.networks.keys())

    def update_accounts(self, network):
        names = []
        network = self.select_network.currentText()

        if network == "local":
            names = self.app.accounts["local"].keys()
        else:
            names = self.app.accounts["persistent"].keys()
        
        self.select_account.clear()
        self.select_account.addItems(names)
        
    def insert_function(self, state, contract):
        box = CollapsibleBox(contract.name)
        box_layout = QVBoxLayout()

        for func in contract.get_functions():
            func_layout = QHBoxLayout()
            btn = QPushButton(func["name"])
            input_types = [input["type"] for input in func["inputs"]]
            if input_types != []:
                input_str = ",".join(input_types)
                line_edit = QLineEdit()
                line_edit.setPlaceholderText(input_str)
                btn.clicked.connect(lambda checked, func=func, input_types=input_types, line_edit=line_edit: self.interact_with_contract(state, contract, func["name"],
                func["stateMutability"], input_types,line_edit.text().split(",")))
                add_widgets_to_layout(func_layout, [btn, line_edit])
            else:
                btn.clicked.connect(lambda checked, func=func: self.interact_with_contract(state, contract, func["name"],
                func["stateMutability"], input_types, []))
                add_widgets_to_layout(func_layout, [btn])

            box_layout.addLayout(func_layout)

        box.setContentLayout(box_layout)
        self.layout.addWidget(box)
    
    def interact_with_contract(self, *args):
        network_name = self.select_network.currentText()
        network = self.app.networks[network_name]
        w3 = network.connect_to_node()

        if network_name == "local":
            account = self.app.accounts["local"][self.select_account.currentText()]
        else:
            account = self.app.accounts["persistent"][self.select_account.currentText()]

        #threading.Thread(target=contract_interaction, args=(network, w3, account,*args,)).start()
        result = contract_interaction(network, w3, account, *args)

        self.function_signal.emit(result)

class Project_Widget(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent 
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#f2f5ff'))
        self.setContentsMargins(0,0,0,0)
        self.setPalette(palette)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        layout_label = QLabel("PROJECT FOLDERS")
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
        self.tree_view.setStyleSheet("background-color : #e8e8e8;"
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

        self.setWindowTitle("Add W3Storage Token")
        self.button_box = get_button_box(self)
        self.layout = QVBoxLayout()

        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.set_enabled_button)

        add_widgets_to_layout(self.layout, [self.line_edit, self.button_box])

        self.setLayout(self.layout)

    def get_ipfs_token(self):
        return self.line_edit.text()

    def set_enabled_button(self):
        if self.line_edit.text() != "":
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

class Test_Dialog(QDialog):
    def __init__(self, contracts, project_path):
        super().__init__()
        uic.loadUi("./ui/Test_v2.ui", self)
        self.contracts = contracts
        self.project_path = project_path
        self.instructions = []

        self.add_inst_btn.clicked.connect(self.add_instruction)
        self.run_test_btn.clicked.connect(self.run_test)
        self.create_accounts_btn.clicked.connect(self.create_accounts)
        self.create_test_btn.clicked.connect(self.create_test)

        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_widget.setLayout(self.scroll_widget_layout)

        self.test = Test()

    def add_instruction(self):
        instruction = Instruction_Widget(self.contracts)
        self.scroll_widget_layout.addWidget(instruction)

    def create_accounts(self):
        value = self.accounts_number.value()

        if value != 0:
            self.test.create_accounts(value)
            print(self.test.accounts)

    def create_test(self):
        
        try:
            for i in range(self.scroll_widget_layout.count()):
                self.instructions.append(self.scroll_widget_layout.itemAt(i).widget().get_instruction())
        except:
            error_message = QErrorMessage(self)
            error_message.showMessage("All instructions must be defined")
            return
        
        self.test.name = self.test_name.text()
        self.test.number_of_nodes = self.spinBox.value()
        self.test.concurrency_number = self.spinBox_2.value()
        self.test.instructions = self.instructions
        self.test.project_path = self.project_path

        if Path(os.path.join(self.project_path, "tests", self.test.name)).exists():
            error_message = QErrorMessage(self)
            error_message.showMessage("There's already a test with the same name")
            return

        self.run_test_btn.setEnabled(True)
        
        print(self.instructions)
    
    def run_test(self):
        try:
            self.test.run()
        except Exception as e:
            print(e)
            

class Argument_Dialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./ui/Argument_Dialog.ui", self)
        self.current_toggled = None

        self.max_columns = {"File:" : [0, 2] , "Sequence:" : [1, 4], "Random:" : [2,3]}

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.radioButton.toggled.connect(lambda : self.disable_enable_children(self.radioButton.text()))
        self.radioButton.toggled.connect(self.validate_row_1)
        self.radioButton_2.toggled.connect(lambda : self.disable_enable_children(self.radioButton_2.text()))
        self.radioButton_2.toggled.connect(self.validate_row_2)
        self.radioButton_3.toggled.connect(lambda : self.disable_enable_children(self.radioButton_3.text()))
        self.radioButton_3.toggled.connect(self.validate_row_3)

        self.lineEdit.textChanged.connect(self.validate_row_1)

        self.spinBox.valueChanged.connect(self.validate_row_2)
        self.spinBox_2.valueChanged.connect(self.validate_row_2)

        self.spinBox_4.valueChanged.connect(self.validate_row_3)
        self.spinBox_5.valueChanged.connect(self.validate_row_3)
        
        self.pushButton.clicked.connect(self.get_path)

    def get_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All files (*)")

        self.lineEdit.setText(path)

    def disable_enable_children(self, text):
        self.change_enabled_widgets(text, True)

        if self.current_toggled != None:
            self.change_enabled_widgets(self.current_toggled, False)

        self.current_toggled = text

    def change_enabled_widgets(self, text, enabled):
        row, max_column = self.max_columns[text]

        for i in range(1, max_column):
            for j in range(2):
                self.gridLayout.itemAtPosition(row, i).itemAt(j).widget().setEnabled(enabled)

    def validate_row_1(self):
        path = self.lineEdit.text()

        if Path(path).exists() and path != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def validate_row_2(self):

        if self.spinBox_2.value() >= self.spinBox.value():
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def validate_row_3(self):

        if self.spinBox_5.value() >= self.spinBox_4.value():
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)


    def get_checked_button_values(self):

        if self.radioButton.isChecked():
            path = self.lineEdit.text() #trim probablemente. check if is path

            return File(file_path=path)

        elif self.radioButton_2.isChecked():
            start = self.spinBox.value()
            end = self.spinBox_2.value()
            step = self.spinBox_3.value()

            return Sequence(start, end, step=step)
            

        elif self.radioButton_3.isChecked():
            start = self.spinBox_4.value()
            end = self.spinBox_5.value()

            return Random(start, end)
        
        else:
            print("upss")
            

        
class Instruction_Widget(QWidget):
    def __init__(self, contracts):
        super().__init__()
        uic.loadUi("./ui/Instruction.ui", self)
        self.contracts = contracts
        self.arguments = []
        self.argument_list = []

        self.select_contract.addItems(self.contracts.keys())
        self.select_contract.currentIndexChanged.connect(self.set_versions)
        
        self.select_version.currentIndexChanged.connect(self.set_functions)

        self.select_function.currentIndexChanged.connect(self.set_arguments)

        self.select_arguments.clicked.connect(self.select_args)

    def select_args(self):
        dlg = List_Arguments_Dialog(self.arguments)

        if dlg.exec():
            for i in range(dlg.scroll_widget_layout.count()):
                self.argument_list.append(dlg.scroll_widget_layout.itemAt(i).widget().arg)
            print(self.argument_list)
        else:
            print("wains")

    def set_versions(self, index):
        versions = len(self.contracts[self.select_contract.currentText()])

        self.select_version.clear()
        self.select_version.addItems([str(i) for i in range(versions)])

    def set_functions(self, index):
        contract = self.contracts[self.select_contract.currentText()][index]
        functions = contract.get_functions()

        # Chequear que el contrato efectivamente tenga un constructor primero

        self.select_function.addItems(["constructor"]+[function["name"] for function in functions])

    def set_arguments(self, index):
        contract = self.contracts[self.select_contract.currentText()][self.select_version.currentIndex()]
        functions = contract.get_functions()
        function_name = self.select_function.currentText()

        function_dict = {}

        if function_name == "constructor":
            function_dict = contract.get_constructor()
        else:
            for function in functions:
                if function["name"] == function_name:
                    function_dict = function
        
        self.arguments = [input["name"] for input in function_dict["inputs"]]

    def get_instruction(self):
        contract = self.contracts[self.select_contract.currentText()][self.select_version.currentIndex()]
        function_name = self.select_function.currentText()
        exec_n = self.iterations.value()
        time_interval = self.time_interval.value()

        return Instruction(contract, function_name, exec_n, self.argument_list, time_interval)


class Argument_Widget_v2(QWidget):
    def __init__(self, arg_name):
        super().__init__()
        uic.loadUi("./ui/Argument_Widget_v2.ui", self)

        self.arg = None

        self.label.setText(arg_name)
        self.pushButton.clicked.connect(self.select_args)


    def select_args(self):
        dlg = Argument_Dialog()

        if dlg.exec():
            self.arg = dlg.get_checked_button_values()
            print(self.arg)
        else:
            print("NOOOO")

class List_Arguments_Dialog(QDialog):
    def __init__(self, args):
        super().__init__()
        uic.loadUi("./ui/List_Arguments_Dialog.ui", self)

        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.select_accounts_btn.clicked.connect(self.add_accounts)

        self.widget.setLayout(self.scroll_widget_layout)
        self.add_widgets(args)

    def add_widgets(self, args):
        for arg in args:
            select_arg_widget = Argument_Widget_v2(arg)
            #select_arg_widget.pushButton.clicked.connect(self.select_args)
            self.scroll_widget_layout.addWidget(select_arg_widget)

    def check_valid_args(self):
        for i in range(self.scroll_widget_layout.count()):
            if self.scroll_widget_layout.itemAt(i).widget().arg == None:
                return False
        
        return True

    def add_accounts(self):
        dlg = Select_Account_Dialog()

        if dlg.exec():
            print("baaaa")
        else:
            pass

    def accept(self):
        are_args_valid = self.check_valid_args()

        if are_args_valid:
            return super().accept()
        else:
            error_message = QErrorMessage(self)
            error_message.showMessage("All arguments must be defined")

class Select_Account_Dialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./ui/Select_Account_Dialog.ui", self)







