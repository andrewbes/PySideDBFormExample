"""Сутності доменної моделі (відповідають таблицям SQLite)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Firma:
    kod_firma: int
    firma: str


@dataclass(frozen=True)
class Goods:
    kod_goods: int
    goods: str


@dataclass
class SpecRow:
    """Рядок специфікації документа.

    KodSpec — сурогатний ключ (у схемі з рисунка його немає).
    Він потрібен, щоб зручно редагувати та видаляти окремі рядки.
    """

    kod_goods: Optional[int] = None
    quantity: float = 0.0
    cost: float = 0.0
    kod_spec: Optional[int] = None

    @property
    def amount(self) -> float:
        return round(self.quantity * self.cost, 2)


@dataclass
class Document:
    kod_doc: Optional[int] = None
    number_doc: str = ""
    date_doc: date = field(default_factory=date.today)
    kod_firma: Optional[int] = None
    operation: str = "+"
    specs: list[SpecRow] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(row.amount for row in self.specs), 2)
