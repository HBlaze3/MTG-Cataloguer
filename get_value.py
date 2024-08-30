from PyQt5.QtCore import Qt

def get_value(model, row, column_name, data_type=int):
    for col in range(model.columnCount()):
        if model.headerData(col, Qt.Horizontal) == column_name:
            try:
                return data_type(model.index(row, col).data(Qt.DisplayRole))
            except (ValueError, TypeError):
                return data_type(0)
    return data_type(0)