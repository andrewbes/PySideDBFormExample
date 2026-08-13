"""Шар доступу до SQLite: підключення та CRUD для форми документа."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from src.model.entities import Document, Firma, Goods, SpecRow

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "warehouse.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tblFirma (
    KodFirma INTEGER PRIMARY KEY AUTOINCREMENT,
    Firma    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tblGoods (
    KodGoods INTEGER PRIMARY KEY AUTOINCREMENT,
    Goods    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tblDoc (
    KodDoc    INTEGER PRIMARY KEY AUTOINCREMENT,
    NumberDoc TEXT NOT NULL,
    DateDoc   TEXT NOT NULL,
    KodFirma  INTEGER NOT NULL,
    Operation TEXT NOT NULL CHECK (Operation IN ('+', '-')),
    FOREIGN KEY (KodFirma) REFERENCES tblFirma (KodFirma)
);

CREATE TABLE IF NOT EXISTS tblSpecification (
    KodSpec    INTEGER PRIMARY KEY AUTOINCREMENT,
    KodDoc     INTEGER NOT NULL,
    KodGoods   INTEGER NOT NULL,
    QuantGoods REAL    NOT NULL DEFAULT 0,
    CostGoods  REAL    NOT NULL DEFAULT 0,
    FOREIGN KEY (KodDoc)   REFERENCES tblDoc (KodDoc) ON DELETE CASCADE,
    FOREIGN KEY (KodGoods) REFERENCES tblGoods (KodGoods)
);
"""


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


class Database:
    """Репозиторій: єдина точка роботи з файлом SQLite."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self._conn.close()

    def init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def get_firms(self) -> list[Firma]:
        rows = self._conn.execute(
            "SELECT KodFirma, Firma FROM tblFirma ORDER BY Firma"
        ).fetchall()
        return [Firma(kod_firma=row["KodFirma"], firma=row["Firma"]) for row in rows]

    def get_goods(self) -> list[Goods]:
        rows = self._conn.execute(
            "SELECT KodGoods, Goods FROM tblGoods ORDER BY Goods"
        ).fetchall()
        return [Goods(kod_goods=row["KodGoods"], goods=row["Goods"]) for row in rows]

    def get_document_ids(self) -> list[int]:
        rows = self._conn.execute(
            "SELECT KodDoc FROM tblDoc ORDER BY DateDoc, KodDoc"
        ).fetchall()
        return [row["KodDoc"] for row in rows]

    def find_doc_id_by_number(self, number_doc: str) -> Optional[int]:
        row = self._conn.execute(
            "SELECT KodDoc FROM tblDoc WHERE NumberDoc = ? COLLATE NOCASE",
            (number_doc.strip(),),
        ).fetchone()
        return None if row is None else int(row["KodDoc"])

    def get_document(self, kod_doc: int) -> Optional[Document]:
        row = self._conn.execute(
            """
            SELECT KodDoc, NumberDoc, DateDoc, KodFirma, Operation
            FROM tblDoc
            WHERE KodDoc = ?
            """,
            (kod_doc,),
        ).fetchone()
        if row is None:
            return None

        spec_rows = self._conn.execute(
            """
            SELECT KodSpec, KodGoods, QuantGoods, CostGoods
            FROM tblSpecification
            WHERE KodDoc = ?
            ORDER BY KodSpec
            """,
            (kod_doc,),
        ).fetchall()

        specs = [
            SpecRow(
                kod_spec=item["KodSpec"],
                kod_goods=item["KodGoods"],
                quantity=float(item["QuantGoods"]),
                cost=float(item["CostGoods"]),
            )
            for item in spec_rows
        ]
        return Document(
            kod_doc=row["KodDoc"],
            number_doc=row["NumberDoc"],
            date_doc=_parse_date(row["DateDoc"]),
            kod_firma=row["KodFirma"],
            operation=row["Operation"],
            specs=specs,
        )

    def save_document(self, document: Document) -> int:
        """Вставляє новий або оновлює існуючий документ разом зі специфікацією."""
        try:
            if document.kod_doc is None:
                cursor = self._conn.execute(
                    """
                    INSERT INTO tblDoc (NumberDoc, DateDoc, KodFirma, Operation)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        document.number_doc,
                        document.date_doc.isoformat(),
                        document.kod_firma,
                        document.operation,
                    ),
                )
                kod_doc = int(cursor.lastrowid)
            else:
                kod_doc = document.kod_doc
                self._conn.execute(
                    """
                    UPDATE tblDoc
                    SET NumberDoc = ?, DateDoc = ?, KodFirma = ?, Operation = ?
                    WHERE KodDoc = ?
                    """,
                    (
                        document.number_doc,
                        document.date_doc.isoformat(),
                        document.kod_firma,
                        document.operation,
                        kod_doc,
                    ),
                )
                self._conn.execute(
                    "DELETE FROM tblSpecification WHERE KodDoc = ?",
                    (kod_doc,),
                )

            for spec in document.specs:
                if spec.kod_goods is None:
                    continue
                self._conn.execute(
                    """
                    INSERT INTO tblSpecification (KodDoc, KodGoods, QuantGoods, CostGoods)
                    VALUES (?, ?, ?, ?)
                    """,
                    (kod_doc, spec.kod_goods, spec.quantity, spec.cost),
                )

            self._conn.commit()
            return kod_doc
        except sqlite3.Error:
            self._conn.rollback()
            raise

    def delete_document(self, kod_doc: int) -> None:
        try:
            self._conn.execute("DELETE FROM tblDoc WHERE KodDoc = ?", (kod_doc,))
            self._conn.commit()
        except sqlite3.Error:
            self._conn.rollback()
            raise
