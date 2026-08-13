"""Делегати комірок таблиці: combobox товарів і числові поля."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QStyledItemDelegate, QWidget

from src.viewmodel.spec_table_model import SpecTableModel


class GoodsDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option, index) -> QWidget:  # noqa: N802
        combo = QComboBox(parent)
        combo.setFrame(False)
        model: SpecTableModel = index.model()
        combo.addItem("— оберіть товар —", None)
        for item in model.goods():
            combo.addItem(item.goods, item.kod_goods)
        return combo

    def setEditorData(self, editor: QComboBox, index) -> None:  # noqa: N802
        kod_goods = index.data(Qt.ItemDataRole.EditRole)
        position = editor.findData(kod_goods)
        editor.setCurrentIndex(max(position, 0))

    def setModelData(self, editor: QComboBox, model, index) -> None:  # noqa: N802
        model.setData(index, editor.currentData(), Qt.ItemDataRole.EditRole)


class MoneyDelegate(QStyledItemDelegate):
    def __init__(self, decimals: int = 2, parent=None) -> None:
        super().__init__(parent)
        self._decimals = decimals

    def createEditor(self, parent: QWidget, option, index) -> QWidget:  # noqa: N802
        spin = QDoubleSpinBox(parent)
        spin.setFrame(False)
        spin.setDecimals(self._decimals)
        spin.setMinimum(0)
        spin.setMaximum(1_000_000_000)
        spin.setGroupSeparatorShown(True)
        return spin

    def setEditorData(self, editor: QDoubleSpinBox, index) -> None:  # noqa: N802
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setValue(float(value or 0))

    def setModelData(self, editor: QDoubleSpinBox, model, index) -> None:  # noqa: N802
        model.setData(index, editor.value(), Qt.ItemDataRole.EditRole)
