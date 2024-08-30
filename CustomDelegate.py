from itertools import zip_longest
from typing import OrderedDict
from PyQt5.QtWidgets import QItemDelegate, QLineEdit, QCompleter, QMessageBox
from PyQt5.QtCore import Qt
from EditCellCommand import EditCellCommand

class CustomDelegate(QItemDelegate):
    def __init__(self, all_cards, parent=None, undo_stack=None, editable_columns=None, sets=None, langs=None):
        super().__init__(parent)
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
                command = EditCellCommand(self.parent(), index.row(), index.column(), old_value, new_value, self)
                self.undo_stack.push(command)
            model.setData(index, new_value, Qt.EditRole)

            quantity_columns = ["Quantity", "Deck Quantity", "Deck Quantity 2", "Deck Quantity 3", "Deck Quantity 4"]
            price_columns = ["Quantity", "Quantity Foil", "USD", "USD Foil"]
            data_columns = ['Language', 'Set', 'Collector Number']

            if header_text in quantity_columns:
                self.update_quantity(model, index.row(), quantity_columns)
            if header_text in price_columns:
                self.update_price(model, index.row(), price_columns)
            if header_text in data_columns:
                self.update_row_data(index)
        
    def update_row_data(self, index):
        model = index.model()
        row = index.row()
        language = self.get_value(model, row, 'Language', str)
        set_code = self.get_value(model, row, 'Set', str)
        col_num = self.get_value(model, row, 'Collector Number', str)

        if language and set_code and col_num:
            set_codes = set_code.split(" // ") if " // " in set_code else [set_code]
            col_nums = col_num.split(" // ") if " // " in col_num else [col_num]
            set_codes = list(OrderedDict.fromkeys(set_codes))
            col_nums = list(OrderedDict.fromkeys(col_nums))
            max_length = max(len(set_codes), len(col_nums))
            set_codes += [set_codes[0]] * (max_length - len(set_codes))
            col_nums += [col_nums[0]] * (max_length - len(col_nums))
            set_iterator = zip_longest(set_codes, col_nums, fillvalue=None)
            for set_code, col_num in set_iterator:
                if set_code is None or col_num is None:
                    break
                key = (language, set_code, col_num)
                if key in self.all_cards:
                    card = self.all_cards[key]
                    self.update_cell(model, row, 'Release Date', card['release_date'])
                    self.update_cell(model, row, 'Name', card['name'])
                    self.update_cell(model, row, 'Type Line', card['type_line'])
                    self.update_cell(model, row, 'Set Name', card['set_name'])
                    self.update_cell(model, row, 'USD', card['usd'])
                    self.update_cell(model, row, 'USD Foil', card['usd_foil'])

    def update_cell(self, model, row, column_name, value):
        for col in range(model.columnCount()):
            if model.headerData(col, Qt.Horizontal) == column_name:
                model.setData(model.index(row, col), value, Qt.EditRole)
                break

    def update_price(self, model, row, price_columns):
        total_values = []
        for price_column in price_columns[:2]:
            total_values.append(self.get_value(model, row, price_column))
        for price_column in price_columns[2:]:
            total_values.append(self.get_value(model, row, price_column, float))

        total_usd = (total_values[0] - total_values[1]) * total_values[2]
        total_usd_foil = total_values[1] * total_values[3]

        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal)
            if header == "Total USD":
                total_usd_index = model.index(row, col)
                model.setData(total_usd_index, "" if total_usd == 0 else f"{total_usd:.2f}", Qt.EditRole)
            elif header == "Total USD Foil":
                total_usd_foil_index = model.index(row, col)
                model.setData(total_usd_foil_index, "" if total_usd_foil == 0 else f"{total_usd_foil:.2f}", Qt.EditRole)

    def update_quantity(self, model, row, quantity_columns):
        quantity_values = []
        for quantity_column in quantity_columns:
            quantity_values.append(self.get_value(model, row, quantity_column))
        
        storage_quantity = quantity_values[0] - (sum(quantity_values[1:]))

        for col in range(model.columnCount()):
            if model.headerData(col, Qt.Horizontal) == "Storage Quantity":
                storage_index = model.index(row, col)
                model.setData(storage_index, str(storage_quantity), Qt.EditRole)
                break
    
    def get_value(self, model, row, column_name, data_type=int):
        for col in range(model.columnCount()):
            if model.headerData(col, Qt.Horizontal) == column_name:
                try:
                    return data_type(model.index(row, col).data(Qt.DisplayRole))
                except (ValueError, TypeError):
                    return data_type(0)
        return data_type(0)
