from PyQt5.QtWidgets import QTableWidgetItem, QUndoCommand, QMessageBox
from PyQt5.QtCore import Qt
from itertools import zip_longest
from typing import OrderedDict
from sharedFunctions import get_value

class EditCellCommand(QUndoCommand):
    def __init__(self, all_cards, table, row, column, old_value, new_value):
        super().__init__("Edit Cell")
        self.get_value = get_value
        self.table = table
        self.row = row
        self.column = column
        self.old_value = old_value
        self.new_value = new_value
        self.all_cards = all_cards
    
    def undo(self):
        self.perform_edit(self.old_value)

    def redo(self):
        self.perform_edit(self.new_value)

    def perform_edit(self, value):
        item = self.table.item(self.row, self.column)
        if item is None:
            item = QTableWidgetItem(value)
            self.table.setItem(self.row, self.column, item)
        else:
            item.setText(value)
        self.table.model().setData(self.table.model().index(self.row, self.column), value, Qt.EditRole)
        self.update_related_data()

    def update_related_data(self):
        header_text = self.table.model().headerData(self.column, Qt.Horizontal)
        model = self.table.model()
        
        quantity_columns = ["Quantity", "Deck Quantity", "Deck Quantity 2", "Deck Quantity 3", "Deck Quantity 4"]
        price_columns = ["Quantity", "Quantity Foil", "USD", "USD Foil"]
        
        if header_text in quantity_columns:
            self.update_quantity(model, self.row, quantity_columns)
        if header_text in price_columns:
            self.update_price(model, self.row, price_columns)
        if header_text in ['Language', 'Set', 'Collector Number']:
            self.update_row_data(model, self.row)
        
    def update_row_data(self, model, row):
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
                    self.update_cell(model, row, 'Type', card['type_line'])
                    self.update_cell(model, row, 'Color Identity', card['color_identity'])
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
    
