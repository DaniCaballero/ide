from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox, QTextEdit, QWidget,
                             QHBoxLayout, QFrame, QToolButton, QPushButton, QTreeView, QSizePolicy, QFileDialog, 
                             QErrorMessage, QGraphicsDropShadowEffect, QCheckBox, QDoubleSpinBox, QMenu, QListView, QApplication, QGridLayout)
from PyQt6.QtGui import QPalette, QColor, QIcon, QFileSystemModel, QRgba64, QDragEnterEvent, QDragLeaveEvent, QTextCursor
from PyQt6.QtCore import QSize, Qt, QDir, pyqtSignal, QThread, QItemSelectionModel
from PyQt6 import uic, QtWidgets
import time, threading
from os.path import isfile, join
from os import listdir

class Visualizer_Container(QWidget):
    def __init__(self, nodes_names):
        super().__init__()
        uic.loadUi("./ui/Visualizador_Container.ui", self)

        self.comboBox.addItems(nodes_names)


class Visualizer(QDialog):
    def __init__(self, nodes_number, dir):
        super().__init__()
        uic.loadUi("./ui/Visualizador.ui", self)
        self.nodes_number = nodes_number

        self.init_UI()
        self.leer(dir)

    def init_UI(self):
        grid = QGridLayout()
        self.nodes_widgets = []
        self._pos, self.entries, self.all_entries = 0, [], []

        self.set_node_names()

        positions = [(i,j) for i in range(4) for j in range(4)]

        for position, selection in zip(positions, self.node_names):
            container = Visualizer_Container(self.node_names)
            container.comboBox.setCurrentText(selection)
            grid.addWidget(container, *position)

            self.nodes_widgets.append((container.comboBox, container.textEdit))

        # connect buttons signals to slots
        self.del_btn.clicked.connect(self.DelAllEntries)
        self.back_btn.clicked.connect(self.DelEntry)
        self.next_btn.clicked.connect(self.NextEntry)
        #self.all_btn.clicked.connect(self.)

        self.verticalLayout_2.addLayout(grid)

    def set_node_names(self):
        self.node_names = [f"node{i}" for i in range(self.nodes_number)]

        if len(self.node_names) < 16:
            for i in range(16 - len(self.node_names)):
                self.node_names.append('--')

    
    def follow(self, _file, index):
        log_filter = ["Unlocked account", "Commit new sealing work", "Successfully seal new block", "mined potential block",
                      "Submitted contract creation", "Submitted transaction", "block reached canonical chain", "block lost",
                      "Setting new local account", "Imported new chain segment", "Chain reorg detected"]
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
        # for line in lg:
        #     tmp = line.split(',')
        #     if tmp[2] == 'blockMined' or tmp[3] == 'block' or tmp[3] == 'blockAck':
        #         entradasBloque.append(tmp)
        #     elif (tmp[3] == 'newTransaction' or tmp[3] == 'newTransactionAck' or
        #         tmp[3] == 'Transaction' or tmp[3] == 'TransactionAck'):
        #         entradasTx.append(tmp)

        #     entradasTodos.append(tmp)
        separators = ["number", "hash", "address"]
        for line in lg:
            new_line = []
            for sep in separators:
                tmp = line.split(sep)
                if len(tmp) > 1:
                    tmp[1] = sep + tmp[1]
                    for i, sub in enumerate(tmp):
                        tmp_sub = sub.split(" ")
                        if i == 0:
                            tmp_sub = tmp_sub[:3] + [" ".join(tmp_sub[3:])]
                        new_line += tmp_sub
                    break
            
            tmp_date = new_line[2]
            new_line[2] = new_line[0]
            new_line[0] = tmp_date
            new_line[3] = new_line[3].strip()
            print("new line ", new_line)
            self.all_entries.append(new_line)

    def buildEntry(self):
        #global pos, posLast

        posLast = self._pos   
        tmp = f"Acc:{self._pos}:\n{self.all_entries[self._pos][0]}"

        tmp += f"\n{self.all_entries[self._pos][3]}"

        # if self.entries[self._pos][2] == 'SENT' or self.entries[self._pos][2] == 'RECEIVED':
        #     tmp += f"{self.entries[self._pos][2]}\nType: {self.entries[self._pos][3]}, {self.entries[self._pos][4]}"
        #     tmp += f", {self.entries[self._pos][5]}" if len(self.entries[self._pos]) == 6 else ''
        # elif self.entries[self._pos][2] == 'blockMined':
        #     tmp += f"\nType: {self.entries[self._pos][2]}, {self.entries[self._pos][3]}"
        
        return tmp

    def NextEntry(self):
        #global pos

        if (self._pos == 0):
            # print("Dato: ", tipoDato_cb.get())

            # print("Time Ini", tsi.get())
            # print("Time Fin", tsf.get())

            # print("Acciones: ", tipoAccion_cb.get())
            # print("------\n\n")
            pass

        try:
            print(f"Procesando log: {self.all_entries[self._pos]}")

            for (i, j) in self.nodes_widgets:
                if i.currentText() == self.all_entries[self._pos][2] or len(self.nodes_widgets) == 1:
                    tmp = self.buildEntry()

                    #j.config(state=NORMAL)
                    #j.insert(1.0,f"{tmp}\n\n")
                    j.append(f"{tmp}\n\n")
                    #j.config(state=DISABLED)

            self._pos = self._pos + 1
        except IndexError:
            print("Alcanzado el final de los logs actuales. Espere a que se generen mas.")
            pass

    def DelEntry(self):

        if self._pos > 0:
            for (i, j) in self.nodes_widgets:
                if i.currentText() == self.all_entries[self._pos-1][2] or len(self.nodes_widgets) == 1:
                    #j.config(state=NORMAL)
                    #j.delete(1.0, 5.0)
                    cursor = j.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.movePosition(QTextCursor.MoveOperation.PreviousBlock, QTextCursor.MoveMode.KeepAnchor, 5)
                    cursor.removeSelectedText()
                    j.setTextCursor(cursor)
                    #j.config(state=DISABLED)
            self._pos = max(0, self._pos-1)

    def DelAllEntries(self):

        self._pos = 0
        for (i, j) in self.nodes_widgets:
            #j.config(state=NORMAL)
            j.delete(1.0, "end")
            #j.config(state=DISABLED)

    def leer(self, d):
        # obtiene nombre nodos
        # Todas estas variables globales son mala practica, pero como ya el script lo tenia aprovecho y lo hago mal tambien
        global nodeNames, fechaI, fechaF, entradas, log_generators, entradasBloque, entradasTodos, entradasTx, tipoDato
        global datoBloque, datoTx, accPres, accNTx, accPTx, tipoAcc

        log_filenames = [join(d, f) for f in listdir(d) if isfile(join(d, f))]
        log_files = [open(fn, 'r') for fn in log_filenames]
        log_generators = [self.follow(f,i) for i,f in enumerate(log_files)]

        nodeNames = [name[:-4] for name in listdir(d) if isfile(join(d, name))]
        if len(nodeNames) < 16:
            for i in range(16 - len(nodeNames)):
                nodeNames.append('--')

        
        # obtiene entradas del log

        entradas = []
        entradasTodos = []
        entradasTx = []
        entradasBloque = []

        tipoDato = 'Todos'
        tipoAcc = 'Todos'

        datoTx = ['Transaction', 'TransactionAck', 'newTransaction', 'newTransactionAck']
        datoBloque = ['blockMined']
        accPres = ['announce', 'announceAck']
        accNTx = ['newTransaction', 'newTransactionAck']
        accPTx = ['Transaction', 'TransactionAck']

        generator_threads = [threading.Thread(target=self.generate, args=(lg, ), daemon=True) for lg in log_generators]
        for gt in generator_threads:
            gt.start()

        time.sleep(0.1) # dar tiempo a que los hilos populen las listas

        # entradasTodos = sorted(entradasTodos)
        # entradas = entradasTodos
        # entradasTx = sorted(entradasTx)
        # entradasBloque = sorted(entradasBloque)
        self.all_entries = sorted(self.all_entries)

        # fechaI = entradasTodos[0][0]
        # fechaF = entradasTodos[-1][0]
