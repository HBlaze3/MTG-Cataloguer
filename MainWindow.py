from csv import writer
from json import dump, load
from AddRowCommand import AddRowCommand
from CustomDelegate import CustomDelegate
from DeleteRowCommand import DeleteRowCommand
from PathSelectionDialog import PathSelectionDialog
from PreconsTab import PreconsTab
from SettingsDialog import SettingsDialog
from TabWidget import TabWidget
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, 
                             QMenuBar, QAction, QLabel, QHBoxLayout, QAbstractItemView, QMessageBox, QUndoStack, QInputDialog)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QIcon
from os.path import exists, basename, join
from os import listdir
from ijson import items, IncompleteJSONError
from sharedFunctions import sort_json_data
from StyleSheet import MENUSTYLE, PAD, BUTTONSTYLE, TITLESTYLE, THEMESTYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sort_json_data = sort_json_data
        self.settings = QSettings("HBlaze3", "MTG-Cataloguer")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("JSON Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        if self.settings.value("first_startup", True, type=bool):
            settings_dialog = SettingsDialog(self)
            settings_dialog.check_updates()
            self.settings.setValue("first_startup", False)
        self.langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'ru', 'zhs', 'zht', 'ph']
        self.sets = self.load_local_file('sets.json')
        self.all_cards = self.load_local_file('all_cards.json')
        self.DeckList = self.load_local_file('DeckList.json')
        self.ADFDir = "./AllDeckFiles"
        self.ADFFiles = [join(self.ADFDir, file) for file in listdir(self.ADFDir)]
        self.AllDeckFiles = self.load_local_AllDeckFiles(self.ADFFiles)
        self.undo_stack = QUndoStack(self)

        self.column_mapping = {
            "lang": "Language",
            "release_date": "Release Date",
            "name": "Name",
            "type_line": "Type",
            "color_identity": "Color Identity",
            "set_name": "Set Name",
            "set": "Set",
            "collector_number": "Collector Number",
            "quantity": "Quantity",
            "quantity_foil": "Quantity Foil",
            "usd": "USD",
            "usd_foil": "USD Foil",
            "total_usd": "Total USD",
            "total_usd_foil": "Total USD Foil",
            "storage_areas": "Storage Areas",
            "storage_quantity": "Storage Quantity",
            "deck_type": "Deck Type",
            "deck_quantity": "Deck Quantity",
            "deck_type_two": "Deck Type 2",
            "deck_quantity_two": "Deck Quantity 2",
            "deck_type_three": "Deck Type 3",
            "deck_quantity_three": "Deck Quantity 3",
            "deck_type_four": "Deck Type 4",
            "deck_quantity_four": "Deck Quantity 4"
        }

        self.editable_column_names = {
            "Language": "lang",
            "Set": "set", 
            "Collector Number": "collector_number", 
            "Quantity": "quantity", 
            "Quantity Foil": "quantity_foil", 
            "Storage Areas": "storage_areas",
            "Deck Type": "deck_type", 
            "Deck Quantity": "deck_quantity", 
            "Deck Type 2": "deck_type_two", 
            "Deck Quantity 2": "deck_quantity_two",
            "Deck Type 3": "deck_type_three", 
            "Deck Quantity 3": "deck_quantity_three", 
            "Deck Type 4": "deck_type_four", 
            "Deck Quantity 4": "deck_quantity_four"
        }
        
        self.editable_columns = set(self.editable_column_names.values())
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet(TITLESTYLE)
        self.title_bar.setFixedHeight(30)
        self.title_label = QLabel("JSON Viewer", self.title_bar)
        self.title_label.setStyleSheet(PAD+"5px;")
        self.minimize_button = QPushButton("-", self.title_bar)
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet(BUTTONSTYLE)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.fullscreen_button = QPushButton("□", self.title_bar)
        self.fullscreen_button.setFixedSize(30, 30)
        self.fullscreen_button.setStyleSheet(BUTTONSTYLE)
        self.fullscreen_button.clicked.connect(self.toggle_maximized)
        self.exit_button = QPushButton("X", self.title_bar)
        self.exit_button.setFixedSize(30, 30)
        self.exit_button.setStyleSheet(BUTTONSTYLE)
        self.exit_button.clicked.connect(self.close)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.fullscreen_button)
        title_layout.addWidget(self.exit_button)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        self.menu_bar = QMenuBar(self)
        self.file_menu = self.menu_bar.addMenu("File")
        self.load_action = QAction("Load JSON", self)
        self.load_action.triggered.connect(self.load_json)
        self.file_menu.addAction(self.load_action)
        self.save_action = QAction("Save Changes", self)
        self.save_action.triggered.connect(self.save_changes)
        self.file_menu.addAction(self.save_action)
        self.file_convert = QAction("Convert File", self)
        self.file_convert.triggered.connect(self.file_conversion)
        self.file_menu.addAction(self.file_convert)
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.open_settings_dialog)
        self.menu_bar.addAction(self.settings_action)
        self.undo_action = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        self.undo_action.triggered.connect(self.undo)
        self.menu_bar.addAction(self.undo_action)
        self.redo_action = QAction(QIcon.fromTheme("edit-redo"), "Redo", self)
        self.redo_action.triggered.connect(self.redo)
        self.menu_bar.addAction(self.redo_action)
        self.menu_bar.setStyleSheet(MENUSTYLE)

        central_layout = QVBoxLayout()
        central_layout.addWidget(self.title_bar)
        central_layout.addWidget(self.menu_bar)
        self.tab_widget = TabWidget()
        central_layout.addWidget(self.tab_widget)
        central_widget = QWidget(self)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)
        self.add_precons_tab()
        self.load_settings()
        self._drag_start_pos = None
        self._drag_start_geometry = None
        self._is_resizing = False
        self._resize_edge = None
        
    def add_precons_tab(self):
        precons_tab = PreconsTab(self, self.DeckList)
        tab_index = self.tab_widget.add_tab(precons_tab, "Precons", False)
        self.tab_widget.setCurrentIndex(tab_index)

    def load_local_AllDeckFiles(self, file_paths):
        results = {}
        try:
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = items(f, 'item')
                    results[basename(file_path)] = data
            return results
        except Exception as e:
            return []

    def load_local_file(self, filename):
        try:
            with open(filename, 'r') as file:
                file.readline()
                if filename == 'all_cards.json':
                    data = items(file, 'item')
                    processed_data = {}
                        
                    for item in data:
                            key = (item["lang"], item["set"], item["collector_number"])
                            processed_data[key] = item
                    return processed_data
                return load(file)
        except (FileNotFoundError, IncompleteJSONError, KeyError):
            QMessageBox.critical(self, "Error", filename + " file not found or corrupted.")
            return []
    
    def get_tab_count(self):
        return self.tab_widget.count()
    @classmethod
    def reload_sets(self):
        self.sets = self.load_local_file(self, 'sets.json')
    @classmethod
    def reload_all_cards(self):
        self.all_cards = self.load_local_file(self, 'all_cards.json')
    @classmethod
    def reload_DeckList(self):
        self.DeckList = self.load_local_file(self, 'DeckList.json')
    @classmethod
    def reload_AllDeckFiles(self):
        self.ADFFiles = [join(self.ADFDir, file) for file in listdir(self.ADFDir)]
        self.AllDeckFiles = self.load_local_AllDeckFiles(self.ADFFiles)

    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
            self.fullscreen_button.setText("□")
        else:
            self.showMaximized()
            self.fullscreen_button.setText("🗖")

    def add_tab(self, tab_name, data):
        tab_name = tab_name.split('/')[-1]
        tab_content = QWidget()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.delegate = CustomDelegate(all_cards=self.all_cards, parent=self.table, undo_stack=self.undo_stack, editable_columns=self.editable_column_names, sets=self.sets, langs=self.langs)
        self.table.setItemDelegate(self.delegate)
        self.add_button = QPushButton("Add Row")
        self.add_button.clicked.connect(self.add_row)
        self.delete_button = QPushButton("Delete Row")
        self.delete_button.clicked.connect(self.delete_row)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        tab_content.setLayout(layout)
        self.populate_table(self.table, data)
        tab_index = self.tab_widget.add_tab(tab_content, tab_name)
        self.tab_widget.setCurrentIndex(tab_index)

    def populate_table(self, table, data):
        all_columns = set()
        for card in data:
            all_columns.update(card.keys())
        
        columns = [col for col in self.column_mapping.keys() if col in all_columns]
        display_columns = [self.column_mapping[col] for col in columns]
        table.setColumnCount(len(display_columns))
        table.setHorizontalHeaderLabels(display_columns)
        table.setRowCount(len(data))

        for row, card in enumerate(data):
            for col, column in enumerate(columns):
                value = card.get(column, "")
                item = QTableWidgetItem(value)
                if column in self.editable_columns:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, col, item)
        table.resizeColumnsToContents()

    def add_row(self):
        row_position = self.table.rowCount()
        self.undo_stack.push(AddRowCommand(self.table, row_position, self.editable_column_names))

    def delete_row(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            self.undo_stack.push(DeleteRowCommand(self.table, selected_row))
            self.table.removeRow(selected_row)

    def load_json(self):
        dialog = PathSelectionDialog(self.settings, self)
        if dialog.exec_():
            selected_paths = dialog.get_selected_paths()
            for file_path, key in selected_paths:
                if not exists(file_path):
                    user_choice = self.handle_missing_file(file_path)
                    if user_choice == "create":
                        with open(file_path, 'w') as file:
                            dump([], file)
                    elif user_choice == "change":
                        new_file_path, _ = QFileDialog.getOpenFileName(self, "Select New Path for JSON", "", "JSON Files (*.json)")
                        if new_file_path:
                            self.settings.setValue(key, new_file_path)
                            file_path = new_file_path
                        else:
                            QMessageBox.warning(self, "Warning", "No file selected. Skipping this file.")
                            continue
                    else:
                        continue
                try:
                    with open(file_path, 'r') as file:
                        data = load(file)
                        self.add_tab(key, data)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load JSON file: {str(e)}")

    def handle_missing_file(self, file_path):
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle("File Not Found")
        message_box.setText(f"The file '{file_path}' does not exist.")
        message_box.setInformativeText("Would you like to create a new file, change the path, or cancel?")
        create_button = message_box.addButton("Create", QMessageBox.AcceptRole)
        change_button = message_box.addButton("Change Path", QMessageBox.AcceptRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)

        message_box.exec_()
        if message_box.clickedButton() == create_button:
            return "create"
        elif message_box.clickedButton() == change_button:
            return "change"
        else:
            return "cancel"

    def get_tab_changes(self):
        tab_index = self.tab_widget.currentIndex()
        if tab_index <= 0:
            QMessageBox.warning(self, "No Tab Selected", "Please select a tab to save.")
            return
        tab_title = self.tab_widget.tabText(tab_index)
        settings = QSettings("HBlaze3", "MTG-Cataloguer")
        file_path = settings.value(f"paths/{tab_title}")
        if not file_path:
            QMessageBox.warning(self, "File Path Not Found", f"No saved file path for tab: {tab_title}")
            return
        data = self.extract_data_from_table(self.tab_widget.widget(tab_index).findChild(QTableWidget))
        if tab_title == "Art":
            sorted_data = self.sort_json_data(data)
        else:
            sorted_data = self.sort_json_data(data, self.all_cards)
        return tab_title, file_path, sorted_data

    def save_changes(self):
        tab_changes = self.get_tab_changes()
        if tab_changes is None:
            return
        tab_title, file_path, sorted_data = tab_changes
        try:
            with open(file_path, 'w') as file:
                dump(sorted_data, file)
            QMessageBox.information(self, "Success", f"Changes saved successfully to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save JSON file: {str(e)}")
        self.tab_widget.close_tab(tab_title)
        self.add_tab(tab_title, sorted_data)

    def file_conversion(self):
        platforms = ["Moxfield", "Archidekt", "CardSphere", "DeckBox", "Decked Builder", "DeckStats", 
                    "Helvault", "ManaBox", "TappedOut", "DragonShield", "TopDecked", "MTGGoldfish", 
                    "CardKingdom", "TCGPlayer"]
        platform, ok = QInputDialog.getItem(self, "Select Platform", "Choose platform to export deck to:", platforms, 0, False)
        if not ok:
            return
        tab_changes = self.get_tab_changes()
        if tab_changes is None:
            return
        _, _, sorted_data = tab_changes
        platform_headers = {
            "Moxfield": {
                "file_headers": ["Count", "Name", "Edition", "Collector Number"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number"]
            },
            "Archidekt": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number"]
            },
            "CardSphere": {
                "file_headers": ["Quantity", "Name", "Set", "USD", "Quantity Foil", "USD Foil"], 
                "headers": ["Quantity", "Name", "Set", "USD", "Quantity Foil", "USD Foil"]
            },
            "DeckBox": {
                "file_headers": ["Quantity", "Name", "Set", "Collector Number", "Storage Areas"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number", "Storage Areas"]
            },
            "Decked Builder": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "USD", "Quantity Foil", "Total USD", "Total USD Foil"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "USD", "Quantity Foil", "Total USD", "Total USD Foil"]
            },
            "DeckStats": {
                "file_headers": ["Quantity", "Name", "Set", "Collector Number", "Deck Type", "Deck Quantity"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number", "Deck Type", "Deck Quantity"]
            },
            "Helvault": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Deck Quantity", "Deck Type 2", "Deck Quantity 2"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Deck Quantity", "Deck Type 2", "Deck Quantity 2"]
            },
            "ManaBox": {
                "file_headers": ["Quantity", "Name", "Set", "Collector Number", "Color Identity"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number", "Color Identity"]
            },
            "TappedOut": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Deck Quantity"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Deck Quantity"]
            },
            "DragonShield": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Storage Areas"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "Deck Type", "Storage Areas"]
            },
            "TopDecked": {
                "file_headers": ["Quantity", "Name", "Set", "Collector Number", "Deck Type", "Deck Quantity", "Storage Areas"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number", "Deck Type", "Deck Quantity", "Storage Areas"]
            },
            "MTGGoldfish": {
                "file_headers": ["Quantity", "Name", "Set", "Collector Number", "USD", "Total USD"], 
                "headers": ["Quantity", "Name", "Set", "Collector Number", "USD", "Total USD"]
            },
            "CardKingdom": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "USD"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "USD"]
            },
            "TCGPlayer": {
                "file_headers": ["Name", "Quantity", "Set", "Collector Number", "USD", "USD Foil", "Total USD", "Total USD Foil"], 
                "headers": ["Name", "Quantity", "Set", "Collector Number", "USD", "USD Foil", "Total USD", "Total USD Foil"]
            }
        }
        if platform not in platform_headers:
            QMessageBox.critical(self, "Error", f"Export format for {platform} is not supported.")
            return
        file_headers = platform_headers[platform]["file_headers"]
        headers = platform_headers[platform]["headers"]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not save_path:
            return
        try:
            with open(save_path, mode='w', newline='', encoding='utf-8') as file:
                csver = writer(file)
                csver.writerow(file_headers)
                
                for row in sorted_data:
                    row_data = []
                    for header in headers:
                        db_column = self.editable_column_names.get(header, header.lower())
                        row_data.append(row.get(db_column, ""))
                    csver.writerow(row_data)
            QMessageBox.information(self, "Success", f"File successfully exported to {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")
    
    def extract_data_from_table(self, table):
        columns = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        display_to_db_column = {v: k for k, v in self.column_mapping.items()}
        
        data = []
        for row in range(table.rowCount()):
            row_data = {}
            for col, column in enumerate(columns):
                item = table.item(row, col)
                database_name = display_to_db_column.get(column)
                if database_name:
                    row_data[database_name] = item.text() if item else ''
                else:
                    row_data[column.lower()] = item.text() if item else ''
            data.append(row_data)
        
        return data

    def undo(self):
        self.undo_stack.undo()

    def redo(self):
        self.undo_stack.redo()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self, self.all_cards)
        if dialog.exec_():
            self.toggle_theme()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        settings = QSettings("HBlaze3", "MTG-Cataloguer")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("theme", QSettings("HBlaze3", "MTG-Cataloguer").value("theme", True, type=bool))

    def load_settings(self):
        settings = QSettings("HBlaze3", "MTG-Cataloguer")
        self.restoreGeometry(settings.value("geometry", b""))
        self.restoreState(settings.value("windowState", b""))
        self.apply_theme(settings.value("theme", True, type=bool))

    def toggle_theme(self):
        dark_mode = QSettings("HBlaze3", "MTG-Cataloguer").value("theme", True, type=bool)
        self.apply_theme(dark_mode)

    def apply_theme(self, dark_mode):
        if dark_mode:
            self.setStyleSheet(THEMESTYLE)
        else:
            self.setStyleSheet("")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.globalPos()
            self._drag_start_geometry = self.geometry()

            edge_size = 10
            rect = self.rect()
            if event.pos().x() < edge_size and event.pos().y() < edge_size:
                self._is_resizing, self._resize_edge = True, 'top-left'
            elif event.pos().x() < edge_size and event.pos().y() > rect.height() - edge_size:
                self._is_resizing, self._resize_edge = True, 'bottom-left'
            elif event.pos().x() > rect.width() - edge_size and event.pos().y() < edge_size:
                self._is_resizing, self._resize_edge = True, 'top-right'
            elif event.pos().x() > rect.width() - edge_size and event.pos().y() > rect.height() - edge_size:
                self._is_resizing, self._resize_edge = True, 'bottom-right'
            else:
                self._is_resizing = False

    def mouseMoveEvent(self, event):
        if not hasattr(self, '_drag_start_pos'):
            return

        if self._is_resizing:
            delta = event.globalPos() - self._drag_start_pos
            if self._resize_edge == 'top-left':
                self.resize(self.width() - delta.x(), self.height() - delta.y())
                self.move(self.x() + delta.x(), self.y() + delta.y())
            elif self._resize_edge == 'bottom-left':
                self.resize(self.width() - delta.x(), self.height() + delta.y())
                self.move(self.x() + delta.x(), self.y())
            elif self._resize_edge == 'top-right':
                self.resize(self.width() + delta.x(), self.height() - delta.y())
                self.move(self.x(), self.y() + delta.y())
            elif self._resize_edge == 'bottom-right':
                self.resize(self.width() + delta.x(), self.height() + delta.y())
            self._drag_start_pos = event.globalPos()
        else:
            delta = event.globalPos() - self._drag_start_pos
            self.setGeometry(self._drag_start_geometry.translated(delta))

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_drag_start_pos'):
            del self._drag_start_pos
            del self._drag_start_geometry
            if hasattr(self, '_resize_edge'):
                del self._resize_edge
            self._is_resizing = False