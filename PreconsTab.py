from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QMessageBox
from PyQt5.QtCore import QSettings
from json import load, dump
from os.path import join
from sharedFunctions import sort_json_data

class PreconsTab(QWidget):
    def __init__(self, main_window, deck_list_file, parent=None):
        super().__init__(parent)
        self.sort_json_data = sort_json_data
        self.main_window = main_window
        self.deck_list_file = deck_list_file
        self.deck_names, self.deck_files = self.load_deck_names(self.deck_list_file)

        layout = QVBoxLayout()

        self.deck_list_widget = QListWidget(self)
        self.populate_deck_list(self.deck_names)
        layout.addWidget(self.deck_list_widget)
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search decks...")
        self.search_bar.textChanged.connect(self.filter_deck_list)
        layout.addWidget(self.search_bar)
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit_selection)
        layout.addWidget(self.submit_button)
        self.setLayout(layout)

    def load_deck_names(self, file_data):
        try:
            deck_names = []
            deck_files = []
            for deck in file_data:
                deck_names.append(deck['name'])
                deck_files.append(deck['fileName'])
            return deck_names, deck_files
        except Exception as e:
            return [], []

    def populate_deck_list(self, deck_names):
        self.deck_list_widget.clear()
        self.deck_list_widget.addItems(deck_names)

    def filter_deck_list(self):
        search_term = self.search_bar.text().lower()
        filtered_decks = [name for name in self.deck_names if search_term in name.lower()]
        self.populate_deck_list(filtered_decks)

    def submit_selection(self):
        if self.main_window.get_tab_count() > 1:
            QMessageBox.warning(self, "Close Tabs", "Please close all other tabs to ensure data consistency.")
            return
        selected_items = self.deck_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a deck from the list.")
            return

        selected_deck = selected_items[0].text()
        deck_index = self.deck_names.index(selected_deck)

        selected_deck_file = self.deck_files[deck_index]
        deck_file_path = join("./AllDeckFiles", selected_deck_file)

        def get_color(color_id):
            if "," in color_id:
                return "Multicolored"
            match color_id:
                case "B":
                    return "Black"
                case "G":
                    return "Green"
                case "R":
                    return "Red"
                case "U":
                    return "Blue"
                case "W":
                    return "White"
                case "":
                    return "Colorless"
                
        try:
            with open(deck_file_path, 'r', encoding='utf-8') as f:
                deck_data = load(f)

            settings = QSettings("HBlaze3", "MTG-Cataloguer")

            for card in deck_data:
                label = f"paths/{get_color(card['color_identity'])}"
                json_file_path = settings.value(label)
                
                if not json_file_path:
                    QMessageBox.critical(self, "Error", f"Path for {label} not found.")
                    return
                
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    existing_data = load(f)
                
                duplicate_found = False
                for existing_card in existing_data:
                    if (existing_card['lang'] == card['lang'] and
                        existing_card['set'] == card['set'] and
                        existing_card['collector_number'] == card['collector_number']):
                        
                        existing_card['quantity'] = str(int(existing_card['quantity']) + int(card['quantity']))
                        existing_card['quantity_foil'] = str(int(existing_card['quantity_foil']) + int(card['quantity_foil']) if card['quantity_foil'] else existing_card['quantity_foil'])
                        existing_card['storage_quantity'] = str(int(existing_card['storage_quantity']) + int(card['storage_quantity']))
                        
                        duplicate_found = True
                        break
                
                if not duplicate_found:
                    existing_data.append(card)

                sorted_data = self.sort_json_data(existing_data)

                with open(json_file_path, 'w', encoding='utf-8') as f:
                    dump(sorted_data, f)

            QMessageBox.information(self, "Success", "Deck data has been written to the appropriate JSON files.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process deck: {str(e)}")