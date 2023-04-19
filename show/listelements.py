from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

from .components import components

import subprocess, os, platform

def open_file(filepath):
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(filepath)
    else:                                   # linux variants
        subprocess.call(('xdg-open', filepath))

class ListWidget(QListWidget):
    def __init__(self, parent=None):
        super(ListWidget, self).__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setUniformItemSizes(True)
        self.itemDoubleClicked.connect(self.doubleClicked)
        self.setStyleSheet("""
            QListWidget::item {
                color: white;
                background-color: #404040;
                height: 80px;
                margin: 5px;
                border-radius: 5px;
            }

            QListWidget::item:hover {
                background-color: #424242;
            }

            QListWidget::item:selected {
                background-color: #2980b9;
            }

            QListWidget {
                border: none;
            }
        """)

    def doubleClicked(self, event: QListWidgetItem):
        open_file(event.data(1))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                self.addItem(url.path())
            event.accept()
        else:
            super().dropEvent(event)

    def add_item(self):
        filter_ext = []
        for c in components:
            filter_ext += c.extensions()

        (path, _) = QFileDialog.getOpenFileName(self, "Open Image", filter="Files (" + ' '.join(filter_ext) + ")")

        if path == '':
            return

        item = QListWidgetItem()
        item.setData(1, path)
        item.setText(os.path.basename(path))

        label_widget = QWidget()
        label_widget.setStyleSheet("""
            width: 10px;
            height: 20px;
            margin: 40px;
            padding: 100px;
        """)

        self.addItem(item)
        self.setItemWidget(item, label_widget)


    def remove_item(self):
        selected = self.currentRow()
        if selected != -1:
            self.takeItem(selected)
