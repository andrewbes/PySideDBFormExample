"""ViewModel форми документа: навігація, збереження, підсумки."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QObject, Signal

from src.model.database import Database
from src.model.entities import Document, Firma, Goods
from src.viewmodel.spec_table_model import SpecTableModel, format_money


class DocumentViewModel(QObject):
    documentChanged = Signal()
    totalChanged = Signal(str)
    positionChanged = Signal(int, int)
    dirtyChanged = Signal(bool)
    errorOccurred = Signal(str)
    infoOccurred = Signal(str)

    def __init__(self, database: Database, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._db = database
        self._firms: list[Firma] = []
        self._goods: list[Goods] = []
        self._ids: list[int] = []
        self._index = -1
        self._document = Document()
        self._dirty = False
        self._loading = False

        self.spec_model = SpecTableModel(self)
        self.spec_model.specsMutated.connect(self._on_specs_mutated)

    @property
    def position(self) -> tuple[int, int]:
        current = 0 if self.is_new else self._index + 1
        return current, len(self._ids)

    @property
    def document(self) -> Document:
        return self._document

    @property
    def firms(self) -> list[Firma]:
        return self._firms

    @property
    def goods(self) -> list[Goods]:
        return self._goods

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def is_new(self) -> bool:
        return self._document.kod_doc is None

    def load(self) -> None:
        self._firms = self._db.get_firms()
        self._goods = self._db.get_goods()
        self.spec_model.set_goods(self._goods)
        self._ids = self._db.get_document_ids()
        if self._ids:
            self._show_at(len(self._ids) - 1)
        else:
            self.new_document()

    def new_document(self) -> None:
        self._loading = True
        default_firma = self._firms[0].kod_firma if self._firms else None
        self._document = Document(
            number_doc="",
            date_doc=date.today(),
            kod_firma=default_firma,
            operation="+",
        )
        self._index = len(self._ids)
        self.spec_model.set_rows(self._document.specs)
        self.spec_model.add_row()
        self._document.specs = self.spec_model.rows()
        self._loading = False
        self._set_dirty(False)
        self._emit_state()

    def go_first(self) -> None:
        if self._ids:
            self._show_at(0)

    def go_previous(self) -> None:
        if self._index > 0:
            self._show_at(self._index - 1)

    def go_next(self) -> None:
        if 0 <= self._index < len(self._ids) - 1:
            self._show_at(self._index + 1)

    def go_last(self) -> None:
        if self._ids:
            self._show_at(len(self._ids) - 1)

    def search_by_number(self, number: str) -> bool:
        kod_doc = self._db.find_doc_id_by_number(number)
        if kod_doc is None or kod_doc not in self._ids:
            self.errorOccurred.emit(f"Документ № {number.strip()} не знайдено.")
            return False
        self._show_at(self._ids.index(kod_doc))
        return True

    def set_number(self, value: str) -> None:
        if self._document.number_doc != value:
            self._document.number_doc = value
            self._set_dirty(True)

    def set_date(self, value: date) -> None:
        if self._document.date_doc != value:
            self._document.date_doc = value
            self._set_dirty(True)

    def set_firma(self, kod_firma: int) -> None:
        if self._document.kod_firma != kod_firma:
            self._document.kod_firma = kod_firma
            self._set_dirty(True)

    def set_operation(self, operation: str) -> None:
        if operation not in ("+", "-"):
            return
        if self._document.operation != operation:
            self._document.operation = operation
            self._set_dirty(True)
            self.documentChanged.emit()

    def add_spec_row(self) -> None:
        self.spec_model.add_row()
        self._set_dirty(True)

    def remove_spec_row(self, row: int) -> None:
        if self.spec_model.remove_row(row):
            self._set_dirty(True)

    def save(self) -> bool:
        if not self._document.number_doc.strip():
            self.errorOccurred.emit("Вкажіть номер документа.")
            return False
        if self._document.kod_firma is None:
            self.errorOccurred.emit("Оберіть фірму.")
            return False

        filled = [row for row in self.spec_model.rows() if row.kod_goods is not None]
        if not filled:
            self.errorOccurred.emit("Додайте хоча б один рядок специфікації.")
            return False

        self._document.specs = filled
        try:
            kod_doc = self._db.save_document(self._document)
        except Exception as exc:  # noqa: BLE001 — показуємо студенту текст помилки БД
            self.errorOccurred.emit(f"Не вдалося зберегти: {exc}")
            return False

        self._ids = self._db.get_document_ids()
        self._index = self._ids.index(kod_doc)
        loaded = self._db.get_document(kod_doc)
        if loaded is None:
            self.errorOccurred.emit("Документ збережено, але не вдалося його перечитати.")
            return False
        self._loading = True
        self._document = loaded
        self.spec_model.set_rows(self._document.specs)
        self._loading = False
        self._set_dirty(False)
        self._emit_state()
        self.infoOccurred.emit("Документ збережено.")
        return True

    def delete_current(self) -> bool:
        if self._document.kod_doc is None:
            self.new_document()
            return True
        try:
            self._db.delete_document(self._document.kod_doc)
        except Exception as exc:  # noqa: BLE001
            self.errorOccurred.emit(f"Не вдалося видалити: {exc}")
            return False

        self._ids = self._db.get_document_ids()
        if self._ids:
            self._show_at(min(self._index, len(self._ids) - 1))
        else:
            self._index = -1
            self.new_document()
        self.infoOccurred.emit("Документ видалено.")
        return True

    def formatted_total(self) -> str:
        return format_money(self.spec_model.total())

    def _show_at(self, index: int) -> None:
        kod_doc = self._ids[index]
        document = self._db.get_document(kod_doc)
        if document is None:
            self.errorOccurred.emit("Не вдалося завантажити документ.")
            return
        self._loading = True
        self._index = index
        self._document = document
        self.spec_model.set_rows(self._document.specs)
        self._loading = False
        self._set_dirty(False)
        self._emit_state()

    def _on_specs_mutated(self) -> None:
        self._document.specs = self.spec_model.rows()
        self.totalChanged.emit(self.formatted_total())
        if not self._loading:
            self._set_dirty(True)

    def _set_dirty(self, value: bool) -> None:
        if self._dirty != value:
            self._dirty = value
            self.dirtyChanged.emit(value)

    def _emit_state(self) -> None:
        self.documentChanged.emit()
        self.totalChanged.emit(self.formatted_total())
        current = 0 if self.is_new else self._index + 1
        total = len(self._ids)
        self.positionChanged.emit(current, total)
