from PyQt6.QtCore import QSize, Qt, QThread
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QMenu, QHBoxLayout, QTextEdit, 
                            QTabWidget, QStackedLayout, QFrame, QToolButton, QSplitter, QStyleFactory, QMessageBox)
from menu_functions import *
from dialogs import (Compile_Dialog, Add_Account_Dialog, Add_Node_Dialog, Deploy_Dialog, IPFS_Token_Dialog, Functions_Layout, 
                    Project_Widget, Left_Widget, Test_Dialog, Create_Project_Dialog)
from account import Account, add_local_accounts
from network import Network, init_ganache
from ipfs import IPFS
from interact import contract_interaction
from project import Editor, Project
from PyQt6.QtGui import QAction, QColor, QPalette, QIcon, QFont, QFontDatabase
import os, signal, psutil, sys, pickle, time

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
        self.ipfs = ""

        #self.setObjectName("mainWindow")

        self.setStyleSheet("""QComboBox,QLineEdit,QDoubleSpinBox {border: 1px solid #ced4da; border-radius: 4px;padding: 5px 10px;background-color: white} 
                            QComboBox::drop-down {border: none} QComboBox::down-arrow {image: url(./down.png); width: 12px; height: 12px; 
                            margin-right: 15px} QDoubleSpinBox::down-button {border-radius: 4px} QDoubleSpinBox::up-button {border-radius: 4px}
                            QDoubleSpinBox::down-arrow {image: url(./down.png); width: 12px; height: 12px; margin-right: 15px}
                            QDoubleSpinBox::up-arrow {image: url(./up-arrow.png); width: 12px; height: 12px; margin-right: 15px}""")
        

        font_id = QFontDatabase.addApplicationFont("RobotoMono.ttf")
        self.font_families = QFontDatabase.applicationFontFamilies(font_id)

        editor = Editor(font_families=self.font_families)

        print("FONT ID: ", font_id)

        self.output = QTextEdit()
        self.output.setMaximumHeight(400)
        self.output.setFrameStyle(0)

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
    
    def add_to_output(self, text):
        self.output.append(text)

    def create_menu_bar(self):
        menu = self.menuBar()

        create_menu_option("File", ["New File", "Open", "Save", "Save As", "Close"], [self.new_file, self.open_file, self.save, self.save_as, self.close_file], ["Ctrl+N", "", "Ctrl+S", "Ctrl+Shift+S", ""],menu, self)
        create_menu_option("Project", ["Initialize", "Open", "Delete"], [self.init_project, self.open_project, self.delete_project], ["", "", ""],menu, self)
        create_menu_option("Compile", ["Compile File", "Compile All"], [lambda_func(compile_file, self), lambda_func(compile_file, self)],["",""], menu, self)
        create_menu_option("Accounts", ["Add account", "Generate account"], [lambda_func(add_account, self), lambda_func(generate_account, self)], ["",""],menu, self)
        create_menu_option("Networks", ["Add node provider"], [lambda_func(add_node_provider, self)], [""], menu, self)
        create_menu_option("IPFS", ["Add Token ID", "Add file"], [lambda_func(add_token_id, self), lambda_func(add_file_to_ipfs, self)], [","], menu, self)
        create_menu_option("Deploy", ["Deploy contract"], [lambda_func(deploy_contract, self)], [""], menu, self)
        create_menu_option("Tests", ["Create Test"], [self.create_test], [""], menu, self)
        

    def project_button_clicked(self):
        self.stacked_layout.setCurrentIndex(0)

    def function_button_clicked(self):
        self.stacked_layout.setCurrentIndex(1)

    def init_project(self):
        dlg = Create_Project_Dialog()

        if dlg.exec():
            try:
                project_name = dlg.project_name.text()
                project_path = dlg.project_path.text()
                path = os.path.join(project_path, project_name)
                os.mkdir(path)
                
                self.project.path = path
                self.project.init_project()

                self.project_widget.add_tree_view(path)
                            
                init_ganache(self)
                time.sleep(3)
                add_local_accounts(self)
                self.functions_widget.update_networks()

                #self.output.append(f"Project initialized at {path}\n")
                self.statusBar().showMessage(f"Project initialized at {path}", 2000)
            except:
                self.statusBar().showMessage(f"Unable to initialize project at {path}", 2500)

    def open_project(self):
        if self.project.path != "":
            self.save_data()
            self.project = Project()
            
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        is_project = self.project.exists_project(path)

        if is_project:
            try:
                self.project.path = path
                self.project_widget.add_tree_view(path)
                
                init_ganache(self)
                self.load_data()
                add_local_accounts(self)

                self.functions_widget.update_networks()

                #self.output.append(f"Project found at {path}\n")
                self.statusBar().showMessage(f"Project found at {path}", 2000)
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
        editor = Editor(self.font_families)
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

    def close_file(self):
        index = self.editor_tab.currentIndex()


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
        dlg = Test_Dialog(self.contracts, self.project.path)

        if dlg.exec():
            print("YAY")
        else:
            print("WAINS")

    def load_data(self):
        try:
            path = self.project.path
            with open(os.path.join(path, "data.pkl"), "rb") as f:
                data = pickle.load(f)
            
            self.accounts = data["accounts"]
            self.networks = data["networks"]
            self.contracts = data["contracts"]

        except Exception:
            pass

    def save_data(self):
        path = self.project.path
        data = {}
        data["accounts"] = self.accounts
        data["networks"] = self.networks
        data["contracts"] = self.contracts

        with open(os.path.join(path, "data.pkl"), "wb") as f:
            pickle.dump(data, f)

    def closeEvent(self, event):
        self.save_data()

        for child in psutil.Process(os.getpid()).children():
            for child2 in psutil.Process(child.pid).children():
                child2.terminate()
            child.terminate()

    def test(self, contract_name):
        
        return len(self.contracts[contract_name])


app = QApplication([])


window = MainWindow()
window.show()

app.exec()


#sys.exit(app)