from PyQt5.QtWidgets import QUndoCommand, QTableWidgetItem

class DeleteRowCommand(QUndoCommand):
    def __init__(self, table, row_position):
        super().__init__("Delete Row")
        self.table = table
        self.row_position = row_position
        self.row_data = self._get_row_data()

    def _get_row_data(self):
        return [self.table.item(self.row_position, col).text() if self.table.item(self.row_position, col) else '' 
                for col in range(self.table.columnCount())]

    def redo(self):
        self.table.removeRow(self.row_position)

    def undo(self):
        self.table.insertRow(self.row_position)
        for col, value in enumerate(self.row_data):
            item = QTableWidgetItem(value)
            self.table.setItem(self.row_position, col, item)