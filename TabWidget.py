from PyQt5.QtWidgets import QTabWidget, QLabel, QHBoxLayout, QWidget, QPushButton, QTabBar
from PyQt5.QtGui import QIcon
from StyleSheet import CTBUTTON

class TabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.tab_titles = {}

    def add_tab(self, widget, title, closable=True):
        tab_index = self.addTab(widget, title)
        self.setTabIcon(tab_index, QIcon())
        close_button = QPushButton('x')
        close_button.setFixedSize(16, 16)
        close_button.setStyleSheet(CTBUTTON)
        close_button.clicked.connect(lambda: self.close_tab(title))
        if closable:
            self.tab_titles[title] = tab_index
        else:
            close_button = None
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(5, 0, 5, 0)
        tab_layout.addWidget(QLabel(title))
        if closable:
            tab_layout.addWidget(close_button)
        tab_widget = QWidget()
        tab_widget.setLayout(tab_layout)
        self.tabBar().setTabButton(tab_index, QTabBar.RightSide, close_button)
        return tab_index

    def close_tab(self, title):
        tab_index = self.tab_titles.get(title)
        if tab_index is not None and 0 <= tab_index < self.count():
            self.removeTab(tab_index)
            del self.tab_titles[title]
            for t in list(self.tab_titles.keys()):
                if self.tab_titles[t] > tab_index:
                    self.tab_titles[t] -= 1