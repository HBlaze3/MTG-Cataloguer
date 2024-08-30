from PyQt5.QtWidgets import QTabWidget, QLabel, QHBoxLayout, QWidget, QPushButton, QTabBar
from PyQt5.QtGui import QIcon
from StyleSheet import CTBUTTON

class TabWidget(QTabWidget):
    def __init__(self):
        super().__init__()

    def add_closable_tab(self, widget, title):
        tab_index = self.addTab(widget, title)
        self.setTabIcon(tab_index, QIcon())
        close_button = QPushButton('x')
        close_button.setFixedSize(16, 16)
        close_button.setStyleSheet(CTBUTTON)
        close_button.clicked.connect(lambda: self.removeTab(tab_index))
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(5, 0, 5, 0)
        tab_layout.addWidget(QLabel(title))
        tab_layout.addWidget(close_button)
        tab_widget = QWidget()
        tab_widget.setLayout(tab_layout)
        self.tabBar().setTabButton(tab_index, QTabBar.RightSide, close_button)
        return tab_index