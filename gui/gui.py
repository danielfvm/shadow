import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from listelements import ListWidget

from tkinter.filedialog import askopenfilename

class WindowBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the window bar properties
        self.setFixedHeight(40)

        self.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                border: none;
                color: white;
                padding: 25px 25px;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                cursor: pointer;
                margin: 5px 5px;
                border-radius: 2px;
                font-weight: 200;
            }

            QPushButton::hover {
                background-color: #3498db;
            }

            QLabel {
                background-color: rgba(0,0,0,0);
                font-weight: 200;
                color: white;
                margin: 5px;
            }
        """)

        # Create the title label and add it to the layout
        self.title = QLabel("Show - Shader On Wallpaper")

        # Create the close button and add it to the layout
        self.close_btn = QPushButton("X")
        self.close_btn.clicked.connect(self.parent().close)
        self.close_btn.setFixedWidth(40)

        # Create the layout for the window bar
        layout = QHBoxLayout()
        layout.addWidget(self.title)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.close_btn)

        # Set the layout for the window bar
        self.setLayout(layout)

    def paintEvent(self, event):
        # Override the paintEvent to draw a border around the window bar
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width() - 1, self.height() - 1, QColor(20, 20, 20))

    def mousePressEvent(self, event):
        # Override the mousePressEvent to start the dragging process
        if event.button() == Qt.LeftButton:
            self.start_drag_pos = event.globalPos() - self.parent().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        # Override the mouseMoveEvent to move the window when dragging the window bar
        if event.buttons() == Qt.LeftButton:
            self.parent().move(event.globalPos() - self.start_drag_pos)
            event.accept()



class TabWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Remove the window border and set the background color to white
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #303030;
            font-size: 18px;
            color: white;
        """)


        # Create a vertical layout for the Tab widget
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a custom window bar and add it to the layout
        self.window_bar = WindowBar(self)
        layout.addWidget(self.window_bar)

        # Create a Tab widget
        self.tabs = QTabWidget(self)

        # Set the background color of the Tab bar to gray and center the tabs
        self.tabs.setStyleSheet("""
            QTabWidget::tab-bar {
                alignment: center;
                border: none;
            }

            QTabBar::tab {
                background-color: #404040;
                padding: 5px 50px 5px 50px;
                margin: 5px 0px 5px 0px;
                text-align: center;
                border-radius: 2px;
                font-weight: 200;
            }

            QTabBar::tab:selected {
                background-color: #2980b9;
            }

            QTabBar::tab:pressed {
                background-color: #2980b9;
            }

            QTabWidget::pane {
                border: 0
            }
        """)

        # Add the tabs to the Tab widget
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.addTab(self.tab1, "Browse")
        self.tabs.addTab(self.tab2, "Current")
        self.tabs.addTab(self.tab3, "Settings")
        self.tabs.setGeometry(100, 0, 200, 50)

        #self.tab2.setStyleSheet("""
        #    QPushButton {
        #        background-color: #2980b9;
        #        border: none;
        #        color: white;
        #        padding: 5px 25px;
        #        text-decoration: none;
        #        display: inline-block;
        #        font-size: 16px;
        #        cursor: pointer;
        #        margin: 5px 5px;
        #        border-radius: 2px;
        #        font-weight: 200;
        #    }
        #""")

        self.list_widget = ListWidget(self.tab2)
        self.list_widget.setGeometry(0, 0, 600, 600)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)

        add_button = QPushButton('Import', self.tab2)
        add_button.setGeometry(20, 650, 200, 50)

        add_button.clicked.connect(self.list_widget.add_item)

        remove_button = QPushButton('Remove', self.tab2)
        remove_button.clicked.connect(self.list_widget.remove_item)
        remove_button.setGeometry(20 + 200 + 20, 650, 200, 50)


        # Add the Tab widget to the layout
        layout.addWidget(self.tabs)

        # Set the layout for the widget
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = TabWidget()
    widget.setMinimumSize(600, 800)
    widget.show()
    sys.exit(app.exec_())
