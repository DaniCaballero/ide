import os, shutil, keyword, pkgutil
from PyQt6.QtWidgets import QTextEdit
from pathlib import Path
from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciLexerJavaScript, QsciAPIs
from PyQt6.QtGui import QColor, QFont
from solidity_lexer import CustomSolidityLexer

class Project:
    def __init__(self, path=""):
        self.path = path
        self.dir_names = ["build", "contracts", "NFTs", "tests", "scripts"]

    def init_project(self):
        dir_list = os.listdir(self.path)

        if len(dir_list) == 0:
            for dir in self.dir_names:
                dir_path = os.path.join(self.path, dir)

                try:
                    os.mkdir(dir_path)
                except OSError as error:
                    print(error)

            print("Folders successfully created!")
        else:
            self.path = ""
            print("Folder must be empty")

    def delete_project(self):
        for dir in self.dir_names:
            dir_path = os.path.join(self.path, dir)

            try:
                shutil.rmtree(dir_path, ignore_errors=False)
            except OSError as error:
                print(error)

        print("Folders successfully deleted!")

    def exists_project(self, path):
        for dir in self.dir_names:
            dir_path = os.path.join(path, dir)
            is_dir = os.path.isdir(dir_path)
            if is_dir == False:
                return False
        
        return True

class State:
    def __init__(self, project, editor, output):
        self.project = project
        self.editor_list = [editor]
        self.current_editor = editor
        self.output = output
        self.contracts = {}
        self.accounts = {}   

    def load_project_info(self):
        pass

class Editor(QsciScintilla):
    def __init__(self, file_path=""):
        super().__init__()
        self.file_path = file_path
        self.file_name = "Untitled"
        self.setFrameStyle(0)

        self.setUtf8(True)

        # set brace matching
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)

        # font
        self.window_font = QFont("Consolas", pointSize=12)
        self.setFont(self.window_font)
    
        # indentation
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(True) #chequear si prefiero en false o true. Cual es mas comun?
        self.setAutoIndent(True)

        # try python lexer
        #self.pylexer = QsciLexerPython()
        #self.pylexer.setDefaultFont(self.window_font)

        #self.api = QsciAPIs(self.pylexer)

        # autocomplete
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        #self.setLexer(self.pylexer)

        # line numbers
        self.setMarginType( 0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "000")
        self.setMarginsForegroundColor(QColor("#616161"))
        self.setMarginsBackgroundColor(QColor("#ededed"))

        #self.insert_py_keywords()


    def insert_py_keywords(self):
        for key in keyword.kwlist + dir(__builtins__):
            self.api.add(key)
        
        for _, name, _ in pkgutil.iter_modules():
            self.api.add(name)

    def change_name(self, file_name):
        self.file_name = file_name
        file_extension = Path(self.file_name).suffix

        if file_extension == ".py":
            self.lexer = QsciLexerPython()
            self.lexer.setDefaultFont(self.window_font)
            self.api = QsciAPIs(self.lexer)
            self.insert_py_keywords()
            self.setLexer(self.lexer)
            self.api.prepare()
        elif file_extension == ".js":
            self.lexer = QsciLexerJavaScript()
            self.lexer.setDefaultFont(self.window_font)
            self.api = QsciAPIs(self.lexer)
            #self.insert_py_keywords()
            self.setLexer(self.lexer)
            self.api.prepare()
        elif file_extension == ".sol":
            self.lexer = CustomSolidityLexer(self)
            self.lexer.setDefaultFont(self.window_font)
            self.api = QsciAPIs(self.lexer)
            self.setLexer(self.lexer)
            self.api.prepare()
