from PyQt6.QtCore import QSize, Qt, QThread
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QMenu, QHBoxLayout, QTextEdit, 
                            QTabWidget, QStackedLayout, QFrame, QToolButton, QSplitter)
#from menu_functions import *
from dialogs import Compile_Dialog, Add_Account_Dialog, Add_Node_Dialog, Deploy_Dialog, IPFS_Token_Dialog, Functions_Layout, Project_Widget, Left_Widget, Test_Dialog
from account import Account, add_local_accounts
#from network import Network, init_ganache
#from ipfs import IPFS
from interact import contract_interaction
#from project import Editor, Project
from PyQt6.QtGui import QAction, QColor, QPalette, QIcon
import os, signal, psutil, sys, pickle, time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        start_time = time.time()
        self.setWindowTitle("IDE")
        self.setMinimumSize(QSize(800,600))
        #self.project = Project()
        self.networks = {}
        self.accounts = {}
        self.contracts = {}
        self.ipfs = ""
        #editor = Editor()
        self.output = QTextEdit()
        self.output.setMaximumHeight(400)
        self.output.setFrameStyle(0)

        #self.create_menu_bar()

        self.editor_tab = QTabWidget()
        # self.editor_tab.addTab(editor, editor.file_name)
        # self.editor_tab.setTabsClosable(True)
        #self.editor_tab.tabCloseRequested.connect(self.close_file)

        #self.buttons_widget = Left_Widget()
        #self.buttons_widget.project_button.clicked.connect(self.project_button_clicked)
        #self.buttons_widget.function_button.clicked.connect(self.function_button_clicked)

        main_layout = QHBoxLayout()

        self.hsplit = QSplitter(Qt.Orientation.Horizontal)

        self.stacked_layout = QStackedLayout()
        #self.project_widget = Project_Widget(self)
        #self.functions_widget = Functions_Layout(self)
        #self.functions_widget.function_signal.connect(self.add_to_output)

        # stacked_widget = QWidget()
        # self.stacked_layout.addWidget(self.project_widget)
        # self.stacked_layout.addWidget(self.functions_widget)
        # stacked_widget.setLayout(self.stacked_layout)
        
        # editor_split = QSplitter(Qt.Orientation.Vertical)
        # editor_split.addWidget(self.editor_tab)
        # editor_split.addWidget(self.output)
        # editor_split.setSizes([self.height() - 200, 200])


        # self.hsplit.addWidget(stacked_widget)
        # self.hsplit.addWidget(editor_split)
        # self.hsplit.setSizes([150, self.width() - 150])

        # main_layout.addWidget(self.buttons_widget, 10)
        # main_layout.addWidget(self.hsplit, 90)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

        print("Time to load: ", time.time() - start_time)

app = QApplication([])

window = MainWindow()
window.show()

app.exec()