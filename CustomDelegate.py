from PyQt5.QtWidgets import QItemDelegate, QLineEdit, QCompleter, QMessageBox
from PyQt5.QtCore import Qt
from EditCellCommand import EditCellCommand
from get_value import get_value

class CustomDelegate(QItemDelegate):
    def __init__(self, all_cards, parent=None, undo_stack=None, editable_columns=None, sets=None, langs=None):
        super().__init__(parent)
        self.get_value = get_value
        self.all_cards = all_cards
        self.undo_stack = undo_stack
        self.editable_columns = editable_columns or []
        self.sets = sets or []
        self.langs = langs or []

    def createCompleter(self, header, header_list, editor, index):
        header_text = index.model().headerData(index.column(), Qt.Horizontal)
        if header_text in self.editable_columns and header_text.lower() == header:
            completer = QCompleter(header_list, editor)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            editor.setCompleter(completer)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        self.createCompleter('set', self.sets, editor, index)
        self.createCompleter('language', self.langs, editor, index)
        return editor

    def setModelData(self, editor, model, index):
        new_value = editor.text()
        header_text = index.model().headerData(index.column(), Qt.Horizontal)

        def headerwarning(header, header_list):
            if header_text.lower() == header and new_value not in header_list:
                QMessageBox.warning(editor, "Invalid " + header, f"'{new_value}' is not a valid " + header +" code.")
                return True

        if headerwarning('set', self.sets) or headerwarning('language', self.langs):
            return
        
        old_value = index.model().data(index, Qt.DisplayRole)

        if old_value != new_value:
            if header_text in self.editable_columns:
                if header_text in ['Language', 'Set', 'Collector Number']:
                    language = self.get_value(model, index.row(), 'Language', str)
                    set_code = self.get_value(model, index.row(), 'Set', str)
                    col_num = self.get_value(model, index.row(), 'Collector Number', str)

                    if header_text == 'Language':
                        language = new_value
                    elif header_text == 'Set':
                        set_code = new_value
                    elif header_text == 'Collector Number':
                        col_num = new_value

                    if self.check_duplicate(index, language, set_code, col_num):
                        return
                command = EditCellCommand(self.all_cards, self.parent(), index.row(), index.column(), old_value, new_value)
                self.undo_stack.push(command)
            model.setData(index, new_value, Qt.EditRole)
            
    def check_duplicate(self, index, language, set_code, col_num):
        existing_row = self.find_duplicate_row(index, language, set_code, col_num)
        if existing_row is not None and existing_row is not index.row():
            reply = QMessageBox.question(self.parent(), 'Duplicate Entry',
                                         "A similar entry exists at row "+str((existing_row+1))+". Do you want to edit the existing entry?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.parent().selectRow(existing_row)
                return True
        return False
    
    def find_duplicate_row(self, index, language, set_code, col_num):
        model = index.model()
        for row in range(model.rowCount()):
            if (self.get_value(model, row, 'Language', str) == language and
                self.get_value(model, row, 'Set', str) == set_code and
                self.get_value(model, row, 'Collector Number', str) == col_num):
                return row
        return None