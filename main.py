from PyQt6.QtCore import QSize, Qt, QThread, QProcess
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QHBoxLayout, QTabWidget, QStackedLayout, QSplitter, 
                            QMessageBox, QErrorMessage, QTextBrowser, QMenu)
from menu_functions import *
from dialogs.dialogs import (Compile_Dialog, Add_Account_Dialog, Add_Node_Dialog, Deploy_Dialog, IPFS_Token_Dialog, Functions_Layout, 
                    Project_Widget, Left_Widget, Test_Dialog, Create_Project_Dialog, Manage_Test, Add_Files_IPFS, Select_Script)
from tests.visualizador import Visualizer, Select_Test_Visualizer
from blockchain.account import Account, add_local_accounts
from blockchain.network import Network, init_ganache
from blockchain.ipfs import IPFS
from project.project import Editor, Project, Code_Output
from PyQt6.QtGui import QAction, QColor, QPalette, QIcon, QFont, QFontDatabase
import os, subprocess, psutil, sys, pickle, time, json, pathlib

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        start_time = time.time()
        self.setWindowTitle("IDE")
        self.setMinimumSize(QSize(800,600))
        self.project = Project()
        self.networks = {}
        self.accounts = {}
        self.contracts = {}
        self.tests = {}
        self.ipfs = ""

        # QProcess, assigned when executing a script
        self.p = None 
        
        with open("./ui/Stylesheets/main_styles.qss", "r") as f:
            _styles = f.read()
            self.setStyleSheet(_styles)

        font_id = QFontDatabase.addApplicationFont("./ui/Fonts/RobotoMono.ttf")
        self.font_families = QFontDatabase.applicationFontFamilies(font_id)

        editor = Editor(font_families=self.font_families)

        #print("FONT ID: ", font_id)

        self.output = Code_Output(self)
        self.output.setMaximumHeight(400)
        self.output.setFrameStyle(0)

        self.menu_actions = []
        self.create_menu_bar()

        self.editor_tab = QTabWidget()
        self.editor_tab.addTab(editor, editor.file_name)
        self.editor_tab.setTabsClosable(True)
        self.editor_tab.tabCloseRequested.connect(self.close_file)

        self.buttons_widget = Left_Widget()
        self.buttons_widget.project_button.clicked.connect(self.project_button_clicked)
        self.buttons_widget.function_button.clicked.connect(self.function_button_clicked)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        self.hsplit = QSplitter(Qt.Orientation.Horizontal)

        self.stacked_layout = QStackedLayout()
        self.project_widget = Project_Widget(self)
        self.functions_widget = Functions_Layout(self)
        self.functions_widget.function_signal.connect(self.add_to_output)

        stacked_widget = QWidget()
        self.stacked_layout.addWidget(self.project_widget)
        self.stacked_layout.addWidget(self.functions_widget)
        stacked_widget.setLayout(self.stacked_layout)
        
        editor_split = QSplitter(Qt.Orientation.Vertical)
        editor_split.addWidget(self.editor_tab)
        editor_split.addWidget(self.output)
        editor_split.setSizes([self.height() - 200, 200])

        self.hsplit.addWidget(stacked_widget)
        self.hsplit.addWidget(editor_split)
        self.hsplit.setSizes([150, self.width() - 150])
        self.hsplit.setHandleWidth(1)

        main_layout.addWidget(self.buttons_widget, 10)
        main_layout.addWidget(self.hsplit, 90)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)
    
    def add_to_output(self, text, deploy_bool = False, json_bool = False, link=""):
        self.output.add_to_output(text, deploy_bool, json_bool, link)
        #self.output.append(f"{text}\n")

    def create_menu_bar(self):
        menu = self.menuBar()

        create_menu_option("File", ["New File", "Open", "Save", "Save As", "Close"], [self.new_file, self.open_file, self.save, self.save_as, self.close_file], ["Ctrl+N", "", "Ctrl+S", "Ctrl+Shift+S", ""],menu, self)
        create_menu_option("Project", ["Initialize", "Open", "Delete"], [self.init_project, self.open_project, self.delete_project], ["", "", ""],menu, self)
        create_menu_option("Compile", ["Compile File", "Compile All"], [lambda_func(compile_file, self), lambda_func(compile_file, self)],["",""], menu, self)
        create_menu_option("Accounts", ["Add account", "Generate account"], [lambda_func(add_account, self), lambda_func(generate_account, self)], ["",""],menu, self)
        create_menu_option("Networks", ["Add node provider"], [lambda_func(add_node_provider, self)], [""], menu, self)
        create_menu_option("IPFS", ["Add Token ID", "Add file"], [lambda_func(add_token_id, self), self.add_to_ipfs], ["",""], menu, self)
        create_menu_option("Deploy", ["Deploy contract"], [lambda_func(deploy_contract, self)], [""], menu, self)
        create_menu_option("Tests", ["Create Test", "Visualize Blockchain Activity"], [self.create_test, self.visualizer], ["", ""], menu, self)
        create_menu_option("Run", ["Select Script", "Run Active File"], [self.run_script], ["", ""], menu, self)
        
    def project_button_clicked(self):
        self.stacked_layout.setCurrentIndex(0)

    def function_button_clicked(self):
        self.stacked_layout.setCurrentIndex(1)

    def enable_menu_actions(self):
        for item in self.menu_actions:
            item.setEnabled(True)

    # copy files needed to run a script from user project
    def copy_scripts_folder(self, path):
        src = "./scripts_files"
        dst = os.path.join(path, "scripts", "scripts_files")

        shutil.copytree(src, dst)

    def init_project(self):
        if self.project.path == "":
            dlg = Create_Project_Dialog(self)

            if dlg.exec():
                try:
                    project_name = dlg.project_name.text()
                    project_path = dlg.project_path.text()
                    path = os.path.join(project_path, project_name)
                    os.mkdir(path)
                    
                    self.project.path = path
                    self.project.init_project()
                                
                    init_ganache(self)
                    # must wait a bit so accounts file gets created and can be added 
                    time.sleep(3)
                    self.copy_scripts_folder(path)
                    add_local_accounts(self)
                    self.functions_widget.update_networks()

                    self.statusBar().showMessage(f"Project initialized at {path}", 5000)
                    self.enable_menu_actions()
                    self.project_widget.add_tree_view(path)
                except:
                    self.statusBar().showMessage(f"Unable to initialize project at {path}", 5000)

    def open_project(self):
        if self.project.path == "":
            #self.save_data()
            #self.project = Project()
            
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
            is_project = self.project.exists_project(path)

            if is_project:
                try:
                    self.project.path = path
                    
                    init_ganache(self)
                    self.load_data()
                    add_local_accounts(self)

                    self.functions_widget.update_networks()

                    #self.output.append(f"Project found at {path}\n")
                    self.statusBar().showMessage(f"Project found at {path}", 2000)
                    self.enable_menu_actions()
                        
                    self.project_widget.add_tree_view(path)
                except:
                    self.statusBar().showMessage(f"Unable to open project at {path}", 2500)

    def delete_project(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")

        if path != "":
            project = Project(path)
            delete_bool = project.delete_project()

            if delete_bool:
                self.statusBar().showMessage(f"Project successfully deleted!", 2000)
            else:
                self.statusBar().showMessage(f"Unable to delete project", 2000)

    def is_binary(self, path):
        with open(path, 'rb') as f:
            return b'\0' in f.read(1024)

    def new_file(self):
        editor = Editor(font_families=self.font_families)
        self.editor_tab.addTab(editor, editor.file_name)

    def open_file(self): 
        path, _ = QFileDialog.getOpenFileName(self, "Open File", self.project.path, "All files (*)")
        if path != "":
            p = Path(path)
            self.add_new_tab(p)

    def save(self):
        editor = self.editor_tab.currentWidget()
        path = editor.file_path

        if path == "":
            self.save_as()
        else:
            print("path ", path)
            path.write_text(editor.text().replace("\r\n", "\n"))
            self.statusBar().showMessage(f"Saved file at {path}", 2000)

    def save_as(self):
        editor = self.editor_tab.currentWidget()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", self.project.path, "All files (*)")

        if path != "":
            path = Path(path)
            path.write_text(editor.text().replace("\r\n", "\n"))
            editor.file_path = path
            editor.change_name(path.name)
            self.editor_tab.setTabText(self.editor_tab.currentIndex(),editor.file_name)
            self.statusBar().showMessage(f"Saved file at {path}", 2000)

    def close_file(self, index):

        if self.editor_tab.currentWidget().text() != "" or self.editor_tab.currentWidget().file_path != "":
            if self.editor_tab.currentWidget().file_path != "":
                with open(self.editor_tab.currentWidget().file_path, "r") as file:
                    content = file.read()

                if content != self.editor_tab.currentWidget().text().replace("\r\n", "\n"):
                    reply = QMessageBox.question(self, "Warning", "Do you want to save the changes you made to the file?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.save()
                    elif reply == QMessageBox.StandardButton.No:
                        pass
                    else:
                        return
            else:
                self.save()

        self.editor_tab.removeTab(index)

    def add_new_tab(self, path):
        if not path.is_file():
            return

        if self.is_binary(path):
            self.statusBar().showMessage("Cannot Open Binary File", 3000)
            return

        for i in range(self.editor_tab.count()):
            if self.editor_tab.tabText(i) == path.name:
                self.editor_tab.setCurrentIndex(i)
                return

        editor = Editor(font_families=self.font_families)
        editor.setText(path.read_text())
        editor.file_path = path
        editor.change_name(path.name)
        self.editor_tab.addTab(editor, path.name)
        self.editor_tab.setCurrentWidget(editor)

    def create_test(self):
        #dlg = Test_Dialog(self.contracts, self.project.path)
        dlg = Manage_Test(self)

        if dlg.exec():
            pass

    def visualizer(self):
        tests_path = os.path.join(self.project.path, "tests")

        try:
            test_names = self.tests.keys()
        except:
            test_names = []

        dlg = Select_Test_Visualizer(test_names)

        if dlg.exec():
            test_name = dlg.comboBox.currentText()
            logs_path = os.path.join(tests_path, test_name, "logs")

            if os.path.isdir(logs_path):
                vis_dlg = Visualizer(logs_path)

                if vis_dlg.exec():
                    pass

    def handle_script_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.add_to_output(stdout)

    def handle_script_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.add_to_output(stderr)

    def script_finished(self):
        self.p = None

    def run_script(self):
        path = os.path.join(self.project.path, "scripts")
        print("listdir of path", os.listdir(path))
        files = [file_name for file_name in os.listdir(path) if os.path.isfile(os.path.join(self.project.path, "scripts", file_name)) == True]

        print("scripts", files)

        dlg = Select_Script(files, self)

        if dlg.exec():
            if self.p is None:
                selected_file = dlg.comboBox.currentText()
                extension = pathlib.Path(selected_file).suffix
                prev_cwd = os.getcwd()
                print("extension ", extension)

                file_path = os.path.join(self.project.path, "scripts", selected_file)

                self.p = QProcess()
                self.p.readyReadStandardOutput.connect(self.handle_script_stdout)
                self.p.readyReadStandardError.connect(self.handle_script_stderr)
                self.p.finished.connect(self.script_finished)

                os.chdir(self.project.path)

                if extension == ".py":
                    self.p.start("python", [file_path])
                    #subprocess.Popen(["python", file_path])
                elif extension == ".mjs":
                    print("uwu")
                    self.p.start("node", [file_path])
                    #subprocess.Popen(["node", file_path])
                
                os.chdir(prev_cwd)

            #subprocess.Popen(["python", tmp_path])
            
    def add_to_ipfs(self):
        dlg = Add_Files_IPFS(self.project.path, self)

        if dlg.exec():
            multiple_files, path, name = dlg.get_input()

            try:
                self.ipfs.upload_to_ipfs(path, name, multiple_files, self.project.path)
            except:
                error_msg = QErrorMessage(self)
                error_msg.showMessage("Unabled to upload files to IPFS")
                

    def load_data(self):
        try:
            path = self.project.path
            with open(os.path.join(path, "data.pkl"), "rb") as f:
                data = pickle.load(f)
            
            self.accounts = data["accounts"]
            self.networks = data["networks"]
            self.contracts = data["contracts"]
            self.tests = data["tests"]
            self.ipfs = data["ipfs"]

        except Exception:
            pass

    def save_data(self):
        path = self.project.path
        data = {}
        data["accounts"] = self.accounts
        data["networks"] = self.networks
        data["contracts"] = self.contracts
        data["tests"] = self.tests
        data["ipfs"] = self.ipfs

        with open(os.path.join(path, "data.pkl"), "wb") as f:
            pickle.dump(data, f)

    def save_to_json(self):
        '''Saves contract information to json to be able to retrieve objs from a python/js script'''
        tmp = {"contracts" : {}, "accounts" : {}, "networks" : {}}
        json_path = os.path.join(self.project.path, "project_data.json")

        for key, values in self.contracts.items():
            tmp["contracts"][key] = [contract.__dict__ for contract in values]


        for key, dict_values in self.accounts.items():
            tmp["accounts"][key] = [account.__dict__ for account in dict_values.values()]

        for key, value in self.networks.items():
            tmp["networks"][key] = value.__dict__

        with open(json_path, "w") as f:
            json.dump(tmp, f)

    def retrieve_from_json(self):
        '''Reassigns address attribute of contract after script execution, in orden to remain synced. Doesn't 
        create new instance of contract objects so references aren't lost'''
        json_path = os.path.join(self.project.path, "project_data.json")

        with open(json_path, "r") as f:
            data_json = json.load(f)
        
        for key, values in self.contracts.items():
            for i in range(len(values)):
                self.contracts[key][i].address = data_json["contracts"][key][i]["address"]


    def closeEvent(self, event):
        if self.project.path != "":
            self.save_data()

        # Ganache has to be terminated when app closes 
        for child in psutil.Process(os.getpid()).children():
            for child2 in psutil.Process(child.pid).children():
                child2.terminate()
            child.terminate()

    def test(self, contract_name):
        
        return len(self.contracts[contract_name])


app = QApplication([])


window = MainWindow()
window.show()

sys.exit(app.exec())


#sys.exit(app)