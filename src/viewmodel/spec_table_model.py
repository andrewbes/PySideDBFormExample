"""Qt-модель таблиці специфікації. Живе у ViewModel: рахує суму рядка."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor

from src.model.entities import Goods, SpecRow


class SpecTableModel(QAbstractTableModel):
    HEADERS = ["Товар", "Кількість", "Ціна за од.", "Сума"]

    specsMutated = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[SpecRow] = []
        self._goods: list[Goods] = []
        self._goods_by_id: dict[int, str] = {}

    def set_goods(self, goods: list[Goods]) -> None:
        self._goods = goods
        self._goods_by_id = {item.kod_goods: item.goods for item in goods}

    def goods(self) -> list[Goods]:
        return self._goods

    def set_rows(self, rows: list[SpecRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rows(self) -> list[SpecRow]:
        return self._rows

    def add_row(self) -> None:
        row_index = len(self._rows)
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self._rows.append(SpecRow())
        self.endInsertRows()
        self.specsMutated.emit()

    def remove_row(self, row: int) -> bool:
        if not (0 <= row < len(self._rows)):
            return False
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._rows[row]
        self.endRemoveRows()
        self.specsMutated.emit()
        return True

    def total(self) -> float:
        return round(sum(item.amount for item in self._rows), 2)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return 4

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        if orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() != 3:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        column = index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if column == 0:
                if role == Qt.ItemDataRole.EditRole:
                    return row.kod_goods
                if row.kod_goods is None:
                    return "— оберіть товар —"
                return self._goods_by_id.get(row.kod_goods, "—")
            if column == 1:
                if role == Qt.ItemDataRole.EditRole:
                    return row.quantity
                return format_number(row.quantity, 3)
            if column == 2:
                if role == Qt.ItemDataRole.EditRole:
                    return row.cost
                return format_money(row.cost)
            if column == 3:
                return format_money(row.amount)

        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor("#111827")

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if column == 0:
                return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            return int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        if role == Qt.ItemDataRole.UserRole and column == 0:
            return row.kod_goods

        return None

    def setData(  # noqa: N802
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        row = self._rows[index.row()]
        column = index.column()

        if column == 0:
            row.kod_goods = int(value) if value not in (None, "", 0) else None
            changed = [index]
        elif column == 1:
            row.quantity = _to_float(value)
            changed = [index, self.index(index.row(), 3)]
        elif column == 2:
            row.cost = _to_float(value)
            changed = [index, self.index(index.row(), 3)]
        else:
            return False

        for item in changed:
            self.dataChanged.emit(item, item)
        self.specsMutated.emit()
        return True


def _to_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def format_number(value: float, decimals: int) -> str:
    text = f"{value:,.{decimals}f}".replace(",", " ")
    text = text.replace(".", ",")
    if decimals > 2:
        text = text.rstrip("0").rstrip(",")
    return text or "0"


def format_money(value: float) -> str:
    return format_number(value, 2)
