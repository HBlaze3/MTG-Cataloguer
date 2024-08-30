from PyQt5.QtWidgets import QUndoCommand, QTableWidgetItem
from PyQt5.QtCore import Qt

class AddRowCommand(QUndoCommand):
    def __init__(self, table, row_position, editable_columns):
        super().__init__("Add Row")
        self.table = table
        self.row_position = row_position
        self.editable_columns = editable_columns

    def redo(self):
        self.table.insertRow(self.row_position)
        for col in range(self.table.columnCount()):
            item = QTableWidgetItem("")
            header_text = self.table.horizontalHeaderItem(col).text()
            if header_text in self.editable_columns:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(self.row_position, col, item)

    def undo(self):
        self.table.removeRow(self.row_position)