# PySideDBFormExample

Навчальний проєкт: одна форма **«Прийом(+) / відвантаження товару(−)»** на **PySide6**, **SQLite** і архітектурі **MVVM**. Це не повноцінна облікова система, а демонстрація, як зв’язати довідники, документ і таблицю специфікації.

## Що показує форма

- шапка документа: номер, дата, фірма (з `tblFirma`), операція `+` / `−`
- таблиця специфікації: товар (з `tblGoods`), кількість, ціна, сума рядка
- загальна сума документа рахується автоматично
- навігація записами, пошук за номером, збереження і видалення

## Схема бази

Чотири таблиці (як на навчальній схемі):

```
tblFirma (1) ──< tblDoc (1) ──< tblSpecification >── (1) tblGoods
```

| Таблиця | Призначення | Поля |
| --- | --- | --- |
| `tblFirma` | Довідник фірм | `KodFirma`, `Firma` |
| `tblGoods` | Довідник товарів | `KodGoods`, `Goods` |
| `tblDoc` | Документ | `KodDoc`, `NumberDoc`, `DateDoc`, `KodFirma`, `Operation` |
| `tblSpecification` | Рядки документа | `KodDoc`, `KodGoods`, `QuantGoods`, `CostGoods` |

У `tblSpecification` додано сурогатний ключ `KodSpec`. У вихідній схемі його немає; він потрібен, щоб зручно редагувати й видаляти окремі рядки.

## Архітектура MVVM

```
View (PySide6)  ←сигнали/слоти→  ViewModel  ←CRUD→  Model (sqlite3)
     main_window.py               document_viewmodel.py    database.py
     delegates.py                 spec_table_model.py      entities.py
```

- **Model** — dataclasses і робота з SQLite без Qt-віджетів.
- **ViewModel** — поточний документ, навігація, валідація, розрахунок сум, `QAbstractTableModel` для сітки.
- **View** — вікно, стилі QSS, делегати combobox/чисел. Не звертається до SQL напряму.

## Структура проєкту

```
├── run.py                 # запуск форми
├── requirements.txt
├── scripts/init_db.py     # створення БД і тестових даних
├── data/warehouse.db      # з’являється після init_db.py (у git не потрапляє)
└── src/
    ├── main.py
    ├── model/
    ├── viewmodel/
    └── view/
```

## Запуск

Потрібні Python 3.11+ і Git.

```bash
python3.11 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python run.py
```

Повторний запуск `scripts/init_db.py` перестворює базу і знову заповнює її тестовими документами.

## Типовий сценарій для заняття

1. Відкрийте останній документ і пройдіться стрілками навігації.
2. Змініть кількість або ціну — сума рядка і «Загальна сума» оновляться одразу.
3. Додайте рядок, оберіть товар з довідника, збережіть документ.
4. Знайдіть документ за номером (наприклад, `15`) і видаліть тестовий запис.

## Ліцензія

Навчальний приклад, можна вільно використовувати й змінювати.
