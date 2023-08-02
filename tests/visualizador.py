from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox, QTextEdit, QWidget,
                             QHBoxLayout, QFrame, QToolButton, QPushButton, QTreeView, QSizePolicy, QFileDialog, 
                             QErrorMessage, QGraphicsDropShadowEffect, QCheckBox, QDoubleSpinBox, QMenu, QListView, QApplication, QGridLayout)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFileSystemModel, QRgba64, QDragEnterEvent, QDragLeaveEvent, QTextCursor
from PyQt6.QtCore import QSize, Qt, QDir, pyqtSignal, QThread, QItemSelectionModel
from PyQt6 import uic, QtWidgets
import time, threading
from os.path import isfile, join
from os import listdir

def apply_filter(entry, filters):

    for filter in filters:
        if filter in entry[3]:
            return True
        
    return False

class Visualizer_Container(QWidget):
    def __init__(self, nodes_names):
        super().__init__()
        uic.loadUi("./ui/Qt/Visualizador_Container.ui", self)

        self.comboBox.addItems(nodes_names)

class Select_Test_Visualizer(QDialog):
    def __init__(self, test_names):
        super().__init__()
        uic.loadUi("./ui/Qt/Select_Test_Visualizer.ui", self)

        self.comboBox.addItems(test_names)

class Visualizer(QDialog):
    def __init__(self, dir):
        super().__init__()
        uic.loadUi("./ui/Qt/Visualizador.ui", self)
        #self.nodes_number = nodes_number

        self.nodes_number = len([file_name for file_name in listdir(dir) if isfile(join(dir, file_name))])
        self.last_textbox = []

        self.init_UI()
        self.read_logs(dir)

    def init_UI(self):
        grid = QGridLayout()
        self.nodes_widgets = []
        self._pos, self.entries, self.all_entries, self.tx_entries, self.block_entries = 0, [], [], [], []
        self.tx_data, self.block_data, self.all_actions, self.block_creation_acc = [], [], [], []
        self.submitted_contract_acc, self.new_tx_acc, self.block_propagation_acc = [],[],[]

        self.data_type_box.currentTextChanged.connect(self.on_data_type_changed)
        self.action_type_box.currentTextChanged.connect(self.on_action_type_changed)

        self.set_node_names()

        positions = [(i,j) for i in range(4) for j in range(4)]
        index = 0

        for position, selection in zip(positions, self.node_names):
            container = Visualizer_Container(self.node_names)
            container.comboBox.setCurrentText(selection)
            container.comboBox.currentTextChanged.connect(lambda checked, index=index: self.on_combobox_text_changed(index))
            grid.addWidget(container, *position)

            self.nodes_widgets.append((container.comboBox, container.textEdit))
            index += 1

        # connect buttons signals to slots
        self.del_btn.clicked.connect(self.DelAllEntries)
        self.back_btn.clicked.connect(self.DelEntry)
        self.next_btn.clicked.connect(self.NextEntry)
        self.all_btn.clicked.connect(self.AllEntries)
        self.skip_btn.clicked.connect(self.SkipEntries)

        self.verticalLayout_2.addLayout(grid)

    def on_data_type_changed(self):
        self.DelAllEntries()

        if self.data_type_box.currentText() == "All":
            self.entries = self.all_entries

        elif self.data_type_box.currentText() == "Blocks":
            self.entries = self.block_entries

        elif self.data_type_box.currentText() == "Tx":
            self.entries = self.tx_entries

        self.action_type_box.setCurrentIndex(0)

    def on_action_type_changed(self):

        self.DelAllEntries()

        data_type = self.data_type_box.currentText()

        if data_type == 'All': self.entries = self.all_entries
        elif data_type == 'Blocks': self.entries = self.block_entries
        elif data_type == 'Tx': self.entries = self.tx_entries

        if self.action_type_box.currentText() == "All":
            self.entries = [elem for elem in self.entries if apply_filter(elem, self.all_actions) == True]

        elif self.action_type_box.currentText() == "Block Creation":
            self.entries = [elem for elem in self.entries if apply_filter(elem, self.block_creation_acc) == True]

        elif self.action_type_box.currentText() == "Contract Creation":
            self.entries = [elem for elem in self.entries if apply_filter(elem, self.submitted_contract_acc) == True]

        elif self.action_type_box.currentText() == "New Transaction":
            self.entries = [elem for elem in self.entries if apply_filter(elem, self.new_tx_acc) == True]

        elif self.action_type_box.currentText() == "Block Propagation":
            self.entries = [elem for elem in self.entries if apply_filter(elem, self.block_propagation_acc) == True]

    def on_combobox_text_changed(self, node_index):
        #print("node index ", node_index)
        (c, j) = self.nodes_widgets[node_index]
        j.clear()

        for i in range(self._pos):
            if c.currentText() == self.entries[i][2]:
                tmp = self.buildEntry(i)
                j.append(f"{tmp}\n\n")

        self.insert_prev_text(self._pos - 1)
        self.change_background_color("255,255,255")
        self.restoreLastPos()
        self.change_background_color("204,230,255")


    def set_node_names(self):
        self.node_names = [f"node{i}" for i in range(self.nodes_number)]

        if len(self.node_names) < 16:
            for i in range(16 - len(self.node_names)):
                self.node_names.append('--')

    def follow(self, _file, index):
        log_filter = ["Commit new sealing work", "Successfully seal new block", "mined potential block",
                      "Submitted contract creation", "Submitted transaction", "block reached canonical chain", "block lost",
                      "Imported new chain segment"]
        while True:
            filter_bool = False
            line = _file.readline().rstrip('\n')
            if not line:
                time.sleep(0.1)
                continue

            for filter in log_filter:
                if filter in line:
                    filter_bool = True
            
            if filter_bool:
                yield f"node{index} {line}"

    def generate(self, lg):

        separators = ["blocks","number", "hash", "address"]
        for line in lg:
            new_line = []
            for sep in separators:
                tmp = line.split(sep)
                if len(tmp) > 1:
                    tmp[1] = sep + tmp[1]
                    break
            
            for i, sub in enumerate(tmp):
                tmp_sub = sub.split(" ")
                if i == 0:
                    tmp_sub = tmp_sub[:3] + [" ".join(tmp_sub[3:])]
                new_line += tmp_sub
            
            tmp_date = new_line[2]
            new_line[2] = new_line[0]
            new_line[0] = tmp_date
            new_line[3] = new_line[3].strip()

            for filter in self.tx_data:
                if filter in new_line[3]:
                    self.tx_entries.append(new_line)

            for filter in self.block_data:
                if filter in new_line[3]:
                    self.block_entries.append(new_line)

            #print("new line ", new_line)
            self.all_entries.append(new_line)

    def buildEntry(self, index):
        #global pos, posLast

        posLast = self._pos   
        tmp = f"Acc:{index}:\n{self.entries[index][0]}"

        tmp += f"\n{self.entries[index][3]}" 
        
        return tmp
    
    def change_background_color(self, color):
        for box in self.last_textbox:
            box.setStyleSheet(f"background-color: rgb({color})")

    def NextEntry(self):
        #global pos
        iter_bool = False

        if (self._pos == 0):
            # print("Dato: ", tipoDato_cb.get())

            # print("Time Ini", tsi.get())
            # print("Time Fin", tsf.get())

            # print("Acciones: ", tipoAccion_cb.get())
            # print("------\n\n")
            pass

        try:
            print(f"Procesando log: {self.entries[self._pos]}")
            self.change_background_color("255,255,255")
            self.last_textbox = []
            for (i, j) in self.nodes_widgets:
                if i.currentText() == self.entries[self._pos][2] or len(self.nodes_widgets) == 1:
                    tmp = self.buildEntry(self._pos)

                    #j.config(state=NORMAL)
                    #j.insert(1.0,f"{tmp}\n\n")
                    j.append(f"{tmp}\n\n")
                    self.last_textbox.append(j)
                    iter_bool = True
                    #j.config(state=DISABLED)
            
            if iter_bool == False:
                self.side_textbox.clear()
                tmp = self.buildEntry(self._pos)
                self.side_textbox.append(f"{tmp}")
                self.last_textbox.append(self.side_textbox)
            
            self.change_background_color("204,230,255")

            self._pos = self._pos + 1
        except IndexError:
            print("Alcanzado el final de los logs actuales. Espere a que se generen mas.")
            pass

    def insert_prev_text(self, index):
        self.side_textbox.clear()
        iter_bool = False

        for i in range(index, -1, -1):
            for (c, j) in self.nodes_widgets:
                if c.currentText() == self.entries[i][2]:
                    iter_bool = True
            
            if iter_bool == False:
                tmp = self.buildEntry(i)
                self.side_textbox.append(f"{tmp}")
                break

            iter_bool = False

    def AllEntries(self):
        self.change_background_color("255,255,255")

        for x in range(self._pos, len(self.entries)):
            self.last_textbox = []
            iter_bool = False
            try:
                for (c,j) in self.nodes_widgets:
                    if c.currentText() == self.entries[self._pos][2]:
                        tmp = self.buildEntry(self._pos)
                        j.append(f"{tmp}\n\n")
                        self.last_textbox.append(j)
                        iter_bool = True

                if iter_bool == False:
                    self.side_textbox.clear()
                    tmp = self.buildEntry(self._pos)
                    self.side_textbox.append(f"{tmp}")
                    self.last_textbox.append(self.side_textbox)

                self._pos += 1
            except:
                pass

        self.change_background_color("204,230,255")

    def SkipEntries(self):
        value = self.skip_value.value()
        self.change_background_color("255,255,255")

        for x in range(self._pos, self._pos + value):
            self.last_textbox = []
            iter_bool = False
            try:
                for (c,j) in self.nodes_widgets:
                    if c.currentText() == self.entries[self._pos][2]:
                        tmp = self.buildEntry(self._pos)
                        j.append(f"{tmp}\n\n")
                        self.last_textbox.append(j)
                        iter_bool = True

                if iter_bool == False:
                    self.side_textbox.clear()
                    tmp = self.buildEntry(self._pos)
                    self.side_textbox.append(f"{tmp}")
                    self.last_textbox.append(self.side_textbox)

                self._pos += 1
            except:
                pass

        self.change_background_color("204,230,255")

    
    def restoreLastPos(self):
        iter_bool = False

        if self._pos > 0:
            self.last_textbox = []

            for (i, j) in self.nodes_widgets:
                if i.currentText() == self.entries[self._pos-1][2] or len(self.nodes_widgets) == 1:
                    self.last_textbox.append(j)
                    iter_bool = True
            
            if iter_bool == False:
                self.last_textbox.append(self.side_textbox)


    def DelEntry(self):
        iter_bool = False

        if self._pos > 0:
            self.change_background_color("255,255,255")

            for (i, j) in self.nodes_widgets:
                if i.currentText() == self.entries[self._pos-1][2] or len(self.nodes_widgets) == 1:
                    #j.config(state=NORMAL)
                    #j.delete(1.0, 5.0)
                    cursor = j.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock, QTextCursor.MoveMode.KeepAnchor, 5)
                    cursor.removeSelectedText()
                    j.setTextCursor(cursor)
                    #j.config(state=DISABLED)
                    iter_bool = True
            
            if iter_bool == False:
                #self.side_textbox.clear()
                self.insert_prev_text(self._pos - 2)

            self._pos = max(0, self._pos-1)
            self.restoreLastPos()
            self.change_background_color("204,230,255")

    def DelAllEntries(self):
        self.change_background_color("255,255,255")
        
        self._pos = 0
        for (i, j) in self.nodes_widgets:
            #j.config(state=NORMAL)
            j.clear()
            #j.config(state=DISABLED)
        
        self.side_textbox.clear()

    def read_logs(self, d):
        # obtiene nombre nodos
        # Todas estas variables globales son mala practica, pero como ya el script lo tenia aprovecho y lo hago mal tambien
        # global nodeNames, fechaI, fechaF, entradas, log_generators, entradasBloque, entradasTodos, entradasTx, tipoDato
        # global datoBloque, datoTx, accPres, accNTx, accPTx, tipoAcc

        log_filenames = [join(d, f) for f in listdir(d) if isfile(join(d, f))]
        log_files = [open(fn, 'r') for fn in log_filenames]
        log_generators = [self.follow(f,i) for i,f in enumerate(log_files)]

        nodeNames = [name[:-4] for name in listdir(d) if isfile(join(d, name))]
        if len(nodeNames) < 16:
            for i in range(16 - len(nodeNames)):
                nodeNames.append('--')

        
        # obtiene entradas del log

        # entradas = []
        # entradasTodos = []
        # entradasTx = []
        # entradasBloque = []

        # tipoDato = 'Todos'
        # tipoAcc = 'Todos'

        # datoTx = ['Transaction', 'TransactionAck', 'newTransaction', 'newTransactionAck']
        # datoBloque = ['blockMined']
        # accPres = ['announce', 'announceAck']
        # accNTx = ['newTransaction', 'newTransactionAck']
        # accPTx = ['Transaction', 'TransactionAck']

        generator_threads = [threading.Thread(target=self.generate, args=(lg, ), daemon=True) for lg in log_generators]
        for gt in generator_threads:
            gt.start()

        time.sleep(0.1) # dar tiempo a que los hilos populen las listas

        # entradasTodos = sorted(entradasTodos)
        # entradas = entradasTodos
        # entradasTx = sorted(entradasTx)
        # entradasBloque = sorted(entradasBloque)
        self.all_entries = sorted(self.all_entries)
        self.entries = self.all_entries
        self.tx_entries = sorted(self.tx_entries)
        self.block_entries = sorted(self.block_entries)

        # Data Types
        self.tx_data = ["Submitted contract creation", "Submitted transaction"]
        self.block_data = ["Commit new sealing work", "Successfully seal new block", "mined potential block", 
                           "block reached canonical chain", "Imported new chain segment", "block lost"]

        # Actions
        self.all_actions = self.tx_data + self.block_data
        self.block_creation_acc = ["Commit new sealing work", "Successfully seal new block", "mined potential block"]
        self.submitted_contract_acc = ["Submitted contract creation"]
        self.new_tx_acc = ["Submitted transaction"]
        self.block_propagation_acc = ["block reached canonical chain", "Imported new chain segment", "block lost"]

        # fechaI = entradasTodos[0][0]
        # fechaF = entradasTodos[-1][0]
