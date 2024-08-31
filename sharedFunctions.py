from decimal import Decimal, InvalidOperation
from PyQt5.QtCore import Qt
from re import findall, split, sub

def get_value(model, row, column_name, data_type=int):
    for col in range(model.columnCount()):
        if model.headerData(col, Qt.Horizontal) == column_name:
            try:
                return data_type(model.index(row, col).data(Qt.DisplayRole))
            except (ValueError, TypeError):
                return data_type(0)
    return data_type(0)

def parse_date(date_str):
    year, month, day = map(int, date_str.split('-'))
    return year, month, day

def extract_collector_number(collector_number):
    if " // " in collector_number:
        collector_number = collector_number.split(" // ")[0]
    numeric_part = int(''.join(findall(r'\d+', collector_number)))
    return split(r'(\d+)', collector_number)[0], numeric_part

def sort_json_data(json_data, all_card_data=None):
    if all_card_data is not None:
        for item in json_data:
            key = (item.get('lang'), item.get('set'), item.get('collector_number'))
            card_data = all_card_data.get(key, {})
            usd_value = card_data.get('usd', '') or ''
            usd_foil_value = card_data.get('usd_foil', '') or ''
            quantity = str(item.get('quantity', '1')).strip()
            quantity_foil = str(item.get('quantity_foil', '0')).strip()

            try:
                quantity_int = max(int(quantity), 1)
            except ValueError:
                quantity_int = 1
            try:
                quantity_foil_int = max(int(quantity_foil), 0)
            except ValueError:
                quantity_foil_int = 0
            
            adjusted_quantity = quantity_int - quantity_foil_int

            try:
                usd_value = Decimal(sub(r'[^\d.]', '', usd_value or ''))
                total_usd = str(adjusted_quantity * usd_value)
            except (ValueError, InvalidOperation):
                total_usd = ""
            try:
                usd_foil_value = Decimal(sub(r'[^\d.]', '', usd_foil_value or ''))
                total_usd_foil = str(quantity_foil_int * usd_foil_value)
            except (ValueError, InvalidOperation):
                total_usd_foil = ""
            item['total_usd'] = total_usd if total_usd != "0.00" else ""
            item['total_usd_foil'] = total_usd_foil if total_usd_foil != "0.00" else ""
            item['usd'] = str(usd_value)
            item['usd_foil'] = str(usd_foil_value)
    sorted_data = sorted(
        json_data,
        key=lambda x: (
            parse_date(x['release_date']),
            x['set'],
            extract_collector_number(x['collector_number'])
        )
    )
    return sorted_data