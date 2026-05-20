from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


def make_label(text, obj_name="field_label"):
    lbl = QLabel(text)
    lbl.setObjectName(obj_name)
    return lbl


def make_separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background-color: #1e2330; border: none; max-height: 1px;")
    return line


class SearchableComboBox(QWidget):
    """A line-edit + dropdown list for searchable selection."""
    selectionChanged = Signal(object)  # emits the selected data object or None

    def __init__(self, placeholder="Search...", parent=None):
        super().__init__(parent)
        self._items = []   # list of (display_text, data_object)
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(placeholder)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(160)
        self.list_widget.hide()
        layout.addWidget(self.list_widget)

        self.search_edit.textChanged.connect(self._on_text_changed)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.search_edit.focusOutEvent = self._focus_out

    def _focus_out(self, event):
        QTimer.singleShot(150, self.list_widget.hide)
        QLineEdit.focusOutEvent(self.search_edit, event)

    def set_items(self, items: list):
        """items: list of (display_text, data_object)"""
        self._items = items
        self._populate(items)

    def _populate(self, items):
        self.list_widget.clear()
        for text, data in items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.list_widget.addItem(item)

    def _on_text_changed(self, text):
        if not text:
            self._selected = None
            self.selectionChanged.emit(None)
            self.list_widget.hide()
            return
        filtered = [(t, d) for t, d in self._items if text.lower() in t.lower()]
        self._populate(filtered)
        self.list_widget.show() if filtered else self.list_widget.hide()

    def _on_item_clicked(self, item):
        self._selected = item.data(Qt.ItemDataRole.UserRole)
        self.search_edit.setText(item.text())
        self.list_widget.hide()
        self.selectionChanged.emit(self._selected)

    def get_selected(self):
        return self._selected

    def clear_selection(self):
        self._selected = None
        self.search_edit.clear()
        self.list_widget.hide()
        self.selectionChanged.emit(None)

    def set_value(self, display_text, data_obj):
        self._selected = data_obj
        self.search_edit.setText(display_text)
        self.list_widget.hide()


class StatCard(QFrame):
    def __init__(self, title, value, color="#38bdf8", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(140)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        lbl_title = QLabel(title.upper())
        lbl_title.setObjectName("subtitle")
        lbl_title.setStyleSheet(f"color: #64748b; font-size: 10px; letter-spacing: 1.5px;")

        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
