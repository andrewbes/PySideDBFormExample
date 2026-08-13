#!/usr/bin/env python3
"""Створює SQLite-базу та наповнює її тестовими даними.

Запуск з кореня проєкту:
    python scripts/init_db.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model.database import DEFAULT_DB_PATH, SCHEMA_SQL  # noqa: E402


FIRMS = [
    "ТОВ «Агросвіт»",
    "ПП «Техноторг»",
    "ТОВ «Смак+»",
    "ФОП Коваленко І.П.",
]

GOODS = [
    "Борошно пшеничне, кг",
    "Цукор білий, кг",
    "Олія соняшникова, л",
    "Крупа гречана, кг",
    "Рис шліфований, кг",
    "Сіль кухонна, кг",
    "Молоко пастеризоване, л",
    "Яйця курячі, десяток",
]

# (номер, дата ISO, індекс фірми 1-based, операція, [(індекс товару, к-сть, ціна), ...])
DOCUMENTS = [
    (
        "15",
        "2008-04-13",
        1,
        "+",
        [
            (1, 50, 10.00),
            (3, 15, 500.00),
            (2, 20, 12.50),
        ],
    ),
    (
        "16",
        "2008-04-20",
        2,
        "-",
        [
            (4, 30, 18.40),
            (5, 25, 22.00),
        ],
    ),
    (
        "21",
        "2024-11-03",
        3,
        "+",
        [
            (7, 40, 32.90),
            (8, 12, 45.00),
            (6, 10, 8.50),
        ],
    ),
    (
        "22",
        "2025-02-14",
        1,
        "-",
        [
            (1, 10, 11.20),
            (2, 8, 14.00),
        ],
    ),
]


def create_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)

        conn.executemany("INSERT INTO tblFirma (Firma) VALUES (?)", [(name,) for name in FIRMS])
        conn.executemany("INSERT INTO tblGoods (Goods) VALUES (?)", [(name,) for name in GOODS])

        for number, date_doc, kod_firma, operation, specs in DOCUMENTS:
            cursor = conn.execute(
                """
                INSERT INTO tblDoc (NumberDoc, DateDoc, KodFirma, Operation)
                VALUES (?, ?, ?, ?)
                """,
                (number, date_doc, kod_firma, operation),
            )
            kod_doc = cursor.lastrowid
            conn.executemany(
                """
                INSERT INTO tblSpecification (KodDoc, KodGoods, QuantGoods, CostGoods)
                VALUES (?, ?, ?, ?)
                """,
                [(kod_doc, kod_goods, qty, cost) for kod_goods, qty, cost in specs],
            )

        conn.commit()
    finally:
        conn.close()


def main() -> None:
    create_database(DEFAULT_DB_PATH)
    print(f"Базу створено: {DEFAULT_DB_PATH}")
    print(f"  фірм: {len(FIRMS)}, товарів: {len(GOODS)}, документів: {len(DOCUMENTS)}")


if __name__ == "__main__":
    main()
