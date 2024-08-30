from PyQt5.QtWidgets import QTableWidgetItem, QUndoCommand

class EditCellCommand(QUndoCommand):
    def __init__(self, table, row, column, old_value, new_value):
        super().__init__("Edit Cell")
        self.table = table
        self.row = row
        self.column = column
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        item = self.table.item(self.row, self.column)
        if item is None:
            item = QTableWidgetItem(self.old_value)
            self.table.setItem(self.row, self.column, item)
        else:
            item.setText(self.old_value)

    def redo(self):
        item = self.table.item(self.row, self.column)
        if item is None:
            item = QTableWidgetItem(self.new_value)
            self.table.setItem(self.row, self.column, item)
        else:
            item.setText(self.new_value)