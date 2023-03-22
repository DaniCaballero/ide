from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont
from pygments_lexer_solidity import SolidityLexer

class CustomSolidityLexer(QsciLexerCustom):
    def __init__(self, parent):
        super().__init__(parent)

        # default text settings
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))

        # define custom styles
        self._define_styles([QColor("#ff000000"),QColor("#ff7f0000"), QColor("#ff0000bf"), QColor("#ff007f00")])

        self.token_style = {
            'Token.Keyword' : 3,
            'Token.Operator' : 2,
            'Token.Keyword.Declaration' : 3,
            'Token.Keyword.Type' : 2,
            'Token.Name.Builtin' : 3,
            'Token.Keyword.Constant' : 1,
            'Token.Punctuation' : 1,
            'Token.Name.Function' : 2,
            'Token.Comment.Single' : 1
        }

    def _define_styles(self, color_list):
        for i, color in enumerate(color_list):
            self.setColor(color, i)
            self.setPaper(QColor("#ffffffff"), i)
            self.setFont(self.parent().window_font)

    def language(self):
        return "Solidity"

    def description(self, style: int):

        if style == 0:
            return "Style_0"
        elif style == 1:
            return "Style_1"
        elif style == 2:
            return "Style_2"
        elif style == 3:
            return "Style_3"

    def styleText(self, start: int, end: int):
        lexer = SolidityLexer()
        self.startStyling(start)

        text = self.parent().text()[start:end]

        # tokenize the text
        token_list = lexer.get_tokens(text)
        token_list = [(token[0], token[1], len(bytearray(token[1], "utf-8"))) for token in token_list]

        # style text in a loop
        for token in token_list:
            try:
                self.setStyling(token[2], self.token_style[str(token[0])])
            except:
                self.setStyling(token[2], 0)