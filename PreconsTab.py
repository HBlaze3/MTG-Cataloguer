from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QMessageBox

class PreconsTab(QWidget):
    def __init__(self, deck_list_file, parent=None):
        super().__init__(parent)
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
            for deck in file_data['data']:
                deck_names.append(f"{deck['name']} {deck['code']}")
                deck_files.append(f"{deck['fileName'] + ".json"}")
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
        selected_items = self.deck_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a deck from the list.")
            return

        selected_deck = selected_items[0].text()
        deck_index = self.deck_names.index(selected_deck)

        selected_deck_file = self.deck_files[deck_index]

        QMessageBox.information(self, "Deck Selected", f"You selected: {selected_deck}\nFile: {selected_deck_file}")