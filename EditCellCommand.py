from PyQt5.QtWidgets import QTableWidgetItem, QUndoCommand
from PyQt5.QtCore import Qt

class EditCellCommand(QUndoCommand):
    def __init__(self, table, row, column, old_value, new_value, delegate):
        super().__init__("Edit Cell")
        self.table = table
        self.row = row
        self.column = column
        self.old_value = old_value
        self.new_value = new_value
        self.delegate = delegate

    def undo(self):
        item = self.table.item(self.row, self.column)
        if item is None:
            item = QTableWidgetItem(self.old_value)
            self.table.setItem(self.row, self.column, item)
        else:
            item.setText(self.old_value)
        self.table.model().setData(self.table.model().index(self.row, self.column), self.old_value, Qt.EditRole)
        self.delegate.update_row_data(self.table.model().index(self.row, self.column))

    def redo(self):
        item = self.table.item(self.row, self.column)
        if item is None:
            item = QTableWidgetItem(self.new_value)
            self.table.setItem(self.row, self.column, item)
        else:
            item.setText(self.new_value)
        self.table.model().setData(self.table.model().index(self.row, self.column), self.new_value, Qt.EditRole)
        self.delegate.update_row_data(self.table.model().index(self.row, self.column))