DARK_THEME = """
/* ── Global ─────────────────────────────────────────────── */
QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #0f1117;
}

/* ── Labels ─────────────────────────────────────────────── */
QLabel {
    color: #94a3b8;
    font-size: 12px;
    letter-spacing: 0.5px;
}
QLabel#title {
    color: #f1f5f9;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
}
QLabel#subtitle {
    color: #64748b;
    font-size: 12px;
}
QLabel#section {
    color: #38bdf8;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
QLabel#field_label {
    color: #cbd5e1;
    font-size: 12px;
    font-weight: 500;
}

/* ── Line Edits ─────────────────────────────────────────── */
QLineEdit {
    background-color: #1e2330;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
    font-size: 13px;
    selection-background-color: #38bdf8;
    selection-color: #0f1117;
}
QLineEdit:focus {
    border-color: #38bdf8;
    background-color: #1a2035;
}
QLineEdit:hover {
    border-color: #4a5568;
}
QLineEdit[readOnly="true"] {
    background-color: #161a24;
    color: #64748b;
    border-color: #1e2330;
}

/* ── ComboBox ───────────────────────────────────────────── */
QComboBox {
    background-color: #1e2330;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
    font-size: 13px;
    min-width: 160px;
}
QComboBox:focus { border-color: #38bdf8; }
QComboBox:hover { border-color: #4a5568; }
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #64748b;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1e2330;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    selection-background-color: #0e4d6e;
    selection-color: #f1f5f9;
    padding: 4px;
}

/* ── SpinBox / DoubleSpinBox ────────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #1e2330;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
    font-size: 13px;
}
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #38bdf8; }

/* ── DateEdit ───────────────────────────────────────────── */
QDateEdit {
    background-color: #1e2330;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f1f5f9;
    font-size: 13px;
}
QDateEdit:focus { border-color: #38bdf8; }
QDateEdit::drop-down { border: none; width: 28px; }
QDateEdit::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #64748b;
    margin-right: 8px;
}
QCalendarWidget {
    background-color: #1e2330;
    color: #f1f5f9;
}
QCalendarWidget QAbstractItemView {
    background-color: #1e2330;
    selection-background-color: #38bdf8;
    selection-color: #0f1117;
}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton {
    background-color: #1e2330;
    color: #94a3b8;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2d3748;
    color: #f1f5f9;
    border-color: #4a5568;
}
QPushButton:pressed { background-color: #374151; }

QPushButton#primary {
    background-color: #0284c7;
    color: #f0f9ff;
    border: none;
    font-weight: 600;
}
QPushButton#primary:hover { background-color: #0369a1; }
QPushButton#primary:pressed { background-color: #075985; }

QPushButton#danger {
    background-color: #7f1d1d;
    color: #fecaca;
    border: none;
}
QPushButton#danger:hover { background-color: #991b1b; }

QPushButton#success {
    background-color: #14532d;
    color: #bbf7d0;
    border: none;
    font-weight: 600;
}
QPushButton#success:hover { background-color: #166534; }

QPushButton#icon_btn {
    background: transparent;
    border: none;
    color: #64748b;
    padding: 4px 8px;
    font-size: 16px;
}
QPushButton#icon_btn:hover { color: #38bdf8; background: transparent; }

/* ── Table ──────────────────────────────────────────────── */
QTableWidget {
    background-color: #131720;
    border: 1px solid #1e2330;
    border-radius: 8px;
    gridline-color: #1e2330;
    selection-background-color: #0e4d6e;
    selection-color: #f1f5f9;
    font-size: 13px;
}
QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #1e2330;
}
QTableWidget::item:selected {
    background-color: #0e4d6e;
    color: #f1f5f9;
}
QHeaderView::section {
    background-color: #1a1f2e;
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid #38bdf8;
}
QTableWidget::item:hover { background-color: #1a2a3a; }

/* ── ScrollBar ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: #1e2330;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #374151;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #4a5568; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1e2330;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #374151;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── GroupBox ───────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #2d3748;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    color: #64748b;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    color: #38bdf8;
}

/* ── Tab ────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2d3748;
    border-radius: 8px;
    background: #131720;
}
QTabBar::tab {
    background: #1e2330;
    color: #64748b;
    padding: 8px 20px;
    border: 1px solid #2d3748;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #131720;
    color: #38bdf8;
    border-color: #38bdf8;
}

/* ── MessageBox ─────────────────────────────────────────── */
QMessageBox {
    background-color: #1e2330;
}
QMessageBox QLabel { color: #e2e8f0; font-size: 13px; }

/* ── Splitter ───────────────────────────────────────────── */
QSplitter::handle { background: #2d3748; }

/* ── StatusBar ──────────────────────────────────────────── */
QStatusBar {
    background: #0a0d14;
    color: #64748b;
    font-size: 11px;
    border-top: 1px solid #1e2330;
}

/* ── ToolTip ────────────────────────────────────────────── */
QToolTip {
    background-color: #1e2330;
    color: #f1f5f9;
    border: 1px solid #38bdf8;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* ── ListWidget (autocomplete) ──────────────────────────── */
QListWidget {
    background-color: #1e2330;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    color: #f1f5f9;
}
QListWidget::item { padding: 6px 12px; }
QListWidget::item:hover { background-color: #0e4d6e; }
QListWidget::item:selected { background-color: #0284c7; color: #fff; }

/* ── Frame (card) ───────────────────────────────────────── */
QFrame#card {
    background-color: #131720;
    border: 1px solid #1e2330;
    border-radius: 10px;
}
QFrame#top_bar {
    background-color: #0a0d14;
    border-bottom: 1px solid #1e2330;
}
"""
