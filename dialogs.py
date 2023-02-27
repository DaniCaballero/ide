from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox, QLineEdit, QWidget,
                             QHBoxLayout, QFrame, QToolButton, QPushButton, QTreeView, QSizePolicy, QFileDialog, 
                             QErrorMessage, QGraphicsDropShadowEffect, QCheckBox, QDoubleSpinBox, QMenu, QListView)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFileSystemModel, QRgba64, QDragEnterEvent, QDragLeaveEvent
from PyQt6.QtCore import QSize, Qt, QDir, pyqtSignal, QThread, QItemSelectionModel
from PyQt6 import uic, QtWidgets
import os, threading, decimal, shutil, pickle, copy
from pathlib import Path
from collapsible import CollapsibleBox
from contract import find_replace_split
from project import Editor, Select_Accounts_Model
from test import Sequence, Random, File, Prev_Output, Test, Instruction, Worker
from web3 import Web3


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
    def __init__(self):
        super().__init__()
        uic.loadUi('./ui/Create_Project_Dialog.ui', self)

        self.project_name.textChanged.connect(self.enable_disable_buttons)
        self.project_path.textChanged.connect(self.enable_disable_buttons)
        self.browse_btn.clicked.connect(self.get_path)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def get_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")

        self.project_path.setText(path)

    def enable_disable_buttons(self):
        path = self.project_path.text()

        if Path(path).exists() and path != "" and self.project_name.text() != "":
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
        self.setWindowTitle("Compile options")

        self.button_box = get_button_box(self)

        self.select_file = QComboBox(self)
        self.select_file.currentIndexChanged.connect(self.set_enabled_button)

        self.overwrite_btn = QCheckBox("Overwrite contract information")
        self.overwrite_btn.setChecked(True)

        self.layout = QVBoxLayout()
        msg = QLabel("Select a file to compile")
        add_widgets_to_layout(self.layout, [msg, self.select_file, self.overwrite_btn, self.button_box])
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
        self.select_version.clear()

        self.select_version.addItems([f"v{i}" for i in range(versions)])

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

        self.setStyleSheet("background-color: #3f5c73;")
        
        self.project_button.setIcon(QIcon("./file-and-folder-white.png"))
        self.project_button.setIconSize(QSize(30,30))
        self.project_button.setStyleSheet("border: none;")
        
        self.function_button = QToolButton(self)
        self.function_button.setIcon(QIcon("./smart-contracts-white.png"))
        self.function_button.setIconSize(QSize(30,30))
        self.function_button.setStyleSheet("border: none;")

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
        palette.setColor(QPalette.ColorRole.Window, QColor("#ebf0f4"))
        self.setPalette(palette)

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
        #self.select_account.addItems(self.app.accounts.keys())
        #add_widgets_to_layout(select_layout, [select_account_label, self.select_account])
        select_layout.addWidget(select_account_label, 30)
        select_layout.addWidget(self.select_account, 70)
        select_layout.setContentsMargins(10,0,10,0)

        ether_layout = QHBoxLayout()
        #msg_value_label = QLabel("Send ether:")
        self.msg_value = QDoubleSpinBox()
        #self.msg_value.setPlaceholderText("ether amount")
        self.select_wei = QComboBox()
        self.select_wei.addItems(["wei", "gwei", "ether"])
        ether_layout.addWidget(self.msg_value, 70)
        ether_layout.addWidget(self.select_wei, 30)
        ether_layout.setContentsMargins(10,0,10,0)
        #add_widgets_to_layout(msg_layout, [msg_value_label, self.msg_value])

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        #add_widgets_to_layout(self.layout, [self.select_account, self.msg_value])
        self.layout.addWidget(layout_label)
        self.layout.addSpacing(15)
        self.layout.addLayout(select_network_layout)
        self.layout.addLayout(select_layout)
        self.layout.addLayout(ether_layout)
        self.layout.addSpacing(70)
        self.layout.setContentsMargins(0,0,0,0)
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
    
    def interact_with_contract(self, contract, *args):
        network_name = self.select_network.currentText()
        network = self.app.networks[network_name]
        w3 = network.connect_to_node()
        msg_value = self.msg_value.value() 
        wei = self.select_wei.currentText()
        msg_value = Web3.toWei(decimal.Decimal(msg_value), wei)

        if network_name == "local":
            account = self.app.accounts["local"][self.select_account.currentText()]
        else:
            account = self.app.accounts["persistent"][self.select_account.currentText()]

        #threading.Thread(target=contract_interaction, args=(network, w3, account,*args,)).start()
        _, result = contract.contract_interaction(network, w3, account, *args, msg_value)

        self.function_signal.emit(str(result))

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

class Add_Files_IPFS(QDialog):
    def __init__(self, project_path):
        super().__init__()
        uic.loadUi("./ui/Add_Files_IPFS.ui", self)

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

class Test_Dialog(QDialog):
    def __init__(self, ui_name, contracts, project_path, test):
        super().__init__()
        uic.loadUi(f"./ui/{ui_name}", self)
        self.contracts = contracts
        self.project_path = project_path
        self.instructions = []
        self.test = test

        self.test_name.setText(self.test.name)
        self.test_name.setEnabled(False)

        self.add_inst_btn.clicked.connect(lambda : self.add_instruction())
        self.run_test_btn.clicked.connect(self.run_test)
        self.create_test_btn.clicked.connect(self.create_test)

        qcombobox = """QComboBox {border: 1px solid #ced4da; border-radius: 4px;padding-left: 10px;background-color: #f2f5ff} QComboBox::drop-down {border: none} QComboBox::down-arrow {image: url(./down.png); width: 12px; height: 12px; margin-right: 15px}
                    QPushButton {border-radius: 4px} #Dialog {background-color: white}"""
                    

        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_widget.setLayout(self.scroll_widget_layout)

        self.setStyleSheet(qcombobox)

        #self.test = Test(name=test_name)

    def add_instruction(self, instruction=None):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor("#ADAAB5"))
        shadow.setOffset(4)
        print("instruction ", instruction )

        ui_instruction = Instruction_Widget(self.contracts, self.test.accounts, self.test.rols, self.test, instruction)
        ui_instruction.setGraphicsEffect(shadow)
        shadow.setEnabled(True)
        self.scroll_widget_layout.addWidget(ui_instruction)

    def save_test(self):
        data_path = os.path.join(self.project_path, "tests", "test_data.pkl")
        test_data = {}

        try:
            with open(data_path, "rb") as f:
                test_data = pickle.load(f)
        except:
            pass

        test_data[self.test.name] = self.test

        with open(data_path, "wb") as f:
            pickle.dump(test_data, f)

    def create_test(self):
        self.instructions = []
        
        try:
            for i in range(self.scroll_widget_layout.count()):
                self.instructions.append(self.scroll_widget_layout.itemAt(i).widget().get_instruction())
        except:
            error_message = QErrorMessage(self)
            error_message.showMessage("All instructions must be defined")
            self.run_test_btn.setEnabled(False)
            return
        
        #self.test.name = self.test_name.text()
        self.test.number_of_nodes = self.spinBox.value()
        self.test.concurrency_number = self.spinBox_2.value()
        self.test.instructions = self.instructions
        self.test.project_path = self.project_path

        try:
            for instruction in self.test.instructions:
                instruction.msg_values.generate_data(instruction.number_of_executions)
                for arg in instruction.args:
                    arg.generate_data(instruction.number_of_executions)
        except:
            error_message.showMessage("Failed to initialize arguments")
            self.run_test_btn.setEnabled(False)
            return

        self.run_test_btn.setEnabled(True)
        
        self.save_test()
    
    def show_error_progress_bar(self):
        self.progressBar.setStyleSheet("QProgressBar::chunk {background-color: red}")
        self.progressBar.setValue(100)
    
    def run_test(self):

        threading.Thread(target=self.test.run).start()

        self.thread = QThread()

        worker = Worker(self.test)
        worker.moveToThread(self.thread)
        worker.progressChanged.connect(self.progressBar.setValue)
        worker.errorFound.connect(self.show_error_progress_bar)
        self.thread.started.connect(worker.work)

        worker.finished.connect(self.thread.quit)
        worker.finished.connect(worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.worker = worker

        self.thread.start()

class Argument_Dialog(QDialog):
    def __init__(self, prev_output_dict, arg = None):
        super().__init__()
        uic.loadUi("./ui/Argument_Dialog.ui", self)
        self.current_toggled = None
        self.arg = arg

        self.max_columns = {"File:" : [0, 2, 2] , "Sequence:" : [1, 4, 2], "Random:" : [2,3, 2], "Previous Output:" : [3,2, 1]}

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.radioButton.toggled.connect(lambda : self.disable_enable_children(self.radioButton.text()))
        self.radioButton.toggled.connect(self.validate_row_1)
        self.radioButton_2.toggled.connect(lambda : self.disable_enable_children(self.radioButton_2.text()))
        self.radioButton_2.toggled.connect(self.validate_row_2)
        self.radioButton_3.toggled.connect(lambda : self.disable_enable_children(self.radioButton_3.text()))
        self.radioButton_3.toggled.connect(self.validate_row_3)
        self.radioButton_4.toggled.connect(lambda : self.disable_enable_children(self.radioButton_4.text()))
        self.radioButton_4.toggled.connect(self.validate_row_4)

        self.lineEdit.textChanged.connect(self.validate_row_1)

        self.spinBox.valueChanged.connect(self.validate_row_2)
        self.spinBox_2.valueChanged.connect(self.validate_row_2)

        self.spinBox_4.valueChanged.connect(self.validate_row_3)
        self.spinBox_5.valueChanged.connect(self.validate_row_3)
        
        self.pushButton.clicked.connect(self.get_path)

        self.select_prev_output.addItems(list(prev_output_dict.keys()))

        if self.arg != None:
            self.set_default_values()

    def set_default_values(self):
        
        class_name = type(self.arg).__name__

        if class_name == "File":
            self.radioButton.setChecked(True)
            self.lineEdit.setText(self.arg.path)

        elif class_name == "Sequence":
            self.radioButton_2.setChecked(True)
            self.spinBox.setValue(self.arg.min)
            self.spinBox_2.setValue(self.arg.max)
            self.spinBox_3.setValue(self.arg.step)

        elif class_name == "Random":
            self.radioButton_3.setChecked(True)
            self.spinBox_4.setValue(self.arg.min)
            self.spinBox_5.setValue(self.arg.max)

        elif class_name == "Prev_Output":
            self.select_prev_output.setText(self.arg.output_dict_name)

    def get_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All files (*)")

        self.lineEdit.setText(path)

    def disable_enable_children(self, text):
        self.change_enabled_widgets(text, True)

        if self.current_toggled != None:
            self.change_enabled_widgets(self.current_toggled, False)

        self.current_toggled = text

    def change_enabled_widgets(self, text, enabled):
        row, max_column, h_layout_max = self.max_columns[text]

        for i in range(1, max_column):
            for j in range(h_layout_max):
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

    def validate_row_4(self):

        if self.select_prev_output.currentText() != "":
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
        
        elif self.radioButton_4.isChecked():
            key_name = self.select_prev_output.currentText()

            return Prev_Output(key_name)
        
        else:
            print("upss")

class Select_Ether_Dialog(Argument_Dialog):
    def __init__(self, arg = None):
        super().__init__(arg)
        
        self.label.setText("Select Ether to send")

        self.msg_values = Random(0,0)

        self.ether_label = QLabel()
        self.ether_label.setText("Wei denomination:")

        self.select_wei_denomination = QComboBox()
        self.select_wei_denomination.addItems(["wei", "gwei", "ether"])

        self.gridLayout.addWidget(self.ether_label, 3, 0)
        self.gridLayout.addWidget(self.select_wei_denomination, 3, 1)

        # Assign default value 
        if self.arg != None:
            self.select_wei_denomination.setCurrentText(self.arg.type)
            
class Instruction_Widget(QWidget):
    def __init__(self, contracts, accounts, rols, test, instruction=None):
        super().__init__()
        uic.loadUi("./ui/Instruction.ui", self)
        self.contracts = contracts
        self.arguments = []
        self.argument_list = []
        self.accounts = accounts
        self.rols = rols
        self.test = test
        self.instruction = instruction
        self.instruction_accounts = []
        self.msg_values = Random(0,0, "ether denomination", "wei")
        self.is_defined = False
        self.prev_output_key = None

        self.select_contract.addItems(self.contracts.keys())
        self.select_contract.currentIndexChanged.connect(self.set_versions)

        self.delete_btn.setIcon(QIcon('./clear.png'))
        self.delete_btn.clicked.connect(self.delete_widget)
        
        self.select_version.currentIndexChanged.connect(self.set_functions)
        self.select_function.currentIndexChanged.connect(self.set_arguments)
        self.select_arguments.clicked.connect(self.select_args)

        if instruction != None:
            self.set_default_values()
            # set default values and block change

    def set_default_values(self):
        
        # set default values for the instruction
        self.select_contract.setCurrentText(self.instruction.contract.name)
        self.iterations.setValue(self.instruction.number_of_executions)
        self.select_version.setCurrentText(str(self.instruction.version))
        self.time_interval.setValue(self.instruction.time_interval)
        self.select_function.setCurrentText(self.instruction.function_name)
        self.argument_list = self.instruction.args
        self.instruction_accounts = self.instruction.accounts
        self.prev_output_key = self.instruction.prev_output_key

        # disable changes to the widgets
        self.select_contract.setEnabled(False)
        self.select_version.setEnabled(False)
        self.select_function.setEnabled(False)

        self.is_defined = True        

    def delete_widget(self):
        parent_layout = self.parent().layout()
        parent_layout.removeWidget(self)
        self.deleteLater()
        del self

    def select_args(self):
        dlg = List_Arguments_Dialog(self.arguments, self.accounts, self.rols, self.test, self.instruction)

        if dlg.exec():
            if dlg.checkBox.isChecked():
                file_path = dlg.file_path.text()

                for arg in self.arguments:
                    self.argument_list.append(File(file_path, arg[0], arg[1]))
            else:
                for i in range(dlg.scroll_widget_layout.count()):
                    self.argument_list.append(dlg.scroll_widget_layout.itemAt(i).widget().arg)

            print(self.argument_list)
        
            self.instruction_accounts = [index for index in dlg.selected_accounts]
            self.msg_values = dlg.msg_values
            self.is_defined = True
            self.prev_output_key = dlg.prev_output_key
        else:
            print("wains")

    def set_versions(self, index):
        self.select_version.clear()

        versions = len(self.contracts[self.select_contract.currentText()])

        self.select_version.clear()
        self.select_version.addItems([str(i) for i in range(versions)])

    def set_functions(self, index):
        self.select_function.clear()

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
        
        try:
            self.arguments = [(input["name"], input["type"]) for input in function_dict["inputs"]]
        except:
            self.arguments = []

    def get_instruction(self):
        if self.is_defined == False:
            raise Exception

        version = self.select_version.currentIndex()
        contract = self.contracts[self.select_contract.currentText()][version]
        function_name = self.select_function.currentText()
        exec_n = self.iterations.value()
        time_interval = self.time_interval.value()

        return Instruction(contract, version, function_name, exec_n, self.argument_list, self.msg_values, self.prev_output_key,time_interval, self.instruction_accounts)

class Argument_Widget_v2(QWidget):
    def __init__(self, test, arg_info, arg = None):
        super().__init__()
        uic.loadUi("./ui/Argument_Widget_v2.ui", self)

        self.arg = arg
        self.arg_name = arg_info[0]
        self.arg_type = arg_info[1]
        self.test = test

        self.label.setText(self.arg_name)
        self.pushButton.clicked.connect(self.select_args)


    def select_args(self):
        dlg = Argument_Dialog(self.test.prev_outputs, self.arg)

        if dlg.exec():
            self.arg = dlg.get_checked_button_values()
            self.arg.name = self.arg_name
            self.arg.type = self.arg_type
            print(self.arg)
        else:
            print("NOOOO")

class List_Arguments_Dialog(QDialog):
    def __init__(self, args, accounts, rols, test, instruction=None):
        super().__init__()
        uic.loadUi("./ui/List_Arguments_Dialog.ui", self)

        self.resize(400,400)

        self.accounts = accounts
        self.rols = rols
        self.instruction = instruction
        self.test = test
        self.prev_output_key = None

        if instruction != None:
            self.selected_accounts = copy.deepcopy(instruction.accounts)
        else:
            self.selected_accounts = []

        self.msg_values = Random(0,0, "ether denomination", "wei")

        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.select_accounts_btn.clicked.connect(self.add_accounts)
        self.select_ether_btn.clicked.connect(self.add_ether_values)
        self.checkBox.toggled.connect(self.enable_disable_widgets)
        self.browse_btn.clicked.connect(self.get_path)
        self.add_output_btn.clicked.connect(self.add_output_key)

        self.widget.setLayout(self.scroll_widget_layout)
        self.add_widgets(args)

    def add_widgets(self, args):
        select_arg_widget = None

        for index, arg in enumerate(args):
            if self.instruction is None:
                select_arg_widget = Argument_Widget_v2(self.test, arg)
            else:
                select_arg_widget = Argument_Widget_v2(self.test, arg, self.instruction.args[index])

            self.scroll_widget_layout.addWidget(select_arg_widget)

    def check_valid_args(self):
        # Check if there is at least an account selected
        if self.selected_accounts == []:
            return False

        # Check if all arguments are set
        for i in range(self.scroll_widget_layout.count()):
            if self.scroll_widget_layout.itemAt(i).widget().arg == None:
                return False
        
        return True

    def enable_disable_widgets(self):
        checked_bool = self.checkBox.isChecked()

        self.file_path.setEnabled(checked_bool)
        self.browse_btn.setEnabled(checked_bool)

    def add_output_key(self):
        new_key = self.save_output_edit.text()

        if new_key not in self.test.prev_outputs.keys():
            self.test.prev_outputs[new_key] = []
            self.prev_output_key = new_key
            print("yay")

    def get_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All files (*)")

        self.file_path.setText(path)

    def add_accounts(self):
        dlg = Select_Account_Dialog(self.accounts, self.rols, self.selected_accounts)

        if dlg.exec():
            self.selected_accounts = dlg.get_selected_accounts_indexes()
        else:
            pass

    def add_ether_values(self):
        dlg = Select_Ether_Dialog()

        if dlg.exec():
            self.msg_values = dlg.get_checked_button_values()
            self.msg_values.type = dlg.select_wei_denomination.currentText()
            self.msg_values.name = "ether denomination"
        else:
            pass

    def accept(self):
        if self.checkBox.isChecked() and Path(self.file_path.text()).exists() and self.file_path.text() != "":
            return super().accept()
        else:
            are_args_valid = self.check_valid_args()
            if are_args_valid:
                return super().accept()

        error_message = QErrorMessage(self)
        error_message.showMessage("All arguments must be defined")

class Select_Account_Dialog(QDialog):
    def __init__(self, accounts, rols, prev_selected_accounts):
        super().__init__()
        uic.loadUi("./ui/Select_Account_Dialog.ui", self)

        self.model = Select_Accounts_Model(accounts)
        self.listView.setModel(self.model)
        self.rols = rols
        self.prev_selected_accounts = prev_selected_accounts
        self.select_accounts(self.prev_selected_accounts)

        self.select_rol.addItems(list(self.rols.keys()))
        self.select_rol.currentTextChanged.connect(self.select_rol_accounts)

    def get_selected_accounts_indexes(self):
        indexes = [index.row() for index in self.listView.selectedIndexes()]

        return indexes

    def select_rol_accounts(self):
        rol = self.rols[self.select_rol.currentText()] # dictionary
        
        self.select_accounts(rol.idx)

    def select_accounts(self, indexes):
        self.listView.clearSelection()

        for idx in indexes:
            ix = self.listView.model().index(idx, 0)
            self.listView.selectionModel().setCurrentIndex(ix, QItemSelectionModel.SelectionFlag.Select)   

class Edit_Test_Dialog(Test_Dialog):
    def __init__(self, contracts, project_path, test):
        super().__init__("Edit_Test.ui",contracts, project_path, test)

        # Assigning test attributes as default values
        self.test = test
        self.test_name.setText(self.test.name)
        self.test_name.setEnabled(False)
        self.spinBox.setValue(self.test.number_of_nodes)
        self.spinBox.setMaximum(self.spinBox.value())
        self.spinBox_2.setValue(self.test.concurrency_number)

        self.add_existing_instructions()
        
    def add_existing_instructions(self):

        for instruction in self.test.instructions:
            self.add_instruction(instruction)

class Manage_Test(QDialog):
    def __init__(self, contracts, project_path):
        super().__init__()
        uic.loadUi("./ui/Manage_Test.ui", self)
        self.project_path = project_path
        self.contracts = contracts

        self.line_edits = {0 : self.lineEdit, 2 : self.copy_test_name}

        # connect signals to change the stacked widget current page
        self.create_btn.clicked.connect(lambda : self.stackedWidget.setCurrentIndex(0))
        self.create_btn.clicked.connect(self.enable_disable_btn)
        self.edit_btn.clicked.connect(lambda : self.stackedWidget.setCurrentIndex(1))
        self.edit_btn.clicked.connect(self.enable_disable_btn)
        self.copy_btn.clicked.connect(lambda : self.stackedWidget.setCurrentIndex(2))
        self.copy_btn.clicked.connect(self.enable_disable_btn)

        # connect onChange signals to enable disable Ok button
        self.lineEdit.textChanged.connect(self.enable_disable_btn)
        self.edit_select.currentTextChanged.connect(self.enable_disable_btn)
        self.copy_select.currentTextChanged.connect(self.enable_disable_btn)
        self.copy_test_name.textChanged.connect(self.enable_disable_btn)

        # fill select widgets
        self.test_data = self.load_test_data()
        self.edit_select.addItems(list(self.test_data.keys()))
        self.copy_select.addItems(list(self.test_data.keys()))

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def enable_disable_btn(self):
        current_index = self.stackedWidget.currentIndex()
        
        if current_index == 0 or current_index == 2:
            if self.line_edits[current_index].text() != "":
                try:
                    test = self.test_data[self.line_edits[current_index].text()]
                    self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                except:
                    self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            else:
                self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        elif current_index == 1:
            if self.edit_select.currentText() != "":
                self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            else:
                self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    # next button ?
    def accept(self) -> None:
        #return super().accept()
        dlg = None

        if self.stackedWidget.currentIndex() == 0: # Create New Test
            test = Test(name=self.lineEdit.text())
            dlg = Manage_Accounts(False, Test_Dialog, self.contracts, self.project_path, test)

        elif self.stackedWidget.currentIndex() == 1: #Edit Existing Test
            try:
                test = self.test_data[self.edit_select.currentText()]
                dlg = Manage_Accounts(True, Edit_Test_Dialog, self.contracts, self.project_path, test)
            except:
                return # meanwhile
        elif self.stackedWidget.currentIndex() == 2: #Copy Existing Test
            try:
                test = self.test_data[self.copy_select.currentText()]
                copied_test = copy.deepcopy(test)
                copied_test.name = self.copy_test_name.text()

                src_path = os.path.join(self.project_path, "tests", test.name)
                dst_path = os.path.join(self.project_path, "tests", copied_test.name)

                #os.mkdir(dst_path)
                shutil.copytree(src_path, dst_path)
                
                #Añadir aqui el nuevo test a la lista de tests?
                dlg = Manage_Accounts(True, Edit_Test_Dialog, self.contracts, self.project_path, copied_test)
            except Exception as e:
                print(e)
                return # meanwhile

        if dlg.exec():
            print("wii")
        else:
            print("woo")

        
    def load_test_data(self):
        data_path = os.path.join(self.project_path, "tests", "test_data.pkl")
        test_data = {}

        try:
            with open(data_path, "rb") as f:
                test_data = pickle.load(f)
        except:
            pass

        return test_data
          
class Manage_Accounts(QDialog):
    def __init__(self, edit_bool, next_dlg, contracts, project_path, test):
        super().__init__()
        uic.loadUi("./ui/Manage_Accounts.ui", self)

        self.next_dlg = next_dlg
        self.contracts = contracts
        self.project_path = project_path
        self.test = test
        self.edit_bool = edit_bool

        self.model = Select_Accounts_Model(self.test.accounts)
        self.listView.setModel(self.model)

        # connect btns clicked signals to slots
        self.create_accounts_btn.clicked.connect(self.create_accounts)
        self.create_rol_btn.clicked.connect(self.create_rol)

    def create_accounts(self):
        number = self.accounts_number_spin.value()
        
        self.test.create_accounts(number)
        
        self.model = Select_Accounts_Model(self.test.accounts)
        self.listView.setModel(self.model)


        # create accounts, adds them to a model and add to the qlistview

    def create_rol(self):
        # hay que verificar que no haya un rol con el mismo nombre primero
        name = self.rol_name.text()
        min_idx = self.rol_spin_1.value()
        max_idx = self.rol_spin_2.value()

        idxs = list(range(min_idx, max_idx))

        self.test.add_new_rol(name, idxs)

    def accept(self) -> None:
        dlg = None

        if self.edit_bool:
            dlg = self.next_dlg(self.contracts, self.project_path, self.test)
        else:
            dlg = self.next_dlg("Test_v2.ui", self.contracts, self.project_path, self.test)

        if dlg.exec():
            print("a")
        else:
            pass





