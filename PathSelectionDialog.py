from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox

class PathSelectionDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select JSON Files to Load")
        self.settings = settings
        layout = QVBoxLayout()
        self.checkboxes = {}
        for label in settings.allKeys():
            if label.startswith("paths/"):
                display_label = label.split("/")[1]
                path = settings.value(label)
                checkbox = QCheckBox(f"{display_label}: {path}", self)
                layout.addWidget(checkbox)
                self.checkboxes[label] = checkbox
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_selected_paths(self):
        selected_paths = []
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected_paths.append([self.settings.value(key), key])
        return selected_paths