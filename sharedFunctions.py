from PyQt5.QtCore import Qt
from re import findall, split

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

def sort_json_data(json_data):
    sorted_data = sorted(
        json_data,
        key=lambda x: (
            parse_date(x['release_date']),
            x['set'],
            extract_collector_number(x['collector_number'])
        )
    )
    return sorted_data