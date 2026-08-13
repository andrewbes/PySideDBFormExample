"""Представлення: головне вікно форми документа."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QStyle,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from src.view.delegates import GoodsDelegate, MoneyDelegate
from src.viewmodel.document_viewmodel import DocumentViewModel

STYLES_PATH = Path(__file__).with_name("styles.qss")


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: DocumentViewModel) -> None:
        super().__init__()
        self._vm = viewmodel
        self.setWindowTitle("Прийом(+) / відвантаження товару(−)")
        self.setMinimumSize(1020, 640)
        self.resize(1100, 720)
        self.setStyleSheet(STYLES_PATH.read_text(encoding="utf-8"))

        self._build_ui()
        self._vm.load()
        self._populate_lookups()
        self._bind()
        self._on_document_changed()
        self._on_total_changed(self._vm.formatted_total())
        self._on_position_changed(*self._vm.position)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 16)
        body_layout.setSpacing(16)
        body_layout.addWidget(self._build_document_card())
        body_layout.addWidget(self._build_spec_card(), stretch=1)
        root.addWidget(body, stretch=1)

        root.addWidget(self._build_footer())

        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("Готово")

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Прийом(+) / відвантаження товару(−)")
        title.setObjectName("appTitle")
        subtitle = QLabel("Навчальний приклад · PySide6 · SQLite · MVVM")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)

        layout.addLayout(titles)
        layout.addStretch()

        self.new_btn = QPushButton("Новий документ")
        self.new_btn.setObjectName("ghostButton")
        self.new_btn.setIcon(self._std_icon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        layout.addWidget(self.new_btn)
        return header

    def _build_document_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(14)

        caption = QLabel("ДОКУМЕНТ")
        caption.setObjectName("cardTitle")
        layout.addWidget(caption)

        fields = QHBoxLayout()
        fields.setSpacing(12)

        self.number_edit = QLineEdit()
        self.number_edit.setPlaceholderText("Наприклад, 15")
        fields.addLayout(self._labeled("Номер документу", self.number_edit), stretch=2)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())
        fields.addLayout(self._labeled("Дата", self.date_edit), stretch=2)

        self.firma_combo = QComboBox()
        fields.addLayout(self._labeled("Фірма", self.firma_combo), stretch=3)

        self.operation_combo = QComboBox()
        self.operation_combo.addItem("Прийом (+)", "+")
        self.operation_combo.addItem("Відвантаження (−)", "-")
        fields.addLayout(self._labeled("Операція", self.operation_combo), stretch=2)

        total_card = QFrame()
        total_card.setObjectName("totalCard")
        total_layout = QVBoxLayout(total_card)
        total_layout.setContentsMargins(16, 10, 16, 10)
        total_caption = QLabel("ЗАГАЛЬНА СУМА")
        total_caption.setObjectName("totalCaption")
        self.total_value = QLabel("0,00")
        self.total_value.setObjectName("totalValue")
        total_layout.addWidget(total_caption)
        total_layout.addWidget(self.total_value)
        fields.addWidget(total_card, stretch=2)

        layout.addLayout(fields)
        return card

    def _build_spec_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        caption = QLabel("СПЕЦИФІКАЦІЯ")
        caption.setObjectName("cardTitle")
        header.addWidget(caption)
        header.addStretch()

        self.add_row_btn = QPushButton("Додати рядок")
        self.remove_row_btn = QPushButton("Видалити рядок")
        header.addWidget(self.add_row_btn)
        header.addWidget(self.remove_row_btn)
        layout.addLayout(header)

        self.table = QTableView()
        self.table.setModel(self._vm.spec_model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        vertical = self.table.verticalHeader()
        vertical.setVisible(False)
        vertical.setMinimumSectionSize(40)
        vertical.setDefaultSectionSize(40)
        vertical.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.setItemDelegateForColumn(0, GoodsDelegate(self.table))
        self.table.setItemDelegateForColumn(1, MoneyDelegate(3, self.table))
        self.table.setItemDelegateForColumn(2, MoneyDelegate(2, self.table))
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setStretchLastSection(False)
        layout.addWidget(self.table)
        return card

    def _build_footer(self) -> QFrame:
        footer = QFrame()
        footer.setObjectName("footerBar")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(8)

        self.first_btn = self._nav_button(QStyle.StandardPixmap.SP_MediaSkipBackward, "Перший")
        self.prev_btn = self._nav_button(QStyle.StandardPixmap.SP_ArrowBack, "Попередній")
        self.position_label = QLabel("0 / 0")
        self.position_label.setObjectName("positionLabel")
        self.position_label.setMinimumWidth(72)
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = self._nav_button(QStyle.StandardPixmap.SP_ArrowForward, "Наступний")
        self.last_btn = self._nav_button(QStyle.StandardPixmap.SP_MediaSkipForward, "Останній")

        layout.addWidget(self.first_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.position_label)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.last_btn)
        layout.addStretch()

        self.search_btn = QPushButton("Пошук")
        self.search_btn.setIcon(self._std_icon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.save_btn = QPushButton("Зберегти")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setIcon(self._std_icon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.delete_btn = QPushButton("Видалити")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setIcon(self._std_icon(QStyle.StandardPixmap.SP_TrashIcon))

        layout.addWidget(self.search_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.delete_btn)
        return footer

    def _labeled(self, text: str, widget: QWidget) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(6)
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        box.addWidget(label)
        box.addWidget(widget)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return box

    def _nav_button(self, pixmap: QStyle.StandardPixmap, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setIcon(self._std_icon(pixmap))
        button.setToolTip(tooltip)
        button.setAutoRaise(False)
        button.setFixedSize(36, 36)
        button.setStyleSheet(
            "QToolButton { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; }"
            "QToolButton:hover { background: #F9FAFB; }"
            "QToolButton:disabled { color: #9CA3AF; background: #F3F4F6; }"
        )
        return button

    def _std_icon(self, pixmap: QStyle.StandardPixmap) -> QIcon:
        return self.style().standardIcon(pixmap)

    def _populate_lookups(self) -> None:
        self.firma_combo.blockSignals(True)
        self.firma_combo.clear()
        for firm in self._vm.firms:
            self.firma_combo.addItem(firm.firma, firm.kod_firma)
        self.firma_combo.blockSignals(False)

    def _bind(self) -> None:
        self._vm.documentChanged.connect(self._on_document_changed)
        self._vm.totalChanged.connect(self._on_total_changed)
        self._vm.positionChanged.connect(self._on_position_changed)
        self._vm.errorOccurred.connect(self._on_error)
        self._vm.infoOccurred.connect(self._on_info)

        self.number_edit.textEdited.connect(self._vm.set_number)
        self.date_edit.dateChanged.connect(self._on_date_changed)
        self.firma_combo.currentIndexChanged.connect(self._on_firma_changed)
        self.operation_combo.currentIndexChanged.connect(self._on_operation_changed)

        self.new_btn.clicked.connect(self._on_new)
        self.first_btn.clicked.connect(lambda: self._navigate(self._vm.go_first))
        self.prev_btn.clicked.connect(lambda: self._navigate(self._vm.go_previous))
        self.next_btn.clicked.connect(lambda: self._navigate(self._vm.go_next))
        self.last_btn.clicked.connect(lambda: self._navigate(self._vm.go_last))
        self.search_btn.clicked.connect(self._on_search)
        self.save_btn.clicked.connect(self._vm.save)
        self.delete_btn.clicked.connect(self._on_delete)
        self.add_row_btn.clicked.connect(self._vm.add_spec_row)
        self.remove_row_btn.clicked.connect(self._on_remove_row)

    def _on_document_changed(self) -> None:
        doc = self._vm.document
        widgets = (self.number_edit, self.date_edit, self.firma_combo, self.operation_combo)
        for widget in widgets:
            widget.blockSignals(True)

        self.number_edit.setText(doc.number_doc)
        self.date_edit.setDate(QDate(doc.date_doc.year, doc.date_doc.month, doc.date_doc.day))
        firma_index = self.firma_combo.findData(doc.kod_firma)
        self.firma_combo.setCurrentIndex(max(firma_index, 0))
        operation_index = self.operation_combo.findData(doc.operation)
        self.operation_combo.setCurrentIndex(max(operation_index, 0))

        for widget in widgets:
            widget.blockSignals(False)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for row in range(self._vm.spec_model.rowCount()):
            self.table.setRowHeight(row, 40)

    def _on_total_changed(self, text: str) -> None:
        self.total_value.setText(f"{text} грн")

    def _on_position_changed(self, current: int, total: int) -> None:
        if self._vm.is_new:
            self.position_label.setText("новий")
            self.first_btn.setEnabled(total > 0)
            self.prev_btn.setEnabled(total > 0)
            self.next_btn.setEnabled(False)
            self.last_btn.setEnabled(False)
            return
        self.position_label.setText(f"{current} / {total}")
        self.first_btn.setEnabled(current > 1)
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total)
        self.last_btn.setEnabled(current < total)

    def _on_date_changed(self, qdate: QDate) -> None:
        self._vm.set_date(date(qdate.year(), qdate.month(), qdate.day()))

    def _on_firma_changed(self, index: int) -> None:
        kod_firma = self.firma_combo.itemData(index)
        if kod_firma is not None:
            self._vm.set_firma(int(kod_firma))

    def _on_operation_changed(self, index: int) -> None:
        operation = self.operation_combo.itemData(index)
        if operation:
            self._vm.set_operation(str(operation))

    def _confirm_leave(self) -> bool:
        if not self._vm.is_dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Незбережені зміни",
            "Є незбережені зміни. Продовжити без збереження?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _navigate(self, action) -> None:
        if self._confirm_leave():
            action()

    def _on_new(self) -> None:
        if self._confirm_leave():
            self._vm.new_document()

    def _on_search(self) -> None:
        if not self._confirm_leave():
            return
        number, ok = QInputDialog.getText(self, "Пошук документа", "Номер документу:")
        if ok and number.strip():
            self._vm.search_by_number(number)

    def _on_delete(self) -> None:
        answer = QMessageBox.question(
            self,
            "Видалення",
            "Видалити поточний документ разом зі специфікацією?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._vm.delete_current()

    def _on_remove_row(self) -> None:
        index = self.table.currentIndex()
        row = index.row() if index.isValid() else self._vm.spec_model.rowCount() - 1
        self._vm.remove_spec_row(row)

    def _on_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 6000)
        QMessageBox.warning(self, "Увага", message)

    def _on_info(self, message: str) -> None:
        self.statusBar().showMessage(message, 4000)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._confirm_leave():
            event.accept()
        else:
            event.ignore()
