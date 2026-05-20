# Inventory Management System

A desktop application built with PySide6 + PostgreSQL for managing items, issues, work orders, contractors, suppliers and more.

---

## Requirements

- Python 3.10+
- PostgreSQL (local or remote)

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

Make sure PostgreSQL is installed and running. Create a database:

```sql
CREATE DATABASE inventory;
```

You can use any PostgreSQL client (pgAdmin, psql, DBeaver etc.).

### 3. Run the app

```bash
python main.py
```

On first launch, a **DB Configuration dialog** will appear. Fill in:
- Host (e.g. `localhost`)
- Port (default: `5432`)
- Database name (e.g. `inventory`)
- Username / Password

The app will auto-create all required tables on first successful connection.

---

## Multi-device Setup

To use the same database from multiple machines:

1. Install PostgreSQL on one central machine (server).
2. In `postgresql.conf`, set: `listen_addresses = '*'`
3. In `pg_hba.conf`, allow connections from your network, e.g.:
   ```
   host    all    all    192.168.1.0/24    md5
   ```
4. On each client machine, run the app and enter the server's IP in the Host field.

---

## Project Structure

```
inventory_app/
├── db/
│   ├── models.py          # SQLAlchemy ORM models
│   └── connection.py      # DB init, session management
├── ui/
│   ├── main_dashboard.py  # Main hub window
│   ├── base_table_window.py
│   ├── dialogs/
│   │   └── db_config_dialog.py
│   └── windows/
│       ├── simple_tables.py       # Contractors, Customers, Suppliers, Item Groups, Item Classes
│       ├── items_window.py        # Items with grade management
│       ├── work_orders_window.py  # Work orders with multi contractor/customer
│       ├── employees_window.py    # Employee records
│       ├── issue_form_window.py   # The main issue form
│       └── issues_log_window.py   # View all submitted issues
└── utils/
    ├── theme.py            # Dark theme stylesheet
    └── widgets.py          # Reusable widgets (SearchableComboBox, StatCard etc.)
main.py                     # Entry point
requirements.txt
```

---

## Tables / Entities

| Table | Key Fields |
|-------|-----------|
| item_groups | id, name |
| item_classes | id, name, item_group_id |
| items | item_code (PK), item_name, unit_price, quantity_in_store |
| item_grades | id, item_code, grade, unit_price |
| contractors | id, name |
| customers | id, name |
| suppliers | id, name |
| work_orders | id, name ↔ many contractors, many customers |
| employees | emp_id (PK), first_name, last_name, dob, category |
| issues | id, timestamp, issue_date, item details, totals, FK references |

---

## Features

- **Searchable item selector** on the issue form — type item name to filter
- **Grade-aware pricing** — if a grade is selected, its price overrides base price
- **Stock deduction** — quantity_in_store decreases on issue submission
- **Work order smart fill** — if WO has 1 contractor/customer, auto-selects; if multiple, shows dropdown
- **Issues log** with date range filtering and text search
- **Dashboard stats** — live counts and total issued value
- **Dark theme** throughout

---

## Adding Fields in Future

- **New column on a table**: Add it to `db/models.py`, the table will be updated next run (or use `ALTER TABLE` in SQL for existing DBs).
- **New table**: Add model class to `models.py`, create a window following the `SimpleTableWindow` pattern.
- **New field on the issue form**: Add to `Issue` model + `issue_form_window.py`.

---

## Planned (not yet built)
- Login / authentication system (employee-based)
- Role-based access control (admin vs regular)
- Export issues to Excel/PDF
- Low stock alerts
