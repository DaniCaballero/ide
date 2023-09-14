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

class Test_Dialog(QDialog):
    def __init__(self, ui_name, main_window, test):
        super().__init__()
        uic.loadUi(f"./ui/Qt/{ui_name}", self)
        self.main_window = main_window
        self.contracts = self.main_window.contracts
        self.project_path = self.main_window.project.path
        self.instructions = []
        self.test = test
        self.thread_event = threading.Event()

        self.test_name.setText(self.test.name)
        self.test_name.setEnabled(False)

        self.add_inst_btn.clicked.connect(self.select_instruction)
        self.run_test_btn.clicked.connect(self.run_test)
        self.create_test_btn.clicked.connect(self.create_test)
        self.results_btn.clicked.connect(self.see_results)
        self.cancel_btn.clicked.connect(self.thread_event.set)

        with open("./ui/Stylesheets/test_dialogs.qss", "r") as f:
            _styles = f.read()
            self.setStyleSheet(_styles)
                    
        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_widget.setLayout(self.scroll_widget_layout)

    def select_instruction(self):
        dlg = Select_Instruction()
        is_contract_instruction = False

        if dlg.exec():
            if dlg.contract_radio.isChecked():
                is_contract_instruction = True
            
            self.add_instruction(is_contract_instruction)
        else:
            pass

    def add_instruction(self, is_contract_instruction, instruction=None):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor("#ADAAB5"))
        shadow.setOffset(4)
        #print("instruction ", instruction )

        if is_contract_instruction:
            ui_instruction = Instruction_Widget(self.contracts, self.test.accounts, self.test.rols, self.test, instruction)
        else:
            ui_instruction = Instruction_Balance_Widget(self.test, instruction)

        ui_instruction.setGraphicsEffect(shadow)
        shadow.setEnabled(True)
        self.scroll_widget_layout.addWidget(ui_instruction)

    def save_test(self):
            self.main_window.tests[self.test.name] = self.test


    def create_test(self):
        self.instructions = []
        self.reset_progress_bar()
        
        try:
            inst_count = self.scroll_widget_layout.count()

            if inst_count == 0:
                return
            
            for i in range(inst_count):
                self.instructions.append(self.scroll_widget_layout.itemAt(i).widget().get_instruction())

            print("All instructions ", self.instructions)
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
        self.test.inst_count = 0
        self.test.results = []
        self.test.error = False
        self.test.nodes = []

        try:
            for instruction in self.test.instructions:
                print("msg_values", instruction.msg_values)
                instruction.msg_values.generate_data(instruction.number_of_executions)
                for arg in instruction.args:
                    arg.generate_data(instruction.number_of_executions)
        except Exception as e:
            print(e)
            error_message = QErrorMessage(self)
            error_message.showMessage("Failed to initialize arguments")
            self.run_test_btn.setEnabled(False)
            return

        self.run_test_btn.setEnabled(True)
        
        self.save_test()

    def see_results(self):
        # check first if there's a problem with test results
        dlg = Results_Dialog(self.test.results)

        if dlg.exec():
            pass
    
    def show_error_progress_bar(self):
        self.progressBar.setStyleSheet("QProgressBar::chunk {background-color: red}")
        self.progressBar.setValue(100)

    def reset_progress_bar(self):
        self.progressBar.setStyleSheet("QProgressBar::chunk {background-color: lightgreen}")
        self.progressBar.reset()
    
    def run_test(self):
        self.run_test_btn.setEnabled(False)
        self.thread_event.clear()

        threading.Thread(target=self.test.run, args=(self.thread_event,)).start()

        self.thread = QThread()

        worker = Worker(self.test)
        worker.moveToThread(self.thread)
        worker.progressChanged.connect(self.progressBar.setValue)
        worker.errorFound.connect(self.show_error_progress_bar)
        self.thread.started.connect(worker.work)

        worker.finished.connect(lambda : self.results_btn.setEnabled(True))
        worker.finished.connect(self.thread.quit)
        worker.finished.connect(worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.worker = worker

        self.thread.start()

class Select_Instruction(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./ui/Qt/Select_Instruction.ui", self)

        self.contract_radio.toggled.connect(self.enable_ok)
        self.balance_radio.toggled.connect(self.enable_ok)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def enable_ok(self):
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

class Argument_Dialog(QDialog):
    def __init__(self, ui_file_name, test, inherit = False, arg = None):
        super().__init__()
        uic.loadUi(f"./ui/Qt/{ui_file_name}", self)
        self.current_toggled = None
        self.arg = arg

        self.max_columns = {"File:" : [0, 2, 2] , "Sequence:" : [4, 4, 2], "Random:" : [3, 3, 2], "Previous Output:" : [1, 2, 2],
                             "List:" : [2, 2, 1], "Accounts:" : [3,2,1], "Time:" : [5, 3, 2]}
        self.prev_output_index = None

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.radioButton.toggled.connect(lambda : self.disable_enable_children(self.radioButton.text()))
        self.radioButton.toggled.connect(self.validate_row_1)

        self.radioButton_4.toggled.connect(lambda : self.disable_enable_children(self.radioButton_4.text()))
        self.radioButton_4.toggled.connect(self.validate_row_4)
        self.radioButton_5.toggled.connect(lambda : self.disable_enable_children(self.radioButton_5.text()))
        self.radioButton_5.toggled.connect(self.validate_row_5)

        self.lineEdit.textChanged.connect(self.validate_row_1)
        self.lineEdit_2.textChanged.connect(self.validate_row_5)
        
        self.pushButton.clicked.connect(self.get_path)
        self.select_index_btn.clicked.connect(self.select_output_index)

        self.select_prev_output.addItems(list(test.prev_outputs.keys()))

        if inherit == False and self.arg != None:
            self.set_default_values()

    def set_default_values(self):
        
        class_name = type(self.arg).__name__

        if class_name == "File":
            self.radioButton.setChecked(True)
            self.lineEdit.setText(self.arg.path)

        elif class_name == "Prev_Output":
            self.radioButton_4.setChecked(True)
            self.select_prev_output.setCurrentText(self.arg.output_dict_name)

        elif class_name == "List_Arg":
            self.radioButton_5.setChecked(True)
            self.lineEdit_2.setText(self.arg.text)

    def get_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;TXT Files (*.txt)")

        self.lineEdit.setText(path)

    def disable_enable_children(self, text):
        self.change_enabled_widgets(text, True)

        if self.current_toggled != None:
            self.change_enabled_widgets(self.current_toggled, False)

        self.current_toggled = text

    def select_output_index(self):
        dlg = Select_Output_Index()

        if dlg.exec():
            if dlg.select_index_radio.isChecked():
                self.prev_output_index = dlg.index_spin.value()


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

    def validate_row_4(self):

        if self.select_prev_output.currentText() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def validate_row_5(self):
        
        if self.lineEdit_2.text() != "":
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)  


    def get_checked_button_values(self):

        if self.radioButton.isChecked():
            path = self.lineEdit.text() #trim probablemente. check if is path
            print("UWU")

            return File(file_path=path)
        
        elif self.radioButton_4.isChecked():
            key_name = self.select_prev_output.currentText()

            return Prev_Output(key_name, self.prev_output_index)
        
        elif self.radioButton_5.isChecked():
            text = self.lineEdit_2.text()

            return List_Arg(text)
        
        else:
            print("upss")

class Argument_Dialog_Int(Argument_Dialog):
    def __init__(self, ui_file_name, test, inherit, arg = None):
        super().__init__(ui_file_name, test, inherit, arg)

        self.radioButton_2.toggled.connect(lambda : self.disable_enable_children(self.radioButton_2.text()))
        self.radioButton_2.toggled.connect(self.validate_row_2)
        self.radioButton_3.toggled.connect(lambda : self.disable_enable_children(self.radioButton_3.text()))
        self.radioButton_3.toggled.connect(self.validate_row_3)
        #self.radioButton_6.toggled.connect(lambda : self.disable_enable_children(self.radioButton_6.text()))
        #self.radioButton_6.toggled.connect(self.activate_checkbox)

        self.spinBox.valueChanged.connect(self.validate_row_2)
        self.spinBox_2.valueChanged.connect(self.validate_row_2)

        self.spinBox_4.valueChanged.connect(self.validate_row_3)
        self.spinBox_5.valueChanged.connect(self.validate_row_3)

        if self.arg != None:
            self.set_default_values()

    def disable_enable_children(self, text):

        return super().disable_enable_children(text)

    # def activate_checkbox(self):
    #     if self.radioButton_6.isChecked():
    #         self.random_checkbox.setEnabled(True)
    #         self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def set_default_values(self):
        class_name = type(self.arg).__name__

        if class_name == "Sequence":
            self.radioButton_2.setChecked(True)
            self.spinBox.setValue(self.arg.min)
            self.spinBox_2.setValue(self.arg.max)
            self.spinBox_3.setValue(self.arg.step)

        elif class_name == "Random":
            self.radioButton_3.setChecked(True)
            self.spinBox_4.setValue(self.arg.min)
            self.spinBox_5.setValue(self.arg.max)
        
        else:
            return super().set_default_values()

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

        if self.radioButton_2.isChecked():
            start = self.spinBox.value()
            end = self.spinBox_2.value()
            step = self.spinBox_3.value()

            return Sequence(start, end, step=step)
            
        elif self.radioButton_3.isChecked():
            start = self.spinBox_4.value()
            end = self.spinBox_5.value()

            return Random(start, end)
        
        else:
            return super().get_checked_button_values()

class Argument_Dialog_Accounts(Argument_Dialog):
    def __init__(self, ui_file_name, test, inherit, arg = None):
        super().__init__(ui_file_name, test, inherit, arg)
        self.accounts = test.accounts
        self.rols = test.rols
        self.selected_accounts = []

        self.radioButton_2.toggled.connect(lambda : self.disable_enable_children(self.radioButton_2.text()))
        self.radioButton_2.toggled.connect(self.validate_row_2)

        self.pushButton_2.clicked.connect(self.select_accounts)

        if self.arg != None:
            self.selected_accounts = arg.data
            self.set_default_values()

    def set_default_values(self):

        class_name = type(self.arg).__name__

        if class_name == "Argument":
            self.radioButton_2.setChecked(True)

        else:
            return super().set_default_values()

    def validate_row_2(self):
        if self.selected_accounts != []:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    def select_accounts(self):
        dlg = Select_Account_Dialog(self.accounts, self.rols, self.selected_accounts)

        if dlg.exec():
            self.selected_accounts = dlg.get_selected_accounts_indexes()
            self.validate_row_2()
        else:
            pass

    def get_checked_button_values(self):
        if self.radioButton_2.isChecked():
            arg = Argument("", "")
            arg.data = self.selected_accounts

            return arg
        else:
            return super().get_checked_button_values()

class Select_Ether_Dialog(Argument_Dialog):
    def __init__(self, ui_file_name, test, inherit, arg = None):
        super().__init__(ui_file_name, test, inherit, arg)
        
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
        uic.loadUi("./ui/Qt/Instruction.ui", self)
        self.contracts = contracts
        self.arguments = []
        self.argument_list = []
        self.accounts = accounts
        self.rols = rols
        self.test = test
        self.instruction = instruction
        self.instruction_accounts = []
        self.msg_values = Random(0,0, "ether", "wei")
        self.is_defined = False
        self.prev_output_key = None

        self.select_arguments.setEnabled(False)

        self.select_contract.addItems(self.contracts.keys())
        self.select_contract.currentIndexChanged.connect(self.set_versions)

        self.delete_btn.setIcon(QIcon('./ui/Icons/clear.png'))
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

            self.argument_list = []

            if dlg.use_csv.isChecked():
                file_path = dlg.file_path.text()

                for arg in self.arguments:
                    self.argument_list.append(File(file_path, arg[0], arg[1]))
            else:
                for i in range(dlg.scroll_widget_layout.count()):
                    self.argument_list.append(dlg.scroll_widget_layout.itemAt(i).widget().arg)

            print(self.argument_list)
        
            self.instruction_accounts = [index for index in dlg.selected_accounts]
            self.msg_values = dlg.msg_values
            self.prev_output_key = dlg.prev_output_key
            self.is_defined = True
            self.instruction = self.get_instruction()


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

        self.select_arguments.setEnabled(True)

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
        uic.loadUi("./ui/Qt/Argument_Widget_v2.ui", self)

        self.arg = arg
        self.arg_name = arg_info[0]
        self.arg_type = arg_info[1]
        self.test = test

        self.label.setText(self.arg_name)
        self.pushButton.clicked.connect(self.select_args)

    def select_args(self):
        class_name, ui_file_name, inherit = self.get_ui_file_name()
        dlg = class_name(ui_file_name, self.test, inherit, self.arg)

        if dlg.exec():
            self.arg = dlg.get_checked_button_values()
            self.arg.name = self.arg_name
            self.arg.type = self.arg_type
            print(self.arg)
        else:
            print("NOOOO")

    def get_ui_file_name(self):
        class_name, ui_file_name, inherit = Argument_Dialog,"Argument_Dialog_Base.ui", False

        if "[" not in self.arg_type:
            if "int" in self.arg_type:
                ui_file_name = "Argument_Dialog_Alt.ui"
                class_name = Argument_Dialog_Int
                inherit = True
            elif "address" in self.arg_type:
                ui_file_name = "Argument_Dialog_Accounts.ui"
                class_name = Argument_Dialog_Accounts
                inherit = True

        return class_name, ui_file_name, inherit

class List_Arguments_Dialog(QDialog):
    def __init__(self, args, accounts, rols, test, instruction=None):
        super().__init__()
        uic.loadUi("./ui/Qt/List_Arguments_Dialog.ui", self)

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

        self.msg_values = Random(0,0, "ether", "wei")

        self.scroll_widget_layout = QVBoxLayout()
        self.scroll_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.select_accounts_btn.clicked.connect(self.add_accounts)
        self.select_ether_btn.clicked.connect(self.add_ether_values)
        self.use_csv.toggled.connect(self.enable_disable_widgets)
        self.browse_btn.clicked.connect(self.get_path)
        self.add_output_btn.clicked.connect(self.add_output_key)

        self.widget.setLayout(self.scroll_widget_layout)
        self.add_widgets(args)

        if args == []:
            self.use_csv.setEnabled(False)

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
        checked_bool = self.use_csv.isChecked()

        self.file_path.setEnabled(checked_bool)
        self.browse_btn.setEnabled(checked_bool)

    def add_output_key(self):
        new_key = self.save_output_edit.text().strip()

        if new_key not in self.test.prev_outputs.keys() and " " not in new_key:
            self.test.prev_outputs[new_key] = []
            self.prev_output_key = new_key
            print("yay")
        else:
            error_message = QErrorMessage(self)
            error_message.showMessage("Key is not valid")

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
        dlg = Select_Ether_Dialog("Argument_Dialog_Base.ui", self.test, False)

        if dlg.exec():
            self.msg_values = dlg.get_checked_button_values()
            self.msg_values.type = dlg.select_wei_denomination.currentText()
            self.msg_values.name = "ether"
            print("ether values", self.msg_values)
        else:
            pass

    def accept(self):
        if self.use_csv.isChecked() and Path(self.file_path.text()).exists() and self.file_path.text() != "":
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
        uic.loadUi("./ui/Qt/Select_Account_Dialog.ui", self)

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
    def __init__(self, main_window, test):
        super().__init__("Edit_Test.ui", main_window, test)

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
            is_contract_instruction = instruction.contract != ""
            self.add_instruction(is_contract_instruction, instruction)

class Manage_Test(QDialog):
    def __init__(self, main_window):
        super().__init__()
        uic.loadUi("./ui/Qt/Manage_Test.ui", self)

        self.main_window = main_window
        self.project_path = self.main_window.project.path
        self.contracts = self.main_window.contracts
        self.test_data = self.main_window.tests

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
        #self.test_data = self.load_test_data()
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
    
    def copy_network_address(self, previous_test, new_test):
        
        for instruction in previous_test.instructions:
            try:
                contract = self.main_window.contracts[instruction.contract.name][instruction.version]
                contract.address[f"geth-{new_test.name}"] = instruction.contract.address[f"geth-{previous_test.name}"]
            except Exception as e:
                print(e)

    # next button ?
    def accept(self) -> None:
        #return super().accept()
        dlg = None

        if self.stackedWidget.currentIndex() == 0: # Create New Test
            test = Test(name=self.lineEdit.text())
            dlg = Manage_Accounts(False, Test_Dialog, self.main_window, test)

        elif self.stackedWidget.currentIndex() == 1: #Edit Existing Test
            try:
                test = self.test_data[self.edit_select.currentText()]
                dlg = Manage_Accounts(True, Edit_Test_Dialog, self.main_window, test)
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

                self.copy_network_address(test, copied_test)
                
                #Añadir aqui el nuevo test a la lista de tests?
                dlg = Manage_Accounts(True, Edit_Test_Dialog, self.main_window, copied_test)
            except Exception as e:
                print(e)
                return # meanwhile

        if dlg.exec():
            pass

        self.close()

class Manage_Accounts(QDialog):
    def __init__(self, edit_bool, next_dlg, main_window, test):
        super().__init__()
        uic.loadUi("./ui/Qt/Manage_Accounts.ui", self)

        with open("./ui/Stylesheets/dialog_styles.qss", "r") as f:
            _styles = f.read()
            self.setStyleSheet(_styles)

        self.main_window = main_window
        self.next_dlg = next_dlg
        self.test = test
        self.edit_bool = edit_bool

        self.model = Select_Accounts_Model(self.test.accounts)
        self.listView.setModel(self.model)

        self.rol_model = Rols_Model(list(self.test.rols.keys()))
        self.rols_view.setModel(self.rol_model)

        # connect btns clicked signals to slots
        self.create_accounts_btn.clicked.connect(self.create_accounts)
        self.create_rol_btn.clicked.connect(self.create_rol)
        self.add_accounts_btn.clicked.connect(self.add_existing_accounts)

    def add_role_to_view(self):
        self.rol_model = Rols_Model(list(self.test.rols.keys()))
        self.rols_view.setModel(self.rol_model)

    def update_model(self):
        self.model = Select_Accounts_Model(self.test.accounts)
        self.listView.setModel(self.model)

    def create_accounts(self):
        number = self.accounts_number_spin.value()
        
        self.test.create_accounts(number)
        
        self.update_model()

        # create accounts, adds them to a model and add to the qlistview

    def add_existing_accounts(self):
        try:
            accounts = self.main_window.accounts["persistent"]
        except:
            accounts = {}

        dlg = Add_Existing_Accounts(list(accounts.values()))

        if dlg.exec():
            accounts = dlg.get_accounts()

            if accounts != []:
                for account in accounts:
                    self.test.accounts.append(account)
                
                self.update_model()

    def create_rol(self):
        # hay que verificar que no haya un rol con el mismo nombre primero
        name = self.rol_name.text().strip()
        existing_names = self.test.rols.keys()

        if name not in existing_names:
            min_idx = self.rol_spin_1.value()
            max_idx = self.rol_spin_2.value()

            if min_idx < max_idx:
                idxs = list(range(min_idx, max_idx))

                if " " not in name:
                    self.test.add_new_rol(name, idxs)
                    self.add_role_to_view()
                else:
                    error_message = QErrorMessage(self)
                    error_message.showMessage("Name cannot contain white spaces")

    def accept(self) -> None:
        dlg = None

        if self.test.accounts == []:
            return

        if self.edit_bool:
            dlg = self.next_dlg(self.main_window, self.test)
        else:
            dlg = self.next_dlg("Test_v2.ui", self.main_window, self.test)

        if dlg.exec():
            pass

        self.close()

class Instruction_Balance_Widget(QWidget):
    def __init__(self, test, instruction = None):
        super().__init__()
        uic.loadUi("./ui/Qt/Instruction_Balance.ui", self)

        self.test = test
        self.instruction = instruction
        
        self.instruction_accounts = []
        self.msg_values = Random(0,0, "ether", "wei")
        self.is_defined = False
        self.prev_output_key = None

        self.delete_btn.setIcon(QIcon('./ui/Icons/clear.png'))

        self.select_accounts_btn.clicked.connect(self.select_accounts)
        self.delete_btn.clicked.connect(self.delete_widget)

        if self.instruction != None:
            self.set_default_values()

    def select_accounts(self):
        dlg = Select_Account_Dialog(self.test.accounts, self.test.rols, self.instruction_accounts)

        if dlg.exec():
            self.instruction_accounts = dlg.get_selected_accounts_indexes()
            self.is_defined = True
        else:
            pass

    def set_default_values(self):
        
        self.instruction_accounts = self.instruction.accounts
        self.iterations = self.instruction.number_of_executions
        self.time_interval = self.instruction.time_interval
        self.is_defined = True

    def delete_widget(self):
        parent_layout = self.parent().layout()
        parent_layout.removeWidget(self)
        self.deleteLater()
        del self

    def get_instruction(self):
        if self.is_defined == False:
            raise Exception

        version = ""
        contract = ""
        function_name = ""
        exec_n = self.iterations.value()
        time_interval = self.time_interval.value()

        return Instruction(contract, version, function_name, exec_n, [], self.msg_values, self.prev_output_key, time_interval, self.instruction_accounts)



class Add_Existing_Accounts(QDialog):
    def __init__(self, accounts):
        super().__init__()
        uic.loadUi("./ui/Qt/Add_Existing_Accounts.ui", self)
        
        self.accounts = accounts
        self.model = Select_Accounts_Model(accounts)
        self.listView.setModel(self.model)

    def get_selected_accounts_indexes(self):
        indexes = [index.row() for index in self.listView.selectedIndexes()]

        return indexes
    
    def get_accounts(self):
        indexes = self.get_selected_accounts_indexes()
        accounts = [self.accounts[i] for i in indexes]

        return accounts

class Results_Dialog(QDialog):
    def __init__(self, results):
        super().__init__()
        uic.loadUi("./ui/Qt/Results_Dialog.ui", self)

        self.model = ResultsModel(results)

        for i,name in enumerate(["Node port","Contract Name", "Account", "Function Name", "Function arguments", "Amount of ether sent", "Return value/Tx hash"]):
            self.model.setHeaderData(i, Qt.Orientation.Horizontal, name)

        self.tableView.setModel(self.model)
        #self.tableView.setColumnHidden(0, True)
        self.tableView.resizeColumnsToContents()
        #self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tableView.horizontalHeader().setStyleSheet("QHeaderView::section {background-color: #3f5c73;color: white; font-weight:bold}")
        self.tableView.horizontalHeader().setStretchLastSection(True)
        #self.tableView.setAlternatingRowColors(True)

        self.adjustSize()

        #self.resize(self.tableView.sizeHint().width(), self.sizeHint().height())

class Select_Output_Index(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("./ui/Qt/Select_Output_Index.ui", self)