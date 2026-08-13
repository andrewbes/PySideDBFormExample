"""Точка входу навчального додатку."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.model.database import DEFAULT_DB_PATH, Database
from src.view.main_window import MainWindow
from src.viewmodel.document_viewmodel import DocumentViewModel


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PySideDBFormExample")
    app.setOrganizationName("FormsExample")

    font = QFont()
    font.setFamily(".AppleSystemUIFont" if sys.platform == "darwin" else "Segoe UI")
    font.setPointSize(13)
    app.setFont(font)

    if not DEFAULT_DB_PATH.exists():
        QMessageBox.critical(
            None,
            "Немає бази даних",
            "Спочатку створіть базу тестовими даними:\n\npython scripts/init_db.py",
        )
        return 1

    database = Database(DEFAULT_DB_PATH)
    viewmodel = DocumentViewModel(database)
    window = MainWindow(viewmodel)
    window.show()
    try:
        return app.exec()
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
