from PyQt5.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QCheckBox, QDialogButtonBox, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QSettings, QTimer
from Startup import Startup

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.default_paths = {
            "Art": "./JSONs/A.json",
            "Black": "./JSONs/B.json",
            "Colorless": "./JSONs/C.json",
            "Green": "./JSONs/G.json",
            "Multicolored": "./JSONs/M.json",
            "Red": "./JSONs/R.json",
            "Tokens": "./JSONs/T.json",
            "Blue": "./JSONs/U.json",
            "White": "./JSONs/W.json"
        }
        self.path_fields = {}
        
        layout = QFormLayout()
        for label, default in self.default_paths.items():
            path_layout = QHBoxLayout()
            self.path_fields[label] = QLineEdit(self)
            self.path_fields[label].setText(default)
            browse_button = QPushButton("Browse", self)
            browse_button.clicked.connect(lambda _, l=label: self.browse_file(l))
            path_layout.addWidget(self.path_fields[label])
            path_layout.addWidget(browse_button)
            layout.addRow(f"{label} Path:", path_layout)

        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        layout.addRow(self.dark_mode_checkbox)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        self.check_updates_button = QPushButton("Check for Updates")
        self.check_updates_button.clicked.connect(self.check_updates)
        self.reset_button = QPushButton("Reset to Default", self)
        self.reset_button.clicked.connect(self.reset_to_default)
        checkres_layout = QHBoxLayout()
        checkres_layout.addWidget(self.check_updates_button)
        checkres_layout.addWidget(self.reset_button)
        layout.addRow(checkres_layout)
        self.setLayout(layout)
        
        self.load_settings()
    
    def check_updates(self):
        if not self.settings.value("first_startup", True, type=bool):
            reply = QMessageBox.question(
                self, 
                "Override Files?", 
                "Some files may already be up-to-date. Do you want to override them?",
                QMessageBox.Yes | QMessageBox.No
            )
            override = (reply == QMessageBox.Yes)
        else:
            override = True
        
        wait_message = QMessageBox(self)
        wait_message.setWindowTitle("Please Wait")
        wait_message.setText("Downloading updates, please wait...\n*Program may seem frozen")
        wait_message.setStandardButtons(QMessageBox.NoButton)
        wait_message.setWindowModality(Qt.ApplicationModal)

        QTimer.singleShot(10, wait_message.exec_)
        QApplication.processEvents()
        def perform_update():
            try:
                Startup.startup_tasks(override)
            except Exception as e:
                QMessageBox.critical(self, "Update Error", f"Failed to update sets: {str(e)}")
            finally:
                wait_message.done(0)
                QMessageBox.information(self, "Update", "Files updated successfully.")
        QTimer.singleShot(100, perform_update)

    def load_settings(self):
        self.settings = QSettings("HBlaze3", "MTG-Cataloguer")
        self.dark_mode_checkbox.setChecked(self.settings.value("theme", True, type=bool))
        for label, default in self.default_paths.items():
            path = self.settings.value(f"paths/{label}", default)
            self.path_fields[label].setText(path)

    def save_settings(self):
        self.settings = QSettings("HBlaze3", "MTG-Cataloguer")
        self.settings.setValue("theme", self.dark_mode_checkbox.isChecked())
        for label, line_edit in self.path_fields.items():
            path = line_edit.text()
            self.settings.setValue(f"paths/{label}", path)

    def browse_file(self, label):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select {label} JSON File", "", "JSON Files (*.json)")
        if file_path:
            self.path_fields[label].setText(file_path)

    def reset_to_default(self):
        self.settings = QSettings("HBlaze3", "MTG-Cataloguer")
        for label, default in self.default_paths.items():
            self.path_fields[label].setText(default)
        self.dark_mode_checkbox.setChecked(True)

    def accept(self):
        for label in self.default_paths.keys():
            self.settings.setValue(f"paths/{label}", self.path_fields[label].text())

        self.settings.setValue("theme", self.dark_mode_checkbox.isChecked())
        super().accept()