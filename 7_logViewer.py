import os, sys, re, logging, multiprocessing
from PyQt5.QtCore import QThread, pyqtSignal, QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QPalette, QSyntaxHighlighter

class QPlainTextEditLogger(logging.Handler):
    
    def __init__(self, parent):
        super().__init__()

        formatter_log = logging.Formatter('[%(levelname)-8s] %(asctime)s %(filename)s[%(funcName)s-line:%(lineno)d] %(message)s')
        self.setFormatter(formatter_log)

        self.queue_msg = multiprocessing.Queue(100)

    def emit(self, record):
        msg = self.format(record)
        self.queue_msg.put(msg)

class LogThread(QThread):
    update_msg = pyqtSignal(str)

    def __init__(self, parent=None, queue_msg=None):
        super().__init__(parent)
        self.is_live = True
        self.queue_msg = queue_msg

    def run(self):
        while(self.is_live):
            msg = self.queue_msg.get()
            self.update_msg.emit(msg)

def format(color, style=''):
    if isinstance(color, QColor):
        word_color = color
    else:
        word_color = QColor()
        word_color.setNamedColor(color)
    word_format = QTextCharFormat()
    if 'log' in style:
        word_format.setBackground(word_color)
    else:
        word_format.setForeground(word_color)
    if 'italic' in style:
        word_format.setFontItalic(True)
    elif 'bold' in style:
        word_format.setFontWeight(QFont.Bold)

    return word_format

STYLE = {
    'keywords': format('#F92672'),
    'booleans': format('#C1FF00'),
    'operators': format('#F92672'),
    'braces': format('#BABAB6'),
    'comments': format('#9EAF9F'),
    'def_class': format('#66D9EF'),
    'string': format('#F2C560'),
    'doc_string': format('#F2C560'),
    'self': format('#FF9721'),
    'numbers': format('#66CB64'),
    'log_info': format('#aaffff'),
    'log_debug': format('#008800'),
    'log_error': format('#ff0000'),
    'log': format('#228822'),
}

class PythonHighlighter(QSyntaxHighlighter):

    keywords = [
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
        'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
        'while', 'with', 'yield',
    ]

    booleans = [
        'True', 'False', 'None',
    ]

    operators = [
        '=',
        '==', '!=', '<', '<=', '>', '>=',
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        '\+=', '-=', '\*=', '/=', '\%=',
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    braces = [
        '\{', '\}', '\[', '\]', '\(', '\)'
    ]

    def __init__(self, document):

        QSyntaxHighlighter.__init__(self, document)

        self.triple_single = (QRegExp("\'\'\'"), 1, STYLE['doc_string'])
        self.triple_double = (QRegExp('\"\"\"'), 2, STYLE['doc_string'])

        # RULES

        rules = []
        # r'' regular expression
        # [] used to indicate set of characters
        # \b matches the empty string, but only at the beginning or end of the word
        # \w matches any alphanumeric chars and the underscore
        # \s matches any whitespace char
        # * causes the resulting regexp to match 0 or more repetitions of the preceding regexp. ab* = a, ab, abb, abbb..
        # + causes the resulting regexp to match 1 or more repetitions of the preceding regexp. ab+ = ab, abb, abbbb..
        # ? causes the resulting regexp to match 0 or 1 repetitions of the preceding regexp. ab? = a, ab
        # ^ matches the start of the string, and in multi line mode also matches immediately after each new line
        # ?: A non-capturing version of regular parentheses
        # QRegExp, int, STYLE

        rules += [(r'\b%s\b' % keyword, 0, STYLE['keywords']) for keyword in PythonHighlighter.keywords]
        rules += [(r'\b%s\b' % boolean, 0, STYLE['booleans']) for boolean in PythonHighlighter.booleans]
        rules += [(r'%s' % operator, 0, STYLE['operators']) for operator in PythonHighlighter.operators]
        rules += [(r'%s' % brace, 0, STYLE['braces']) for brace in PythonHighlighter.braces]
        # Other rules:
        rules += [
            # self
            (r'\bself\b', 0, STYLE['self']),
            # string containing double-quote with escape sequence
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLE['string']),
            # string containing single-quote with escape sequence
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLE['string']),
            # def/class
            (r'\bdef\b\s*(\w+)', 1, STYLE['def_class']),
            (r'\bclass\b\s*(\w+)', 1, STYLE['def_class']),
            # from # until new-line
            (r'#[^\n]*', 0, STYLE['comments']),
            # numbers
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLE['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLE['numbers']),
            # decorator
            (r'@[^\n', 0, STYLE['def_class']),
        ]
        # Build QRegExp for each pattern
        self.rules = [(QRegExp(pattern), index, fmt) for (pattern, index, fmt) in rules]
        # log label: INFO, ERROR, DEBUG, CRITICAL
        self.rules.append((QRegExp(r'^\[INFO *\]'), 0, STYLE['log_info']))
        self.rules.append((QRegExp(r'^\[ERROR *\]'), 0, STYLE['log_error']))
        self.rules.append((QRegExp(r'^\[DEBUG *\]'), 0, STYLE['log_debug']))
        self.rules.append((QRegExp(r'^\[CRITICAL *\]'), 0, STYLE['log_error']))

        # log
        self.rules.append((QRegExp(r'^.*default_log.*$'), 0, STYLE['log']))

    def highlightBlock(self, text):
        for expression, nth, format in self.rules:

            index = expression.indexIn(text, 0)

            while index >= 0:
                index = expression.pos(nth)

                length = len(expression.cap(nth))

                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        in_multiline = self.match_multiline(text, *self.triple_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.triple_double)

    def match_multiline(self, text, delimiter, in_state, style):

        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            start = delimiter.indexIn(text)
            add = delimiter.matchedLength()

        while start >= 0:
            end = delimiter.indexIn(text, start + add)
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add

            self.setFormat(start, length, style)
            start = delimiter.indexIn(text, start + length)

        if self.currentBlockState() == in_state:
            return True
        else:
            return False